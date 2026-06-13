from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from groups.models import Group, GroupMembership
from .models import Expense, ExpenseSplit, Settlement, CurrencyRate
from .serializers import (
    ExpenseSerializer, ExpenseCreateSerializer,
    SettlementSerializer, SettlementCreateSerializer,
    CurrencyRateSerializer,
)
from .split_engine import compute_splits
from .balance_engine import get_group_balances, simplify_debts, get_user_balance_breakdown


def get_user_group(request, group_id):
    """Return group if user is active member, else error response."""
    try:
        group = Group.objects.get(id=group_id)
        if not group.memberships.filter(user=request.user, is_active=True).exists():
            return None, Response(
                {'detail': 'You are not a member of this group.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return group, None
    except Group.DoesNotExist:
        return None, Response({'detail': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)


# ============================================================
# Expense Endpoints
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expense_list_create(request, group_id):
    """
    GET  /api/expenses/<group_id>/    — list all expenses for a group
    POST /api/expenses/<group_id>/    — create a new expense
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    if request.method == 'GET':
        expenses = group.expenses.filter(is_settlement=False).prefetch_related('splits__user').select_related('paid_by')
        # Optional filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        paid_by = request.query_params.get('paid_by')
        if start_date:
            expenses = expenses.filter(expense_date__gte=start_date)
        if end_date:
            expenses = expenses.filter(expense_date__lte=end_date)
        if paid_by:
            expenses = expenses.filter(paid_by__username__iexact=paid_by)
        return Response(ExpenseSerializer(expenses, many=True).data)

    # POST — create expense
    serializer = ExpenseCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated = serializer.validated_data
    payer_username = validated.get('paid_by_username') or request.user.username
    split_with_usernames = validated.get('split_with', [])
    split_details_raw = validated.get('split_details', {})

    try:
        payer = User.objects.get(username__iexact=payer_username)
    except User.DoesNotExist:
        return Response({'detail': f'Payer user "{payer_username}" not found.'}, status=status.HTTP_400_BAD_REQUEST)

    # Resolve participants
    participants = []
    for uname in split_with_usernames:
        try:
            participants.append(User.objects.get(username__iexact=uname))
        except User.DoesNotExist:
            return Response({'detail': f'User "{uname}" not found.'}, status=status.HTTP_400_BAD_REQUEST)

    if not participants:
        return Response({'detail': 'split_with must include at least one user.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create expense
    expense = Expense.objects.create(
        group=group,
        paid_by=payer,
        description=validated['description'],
        amount=validated['amount'],
        currency=validated.get('currency', 'INR'),
        split_type=validated.get('split_type', 'equal'),
        expense_date=validated['expense_date'],
        notes=validated.get('notes', ''),
        is_settlement=validated.get('is_settlement', False),
    )

    # Compute and save splits
    try:
        participant_ids = [u.id for u in participants]
        # Ensure payer is in participants (they also have a share)
        if payer.id not in participant_ids:
            participant_ids.insert(0, payer.id)
            participants.insert(0, payer)

        # Map username keys in split_details to user IDs
        if split_details_raw:
            user_map = {u.username.lower(): u.id for u in participants}
            split_details_by_id = {}
            for key, val in split_details_raw.items():
                uid = user_map.get(key.lower())
                if uid:
                    split_details_by_id[uid] = val
        else:
            split_details_by_id = {}

        # Put payer first so they get the rounding remainder
        if payer.id in participant_ids:
            participant_ids.remove(payer.id)
        participant_ids.insert(0, payer.id)

        splits = compute_splits(expense, participant_ids, split_details_by_id or None)

        ExpenseSplit.objects.bulk_create([
            ExpenseSplit(
                expense=expense,
                user_id=uid,
                share_amount=amount,
                share_value=split_details_by_id.get(uid),
            )
            for uid, amount in splits.items()
        ])
    except (ValueError, Exception) as e:
        expense.delete()  # rollback
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)



@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def expense_detail(request, group_id, expense_id):
    """
    GET    — expense detail with full split breakdown
    PATCH  — update expense (recalculates splits)
    DELETE — delete expense
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    try:
        expense = group.expenses.get(id=expense_id)
    except Expense.DoesNotExist:
        return Response({'detail': 'Expense not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ExpenseSerializer(expense).data)

    if request.method == 'DELETE':
        expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH — partial update (only notes/description for now; amount changes require re-import)
    allowed_fields = {'description', 'notes', 'expense_date'}
    update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
    for field, value in update_data.items():
        setattr(expense, field, value)
    expense.save()
    return Response(ExpenseSerializer(expense).data)


# ============================================================
# Balance Endpoints
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_balances(request, group_id):
    """
    GET /api/expenses/<group_id>/balances/
    Returns net balance per member + simplified debt transactions.
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    balances = get_group_balances(group)
    transactions = simplify_debts(balances)

    # Format for response
    balance_list = [
        {
            'user_id': uid,
            'username': data['user'].username if data['user'] else str(uid),
            'balance': str(data['balance']),
            'owed_to_you': str(data['owed_to_you']),
            'you_owe': str(data['you_owe']),
        }
        for uid, data in balances.items()
    ]

    tx_list = []
    for tx in transactions:
        from_user = balances.get(tx['from_user_id'], {}).get('user')
        to_user = balances.get(tx['to_user_id'], {}).get('user')
        tx_list.append({
            'from_user_id': tx['from_user_id'],
            'from_username': from_user.username if from_user else str(tx['from_user_id']),
            'to_user_id': tx['to_user_id'],
            'to_username': to_user.username if to_user else str(tx['to_user_id']),
            'amount': str(tx['amount']),
            'currency': 'INR',
        })

    return Response({
        'balances': balance_list,
        'simplified_transactions': tx_list,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_balance_breakdown(request, group_id):
    """
    GET /api/expenses/<group_id>/balances/breakdown/
    Returns expense-by-expense breakdown for current user.
    Addresses Rohan's requirement: show exactly which expenses make up the balance.
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    breakdown = get_user_balance_breakdown(group, request.user)
    return Response({'breakdown': breakdown})


# ============================================================
# Settlement Endpoints
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def settlement_list_create(request, group_id):
    """
    GET  — list all settlements for a group
    POST — record a new settlement payment
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    if request.method == 'GET':
        settlements = group.settlements.select_related('paid_by', 'paid_to').order_by('-settlement_date')
        return Response(SettlementSerializer(settlements, many=True).data)

    serializer = SettlementCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    paid_to_username = data.pop('paid_to_username')

    try:
        paid_to = User.objects.get(username__iexact=paid_to_username)
    except User.DoesNotExist:
        return Response({'detail': f'User "{paid_to_username}" not found.'}, status=status.HTTP_404_NOT_FOUND)

    if paid_to == request.user:
        return Response({'detail': 'You cannot settle with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

    settlement = Settlement.objects.create(
        group=group,
        paid_by=request.user,
        paid_to=paid_to,
        **data,
    )
    return Response(SettlementSerializer(settlement).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def settlement_detail(request, group_id, settlement_id):
    """DELETE /api/expenses/<group_id>/settlements/<id>/ — delete a settlement"""
    group, err = get_user_group(request, group_id)
    if err:
        return err

    try:
        settlement = group.settlements.get(id=settlement_id)
    except Settlement.DoesNotExist:
        return Response({'detail': 'Settlement not found.'}, status=status.HTTP_404_NOT_FOUND)

    if settlement.paid_by != request.user:
        return Response({'detail': 'Only the payer can delete a settlement.'}, status=status.HTTP_403_FORBIDDEN)

    settlement.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# Currency Rate Endpoint
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exchange_rate(request):
    """
    GET /api/expenses/exchange-rate/?from=USD&to=INR
    Fetch live exchange rate and return it.
    """
    from_currency = request.query_params.get('from', 'USD').upper()
    to_currency = request.query_params.get('to', 'INR').upper()
    rate = CurrencyRate.get_rate(from_currency, to_currency)
    return Response({
        'from_currency': from_currency,
        'to_currency': to_currency,
        'rate': str(rate),
    })

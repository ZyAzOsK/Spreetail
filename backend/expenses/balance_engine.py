"""
Balance calculation engine.

Computes net balances for each member, simplified debt graph,
and supports drill-down to see which expenses make up a balance.

Key design decisions:
- All amounts converted to INR for balance calculations
- Membership dates respected: expenses only affect members active on that date
- Debt simplification: minimize number of transactions using greedy algorithm
"""
from decimal import Decimal
from collections import defaultdict

from .models import Expense, ExpenseSplit, Settlement, CurrencyRate


def get_group_balances(group):
    """
    Calculate net balance for each user in the group.
    Positive balance = others owe this user money.
    Negative balance = this user owes money.

    Returns:
        {user_id: {'user': User, 'balance': Decimal, 'owed_to_you': Decimal, 'you_owe': Decimal}}
    """
    from django.contrib.auth.models import User

    balances = defaultdict(Decimal)  # user_id -> net balance in INR

    # Process all expense splits
    expenses = Expense.objects.filter(
        group=group, is_settlement=False
    ).prefetch_related('splits', 'splits__user').select_related('paid_by')

    for expense in expenses:
        amount_inr = expense.amount_in_inr
        payer_id = expense.paid_by_id

        for split in expense.splits.all():
            split_user_id = split.user_id
            # Convert split amount to INR
            if expense.currency == 'INR':
                split_inr = split.share_amount
            else:
                rate = CurrencyRate.get_rate(expense.currency, 'INR', expense.expense_date)
                split_inr = (split.share_amount * rate).quantize(Decimal('0.01'))

            if split_user_id != payer_id:
                # split_user owes payer
                balances[payer_id] += split_inr       # payer is owed this
                balances[split_user_id] -= split_inr   # split_user owes this

    # Process settlements
    settlements = Settlement.objects.filter(group=group)
    for s in settlements:
        if s.currency == 'INR':
            amount_inr = s.amount
        else:
            rate = CurrencyRate.get_rate(s.currency, 'INR', s.settlement_date)
            amount_inr = (s.amount * rate).quantize(Decimal('0.01'))

        # paid_by settled their debt: reduce what they owe
        balances[s.paid_by_id] += amount_inr
        balances[s.paid_to_id] -= amount_inr

    # Gather all involved users
    all_user_ids = set(balances.keys())
    users = {u.id: u for u in __import__('django.contrib.auth', fromlist=['models']).models.User.objects.filter(id__in=all_user_ids)}

    result = {}
    for uid, bal in balances.items():
        result[uid] = {
            'user': users.get(uid),
            'user_id': uid,
            'balance': bal,
            'owed_to_you': bal if bal > 0 else Decimal('0'),
            'you_owe': abs(bal) if bal < 0 else Decimal('0'),
        }

    return result


def simplify_debts(balances):
    """
    Debt simplification using greedy algorithm.
    Minimizes the number of transactions needed to settle all debts.

    balances: {user_id: Decimal net_balance}
    Returns: list of {'from_user_id': id, 'to_user_id': id, 'amount': Decimal}
    """
    creditors = []  # people owed money (positive balance)
    debtors = []    # people who owe money (negative balance)

    for uid, data in balances.items():
        bal = data['balance']
        if bal > Decimal('0.01'):
            creditors.append([uid, bal])
        elif bal < Decimal('-0.01'):
            debtors.append([uid, abs(bal)])

    # Sort by amount descending for greedy matching
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    transactions = []
    i, j = 0, 0

    while i < len(creditors) and j < len(debtors):
        creditor_id, credit = creditors[i]
        debtor_id, debt = debtors[j]

        amount = min(credit, debt)
        amount = amount.quantize(Decimal('0.01'))

        if amount > Decimal('0.00'):
            transactions.append({
                'from_user_id': debtor_id,
                'to_user_id': creditor_id,
                'amount': amount,
            })

        creditors[i][1] -= amount
        debtors[j][1] -= amount

        if creditors[i][1] < Decimal('0.01'):
            i += 1
        if debtors[j][1] < Decimal('0.01'):
            j += 1

    return transactions


def get_expense_breakdown(expense):
    """
    For a single expense, return how much each participant owes/paid.
    Used for Rohan's requirement: "I want to see exactly which expenses make that up."
    """
    splits = expense.splits.all().select_related('user')
    return {
        'expense_id': expense.id,
        'description': expense.description,
        'date': expense.expense_date,
        'total': expense.amount,
        'currency': expense.currency,
        'paid_by': expense.paid_by.username,
        'splits': [
            {
                'user': s.user.username,
                'user_id': s.user_id,
                'amount': s.share_amount,
                'is_payer': s.user_id == expense.paid_by_id,
            }
            for s in splits
        ]
    }


def get_user_balance_breakdown(group, user):
    """
    Get the list of expenses that contribute to a specific user's balance.
    Answers Rohan's question: "If the app says I owe X, show me which expenses."
    """
    from django.db.models import Q
    expenses = Expense.objects.filter(
        group=group,
        is_settlement=False,
    ).filter(
        Q(paid_by=user) | Q(splits__user=user)
    ).distinct().prefetch_related('splits', 'splits__user').select_related('paid_by')

    breakdown = []
    for expense in expenses:
        user_split = expense.splits.filter(user=user).first()
        if not user_split:
            continue

        if expense.currency == 'INR':
            split_inr = user_split.share_amount
        else:
            rate = CurrencyRate.get_rate(expense.currency, 'INR', expense.expense_date)
            split_inr = (user_split.share_amount * rate).quantize(Decimal('0.01'))

        is_payer = expense.paid_by_id == user.id
        if is_payer:
            # User paid — others owe them
            net_for_user = expense.amount_in_inr - split_inr
        else:
            # User owes the payer
            net_for_user = -split_inr

        breakdown.append({
            'expense_id': expense.id,
            'description': expense.description,
            'date': str(expense.expense_date),
            'total': str(expense.amount),
            'currency': expense.currency,
            'paid_by': expense.paid_by.username,
            'your_share': str(split_inr),
            'you_paid': is_payer,
            'net_effect': str(net_for_user),  # positive = good for you, negative = you owe
        })

    settlements = Settlement.objects.filter(
        group=group
    ).filter(
        Q(paid_by=user) | Q(paid_to=user)
    ).select_related('paid_by', 'paid_to')

    for s in settlements:
        if s.currency == 'INR':
            amount_inr = s.amount
        else:
            rate = CurrencyRate.get_rate(s.currency, 'INR', s.settlement_date)
            amount_inr = (s.amount * rate).quantize(Decimal('0.01'))

        is_payer = s.paid_by_id == user.id
        net_for_user = amount_inr if is_payer else -amount_inr

        breakdown.append({
            'expense_id': f'settlement_{s.id}',
            'description': f'Settlement: {s.paid_by.username} → {s.paid_to.username}',
            'date': str(s.settlement_date),
            'total': str(s.amount),
            'currency': s.currency,
            'paid_by': s.paid_by.username,
            'your_share': '0.00',
            'you_paid': is_payer,
            'net_effect': str(net_for_user),
        })

    # Sort the breakdown chronologically
    breakdown.sort(key=lambda x: x['date'], reverse=True)

    return breakdown

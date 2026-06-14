"""
Importer API views.

Flow:
  Step 1 — POST /api/import/<group_id>/upload/
    Upload CSV → parse → save ImportReport(status=pending) + ImportAnomaly rows
    Returns: import_report_id, parsed rows, anomaly summary

  Step 2 — GET /api/import/<group_id>/reports/<report_id>/
    Returns the saved report with all anomalies for review UI

  Step 3 — PATCH /api/import/<group_id>/reports/<report_id>/anomalies/<anomaly_id>/
    User resolves an anomaly (approve/skip/modify)

  Step 4 — POST /api/import/<group_id>/reports/<report_id>/finalize/
    Applies resolved data: creates Expense + ExpenseSplit records
    Returns summary of what was created vs skipped
"""
import json
from datetime import datetime, timezone
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from groups.models import Group, GroupMembership
from expenses.models import Expense, ExpenseSplit, Settlement, CurrencyRate
from expenses.split_engine import compute_splits
from .models import ImportReport, ImportAnomaly
from .parser import parse_csv, rows_to_serializable, normalize_name
from .serializers import ImportReportSerializer, ImportAnomalySerializer


def get_user_group(request, group_id):
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


# =====================================================================
# Step 1: Upload & Parse
# =====================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_csv(request, group_id):
    """
    POST /api/import/<group_id>/upload/
    Accepts multipart CSV file upload.
    Parses the CSV, detects anomalies, saves an ImportReport + anomalies.
    Returns the report_id and parsed preview data.
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    if 'file' not in request.FILES:
        return Response({'detail': 'No file uploaded. Send a CSV as "file".'}, status=status.HTTP_400_BAD_REQUEST)

    uploaded = request.FILES['file']
    if not uploaded.name.endswith('.csv'):
        return Response({'detail': 'Only .csv files are accepted.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        csv_text = uploaded.read().decode('utf-8-sig')  # handle BOM
    except UnicodeDecodeError:
        return Response({'detail': 'Could not decode file. Make sure it is UTF-8 encoded.'}, status=status.HTTP_400_BAD_REQUEST)

    # Get group members for validation (include all, not just active, to know historical dates)
    all_memberships = group.memberships.select_related('user')
    membership_timeline = {}
    for m in all_memberships:
        membership_timeline[m.user.username.title()] = {
            'joined_at': m.joined_at,
            'left_at': m.left_at,
        }

    # Parse CSV
    parsed_rows = parse_csv(csv_text, membership_timeline=membership_timeline)
    serializable = rows_to_serializable(parsed_rows)

    # Count stats
    total = len(parsed_rows)
    needs_review = sum(1 for r in parsed_rows if r.needs_review and not r.skip)
    auto_ok = sum(1 for r in parsed_rows if not r.needs_review and r.is_valid and not r.skip)
    skipped = sum(1 for r in parsed_rows if r.skip)

    # Save ImportReport
    report = ImportReport.objects.create(
        group=group,
        imported_by=request.user,
        file_name=uploaded.name,
        status='in_review',
        total_rows=total,
        raw_csv_content=csv_text,
        anomaly_count=sum(len(r.anomalies) for r in parsed_rows),
    )

    # Save anomalies to DB for review
    anomaly_objs = []
    for row in parsed_rows:
        for anomaly in row.anomalies:
            anomaly_objs.append(ImportAnomaly(
                import_report=report,
                row_number=row.row_number,
                anomaly_type=anomaly.anomaly_type,
                severity=anomaly.severity,
                field_name=anomaly.field_name,
                description=anomaly.description,
                original_value=anomaly.original_value,
                suggested_value=anomaly.suggested_value,
                suggested_action=anomaly.suggested_action,
                resolution='auto_fixed' if anomaly.auto_fixed else 'pending',
            ))
    ImportAnomaly.objects.bulk_create(anomaly_objs)

    # Store parsed row data as JSON in the report so finalize can use it
    report.raw_csv_content = json.dumps({
        'original_csv': csv_text,
        'parsed_rows': serializable,
    })
    report.save()

    return Response({
        'report_id': report.id,
        'file_name': uploaded.name,
        'total_rows': total,
        'auto_ok': auto_ok,
        'needs_review': needs_review,
        'skipped': skipped,
        'anomaly_count': report.anomaly_count,
        'rows': serializable,
    }, status=status.HTTP_201_CREATED)


# =====================================================================
# Step 2: Get Report for Review
# =====================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_report(request, group_id, report_id):
    """
    GET /api/import/<group_id>/reports/<report_id>/
    Returns the import report + all anomalies.
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    try:
        report = ImportReport.objects.get(id=report_id, group=group)
    except ImportReport.DoesNotExist:
        return Response({'detail': 'Import report not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Parse stored rows back
    try:
        stored = json.loads(report.raw_csv_content)
        rows = stored.get('parsed_rows', [])
    except (json.JSONDecodeError, TypeError):
        rows = []

    anomalies = report.anomalies.all()

    return Response({
        'report': ImportReportSerializer(report).data,
        'anomalies': ImportAnomalySerializer(anomalies, many=True).data,
        'rows': rows,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_reports(request, group_id):
    """
    GET /api/import/<group_id>/reports/
    List all import reports for a group.
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    reports = group.import_reports.all()
    return Response(ImportReportSerializer(reports, many=True).data)


# =====================================================================
# Step 3: Resolve Anomaly
# =====================================================================

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def resolve_anomaly(request, group_id, report_id, anomaly_id):
    """
    PATCH /api/import/<group_id>/reports/<report_id>/anomalies/<anomaly_id>/
    Body: { resolution: 'user_approved'|'skipped'|'user_modified', resolved_value: '...', user_notes: '...' }
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    try:
        anomaly = ImportAnomaly.objects.get(id=anomaly_id, import_report__id=report_id)
    except ImportAnomaly.DoesNotExist:
        return Response({'detail': 'Anomaly not found.'}, status=status.HTTP_404_NOT_FOUND)

    resolution = request.data.get('resolution')
    if resolution not in ('user_approved', 'skipped', 'user_modified', 'auto_fixed'):
        return Response({'detail': 'Invalid resolution. Use user_approved, skipped, or user_modified.'}, status=status.HTTP_400_BAD_REQUEST)

    anomaly.resolution = resolution
    anomaly.resolved_value = request.data.get('resolved_value', anomaly.suggested_value)
    anomaly.user_notes = request.data.get('user_notes', '')
    anomaly.resolved_at = datetime.now(timezone.utc)
    anomaly.save()

    return Response(ImportAnomalySerializer(anomaly).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_all_auto(request, group_id, report_id):
    """
    POST /api/import/<group_id>/reports/<report_id>/approve-auto/
    Auto-approve all anomalies that were already auto-fixed.
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    try:
        report = ImportReport.objects.get(id=report_id, group=group)
    except ImportReport.DoesNotExist:
        return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

    now = datetime.now(timezone.utc)
    updated = report.anomalies.filter(resolution='auto_fixed').update(
        resolution='auto_fixed', resolved_at=now
    )
    return Response({'approved_count': updated})


# =====================================================================
# Step 4: Finalize Import
# =====================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalize_import(request, group_id, report_id):
    """
    POST /api/import/<group_id>/reports/<report_id>/finalize/
    Body: { row_decisions: { row_number: 'import'|'skip'|'settlement' } }

    Creates Expense/Settlement records for approved rows.
    Skips rows where decision='skip' or that have unresolved critical errors.
    """
    group, err = get_user_group(request, group_id)
    if err:
        return err

    try:
        report = ImportReport.objects.get(id=report_id, group=group)
    except ImportReport.DoesNotExist:
        return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

    if report.status == 'completed':
        return Response({'detail': 'This import has already been completed.'}, status=status.HTTP_400_BAD_REQUEST)

    # Get stored parsed rows
    try:
        stored = json.loads(report.raw_csv_content)
        rows = stored.get('parsed_rows', [])
    except (json.JSONDecodeError, TypeError):
        return Response({'detail': 'Import data not found. Please re-upload the file.'}, status=status.HTTP_400_BAD_REQUEST)

    # Get per-row decisions from request
    row_decisions = request.data.get('row_decisions', {})
    # Convert keys to int
    row_decisions = {int(k): v for k, v in row_decisions.items()}

    # Get group members (user objects)
    member_map = {}
    for m in group.memberships.select_related('user'):
        member_map[m.user.username.lower()] = m.user
        member_map[m.user.username.title().lower()] = m.user

    created_expenses = 0
    created_settlements = 0
    skipped_rows = 0
    errors = []

    for row_data in rows:
        row_num = row_data['row_number']
        decision = row_decisions.get(row_num, 'auto')

        # Skip logic
        if row_data.get('skip'):
            skipped_rows += 1
            continue

        if decision == 'skip':
            skipped_rows += 1
            continue

        # Require valid data for import
        if not row_data.get('is_valid') and decision not in ('import', 'settlement'):
            skipped_rows += 1
            continue

        is_settlement = decision == 'settlement' or row_data.get('is_settlement', False) and decision != 'import'

        expense_date_str = row_data.get('date')
        if not expense_date_str:
            errors.append(f'Row {row_num}: No valid date. Skipped.')
            skipped_rows += 1
            continue

        try:
            from datetime import date
            expense_date = date.fromisoformat(expense_date_str)
        except ValueError:
            errors.append(f'Row {row_num}: Invalid date "{expense_date_str}". Skipped.')
            skipped_rows += 1
            continue

        # Resolve paid_by
        paid_by_name = (row_data.get('paid_by_normalized') or row_data.get('paid_by', '')).strip()
        payer = member_map.get(paid_by_name.lower())
        if not payer:
            payer, _ = User.objects.get_or_create(username__iexact=paid_by_name, defaults={'username': paid_by_name})
            GroupMembership.objects.get_or_create(
                group=group, user=payer,
                defaults={'joined_at': expense_date, 'is_active': True}
            )
            member_map[paid_by_name.lower()] = payer
        else:
            membership = group.memberships.filter(user=payer).first()
            if membership and membership.joined_at > expense_date:
                membership.joined_at = expense_date
                membership.save()

        # === SETTLEMENT ===
        if is_settlement:
            split_with = row_data.get('split_with', [])
            paid_to_name = split_with[0].strip() if split_with else None
            paid_to = None
            if paid_to_name:
                paid_to = member_map.get(paid_to_name.lower())
                if not paid_to:
                    paid_to, _ = User.objects.get_or_create(username__iexact=paid_to_name, defaults={'username': paid_to_name})
                    GroupMembership.objects.get_or_create(
                        group=group, user=paid_to,
                        defaults={'joined_at': expense_date, 'is_active': True}
                    )
                    member_map[paid_to_name.lower()] = paid_to
                else:
                    membership = group.memberships.filter(user=paid_to).first()
                    if membership and membership.joined_at > expense_date:
                        membership.joined_at = expense_date
                        membership.save()

            if payer and paid_to and row_data.get('amount'):
                Settlement.objects.create(
                    group=group,
                    paid_by=payer,
                    paid_to=paid_to,
                    amount=Decimal(row_data['amount']),
                    currency=row_data.get('currency', 'INR'),
                    settlement_date=expense_date,
                    notes=f'[Imported] {row_data.get("notes", "")}',
                )
                created_settlements += 1
            else:
                errors.append(f'Row {row_num}: Could not create settlement. Skipped.')
                skipped_rows += 1
            continue

        # === EXPENSE ===
        try:
            amount = Decimal(row_data['amount'])
        except (InvalidError := Exception, KeyError, TypeError):
            errors.append(f'Row {row_num}: Invalid amount. Skipped.')
            skipped_rows += 1
            continue

        expense = Expense.objects.create(
            group=group,
            paid_by=payer,
            description=row_data['description'],
            amount=amount,
            currency=row_data.get('currency', 'INR'),
            split_type=row_data.get('split_type', 'equal'),
            expense_date=expense_date,
            notes=f'[Imported] {row_data.get("notes", "")}',
            import_row_number=row_num,
            is_settlement=False,
        )

        # Resolve split_with members
        split_with_names = row_data.get('split_with', [])
        participants = []
        for name in split_with_names:
            u = member_map.get(name.lower())
            if u:
                membership = group.memberships.filter(user=u).first()
                if membership and membership.joined_at > expense_date:
                    membership.joined_at = expense_date
                    membership.save()
                participants.append(u)
            else:
                # Auto-create guest/unknown
                u, _ = User.objects.get_or_create(username__iexact=name.strip(), defaults={'username': name.strip()})
                GroupMembership.objects.get_or_create(
                    group=group, user=u,
                    defaults={'joined_at': expense_date, 'is_active': True}
                )
                member_map[name.strip().lower()] = u
                participants.append(u)

        if not participants:
            participants = [payer]

        participant_ids = [u.id for u in participants]
        if payer.id not in participant_ids:
            participant_ids.insert(0, payer.id)
            participants.insert(0, payer)
        else:
            participant_ids.remove(payer.id)
            participant_ids.insert(0, payer.id)

        # Build split_details_by_id
        split_details_raw = row_data.get('split_details', {})
        split_details_by_id = {}
        if split_details_raw:
            for uname, val in split_details_raw.items():
                u = member_map.get(uname.lower())
                if u:
                    split_details_by_id[u.id] = Decimal(str(val))

        try:
            splits = compute_splits(expense, participant_ids, split_details_by_id or None)
            ExpenseSplit.objects.bulk_create([
                ExpenseSplit(
                    expense=expense,
                    user_id=uid,
                    share_amount=share,
                    share_value=split_details_by_id.get(uid),
                )
                for uid, share in splits.items()
            ])
            created_expenses += 1
        except Exception as e:
            expense.delete()
            errors.append(f'Row {row_num}: Split calculation failed — {e}. Skipped.')
            skipped_rows += 1

    # Update report
    report.status = 'completed'
    report.successful_rows = created_expenses + created_settlements
    report.skipped_rows = skipped_rows
    report.completed_at = datetime.now(timezone.utc)
    report.save()

    return Response({
        'status': 'completed',
        'created_expenses': created_expenses,
        'created_settlements': created_settlements,
        'skipped_rows': skipped_rows,
        'errors': errors,
        'report_id': report.id,
    })

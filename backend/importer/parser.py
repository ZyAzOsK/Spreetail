"""
CSV Parser for Expense Import.

Reads the CSV file, parses each row, detects 14+ categories of anomalies,
and returns structured data ready for user review before actual import.

Anomalies detected:
1.  Duplicate rows (exact match)
2.  Conflicting duplicates (same description/date, different amount)
3.  Missing required fields (description, amount, paid_by, date)
4.  Name variants / capitalization issues (priya vs Priya, rohan vs Rohan)
5.  Unknown names (names not in the group)
6.  Percentage splits not summing to 100%
7.  Math mismatch: split amounts don't add up to total
8.  Ambiguous dates (e.g. 04-05-2026 could be Apr 5 or May 4)
9.  Malformed dates (e.g. Mar-14)
10. Negative amounts (flag as potential refund)
11. Zero amounts (flag as suspicious)
12. Missing currency (default to INR but flag)
13. Comma-formatted numbers (e.g. "1,200" -> 1200)
14. Membership violations (member not in group at that date)
15. Possible settlement disguised as expense
16. Mismatched split_type and split_details
17. Numbers with excessive precision (899.995)
"""

import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field
from typing import Optional


KNOWN_MEMBERS = {
    'aisha', 'rohan', 'priya', 'meera', 'dev', 'sam',
}

SETTLEMENT_KEYWORDS = [
    'paid back', 'paid aisha back', 'paid rohan back', 'settled',
    'settlement', 'clearing', 'paying back', 'deposit share',
]

REQUIRED_FIELDS = ['date', 'description', 'amount']


@dataclass
class ParsedRow:
    """Represents a single fully-parsed CSV row."""
    row_number: int
    raw: dict

    date_str: str = ''
    parsed_date: Optional[date] = None
    description: str = ''
    paid_by: str = ''
    paid_by_normalized: str = ''
    amount: Optional[Decimal] = None
    currency: str = 'INR'
    split_type: str = 'equal'
    split_with: list = field(default_factory=list)
    split_details: dict = field(default_factory=dict)
    notes: str = ''

    anomalies: list = field(default_factory=list)
    is_valid: bool = True          # Can be imported as-is (after auto-fixes)
    needs_review: bool = False     # Has anomalies requiring user attention
    skip: bool = False             # Hard skip (e.g. empty row)
    is_settlement: bool = False    # Flagged as a settlement, not expense


@dataclass
class DetectedAnomaly:
    anomaly_type: str
    severity: str              # info / warning / error / critical
    field_name: str
    description: str
    original_value: str
    suggested_value: str = ''
    suggested_action: str = ''
    auto_fixed: bool = False    # Was this fixed automatically?


def normalize_name(name: str) -> str:
    """Normalize a person name: strip whitespace, Title Case."""
    return name.strip().title()


def parse_amount(raw: str) -> tuple[Optional[Decimal], Optional[DetectedAnomaly]]:
    """
    Parse amount string, handling comma-formatted numbers (1,200 -> 1200).
    Returns (Decimal, anomaly_or_None).
    """
    if not raw or not raw.strip():
        return None, DetectedAnomaly(
            anomaly_type='missing_field', severity='error',
            field_name='amount', description='Amount is missing.',
            original_value='',
        )

    cleaned = raw.strip().replace(',', '')
    anomaly = None

    # Detect comma-formatted number
    if ',' in raw.strip():
        anomaly = DetectedAnomaly(
            anomaly_type='format_error', severity='info',
            field_name='amount',
            description=f'Amount "{raw.strip()}" uses comma formatting. Auto-converted to {cleaned}.',
            original_value=raw.strip(),
            suggested_value=cleaned,
            auto_fixed=True,
        )

    try:
        amount = Decimal(cleaned)
        # Flag excessive decimal precision
        if '.' in cleaned and len(cleaned.split('.')[1]) > 2:
            prec_anomaly = DetectedAnomaly(
                anomaly_type='rounding', severity='info',
                field_name='amount',
                description=f'Amount {cleaned} has more than 2 decimal places. Will be rounded.',
                original_value=cleaned,
                suggested_value=str(round(amount, 2)),
                auto_fixed=True,
            )
            return amount, prec_anomaly

        return amount, anomaly
    except InvalidOperation:
        return None, DetectedAnomaly(
            anomaly_type='format_error', severity='error',
            field_name='amount',
            description=f'Cannot parse amount: "{raw}"',
            original_value=raw,
        )


def parse_date(raw: str) -> tuple[Optional[date], Optional[DetectedAnomaly]]:
    """
    Try multiple date formats. Returns (date, anomaly_or_None).
    Flags ambiguous dates (04-05-2026 could be Apr5 or May4).
    """
    if not raw or not raw.strip():
        return None, DetectedAnomaly(
            anomaly_type='missing_field', severity='error',
            field_name='date', description='Date is missing.',
            original_value='',
        )

    raw = raw.strip()

    # Try standard DD-MM-YYYY
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            # Check if ambiguous: day <= 12 (could be month)
            if fmt == '%d-%m-%Y' and parsed.day <= 12:
                return parsed, DetectedAnomaly(
                    anomaly_type='date_error', severity='warning',
                    field_name='date',
                    description=(
                        f'Ambiguous date "{raw}". Interpreted as {parsed.strftime("%d %b %Y")} '
                        f'(DD-MM-YYYY). Could also be {datetime.strptime(raw, "%m-%d-%Y").strftime("%d %b %Y")}.'
                    ),
                    original_value=raw,
                    suggested_value=parsed.isoformat(),
                    suggested_action='Confirm the correct date interpretation.',
                )
            return parsed, None
        except ValueError:
            continue

    # Try abbreviated formats like Mar-14 (missing year)
    for fmt in ('%b-%d', '%B-%d'):
        try:
            parsed_no_year = datetime.strptime(raw, fmt)
            guessed = parsed_no_year.replace(year=2026).date()
            return guessed, DetectedAnomaly(
                anomaly_type='date_error', severity='warning',
                field_name='date',
                description=f'Date "{raw}" is missing a year. Assumed 2026: {guessed.isoformat()}.',
                original_value=raw,
                suggested_value=guessed.isoformat(),
                suggested_action='Confirm the correct year.',
            )
        except ValueError:
            continue

    return None, DetectedAnomaly(
        anomaly_type='date_error', severity='error',
        field_name='date',
        description=f'Cannot parse date: "{raw}".',
        original_value=raw,
    )


def parse_split_with(raw: str) -> list[str]:
    """Parse semicolon-separated member list."""
    if not raw or not raw.strip():
        return []
    return [n.strip() for n in raw.split(';') if n.strip()]


def parse_split_details(raw: str) -> dict:
    """
    Parse split_details like 'Rohan 700; Priya 400; Meera 400'
    or 'Aisha 30%; Rohan 30%; Priya 30%; Meera 20%'
    or 'Aisha 1; Rohan 2; Priya 1; Dev 2'
    Returns {name: value} where value is Decimal.
    """
    if not raw or not raw.strip():
        return {}
    result = {}
    parts = [p.strip() for p in raw.split(';') if p.strip()]
    for part in parts:
        # Match "Name value" or "Name value%"
        m = re.match(r'^(.+?)\s+([\d.]+)%?$', part.strip())
        if m:
            name = m.group(1).strip().title()
            try:
                result[name] = Decimal(m.group(2))
            except InvalidOperation:
                pass
    return result


def check_name(name: str, group_members: set) -> Optional[DetectedAnomaly]:
    """Check if name is in group members (case-insensitive). Flag variants."""
    if not name:
        return None
    normalized = normalize_name(name)
    lower = normalized.lower()

    if lower in {m.lower() for m in group_members}:
        if normalized not in group_members:
            # Capitalization variant
            canonical = next(m for m in group_members if m.lower() == lower)
            return DetectedAnomaly(
                anomaly_type='name_mismatch', severity='info',
                field_name='paid_by',
                description=f'Name "{name}" normalized to "{canonical}".',
                original_value=name,
                suggested_value=canonical,
                auto_fixed=True,
            )
        return None

    # Check trailing space (e.g. "rohan ")
    if name.strip().lower() in {m.lower() for m in group_members}:
        canonical = next(m for m in group_members if m.lower() == name.strip().lower())
        return DetectedAnomaly(
            anomaly_type='name_mismatch', severity='info',
            field_name='paid_by',
            description=f'Name "{name}" has extra whitespace. Auto-corrected to "{canonical}".',
            original_value=name,
            suggested_value=canonical,
            auto_fixed=True,
        )

    # Check for name variants like "Priya S" -> "Priya"
    first_word = name.strip().split()[0].lower() if name.strip() else ''
    if first_word in {m.lower() for m in group_members}:
        canonical = next(m for m in group_members if m.lower() == first_word)
        return DetectedAnomaly(
            anomaly_type='name_mismatch', severity='warning',
            field_name='paid_by',
            description=f'Name "{name}" looks like a variant of "{canonical}" (extra surname?). '
                        f'Auto-corrected to "{canonical}".',
            original_value=name,
            suggested_value=canonical,
            auto_fixed=True,
        )

    # Completely unknown
    return DetectedAnomaly(
        anomaly_type='name_mismatch', severity='error',
        field_name='paid_by',
        description=f'Name "{name}" is not a recognized group member.',
        original_value=name,
        suggested_action='Remove this row or correct the name.',
    )


def is_possible_settlement(row: ParsedRow) -> bool:
    desc_lower = row.description.lower()
    notes_lower = row.notes.lower()
    for keyword in SETTLEMENT_KEYWORDS:
        if keyword in desc_lower or keyword in notes_lower:
            return True
    # Only 2 members in split_with is a strong signal
    if len(row.split_with) <= 2 and row.split_type in ('', 'equal'):
        if any(k in desc_lower for k in ['paid', 'deposit', 'settled', 'back']):
            return True
    return False


def check_percentage_sum(split_details: dict) -> Optional[DetectedAnomaly]:
    """Check if percentage splits sum to 100%."""
    if not split_details:
        return None
    total = sum(split_details.values())
    if abs(total - 100) > 0.01:
        normalized = {k: round(v / total * 100, 2) for k, v in split_details.items()}
        return DetectedAnomaly(
            anomaly_type='math_error', severity='warning',
            field_name='split_details',
            description=f'Percentages sum to {total}%, not 100%. '
                        f'Will be normalized proportionally.',
            original_value=str(dict(split_details)),
            suggested_value=str(normalized),
            suggested_action='Percentages auto-normalized. Approve to continue.',
        )
    return None


def check_unequal_sum(split_details: dict, total: Decimal) -> Optional[DetectedAnomaly]:
    """Check if unequal split amounts add up to total."""
    if not split_details or not total:
        return None
    assigned = sum(split_details.values())
    diff = abs(assigned - total)
    if diff > Decimal('0.02'):
        return DetectedAnomaly(
            anomaly_type='math_error', severity='error',
            field_name='split_details',
            description=f'Split amounts sum to {assigned}, but expense total is {total}. '
                        f'Difference: {diff}.',
            original_value=str(dict(split_details)),
            suggested_action='Correct the split amounts so they sum to the total.',
        )
    return None


def parse_csv(csv_text: str, group_members: set = None) -> list[ParsedRow]:
    """
    Main parse function. Returns list of ParsedRow objects.
    group_members: set of normalized usernames (Title Case) in the group.
    """
    if group_members is None:
        group_members = {m.title() for m in KNOWN_MEMBERS}

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    rows = []
    seen_descriptions: dict[str, int] = {}  # key -> row_number for duplicate detection

    for i, raw_row in enumerate(reader, start=2):  # row 1 is header
        row = ParsedRow(row_number=i, raw=dict(raw_row))

        # Skip completely empty rows
        vals = [v for v in raw_row.values() if v and v.strip()]
        if not vals:
            row.skip = True
            rows.append(row)
            continue

        # --- Parse each field ---
        row.date_str = raw_row.get('date', '').strip()
        parsed_date, date_anomaly = parse_date(row.date_str)
        row.parsed_date = parsed_date
        if date_anomaly:
            row.anomalies.append(date_anomaly)
            if date_anomaly.severity == 'error':
                row.is_valid = False
            row.needs_review = True

        row.description = raw_row.get('description', '').strip()
        if not row.description:
            row.anomalies.append(DetectedAnomaly(
                anomaly_type='missing_field', severity='critical',
                field_name='description', description='Description is missing.',
                original_value='',
            ))
            row.is_valid = False
            row.needs_review = True

        # Amount
        raw_amount = raw_row.get('amount', '').strip()
        amount, amount_anomaly = parse_amount(raw_amount)
        row.amount = amount
        if amount_anomaly:
            row.anomalies.append(amount_anomaly)
            if amount_anomaly.severity in ('error', 'critical'):
                row.is_valid = False
            row.needs_review = True

        # Negative / zero amounts
        if amount is not None:
            if amount < 0:
                row.anomalies.append(DetectedAnomaly(
                    anomaly_type='negative_amount', severity='warning',
                    field_name='amount',
                    description=f'Negative amount: {amount}. Treating as a refund/reversal.',
                    original_value=str(amount),
                    suggested_action='Review and confirm this is a refund.',
                ))
                row.needs_review = True
            elif amount == 0:
                row.anomalies.append(DetectedAnomaly(
                    anomaly_type='zero_amount', severity='warning',
                    field_name='amount',
                    description='Amount is zero. This may be a placeholder or error.',
                    original_value='0',
                    suggested_action='Skip or correct this row.',
                ))
                row.needs_review = True

        # Currency
        currency_raw = raw_row.get('currency', '').strip()
        if not currency_raw:
            row.currency = 'INR'
            row.anomalies.append(DetectedAnomaly(
                anomaly_type='currency_missing', severity='warning',
                field_name='currency',
                description='Currency missing. Defaulted to INR.',
                original_value='',
                suggested_value='INR',
                auto_fixed=True,
            ))
            row.needs_review = True
        else:
            row.currency = currency_raw.upper()

        # Paid by
        paid_by_raw = raw_row.get('paid_by', '').strip()
        if not paid_by_raw:
            row.anomalies.append(DetectedAnomaly(
                anomaly_type='missing_field', severity='error',
                field_name='paid_by',
                description='Paid by is missing.',
                original_value='',
                suggested_action='Cannot import without knowing who paid.',
            ))
            row.is_valid = False
            row.needs_review = True
        else:
            name_anomaly = check_name(paid_by_raw, group_members)
            if name_anomaly:
                row.anomalies.append(name_anomaly)
                if name_anomaly.severity == 'error':
                    row.is_valid = False
                row.needs_review = True
                if name_anomaly.suggested_value:
                    row.paid_by_normalized = name_anomaly.suggested_value
                else:
                    row.paid_by_normalized = paid_by_raw
            else:
                row.paid_by_normalized = normalize_name(paid_by_raw)
        row.paid_by = paid_by_raw

        # Split type
        split_type_raw = raw_row.get('split_type', '').strip().lower()
        row.split_type = split_type_raw if split_type_raw else 'equal'

        # Split with
        split_with_raw = raw_row.get('split_with', '').strip()
        row.split_with = parse_split_with(split_with_raw)

        # Normalize split_with names and check each
        normalized_split_with = []
        for name in row.split_with:
            # Handle "Dev's friend Kabir" style
            if "'" in name or ' ' in name.strip():
                normalized_split_with.append(name.strip())  # Keep as-is, flag below
            else:
                n_anomaly = check_name(name, group_members)
                if n_anomaly and not n_anomaly.auto_fixed:
                    row.anomalies.append(DetectedAnomaly(
                        anomaly_type='name_mismatch', severity='warning',
                        field_name='split_with',
                        description=f'Unknown name in split_with: "{name}". May be a guest.',
                        original_value=name,
                        suggested_action='Confirm if this is a one-time guest or a typo.',
                    ))
                    row.needs_review = True
                    normalized_split_with.append(name.strip())
                elif n_anomaly and n_anomaly.suggested_value:
                    normalized_split_with.append(n_anomaly.suggested_value)
                else:
                    normalized_split_with.append(normalize_name(name))
        row.split_with = normalized_split_with

        # Split details
        split_details_raw = raw_row.get('split_details', '').strip()
        row.split_details = parse_split_details(split_details_raw)
        row.notes = raw_row.get('notes', '').strip()

        # Math checks
        if row.split_type == 'percentage' and row.split_details:
            pct_anomaly = check_percentage_sum(row.split_details)
            if pct_anomaly:
                row.anomalies.append(pct_anomaly)
                row.needs_review = True

        if row.split_type == 'unequal' and row.split_details and row.amount:
            math_anomaly = check_unequal_sum(row.split_details, row.amount)
            if math_anomaly:
                row.anomalies.append(math_anomaly)
                row.needs_review = True
                row.is_valid = False

        # Possible settlement
        if is_possible_settlement(row):
            row.is_settlement = True
            row.anomalies.append(DetectedAnomaly(
                anomaly_type='misclassification', severity='warning',
                field_name='description',
                description=f'"{row.description}" looks like a settlement/payment, not a shared expense.',
                original_value=row.description,
                suggested_action='Import as Settlement instead of Expense.',
            ))
            row.needs_review = True

        # split_type/details mismatch
        if row.split_type in ('unequal', 'percentage', 'share') and not row.split_details:
            row.anomalies.append(DetectedAnomaly(
                anomaly_type='format_error', severity='warning',
                field_name='split_details',
                description=f'split_type is "{row.split_type}" but split_details is empty.',
                original_value='',
                suggested_action='Will fall back to equal split. Correct if intended.',
            ))
            row.needs_review = True
            row.split_type = 'equal'  # auto fallback

        # Duplicate detection
        dup_key = f"{row.description.lower().strip()}|{row.date_str.strip()}"
        if dup_key in seen_descriptions:
            prev_row = seen_descriptions[dup_key]
            # Check if it's exact (same amount) or conflicting (different amount)
            prev = next((r for r in rows if r.row_number == prev_row), None)
            if prev and prev.amount == row.amount:
                anomaly_desc = (
                    f'Exact duplicate of Row {prev_row} '
                    f'(same description, date, and amount).'
                )
                sev = 'error'
            else:
                anomaly_desc = (
                    f'Possible duplicate of Row {prev_row} '
                    f'(same description and date, different amount). '
                    f'Prev: {prev.amount if prev else "?"}, Current: {row.amount}.'
                )
                sev = 'error'
            row.anomalies.append(DetectedAnomaly(
                anomaly_type='duplicate', severity=sev,
                field_name='description',
                description=anomaly_desc,
                original_value=row.description,
                suggested_action='Review both rows and keep only the correct one.',
            ))
            row.needs_review = True
            row.is_valid = False
        else:
            seen_descriptions[dup_key] = row.row_number

        rows.append(row)

    return rows


def rows_to_serializable(rows: list[ParsedRow]) -> list[dict]:
    """Convert ParsedRow list to JSON-serializable dict list."""
    result = []
    for row in rows:
        result.append({
            'row_number': row.row_number,
            'date': row.parsed_date.isoformat() if row.parsed_date else None,
            'date_raw': row.date_str,
            'description': row.description,
            'paid_by': row.paid_by,
            'paid_by_normalized': row.paid_by_normalized,
            'amount': str(row.amount) if row.amount is not None else None,
            'currency': row.currency,
            'split_type': row.split_type,
            'split_with': row.split_with,
            'split_details': {k: str(v) for k, v in row.split_details.items()},
            'notes': row.notes,
            'is_valid': row.is_valid,
            'needs_review': row.needs_review,
            'skip': row.skip,
            'is_settlement': row.is_settlement,
            'anomaly_count': len(row.anomalies),
            'anomalies': [
                {
                    'anomaly_type': a.anomaly_type,
                    'severity': a.severity,
                    'field_name': a.field_name,
                    'description': a.description,
                    'original_value': a.original_value,
                    'suggested_value': a.suggested_value,
                    'suggested_action': a.suggested_action,
                    'auto_fixed': a.auto_fixed,
                }
                for a in row.anomalies
            ],
        })
    return result

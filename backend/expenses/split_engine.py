"""
Split calculation engine.
Handles equal, unequal, percentage, and share-based splits.
Rounding policy: round each share down to 2 decimal places;
remainder goes to the payer's share.
"""
from decimal import Decimal, ROUND_DOWN


def round_currency(amount):
    """Round a decimal to 2 places (paisa precision)."""
    return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)


def calculate_equal_split(total, participants):
    """
    Split total equally among all participants.
    Returns {user_id: share_amount} dict.
    Payer gets the remainder from rounding.
    """
    n = len(participants)
    if n == 0:
        return {}
    per_person = round_currency(total / n)
    splits = {uid: per_person for uid in participants}
    # Assign remainder to first participant (payer)
    assigned = per_person * n
    remainder = round_currency(total - assigned)
    if remainder != Decimal('0.00'):
        splits[participants[0]] = round_currency(splits[participants[0]] + remainder)
    return splits


def calculate_unequal_split(total, participant_amounts):
    """
    Split by explicit amounts per person.
    participant_amounts: {user_id: amount}
    Validates that sum matches total (within 0.01 tolerance).
    """
    total_assigned = sum(Decimal(str(v)) for v in participant_amounts.values())
    diff = abs(total_assigned - Decimal(str(total)))
    if diff > Decimal('0.02'):
        raise ValueError(
            f'Unequal split amounts ({total_assigned}) do not match total ({total}). '
            f'Difference: {diff}'
        )
    return {uid: round_currency(amt) for uid, amt in participant_amounts.items()}


def calculate_percentage_split(total, participant_percentages):
    """
    Split by percentage.
    participant_percentages: {user_id: percentage_value (e.g. 30.0 for 30%)}
    Percentages are normalized to 100% if they don't sum to exactly 100.
    """
    total_pct = sum(Decimal(str(v)) for v in participant_percentages.values())
    if total_pct == 0:
        raise ValueError('Percentages sum to zero.')

    splits = {}
    total_dec = Decimal(str(total))
    participants = list(participant_percentages.keys())

    for uid in participants:
        pct = Decimal(str(participant_percentages[uid]))
        # Normalize against actual sum (handles 110% case)
        share = round_currency((pct / total_pct) * total_dec)
        splits[uid] = share

    # Assign rounding remainder to first participant
    assigned = sum(splits.values())
    remainder = round_currency(total_dec - assigned)
    if remainder != Decimal('0.00'):
        splits[participants[0]] = round_currency(splits[participants[0]] + remainder)

    return splits


def calculate_share_split(total, participant_shares):
    """
    Split by ratio/shares.
    participant_shares: {user_id: share_count (e.g. Rohan: 2, others: 1)}
    """
    total_shares = sum(Decimal(str(v)) for v in participant_shares.values())
    if total_shares == 0:
        raise ValueError('Total shares sum to zero.')

    splits = {}
    total_dec = Decimal(str(total))
    participants = list(participant_shares.keys())

    for uid in participants:
        share_count = Decimal(str(participant_shares[uid]))
        amount = round_currency((share_count / total_shares) * total_dec)
        splits[uid] = amount

    # Assign rounding remainder to first participant
    assigned = sum(splits.values())
    remainder = round_currency(total_dec - assigned)
    if remainder != Decimal('0.00'):
        splits[participants[0]] = round_currency(splits[participants[0]] + remainder)

    return splits


def compute_splits(expense, participant_ids, split_details_raw=None):
    """
    Main entry point. Given an Expense object and participant user IDs,
    compute the split amounts for each person.

    split_details_raw: dict with per-person values depending on split_type:
        - equal: not needed (or ignored)
        - unequal: {user_id: amount}
        - percentage: {user_id: percentage}
        - share: {user_id: share_count}

    Returns: {user_id: Decimal share_amount}
    """
    total = Decimal(str(expense.amount))
    split_type = expense.split_type

    if split_type == 'equal':
        return calculate_equal_split(total, participant_ids)

    if not split_details_raw:
        raise ValueError(f'split_details required for split_type={split_type}')

    if split_type == 'unequal':
        return calculate_unequal_split(total, split_details_raw)

    if split_type == 'percentage':
        return calculate_percentage_split(total, split_details_raw)

    if split_type == 'share':
        return calculate_share_split(total, split_details_raw)

    raise ValueError(f'Unknown split_type: {split_type}')

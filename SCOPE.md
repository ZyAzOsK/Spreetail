# SCOPE.md — Anomaly Log & Database Schema

> Every data problem found in `Expenses Export.csv`, how it was detected, and how it was handled.

## Part 1: CSV Anomaly Log

The CSV file contains 43 data rows (excluding header) with **14+ deliberate data problems**. Each anomaly is detected during import, surfaced to the user, and handled according to documented policies.

### Anomaly Detection Summary

| # | Row | Field | Anomaly Type | Description | Detection Method | Handling Policy |
|---|-----|-------|-------------|-------------|-----------------|-----------------|
| 1 | 5–6 | description, amount | **Duplicate** | "Dinner at Marina Bites" and "dinner - marina bites" — same date, payer, amount (₹3200) | Case-insensitive string similarity + same-day/payer/amount match | Flag both rows. Keep Row 5 (has explanatory note). Row 6 marked for user approval to delete. |
| 2 | 7 | amount | **Format Error** | Amount `"1,200"` uses comma formatting inside quotes | Regex check for comma-separated numbers | Strip commas, parse as `1200`. Auto-fix with notification. |
| 3 | 9 | paid_by | **Name Mismatch** | `priya` (lowercase) instead of `Priya` | Case comparison against known member names | Normalize to title case → `Priya`. Auto-fix with notification. |
| 4 | 10 | amount | **Rounding Issue** | `899.995` — fractional paisa (3 decimal places) | Decimal place count check | Round to 2 decimal places → `900.00`. Auto-fix with notification. |
| 5 | 11 | paid_by | **Name Variant** | `Priya S` instead of `Priya` | Fuzzy matching (starts-with + known member list) | Normalize to `Priya`. Flag for user confirmation (could be different person). |
| 6 | 13 | paid_by | **Missing Field** | `paid_by` is empty — "can't remember who paid" | Empty field check | Flag as critical anomaly. Require user to assign payer before import. |
| 7 | 14 | split_type, description | **Misclassification** | "Rohan paid Aisha back" — this is a settlement, not an expense. `split_type` is empty. | Keyword detection in description ("paid back", "settlement") + empty split_type | Reclassify as Settlement (Rohan → Aisha, ₹5000). Create Settlement record, not Expense. |
| 8 | 15 | split_details | **Math Error** | Percentages sum to 110%: `30% + 30% + 30% + 20% = 110%` | Sum validation for percentage splits | Flag error. Suggest normalizing proportionally: `27.3%, 27.3%, 27.3%, 18.2%`. User decides. |
| 9 | 23 | split_with | **Non-Member** | `Dev's friend Kabir` is not a regular group member | Name not found in member list | Create Kabir as a guest/temporary participant for this expense only. Flag for user awareness. |
| 10 | 24–25 | description, amount | **Conflicting Duplicate** | Thalassa dinner logged twice: Aisha (₹2400) and Rohan (₹2450), different amounts | Same-day + description similarity + different amounts | Flag both. Note on Row 25 says "hers is wrong" → suggest keeping Row 25 (Rohan's ₹2450). User confirms which to keep. |
| 11 | 26 | amount | **Negative Amount** | `-30 USD` parasailing refund | Negative number check | Treat as refund/reversal. Apply as negative expense — each participant gets credited their share back. |
| 12 | 27 | date, paid_by | **Date Format Error + Name Whitespace** | Date is `Mar-14` instead of `DD-MM-YYYY`. Payer has trailing space: `rohan ` | Date format regex mismatch + whitespace trimming | Parse `Mar-14` as `14-03-2026` (consistent with other dates). Trim `rohan ` → `Rohan`. Auto-fix. |
| 13 | 28 | currency | **Missing Currency** | Currency field is empty — "forgot to set currency" | Empty field check | Default to `INR` (most common currency, 35 of 42 rows). Flag for user confirmation. |
| 14 | 31 | amount | **Zero Amount** | `0 INR` with note "counted twice earlier - fixing later" | Zero value check | Flag as placeholder/invalid entry. Skip import. Surface to user. |
| 15 | 32 | split_details | **Math Error** | Same as #8 — percentages sum to 110%: `30% + 30% + 30% + 20%` | Sum validation | Same handling as #8. |
| 16 | 34 | date | **Ambiguous Date** | `04-05-2026` — could be April 5 or May 4 | Out-of-sequence check + note content analysis | All other dates use DD-MM-YYYY. Interpret as 4th May 2026. But note says "is this April 5 or May 4?" — flag for user decision with both interpretations. |
| 17 | 36 | split_with | **Membership Violation** | Meera included in April expense (₹2640) but she moved out end of March | Member active-date check against expense date | Flag: Meera left the group on ~31-03-2026. Remove Meera from split, recalculate among Aisha, Rohan, Priya. |
| 18 | 38 | description, split_type | **Misclassified Transaction** | "Sam deposit share" — a deposit payment to Aisha, not a shared expense | Keyword detection ("deposit") + only 2 participants | Flag as potential settlement/transfer. Suggest reclassifying as Settlement (Sam → Aisha, ₹15,000). |
| 19 | 42 | split_type, split_details | **Contradictory Data** | `split_type=equal` but `split_details` has share ratios `1:1:1:1` | split_details present when split_type doesn't require it | Since all shares are equal (1:1:1:1), equal split is correct. Flag the contradiction but proceed with equal split. Ignore redundant split_details. |

### Detection Categories

| Category | Count | Examples |
|----------|-------|---------|
| Duplicate entries | 2 | Rows 5-6, Rows 24-25 |
| Missing/empty fields | 3 | Rows 13, 14, 28 |
| Format errors | 3 | Rows 7, 10, 27 |
| Name inconsistencies | 3 | Rows 9, 11, 27 |
| Math errors | 2 | Rows 15, 32 |
| Invalid amounts | 2 | Rows 26, 31 |
| Date issues | 2 | Rows 27, 34 |
| Membership violations | 1 | Row 36 |
| Misclassifications | 2 | Rows 14, 38 |
| Contradictory data | 1 | Row 42 |

---

## Part 2: Database Schema

_Schema documentation with table descriptions and relationships will be completed after models are finalized._

### Core Tables

#### User (Django built-in)
Standard Django User model — username, email, password hash.

#### Group
A group of people who share expenses (e.g., "Flat 4B").

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| name | CharField(200) | Group name |
| description | TextField | Optional description |
| created_by | FK → User | Who created the group |
| created_at | DateTimeField | Auto-set on creation |

#### GroupMembership
Tracks when a person joined and left a group. Supports membership changes over time.

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| group_id | FK → Group | Which group |
| user_id | FK → User | Which member |
| joined_at | DateField | When they joined |
| left_at | DateField (nullable) | When they left (null = still active) |
| is_active | BooleanField | Currently active member |

#### Expense
An expense paid by one person, split among group members.

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| group_id | FK → Group | Which group |
| paid_by | FK → User | Who paid |
| description | CharField(500) | What for |
| amount | Decimal(12,2) | How much |
| currency | CharField(3) | INR or USD |
| split_type | CharField(20) | equal, unequal, percentage, share |
| expense_date | DateField | When the expense occurred |
| notes | TextField | Optional notes |
| is_settlement | BooleanField | True if settlement, not expense |
| import_row_number | IntegerField (nullable) | CSV row number if imported |

#### ExpenseSplit
Per-user breakdown of each expense.

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| expense_id | FK → Expense | Which expense |
| user_id | FK → User | Which person |
| share_amount | Decimal(12,2) | Calculated amount owed |
| share_value | Decimal(12,4) | Raw split value (%, ratio, or fixed) |

#### Settlement
Direct payment between two people.

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| group_id | FK → Group | Which group |
| paid_by | FK → User | Who paid |
| paid_to | FK → User | Who received |
| amount | Decimal(12,2) | How much |
| currency | CharField(3) | INR or USD |
| settlement_date | DateField | When it happened |

#### CurrencyRate
Cached exchange rates from ExchangeRate-API.

| Column | Type | Description |
|--------|------|-------------|
| from_currency | CharField(3) | Source currency |
| to_currency | CharField(3) | Target currency |
| rate | Decimal(12,4) | Exchange rate |
| effective_date | DateField | Rate date |

#### ImportReport & ImportAnomaly
Track CSV import operations and detected anomalies. See models for full schema.

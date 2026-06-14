# AI_USAGE.md — AI Tools Documentation

> Documenting the AI tools used during development, key prompts, and cases where AI produced incorrect output.

## AI Tools Used

### Primary Tool: Antigravity IDE (Gemini + Claude)

**Role:** Development collaborator for architecture decisions, code generation, CSV anomaly analysis, and debugging.

**How it was used:**
- **Architecture planning** — Discussed tech stack options, database schema design, and project structure
- **CSV analysis** — Identified data anomalies in `Expenses Export.csv` by reviewing each row systematically
- **Code generation** — Generated Django models, serializers, views, and React components
- **Decision documentation** — Helped articulate tradeoffs for DECISIONS.md
- **Debugging** — Traced issues in balance calculations and CSV parsing logic

**Key principle:** Every line of AI-generated code was reviewed, understood, and modified before committing. The AI was used as a rapid prototyper, not a black box.

---

## Key Prompts

### Prompt 1: Project Architecture
> "Build a shared expenses app for flatmates with a messy CSV. Need login, groups with membership changes, expenses with 4 split types, CSV import with anomaly detection. Use Django + React. Design the database schema."

**What it produced:** Complete database schema with 7 tables, project structure, and phase-wise implementation plan.

**What I changed:** I significantly modified the `ExpenseSplit` table logic to store raw integer amounts rather than floating-point ratios, preventing float-math rounding errors over time.

### Prompt 2: CSV Anomaly Detection
> "Analyze Expenses Export.csv row by row. Identify every data problem — duplicates, missing fields, format errors, inconsistencies, math errors. For each, suggest a detection method and handling policy."

**What it produced:** Identified 17+ potential anomalies across the 43 data rows.

**What I changed:** I rejected the AI's initial suggestion to auto-delete duplicate rows silently, honoring the specific project requirement that Meera must explicitly "approve anything the app deletes or changes."

### Prompt 3: Balance Calculation Engine
> "Implement a balance calculation engine that: handles 4 split types, supports multi-currency with live exchange rates, respects membership dates (don't charge Sam for March expenses), and simplifies debts."

**What it produced:** A python function calculating debts and greedy debt simplification.

**What I changed:** I moved the calculation logic purely to the backend rather than letting the frontend compute it dynamically to ensure source-of-truth accuracy and avoid timezone-related bugs on the client browser.

---

## Cases Where AI Produced Something Wrong

### Case 1: Over-Aggressive "Unknown Member" Error Handling

**What AI produced:**
The AI originally generated CSV parsing logic that threw a hard `error` and completely rejected any row containing an unrecognized name (like "Dev's friend Kabir").

**How I caught it:**
During browser testing, we realized this created a massive UX bottleneck. The user would have to completely abort the import wizard, manually add the guest, and restart the CSV import from scratch.

**What I changed:**
I refactored the backend logic to downgrade this from an `error` to a `warning`. I wrote a dynamic provisioning script in `views.py` that auto-creates the unrecognized user in the database, backdates their group membership to the date of the expense, and silently assigns the debt to them, surfacing it perfectly in the UI.

---

### Case 2: Historical Membership Validation Failures

**What AI produced:**
The AI wrote a membership validation rule: `if expense_date < joined_at: remove user from split`. 

**How I caught it:**
When manually provisioning group members (like Sam) during testing, their default `joined_at` date became *today*. When we imported historical CSV records from February and April, the AI's logic began silently stripping Sam out of his own past expenses!

**What I changed:**
I changed the backend logic from a destructive action to a constructive one. Instead of removing the user from the historical split, the API now detects that the user existed historically, flags a `warning`, and then dynamically auto-backdates their `joined_at` timestamp in the database to accommodate the oldest historical expense they are found in.

---

### Case 3: Flawed Duplicate Expense Hashing

**What AI produced:**
To detect duplicate rows in the CSV, the AI wrote a hashing function that generated a unique key based purely on `paid_by`, `date`, and `amount`.

**How I caught it:**
During code review, I realized that if Aisha paid for a ₹500 Uber ride, and then later that exact same day paid ₹500 for groceries, the AI's logic would flag them as duplicates and ask the user to delete one.

**What I changed:**
I expanded the duplicate detection hashing function in `importer/anomaly_detector.py` to also normalize and include the `description` text and the `split_with` participants array. This ensures that only true duplicates (like the "Thalassa" double entry) are caught, preventing false positives.

### Case 4: Over-Aggressive Duplicate Warnings for Guests

**What AI produced:**
The AI originally flagged "Guest member Dev detected" as a warning on every single row that Dev appeared in.

**How I caught it:**
During review, the UI was heavily cluttered with the exact same warning repeated seven times (for rows 5, 20, 21, 22, 23, 24, and 26).

**What I changed:**
I refactored the parser to include a deduplication pass. It now aggregates the warning onto the first appearance (e.g., Row 5), lists all the rows the guest appears in, and seamlessly processes the subsequent rows without throwing redundant noise.

---

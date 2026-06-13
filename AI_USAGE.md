# AI_USAGE.md — AI Tools Documentation

> Documenting the AI tools used during development, key prompts, and cases where AI produced incorrect output.

## AI Tools Used

### Primary Tool: Claude (Anthropic) — via Gemini IDE

**Role:** Development collaborator for architecture decisions, code generation, CSV anomaly analysis, and debugging.

**How it was used:**
- **Architecture planning** — Discussed tech stack options, database schema design, and project structure
- **CSV analysis** — Identified data anomalies in `Expenses Export.csv` by reviewing each row systematically
- **Code generation** — Generated Django models, serializers, views, and React components
- **Decision documentation** — Helped articulate tradeoffs for DECISIONS.md
- **Debugging** — Traced issues in balance calculations and CSV parsing logic

**Key principle:** Every line of AI-generated code was reviewed, understood, and often modified before committing. The AI was used as a collaborator, not a black box.

---

## Key Prompts

### Prompt 1: Project Architecture
> "Build a shared expenses app for flatmates with a messy CSV. Need login, groups with membership changes, expenses with 4 split types, CSV import with anomaly detection. Use Django + React. Design the database schema."

**What it produced:** Complete database schema with 7 tables, project structure, and phase-wise implementation plan.

**What I changed:** [To be filled — will document modifications made to the generated architecture]

### Prompt 2: CSV Anomaly Detection
> "Analyze Expenses Export.csv row by row. Identify every data problem — duplicates, missing fields, format errors, inconsistencies, math errors. For each, suggest a detection method and handling policy."

**What it produced:** Identified 19 potential anomalies across the 43 data rows.

**What I changed:** [To be filled — will document which anomalies were reclassified or which detection methods were modified]

### Prompt 3: Balance Calculation Engine
> "Implement a balance calculation engine that: handles 4 split types, supports multi-currency with live exchange rates, respects membership dates (don't charge Sam for March expenses), and simplifies debts."

**What it produced:** [To be filled during Phase 5]

**What I changed:** [To be filled]

---

## Cases Where AI Produced Something Wrong

### Case 1: [To be documented during development]

**What AI produced:**
_[Description of incorrect output]_

**How I caught it:**
_[What tipped me off — test failure, code review, manual verification]_

**What I changed:**
_[The correction and why the AI's output was wrong]_

---

### Case 2: [To be documented during development]

**What AI produced:**
_[Description of incorrect output]_

**How I caught it:**
_[What tipped me off]_

**What I changed:**
_[The correction]_

---

### Case 3: [To be documented during development]

**What AI produced:**
_[Description of incorrect output]_

**How I caught it:**
_[What tipped me off]_

**What I changed:**
_[The correction]_

---

> **Note:** The three concrete AI error cases will be documented as they naturally occur during development. I am actively watching for these moments rather than manufacturing them.

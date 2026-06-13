# DECISIONS.md — Decision Log

> Each significant design and engineering decision, the options considered, and why the chosen option was selected.

---

## Decision 1: Tech Stack — Frontend Framework

**Context:** Need a React-based frontend that can later be adapted for a React Native mobile app.

| Option | Pros | Cons |
|--------|------|------|
| **Next.js** | SSR, SEO, file-based routing | Web-only, no native mobile support, SSR overkill for SPA |
| **Vite + React** ✅ | Fast dev server, simple config, clean separation | No SSR (not needed here) |
| **Expo Router** | Universal (web + mobile) | Premature for web-first assignment, learning curve |

**Decision:** Vite + React. The assignment is a web app. Vite gives fast HMR and simple bundling. The component architecture can later be shared with a React Native app via a monorepo with `packages/shared`.

---

## Decision 2: Tech Stack — Backend Framework

**Context:** Assignment specifically mentions Django as a plus. Need REST APIs and relational DB support.

| Option | Pros | Cons |
|--------|------|------|
| **Django + DRF** ✅ | Assignment mentions Django, excellent ORM, built-in admin, DRF for clean APIs | Heavier than Express |
| **Express.js + Prisma** | Lightweight, JS everywhere | Assignment values Python/Django |
| **FastAPI** | Modern, async, fast | Less mature ORM, less assignment alignment |

**Decision:** Django + Django REST Framework. Directly aligns with the role requirements. Django ORM makes complex queries (balance calculations, membership-date filtering) readable and maintainable.

---

## Decision 3: Authentication Strategy

**Context:** App needs user login. Question is how complex.

| Option | Pros | Cons |
|--------|------|------|
| **JWT (SimpleJWT)** ✅ | Stateless, API-friendly, works well with React SPA | Token management on client |
| **Session auth** | Simpler server-side | Requires CSRF handling, less API-friendly |
| **OAuth/Social** | User convenience | Overkill, external dependency, setup time |

**Decision:** JWT via `djangorestframework-simplejwt`. Stateless auth fits our API-first architecture. 12-hour access token with 7-day refresh token provides good UX without security risk.

---

## Decision 4: Currency Conversion — Fixed Rate vs Live API

**Context:** CSV has USD expenses. Need to convert for balance calculations.

| Option | Pros | Cons |
|--------|------|------|
| **Fixed rate (₹83/USD)** | Simple, deterministic, explainable | Inaccurate for real use, doesn't demonstrate API skills |
| **ExchangeRate-API** ✅ | Real rates, demonstrates API integration, free tier (1500/mo) | External dependency, needs fallback |

**Decision:** ExchangeRate-API with fallback to ₹83/$1 if API is unavailable. Rates are cached per date in the `CurrencyRate` table to avoid redundant API calls. Demonstrates real-world integration skills while maintaining reliability.

---

## Decision 5: Database — SQLite vs PostgreSQL

**Context:** Assignment requires relational DB. Need both dev convenience and production readiness.

| Option | Pros | Cons |
|--------|------|------|
| **SQLite (dev) + PostgreSQL (prod)** ✅ | Zero-config dev, production-grade prod | Minor behavior differences |
| **PostgreSQL everywhere** | Consistency | Requires local Postgres setup |
| **SQLite only** | Simplest | Not production-ready at scale |

**Decision:** SQLite for local development (zero setup), PostgreSQL for Render.com deployment. `dj-database-url` makes switching seamless via `DATABASE_URL` environment variable.

---

## Decision 6: How to Handle Duplicate Expenses

**Context:** CSV has two types of duplicates — exact duplicates (Rows 5-6) and conflicting duplicates (Rows 24-25 with different amounts).

| Option | Pros | Cons |
|--------|------|------|
| **Auto-delete duplicates** | Fast import | Violates Meera's request ("I want to approve anything the app deletes") |
| **Flag for user review** ✅ | Transparent, user has control | Slower import for messy data |
| **Keep both, mark as possible dups** | No data loss | Inflates expenses, confusing balances |

**Decision:** Flag duplicates and present to user for review. For exact duplicates (same amount), suggest keeping the one with more context (notes). For conflicting duplicates (different amounts), show both and let user decide. This directly addresses Meera's requirement.

---

## Decision 7: Percentage Splits That Don't Sum to 100%

**Context:** Rows 15 and 32 have percentage splits summing to 110% (30+30+30+20).

| Option | Pros | Cons |
|--------|------|------|
| **Reject the row** | Safe | Loses data |
| **Normalize proportionally** ✅ | Preserves relative intent | Alters original percentages |
| **Clip to 100% (reduce last person)** | Simple | Unfair to last person |

**Decision:** Flag as a math error and suggest proportional normalization (divide each by 1.1). Show both original and suggested percentages. Let user approve or modify. This preserves the payer's intent while correcting the error.

---

## Decision 8: Rounding Strategy for Expense Splits

**Context:** When splitting ₹100 among 3 people, you get ₹33.33... — where does the remaining paisa go?

| Option | Pros | Cons |
|--------|------|------|
| **Remainder to payer** ✅ | Simple, consistent, payer bears rounding cost | Payer always slightly disadvantaged |
| **Banker's rounding** | Statistically fair | Complex, harder to explain |
| **Round up last person** | Simple | Last person always pays more |

**Decision:** Round each share down to 2 decimal places. Assign any remainder (difference between sum of shares and total) to the payer's share. Example: ₹100 ÷ 3 = ₹33.33 each → payer's share becomes ₹33.34. This is simple, consistent, and easy to explain in the interview.

---

## Decision 9: Handling the Ambiguous Date (Row 34)

**Context:** `04-05-2026` with note "is this April 5 or May 4? format is a mess"

| Option | Pros | Cons |
|--------|------|------|
| **Always DD-MM-YYYY** ✅ | Consistent with all other dates in CSV | Might be wrong for this specific row |
| **Always MM-DD-YYYY** | Follows US convention | Inconsistent with all other rows |
| **Flag for user decision** ✅ | User picks | Import paused |

**Decision:** Default interpretation as DD-MM-YYYY (4th May 2026), consistent with every other date in the CSV. But flag it as an ambiguous date anomaly and show both interpretations to the user during import review. This respects consistency while giving the user final say.

---

## Decision 10: Handling the Negative Amount (Row 26: -30 USD Refund)

**Context:** Parasailing refund of `-30 USD`. Is this an error or a valid reversal?

| Option | Pros | Cons |
|--------|------|------|
| **Reject negative amounts** | Safe | Loses legitimate refund data |
| **Treat as refund/reversal** ✅ | Correct interpretation (note confirms "one slot got cancelled") | Requires negative-amount handling in balance engine |

**Decision:** Treat as a legitimate refund. The negative amount creates negative splits — each participant gets credited their share of the refund. The balance engine handles this by simply summing all splits (positive and negative). This is the correct real-world behavior.

---

## Decision 11: Guest Members (Kabir)

**Context:** Row 23 includes "Dev's friend Kabir" who is not a regular flatmate.

| Option | Pros | Cons |
|--------|------|------|
| **Create as full user** | Simple | Pollutes member list |
| **Create as guest/temporary** ✅ | Clean separation, one-time participant | Need guest concept |
| **Ignore Kabir's share** | Simple | Incorrect balance calculation |

**Decision:** Create Kabir as a regular user (for data integrity) but don't add him as a group member. He only appears in the ExpenseSplit for that one parasailing expense. This keeps the member list clean while correctly splitting the expense 5 ways.

---

## Decision 12: Sam's Deposit (Row 38)

**Context:** "Sam deposit share" — Sam paid Aisha ₹15,000. This is a security deposit transfer, not a shared expense.

| Option | Pros | Cons |
|--------|------|------|
| **Import as regular expense** | Simple | Incorrect — would affect group balances |
| **Reclassify as settlement** ✅ | Correct financial treatment | Need to detect deposit transactions |

**Decision:** Flag as a potential settlement/transfer. Sam paying Aisha his deposit share is a financial transfer between two people, not a group expense. Import as a Settlement record (Sam → Aisha, ₹15,000) rather than an Expense.

---

_More decisions will be added as they arise during development._

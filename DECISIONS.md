# Architecture & Design Decisions

This document logs all the significant technical and product decisions made during the development of the Spreetail Shared Expenses App. 

## 1. Tech Stack Selection
**Decision:** React (Vite) for the frontend + Django REST Framework (DRF) for the backend.
**Options Considered:** 
- Next.js (Full-stack)
- Django (Full-stack with HTML templates)
- React + DRF
**Rationale:** The assignment specifically mentioned React for the frontend and Django as a plus for the backend. While Next.js is popular, using Vite + React creates a completely decoupled Single Page Application (SPA). This strictly enforces an API-first approach on the backend. This is highly beneficial because the frontend React components can eventually be shared in a Monorepo setup to build a React Native mobile app utilizing the exact same Django API endpoints.

## 2. Dealing with Unknown "Guest" Members
**Decision:** Unrecognized names in the CSV (like "Dev's friend Kabir" or "Priya S") trigger an automatic backend User and GroupMembership provisioning.
**Options Considered:**
1. Throw an error and force the user to manually add the member before importing.
2. Store guests as string fields on the Expense table.
3. Silently auto-create them as full members.
**Rationale:** The first option creates a massive UX bottleneck (the user has to abort the import, navigate away, add the member, and restart). The second option ruins the database normalization and makes balance algorithms a nightmare. We chose Option 3 because it allows the app to cleanly integrate the guest into the exact same Balance engine. The app sets their `joined_at` date dynamically to match the expense date, ensuring accurate historic tracking.

## 3. The Auto-Fixing Policy
**Decision:** Some anomalies (like invalid dates `Mar-14` or extra decimal places `899.995`) are auto-fixed behind the scenes without demanding user intervention, but they are still flagged in the audit report. Major anomalies (like Duplicate Expenses) require explicit user approval.
**Options Considered:**
1. Strict parsing (Fail the whole CSV if one row is bad).
2. Completely silent auto-fixing.
**Rationale:** Meera's specific assignment requirement was: *"Clean up the duplicates — but I want to approve anything the app deletes or changes."* To respect this, anything that requires discarding data (like duplicate rows or missing members) forces the user to explicitly click "Skip" or "Import". Safe parsing assumptions (like Bankers Rounding for fractional cents) are auto-fixed to streamline the UX, but they are visually tagged with a yellow `[Warning]` badge in the UI so the user is still technically approving the change by finalizing the import.

## 4. Resolving the "04-05-2026" Date Ambiguity
**Decision:** Interpreted as May 4th, 2026 (DD-MM-YYYY).
**Options Considered:**
- April 5th (MM-DD-YYYY)
- Prompt the user to type the correct date.
**Rationale:** Every single other row in the CSV file strictly adheres to the DD-MM-YYYY format. When writing parsers, inferring format consistency from the document context is standard practice. Furthermore, in the row timeline, Row 34 falls squarely between mid-April entries and mid-May entries, making May 4th the most logically sound chronological interpretation.

## 5. Currency Exchange Strategy
**Decision:** Exchange rates are fetched live via a free API (`ExchangeRate-API`) and multiplied dynamically at calculation time, standardizing all internal group balances to INR.
**Options Considered:**
- Hardcode an exchange rate (e.g. 1 USD = 83 INR).
- Prompt the user for the exchange rate on every import.
**Rationale:** Priya explicitly noted *"a dollar is not a rupee"*. Hardcoding a rate fails immediately if the user uploads a CSV from a different year. The backend is configured to pull the latest exchange rate and cache it in the `CurrencyRate` table. 

## 6. Debt Simplification Algorithm
**Decision:** A greedy algorithm that matches the highest creditor with the highest debtor to minimize transaction counts.
**Rationale:** If A owes B ₹100, and B owes C ₹100, making two transactions is highly inefficient. The Balance Engine creates a net total for every user. Those with positive balances are put in a `creditors` pool, and negative balances in a `debtors` pool. The algorithm loops and greedily settles the largest debts first, ensuring that no user has to make more than 1 or 2 payments to clear their balances.

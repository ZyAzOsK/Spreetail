# Spreetail Shared Expenses App

A powerful, robust shared expenses application built for flatmates. This app allows users to import messy CSV files, detects anomalies intelligently, resolves them via a clean UI, calculates complex balances factoring in membership dates, and simplifies debt settlements. 

## Features
- **CSV Anomaly Detection:** Detects 17+ types of data anomalies (missing members, duplicate expenses, math errors, historic date violations) and provides actionable resolutions.
- **Smart Importer:** Auto-backdates new members, converts currency (USD to INR), and prevents accidental data loss.
- **Balance Calculation Engine:** Computes net balances while perfectly respecting exact membership dates (e.g. Sam joined late, Meera left early).
- **Simplified Debts:** Reduces cyclical debts into minimal direct payments.
- **My Trace:** A dedicated ledger tracing exactly which expenses contributed to a user's balance.
- **Settlement Recording:** Record offline payments and watch the balances update instantly.

## Tech Stack
- **Frontend:** React + Vite
- **Backend:** Django + Django REST Framework (DRF)
- **Database:** SQLite (local development) / PostgreSQL (production ready)
- **Styling:** Vanilla CSS with a polished Spreetail Dark Theme
- **Animations:** GSAP for smooth scroll reveals and UI interactions.

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 20+

### 1. Backend Setup (Django)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

### 2. Frontend Setup (React/Vite)
```bash
cd frontend
npm install
npm run dev
```

### 3. Usage
1. Open `http://localhost:5173/` in your browser.
2. Register a new user (e.g., Aisha) and log in.
3. Create a Group (e.g., "Spreetail Flatmates").
4. Click **Import CSV** inside the group.
5. Upload the `Expenses Export.csv` file from the root folder.
6. The app will detect anomalies and present an interactive UI to review them. Proceed through the wizard to finalize the import.
7. Click **My Trace** to view expense breakdowns or **Record Settlement** to log payments!

## Documentation Links
- [SCOPE.md](./SCOPE.md) - Contains the complete anomaly log, handling policies, and DB schema.
- [DECISIONS.md](./DECISIONS.md) - Explains all significant technical decisions and rationales.
- [AI_USAGE.md](./AI_USAGE.md) - Details AI usage, key prompts, and 3 specific cases where AI produced incorrect outputs that had to be corrected.

## Deployment Notes
This project is configured to be seamlessly deployed. The Django backend uses `django-cors-headers` and is ready for Render/Railway deployment, and the Vite frontend can be built via `npm run build` and served as static files, or deployed independently to Vercel/Netlify.

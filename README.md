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
```

### 2. Live Exchange Rate API Setup (Required for multi-currency)
The application uses the free **ExchangeRate-API** to perform accurate USD-to-INR conversions.
1. Go to [https://www.exchangerate-api.com/](https://www.exchangerate-api.com/) and sign up for a free account.
2. Once logged in, copy your API key from the dashboard.
3. In the `backend/` directory, create a `.env` file (or edit the existing one) and add your key:
```env
EXCHANGE_RATE_API_KEY=your_copied_api_key_here
```
*(If no API key is provided, the backend falls back to a hardcoded 83.0 rate).*

### 3. Start the Backend Server
```bash
# Still inside the backend directory:
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

### 4. Frontend Setup (React/Vite)
```bash
cd frontend
npm install
npm run dev
```

## How to Test the App (A Layman Demo)
If you are evaluating this assignment, here is exactly how to run through the core functionalities from start to finish:

1. **Start the Servers**: Make sure both `python manage.py runserver` (backend) and `npm run dev` (frontend) are running.
2. **Access the App**: Open your browser and go to `http://localhost:5173/`.
3. **Login**: Click "Register" and create an account for yourself (e.g., Username: "Aisha"). Then log in.
4. **Create a Group**: Click the **"+ New Group"** button. Name it "Spreetail Flatmates".
5. **Import the Messy Data**:
   - Open your newly created group.
   - Click the **"Import CSV"** button.
   - Upload the `Expenses Export.csv` file located in the root of this project folder.
6. **Review the Anomalies**: 
   - The app will automatically detect 17+ errors in the CSV (like missing members, formatting errors, Meera's historic dates, and Thalassa duplicates).
   - Some (like extra decimal places) are auto-fixed safely. Others (like the Thalassa duplicate) will ask for your decision.
   - For the duplicate row that says "hers is wrong", click **"Skip"** on the incorrect one.
   - For anything else, you can click **"Import"** (or just click "Auto-decide all" which safely processes the logic).
   - Click **Finalize Import**.
7. **View the Balances Engine**:
   - You will now be redirected back to the Group page.
   - Scroll down to the **Balances** widget. You'll see exactly who owes what based on the complex internal debt simplification algorithm.
8. **The "My Trace" Feature**: 
   - Inside the Balances widget, click **"My Trace"**.
   - A modal will open tracing out exactly which specific expenses (and in what amounts) contribute to your final balance number!
9. **Settle a Debt**:
   - Click **"Record Settlement"**.
   - Say you are paying Rohan ₹1000. Input the details and submit.
   - Watch the Balances widget dynamically update the debts in real-time, and scroll down to the **Settlement History** table to view your transaction!

## Deployment Instructions

### Deploying the Django Backend to Render.com
1. Create a GitHub repository and push this codebase.
2. Sign up for [Render.com](https://render.com/).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub account and select your repository.
5. Set the following details:
   - **Root Directory**: `backend`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt && python manage.py migrate`
   - **Start Command**: `gunicorn config.wsgi`
6. Add Environment Variables:
   - `DJANGO_SECRET_KEY`: (generate a secure random string)
   - `EXCHANGE_RATE_API_KEY`: (your ExchangeRate-API key)
   - `CORS_ALLOWED_ORIGINS`: (the URL where you will deploy your frontend, e.g., `https://spreetail-frontend.vercel.app`)
7. Click **Create Web Service**.

### Deploying the Vite Frontend to Vercel
1. Sign up for [Vercel](https://vercel.com/).
2. Click **Add New** -> **Project**.
3. Import your GitHub repository.
4. Set the **Framework Preset** to `Vite`.
5. Set the **Root Directory** to `frontend`.
6. Add Environment Variables:
   - `VITE_API_BASE_URL`: (the Render URL for your backend, e.g., `https://spreetail-backend.onrender.com/api`) *Note: You'll need to update `frontend/src/services/api.js` to use this environment variable if deploying.*
7. Click **Deploy**.

## Documentation Links
- [SCOPE.md](./SCOPE.md) - Contains the complete anomaly log, handling policies, and DB schema.
- [DECISIONS.md](./DECISIONS.md) - Explains all significant technical decisions and rationales.
- [AI_USAGE.md](./AI_USAGE.md) - Details AI usage, key prompts, and 3 specific cases where AI produced incorrect outputs that had to be corrected.

## Deployment Notes
This project is configured to be seamlessly deployed. The Django backend uses `django-cors-headers` and is ready for Render/Railway deployment, and the Vite frontend can be built via `npm run build` and served as static files, or deployed independently to Vercel/Netlify.

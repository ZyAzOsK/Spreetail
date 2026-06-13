# FairShare — Shared Expenses App

> Built for the Spreetail Software Engineering Intern assignment.  
> A shared expenses app for flatmates with messy data, built with Django + React.

## 🚀 Live Demo

**Deployed URL:** _[Will be added after deployment]_

## 📋 Overview

FairShare helps a group of flatmates (Aisha, Rohan, Priya, Meera, Dev, Sam) track shared expenses, import messy CSV data, detect anomalies, calculate balances, and settle debts. Built to handle real-world data problems — not just happy paths.

### Key Features

- **Smart CSV Import** — Detects 14+ data anomalies (duplicates, missing fields, math errors, membership violations) and surfaces them for user review
- **Multi-Currency Support** — USD ↔ INR conversion via ExchangeRate-API with rate caching
- **Flexible Splitting** — Equal, unequal, percentage, and share-based expense splitting
- **Membership Timeline** — Tracks when members join/leave — Sam's April expenses don't affect Meera's March balance
- **Debt Simplification** — Minimizes the number of transactions needed to settle up
- **Import Reports** — Every anomaly detected during CSV import is logged with the action taken

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.0 + Django REST Framework |
| Frontend | React 19 (Vite) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (djangorestframework-simplejwt) |
| Styling | Vanilla CSS (Spreetail-inspired dark theme) |
| Animations | GSAP |
| Currency API | ExchangeRate-API |
| Deployment | Render.com |

## 🏗️ Setup Instructions

### Prerequisites

- Python 3.12+
- Node.js 20+
- npm 10+

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your EXCHANGE_RATE_API_KEY

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start dev server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create a `backend/.env` file:

```env
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
EXCHANGE_RATE_API_KEY=your-exchangerate-api-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## 🤖 AI Tools Used

See [AI_USAGE.md](./AI_USAGE.md) for detailed documentation of AI tools used, key prompts, and cases where AI produced incorrect output.

**Primary tool:** Claude (Anthropic) — used as a development collaborator for architecture decisions, code generation, and debugging. Every line was reviewed and understood by the developer.

## 📁 Project Structure

```
├── backend/              # Django REST API
│   ├── accounts/         # User authentication
│   ├── groups/           # Group management
│   ├── expenses/         # Expense CRUD + balance engine
│   ├── importer/         # CSV import + anomaly detection
│   └── config/           # Django settings
├── frontend/             # React (Vite) SPA
│   └── src/
│       ├── components/   # Reusable UI components
│       ├── pages/        # Page-level components
│       ├── services/     # API client
│       └── styles/       # CSS
├── SCOPE.md              # Anomaly log + database schema
├── DECISIONS.md          # Decision log
├── AI_USAGE.md           # AI usage documentation
└── Expenses Export.csv   # Original data file
```

## 📄 Other Documentation

- [SCOPE.md](./SCOPE.md) — Every data anomaly found and how it was handled + database schema
- [DECISIONS.md](./DECISIONS.md) — Each significant decision with options considered
- [AI_USAGE.md](./AI_USAGE.md) — AI tools, prompts, and error cases

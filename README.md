# E-Fisheries Management System

E-Fisheries is a full-stack fisheries management platform for fish farmers and aquaculture operators. It combines pond, stock, growth, water-quality, weather, fish-health, feeding, finance, market, and analytics workflows in one application.

The project consists of a React frontend and a Django REST Framework backend backed by PostgreSQL.

## Features

### Farm operations

- User registration, login, profile management, and token-based authentication
- Pond creation, editing, status management, and ownership isolation
- Fish-stock and batch management
- Growth history, average weight, average length, mortality, and feed usage records

### Monitoring and recommendations

- Water-quality readings, thresholds, history, comparison, and trend data
- Weather dashboards using OpenWeather data
- Fish-health records with symptoms, severity, disease matching, recommendations, and alerts
- Treatment plans, treatment tracking, and treatment expense integration
- Feeding recommendations based on biomass, growth, water quality, weather, and feeding history
- Optional Gemini-powered recommendations with formula-based fallbacks
- Market-price analysis by fish species and Bangladesh division

### Finance and marketplace

- Financial accounts, income and expense categories, transactions, budgets, and reports
- Automatic financial records for feed use, treatments, stocking, labor, and harvest sales
- Market listings, buyer orders, seller status transitions, stock reservation, and transaction tracking
- Public store ordering and guest cart ordering for configured store listings
- Dashboard summaries, profit/loss reporting, pond performance, and analytics

## Technology Stack

### Frontend

- React 19
- React Router
- Vite
- JavaScript and CSS

### Backend

- Python 3.13 recommended
- Django 6
- Django REST Framework
- `django-cors-headers`
- Token authentication

### Data and integrations

- PostgreSQL
- OpenWeather API
- Google Gemini API through the shared core service

## Repository Structure

```text
E-fisheries/
├── backend/
│   ├── backend/          # Django settings, URLs, ASGI, and WSGI
│   ├── core/             # Authentication, notifications, shared services
│   ├── ponds/            # Pond management
│   ├── stocks/           # Fish-stock management
│   ├── growth/           # Growth records
│   ├── water_quality/    # Water-quality readings and analytics
│   ├── weather/          # Weather reports and analysis
│   ├── fish_health/      # Disease, health, alerts, and treatments
│   ├── feeding/          # Feeding recommendations and sessions
│   ├── financials/       # Accounts, transactions, budgets, and reports
│   ├── market_analysis/  # Market price snapshots and dashboard
│   ├── market_bridge/    # Listings, orders, and public store
│   ├── manage.py
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
├── requirements.txt
└── README.md
```

## Prerequisites

Install the following before setup:

- Python 3.11 or newer; Python 3.13 is used by the current development environment
- Node.js 18 or newer and npm
- PostgreSQL 14 or newer
- API keys are optional for local development, but required for live weather or Gemini features

## PostgreSQL Setup

Create the application database and a PostgreSQL user with access to it:

```sql
CREATE DATABASE efisheries_db;
CREATE USER efisheries_user WITH PASSWORD 'replace-this-password';
GRANT ALL PRIVILEGES ON DATABASE efisheries_db TO efisheries_user;
```

For PostgreSQL versions that require explicit schema privileges:

```sql
\c efisheries_db
GRANT ALL ON SCHEMA public TO efisheries_user;
```

## Backend Setup

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
cp .env.example .env
```

Edit `backend/.env` with the PostgreSQL credentials. The backend always uses the database named `efisheries_db`.

Apply migrations and create an administrator:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Start the API server:

```bash
python manage.py runserver
```

The backend is available at `http://127.0.0.1:8000/`.

The Django admin is available at `http://127.0.0.1:8000/admin/`.

## Frontend Setup

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend is normally available at `http://127.0.0.1:5173/`.

The frontend environment file should contain:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Useful frontend commands:

```bash
npm run dev       # Start Vite development server
npm run build     # Create a production build
npm run preview   # Preview the production build
npm run lint      # Run ESLint
```

## Environment Variables

Backend variables are documented in `backend/.env.example`.

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Yes in production | Django secret key |
| `DEBUG` | No | Enables Django debug mode |
| `ALLOWED_HOSTS` | No | Comma-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | No | Frontend origins allowed by the API |
| `DB_USER` | Yes | PostgreSQL username |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `DB_HOST` | No | PostgreSQL host, default `localhost` |
| `DB_PORT` | No | PostgreSQL port, default `5432` |
| `OPENWEATHER_API_KEY` | Optional | Enables OpenWeather requests |
| `OPENWEATHER_TIMEOUT_SECONDS` | No | Weather request timeout |
| `OPENWEATHER_GEOCODING_COUNTRY_CODE` | No | Geocoding country filter, default `BD` |
| `WEATHER_REPORT_CACHE_MINUTES` | No | Weather report cache duration |
| `GEMINI_API_KEY` | Optional | Enables Gemini recommendations |
| `GEMINI_MODEL` | No | Gemini model name |
| `GEMINI_TIMEOUT_SECONDS` | No | Gemini request timeout |

When API keys are absent or an external service fails, the application uses local fallback logic for supported recommendation workflows.

## Authentication

The API uses Django REST Framework token authentication. Login returns a token that should be sent on protected requests:

```http
Authorization: Token <your-token>
```

Core authentication endpoints:

```text
POST /api/auth/signup/
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/auth/me/
GET  /api/auth/profile/
```

Most operational endpoints require an authenticated user. Data is scoped to the authenticated user's ponds and related records; staff users can access broader administrative data where implemented.

## API Modules

All endpoints are served from the backend API base URL.

| Module | Base paths | Main capabilities |
| --- | --- | --- |
| Core | `/api/` | Auth, homepage, notifications, AI advisor |
| Ponds | `/api/ponds/` | Pond CRUD |
| Stocks | `/api/ponds/<pond_id>/stocks/` | Stock CRUD by pond |
| Growth | `/api/stocks/<stock_id>/growth/` | Growth history and details |
| Water quality | `/api/water-quality/` | Readings, dashboard, history, graph, comparison |
| Weather | `/api/weather/` | Weather dashboard and reports |
| Fish health | `/api/fish-health/` | Diseases, health records, treatments, alerts, recommendations |
| Feeding | `/api/feeding/` | Dashboard, history, recommendation acceptance/editing, session completion |
| Financials | `/api/financials/` | Accounts, categories, transactions, budgets, reports, analytics |
| Market analysis | `/api/market-analysis/` | Market dashboard and price data |
| Market bridge | `/api/market-bridge/` | Listings, orders, public store, price recommendations, tracking |

Important feeding endpoints:

```text
GET   /api/feeding/dashboard/?pond=<pond_id>
GET   /api/feeding/history/?pond=<pond_id>
POST  /api/feeding/recommendations/<id>/accept/
PATCH /api/feeding/recommendations/<id>/edit/
POST  /api/feeding/sessions/<id>/complete/
```

Important fish-health endpoints:

```text
GET  /api/fish-health/diseases/
GET  /api/fish-health/health-records/
POST /api/fish-health/health-records/
GET  /api/fish-health/treatments/
POST /api/fish-health/treatments/<id>/tracking/
GET  /api/fish-health/dashboard/
GET  /api/fish-health/recommendation/
GET  /api/fish-health/alerts/
```

Important financial endpoints:

```text
GET  /api/financials/dashboard/
GET  /api/financials/profit-loss/
GET  /api/financials/pond-performance/
GET  /api/financials/analytics/
POST /api/financials/automatic-records/
```

Important marketplace endpoints:

```text
GET  /api/market-bridge/listings/
POST /api/market-bridge/listings/
GET  /api/market-bridge/orders/
POST /api/market-bridge/public-store/orders/
POST /api/market-bridge/public-store/cart-orders/
GET  /api/market-bridge/public-store/track/<transaction_code>/
```

## Testing

The Django test suite uses PostgreSQL because the project is configured with the PostgreSQL backend.

Run the complete backend suite:

```bash
cd backend
python manage.py test
```

Run an individual module:

```bash
python manage.py test fish_health
python manage.py test feeding
python manage.py test financials
python manage.py test market_bridge
```

Tests are organized by responsibility where coverage has been expanded:

```text
<app>/tests/test.py           # API and workflow tests
<app>/tests/test_models.py    # Model validation and behavior
<app>/tests/test_services.py  # Service and calculation tests
<app>/tests/test_serializers.py
```

## Development Workflow

1. Start PostgreSQL and confirm the `efisheries_db` database is available.
2. Activate the backend virtual environment.
3. Run migrations after pulling schema changes.
4. Start Django and Vite in separate terminals.
5. Create a user and pond before testing pond-scoped modules.
6. Run the focused module tests before running the full suite.
7. Run `npm run lint` and `npm run build` before frontend changes are considered complete.

## Common Troubleshooting

### PostgreSQL connection errors

Confirm PostgreSQL is running and that `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `backend/.env` match the local server. The database name is fixed as `efisheries_db` in the Django settings.

### CORS errors in the browser

Add the frontend origin to `CORS_ALLOWED_ORIGINS` in `backend/.env`, for example:

```env
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

Restart Django after changing environment variables.

### Weather or AI features are unavailable

Check the relevant API key and timeout settings. Core recommendation flows provide fallback behavior when external APIs are not configured, but live weather data requires `OPENWEATHER_API_KEY`.

### Migrations are missing

Run:

```bash
python manage.py showmigrations
python manage.py makemigrations
python manage.py migrate
```

Review generated migrations before committing them.

## Production Notes

Before deployment:

- Set `DEBUG=False`.
- Use a strong, private `SECRET_KEY`.
- Configure production `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.
- Store PostgreSQL and API credentials outside version control.
- Serve Django through a production WSGI or ASGI server.
- Configure static and media file storage.
- Run `python manage.py check --deploy`.
- Apply migrations during deployment.
- Set up backups for PostgreSQL and uploaded media.

## License

No license file is currently included in the repository.


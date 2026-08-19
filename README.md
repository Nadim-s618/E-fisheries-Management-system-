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

Edit `backend/.env` with the PostgreSQL credentials. Local development normally uses the database named `efisheries_db`; production can use another PostgreSQL database, including a Supabase project.

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
| `DB_NAME` | No | PostgreSQL database name, default `efisheries_db` |
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

### Static test inventory

The following counts were identified by static inspection of the source tree:

| Area | Observed test files / intent | Test files | Test blocks/methods |
|---|---|---:|---:|
| Authentication and pages | `AuthPage`, `HomePage`, `DashboardPage`, `FishStorePage`, and `ProfilePage` tests | 5 | 13 |
| Dashboard components | Sidebar, summary, topbar, pond management, and stock/growth management | 5 | 14 |
| Domain components | AI advisor, feeding, financials, fish health, market analysis, market bridge, water quality, and weather | 8 | 44 |
| Frontend integration | Auth, Dashboard, Feeding, Financials, FishHealth, FishStore, HomePage, MarketBridge, Profile, and WaterQuality | 10 | 20 |
| **Frontend total** |  | **28** | **91** |
| Backend models/services/serializers | 11 model-test modules covering persistence and validation; 8 serializer-test modules covering representation and input validation; and 11 service-test modules covering recommendations, calculations, ownership rules, notifications, and integrations | 30 | 188 |
| Backend API/workflow and specialist tests | 9 app workflow modules and 2 explicit API modules covering authentication, ponds, growth, feeding, financials, fish health, market analysis, market bridge, water quality, and weather; specialist modules cover water-quality analysis plus weather analysis and report caching | 25 | 104 |
| **Backend total** |  | **55** | **292** |

These are source-level inventory counts, not runtime pass/fail results or coverage percentages. The frontend integration count includes `Auth.integration.test.jsx`; the backend count includes `tests/__init__.py` files and specialist test modules.

## Development Workflow

1. Start PostgreSQL and confirm the `efisheries_db` database is available.
2. Activate the backend virtual environment.
3. Run migrations after pulling schema changes.
4. Start Django and Vite in separate terminals.
5. Create a user and pond before testing pond-scoped modules.
6. Run the focused module tests before running the full suite.
7. Run `npm run lint` and `npm run build` before frontend changes are considered complete.

## Deployment

The recommended production layout is:

```text
Vercel       -> React/Vite frontend
Render       -> Django REST API
Supabase     -> PostgreSQL database and optional object storage
```

The frontend and backend are deployed separately. The frontend must never contain database passwords, Supabase service-role keys, or other backend secrets.

### Deploy the frontend to Vercel

Create a Vercel project connected to the repository and use these settings:

```text
Root Directory: frontend
Build Command:  npm run build
Output Directory: dist
```

Set this Vercel environment variable for Production, Preview, and Development as needed:

```env
VITE_API_BASE_URL=https://your-render-service.onrender.com/api
```

The `frontend/vercel.json` file contains the single-page application rewrite required by React Router. Every frontend deployment should be tested at `/`, `/login`, `/signup`, and `/fish-store`.

The public homepage content is bundled in `frontend/src/data/homepage.js`, so the first homepage render does not depend on the backend `/api/homepage/` request.

### Deploy the backend to Render

Create a Render Web Service connected to the repository with:

```text
Root Directory: backend
Build Command: pip install -r ../requirements.txt && python manage.py collectstatic --noinput
Start Command: gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT
```

Run migrations as a Render pre-deploy command when available:

```bash
python manage.py migrate
```

Set these Render environment variables:

```env
DEBUG=False
SECRET_KEY=<long-random-production-secret>
ALLOWED_HOSTS=your-render-service.onrender.com
CORS_ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
DB_NAME=<database-name>
DB_USER=<database-user>
DB_PASSWORD=<database-password>
DB_HOST=<database-host>
DB_PORT=5432
```

If a custom frontend domain is used, add it to both `CORS_ALLOWED_ORIGINS` and the Vercel project configuration as appropriate. Separate origins with commas and do not add trailing slashes.

Render free web services may sleep after inactivity, which causes a slow first API request after the service wakes. A paid instance avoids this cold-start behavior.

### Use Supabase for PostgreSQL

Supabase can host the complete Django PostgreSQL database while Render hosts the API. The frontend does not connect directly to the database.

For a persistent Django backend, copy the Supabase session-pooler connection details from the Supabase Dashboard's Connect panel into Render:

```env
DB_NAME=postgres
DB_USER=postgres.<project-ref>
DB_PASSWORD=<supabase-database-password>
DB_HOST=aws-<region>.pooler.supabase.com
DB_PORT=5432
```

Use the connection values supplied by Supabase for the specific project rather than copying the example host above. Keep the database password only in Render environment variables and local untracked `.env` files.

To move an existing local database to Supabase, create a backup and restore it into the Supabase database using the connection details from the Supabase dashboard:

```bash
pg_dump -h localhost -U <local-user> -d efisheries_db --no-owner --no-privileges > efisheries.sql
psql "<supabase-connection-string>" < efisheries.sql
```

After configuring Render, verify the schema with:

```bash
python manage.py migrate
python manage.py check --deploy
```

Supabase Storage is optional. When `SUPABASE_S3_ENDPOINT` is empty, this project uses local filesystem storage for development. When the Supabase S3 endpoint and credentials are configured, uploaded profile and listing images use Supabase Storage. Render's local filesystem should not be treated as permanent production media storage.

### Production deployment checklist

- Set `DEBUG=False`.
- Generate a new production `SECRET_KEY`.
- Configure the exact Render and Vercel origins.
- Configure the Supabase or other PostgreSQL connection in Render.
- Run migrations before serving traffic.
- Configure Supabase Storage or another durable media provider.
- Set `OPENWEATHER_API_KEY` if live weather data is required.
- Set `GEMINI_API_KEY` if Gemini-powered recommendations are required.
- Confirm database backups and recovery procedures.
- Test signup, login, dashboard loading, image upload, weather, and public store ordering after deployment.

## Performance Notes

The initial homepage is static and renders from the frontend bundle. Authenticated dashboard data is loaded after login and can involve multiple API calls for ponds, stock, water quality, and notifications.

For faster first visits:

- Keep the frontend deployed as a Vercel static build.
- Avoid putting secrets or database calls in frontend code.
- Keep the Render backend awake with a paid instance if cold starts are unacceptable.
- Load weather, finance, market, and feeding sections when the user opens them.
- Prefer aggregated dashboard endpoints over one request per pond as the application grows.
- Use browser DevTools Network timing to identify whether the delay is the Vercel bundle, Render cold start, API response, database query, or external weather/AI service.

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

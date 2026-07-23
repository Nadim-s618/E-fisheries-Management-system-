# E-Fisheries Management System

A full-stack application for fish farmers to manage ponds, fish-stock batches, and growth measurements. The React client consumes a Django REST Framework API backed by PostgreSQL. Records are ownership-aware: a user owns ponds, a pond owns stock batches, and a stock batch owns growth records.

## Features

- Account registration, login, logout, and protected routes
- Pond CRUD with capacity, source, status, and location data
- Fish-stock CRUD scoped to a pond
- Growth-record CRUD scoped to a stock batch
- Growth analysis including biomass, survival, daily growth rate, and optional FCR
- Django admin and server-side validation/database constraints
- Token-auth compatibility for the existing frontend plus JWT endpoints for new clients

## Tech stack

- Frontend: React 19, React Router, Vite, ESLint
- Backend: Python, Django, Django REST Framework
- Database: PostgreSQL (via psycopg)
- Authentication: DRF Token Authentication and Simple JWT

## Project structure

```text
.
├── backend/
│   ├── backend/          # Django settings and root routes
│   ├── core/             # Authentication and homepage content
│   ├── ponds/            # Pond domain
│   ├── stocks/           # Fish-stock domain
│   ├── growth/           # Growth-record domain
│   ├── .env.example
│   └── manage.py
├── frontend/             # React/Vite application
├── docs/
│   ├── screenshots/
│   ├── diagrams/
│   └── sprint-reports/
├── requirements.txt
├── setup.sh              # macOS/Linux bootstrap
├── setup.ps1             # Windows PowerShell bootstrap
└── Makefile
```

## Prerequisites

- Python 3.12 or later
- Node.js 20 or later (includes npm)
- PostgreSQL 14 or later
- Git

## Installation

```bash
git clone https://github.com/<your-org>/E-fisheries-Management-system-.git
cd E-fisheries-Management-system-
```

### PostgreSQL setup

Create a local database and a dedicated user. Substitute secure values for the password.

```bash
psql postgres
CREATE USER efisheries_user WITH PASSWORD 'replace-with-a-strong-password';
CREATE DATABASE efisheries_db OWNER efisheries_user;
\q
```

On Windows, run these SQL commands in `psql` (installed with PostgreSQL) or pgAdmin's Query Tool.

### Configure environment variables

Copy the backend template and update the values for your database. The bootstrap scripts do this copy when the file does not exist.

```bash
cp backend/.env.example backend/.env
```

Required backend variables:

| Variable | Purpose | Development example |
| --- | --- | --- |
| `SECRET_KEY` | Django cryptographic key | a new long random value |
| `DEBUG` | Enables development debug pages | `True` |
| `ALLOWED_HOSTS` | Comma-separated Django hosts | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Browser origins allowed to call the API | `http://localhost:5173` |
| `DB_NAME` | PostgreSQL database name | `efisheries_db` |
| `DB_USER` | PostgreSQL role | `efisheries_user` |
| `DB_PASSWORD` | PostgreSQL password | your local password |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |

The optional frontend configuration is in `frontend/.env.example`. `VITE_API_BASE_URL` defaults to `http://127.0.0.1:8000/api` and normally needs no change for local development.

## Quick setup

macOS/Linux:

```bash
chmod +x setup.sh
./setup.sh
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

The scripts create `.venv`, install Python and Node dependencies, copy `backend/.env.example` when necessary, create project folders, and run migrations. PostgreSQL must be running and the database credentials in `backend/.env` must be valid before the migration step.

## Manual setup and running the project

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser  # optional, for /admin/
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/` and the Django admin at `http://127.0.0.1:8000/admin/`.

### Frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the URL Vite prints, normally `http://localhost:5173`.

## Make commands

On macOS/Linux after `./setup.sh`:

```bash
make setup       # run the bootstrap script
make backend     # start Django
make frontend    # start Vite
make migrate     # apply migrations
make superuser   # create a Django admin user
make test        # run Django tests
make lint        # run the frontend linter
```

## API modules

All routes are prefixed with `/api/`. Collection/detail endpoints use conventional `GET`, `POST`, `PATCH`, and `DELETE` semantics.

| Module | Endpoints |
| --- | --- |
| Public content | `GET /homepage/` |
| Existing application auth | `POST /auth/signup/`, `/auth/login/`, `/auth/logout/`; `GET /auth/me/` |
| JWT for new API clients | `POST /auth/token/`, `POST /auth/token/refresh/` |
| Ponds | `GET, POST /ponds/`; `GET, PUT, PATCH, DELETE /ponds/{id}/` |
| Stocks | `GET, POST /ponds/{pond_id}/stocks/`; `GET, PUT, PATCH, DELETE /stocks/{id}/` |
| Growth | `GET, POST /stocks/{stock_id}/growth/`; `GET, PUT, PATCH, DELETE /growth/{id}/` |

The existing React application uses `Authorization: Token <key>` from `/auth/login/`. JWT clients use `Authorization: Bearer <access-token>` and obtain tokens with Django's username/password credentials at `/auth/token/`. Both are supported to avoid breaking existing consumers.

## Testing and quality checks

```bash
source .venv/bin/activate
cd backend && python manage.py check && python manage.py test
cd ../frontend && npm run lint && npm run build
```

## Security and repository hygiene

Never commit `backend/.env`, virtual environments, `node_modules`, database dumps, SQLite files, uploaded media, or generated static assets. The root `.gitignore` covers these files. Use a unique `SECRET_KEY`, `DEBUG=False`, HTTPS, restricted hosts/origins, and a managed PostgreSQL service in production.

## Future improvements

- Add API versioning, OpenAPI documentation, pagination, filtering, and throttling
- Replace or retire the legacy opaque-token flow once all clients use JWT refresh tokens
- Add CI for backend tests, frontend lint/build, dependency scanning, and deployment checks
- Add object storage for uploads, structured logging, error tracking, backups, and health checks
- Add feeding, water-quality, health, harvest, finance, reporting, and notification modules

## Contributors

Add project contributors here, for example:

- Your Name — full-stack development

## License

Add the agreed project license before publishing or distributing the application.

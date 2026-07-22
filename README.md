# E-Fisheries

E-Fisheries is a Django REST API and React/Vite frontend for managing fisheries operations such as pond monitoring, feeding, stock health, finance, and market connections.

## Project Structure

```text
backend/
  backend/          Django project settings and root URLs
  store/            Current API app for auth and homepage content
frontend/
  src/
    context/        Auth context and hooks
    lib/            API client helpers
    pages/          Route-level React pages
```

## Backend Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp backend/.env.example backend/.env
cd backend
python manage.py migrate
python manage.py runserver
```

The backend always uses PostgreSQL with the database name `efisheries_db`.
Set `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `backend/.env` if your local PostgreSQL setup needs them.
The backend runs at `http://127.0.0.1:8000` by default.

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend runs at `http://localhost:5173` by default.

## Quality Checks

```bash
cd backend
python manage.py test

cd ../frontend
npm run lint
npm run build
```

## Notes

- Keep real `.env` files out of git.
- Use `backend/.env.example` and `frontend/.env.example` as templates for local setup.
- As the domain grows, split the current `store` Django app into clearer apps such as `accounts`, `ponds`, `water_quality`, `feeding`, `health`, `marketplace`, and `finance`.

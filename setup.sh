#!/usr/bin/env bash
# Bootstrap the backend and frontend for macOS/Linux development.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

command -v python3 >/dev/null || {
  echo "Python 3 is required. Install Python 3.12+ and run this script again."
  exit 1
}
command -v npm >/dev/null || {
  echo "Node.js and npm are required. Install Node.js 20+ and run this script again."
  exit 1
}

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$PROJECT_ROOT/requirements.txt"

if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
  cp "$PROJECT_ROOT/backend/.env.example" "$PROJECT_ROOT/backend/.env"
  echo "Created backend/.env from the example. Update its database credentials."
fi

mkdir -p "$PROJECT_ROOT/docs/screenshots" \
  "$PROJECT_ROOT/docs/diagrams" \
  "$PROJECT_ROOT/docs/sprint-reports" \
  "$PROJECT_ROOT/backend/media" \
  "$PROJECT_ROOT/backend/staticfiles"

echo "Installing frontend dependencies..."
(cd "$PROJECT_ROOT/frontend" && npm ci)

echo "Applying Django migrations..."
(cd "$PROJECT_ROOT/backend" && python manage.py migrate)

cat <<'EOF'

Setup complete.

Start the backend:  source .venv/bin/activate && cd backend && python manage.py runserver
Start the frontend: cd frontend && npm run dev

The frontend is served at http://localhost:5173 and the API at http://127.0.0.1:8000/api/.
EOF

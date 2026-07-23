# Bootstrap the backend and frontend for Windows PowerShell development.
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectRoot '.venv'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python 3.12+ is required. Install it and run this script again.'
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'Node.js 20+ and npm are required. Install them and run this script again.'
}

if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
}

$Python = Join-Path $VenvDir 'Scripts\python.exe'
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $ProjectRoot 'requirements.txt')

$EnvFile = Join-Path $ProjectRoot 'backend\.env'
if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $ProjectRoot 'backend\.env.example') $EnvFile
    Write-Host 'Created backend/.env from the example. Update its database credentials.'
}

New-Item -ItemType Directory -Force -Path @(
    (Join-Path $ProjectRoot 'docs\screenshots'),
    (Join-Path $ProjectRoot 'docs\diagrams'),
    (Join-Path $ProjectRoot 'docs\sprint-reports'),
    (Join-Path $ProjectRoot 'backend\media'),
    (Join-Path $ProjectRoot 'backend\staticfiles')
) | Out-Null

Write-Host 'Installing frontend dependencies...'
Push-Location (Join-Path $ProjectRoot 'frontend')
npm ci
Pop-Location

Write-Host 'Applying Django migrations...'
Push-Location (Join-Path $ProjectRoot 'backend')
& $Python manage.py migrate
Pop-Location

Write-Host @"

Setup complete.

Start the backend:  .\.venv\Scripts\Activate.ps1; cd backend; python manage.py runserver
Start the frontend: cd frontend; npm run dev

The frontend is served at http://localhost:5173 and the API at http://127.0.0.1:8000/api/.
"@

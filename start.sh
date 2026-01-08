#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
VENV_DIR="${BACKEND_DIR}/.venv"

if [ ! -d "${VENV_DIR}" ]; then
  echo "Creating virtual environment..."
  python3.12 -m venv "${VENV_DIR}"
else
  echo "Upgrading virtual environment..."
  python3.12 -m venv --upgrade "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

cd "${BACKEND_DIR}"
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Building frontend..."
cd "${ROOT_DIR}/frontend"
npm install
npm run build

echo "Copying frontend build into backend static directory..."
mkdir -p "${BACKEND_DIR}/app/static"
cp -r dist/* "${BACKEND_DIR}/app/static/"

cd "${BACKEND_DIR}"
echo "Starting app on port 5050..."
exec gunicorn -w 4 -b 0.0.0.0:5050 --worker-class eventlet wsgi:app

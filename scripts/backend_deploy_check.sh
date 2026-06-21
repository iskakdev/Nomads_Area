#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/Nomads_Area}"
APP_DIR="${APP_DIR:-$PROJECT_DIR/nomads_area}"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/venv}"

cd "$PROJECT_DIR"
git pull --ff-only origin main

source "$VENV_DIR/bin/activate"
cd "$APP_DIR"

python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run

sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
sudo systemctl is-active nomadsarea nomadsarea-celery

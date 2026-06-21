#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/Nomads_Area}"
APP_DIR="${APP_DIR:-$PROJECT_DIR/nomads_area}"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/venv}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/nomads-area}"

mkdir -p "$BACKUP_DIR"

cd "$APP_DIR"
source "$VENV_DIR/bin/activate"

DB_NAME="$(
  python manage.py shell -c 'from django.conf import settings; print(settings.DATABASES["default"]["NAME"])' \
    | tail -1
)"

BACKUP_FILE="$BACKUP_DIR/db-${DB_NAME}-$(date +%F-%H%M).dump"

sudo -u postgres pg_dump -Fc "$DB_NAME" -f "$BACKUP_FILE"
ls -lh "$BACKUP_FILE"

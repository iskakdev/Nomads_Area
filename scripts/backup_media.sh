#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/Nomads_Area}"
APP_DIR="${APP_DIR:-$PROJECT_DIR/nomads_area}"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/venv}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/nomads-area}"

mkdir -p "$BACKUP_DIR"

cd "$APP_DIR"
source "$VENV_DIR/bin/activate"

MEDIA_ROOT="$(
  python manage.py shell -c 'from django.conf import settings; print(settings.MEDIA_ROOT)' \
    | tail -1
)"

BACKUP_FILE="$BACKUP_DIR/media-$(date +%F-%H%M).tar.gz"

tar -czf "$BACKUP_FILE" -C "$(dirname "$MEDIA_ROOT")" "$(basename "$MEDIA_ROOT")"
ls -lh "$BACKUP_FILE"

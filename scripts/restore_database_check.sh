#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/db-backup.dump" >&2
  exit 2
fi

BACKUP_FILE="$1"
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 2
fi

RESTORE_DB="${RESTORE_DB:-nomads_restore_check_$(date +%Y%m%d_%H%M%S)}"

cleanup() {
  sudo -u postgres dropdb --if-exists "$RESTORE_DB" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sudo -u postgres createdb "$RESTORE_DB"
sudo -u postgres pg_restore --clean --if-exists --no-owner --no-privileges -d "$RESTORE_DB" "$BACKUP_FILE"

TABLE_COUNT="$(
  sudo -u postgres psql -d "$RESTORE_DB" -tAc \
    "select count(*) from information_schema.tables where table_schema = 'public';"
)"

if [[ "$TABLE_COUNT" -lt 1 ]]; then
  echo "Restore failed: restored database has no public tables" >&2
  exit 1
fi

echo "restore check OK: $BACKUP_FILE restored into $RESTORE_DB with $TABLE_COUNT public tables"

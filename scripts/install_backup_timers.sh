#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/root/Nomads_Area}"
SYSTEMD_DIR="${SYSTEMD_DIR:-$PROJECT_DIR/deploy/systemd}"

sudo install -m 0644 "$SYSTEMD_DIR/nomads-backup-database.service" /etc/systemd/system/
sudo install -m 0644 "$SYSTEMD_DIR/nomads-backup-database.timer" /etc/systemd/system/
sudo install -m 0644 "$SYSTEMD_DIR/nomads-backup-media.service" /etc/systemd/system/
sudo install -m 0644 "$SYSTEMD_DIR/nomads-backup-media.timer" /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now nomads-backup-database.timer nomads-backup-media.timer
sudo systemctl list-timers 'nomads-backup-*' --no-pager

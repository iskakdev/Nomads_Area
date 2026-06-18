#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_URL:?Set TARGET_URL to a read-only API endpoint}"

case "$TARGET_URL" in
  *nomadsarea.com*)
    if [[ "${ALLOW_PRODUCTION:-no}" != "yes" ]]; then
      echo "Production target blocked. Set ALLOW_PRODUCTION=yes during an approved test window."
      exit 2
    fi
    ;;
esac

if ! command -v k6 >/dev/null 2>&1; then
  echo "k6 is not installed. Install it on the separate load-generator VPS."
  exit 1
fi

status="$(curl --max-time 10 --silent --show-error --output /dev/null \
  --write-out '%{http_code}' "$TARGET_URL")"

if [[ "$status" != "200" ]]; then
  echo "Preflight failed: expected HTTP 200, received HTTP $status"
  exit 3
fi

mkdir -p loadtest/results
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"

k6 run \
  --summary-export "loadtest/results/summary-${timestamp}.json" \
  loadtest/tour-detail.js

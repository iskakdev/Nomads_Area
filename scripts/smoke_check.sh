#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://www.nomadsarea.com}"
TOUR_ID="${TOUR_ID:-54}"

curl -fsS "$BASE_URL/healthz/" >/dev/null
curl -fsS "$BASE_URL/readyz/" >/dev/null

for locale in ru en es fr de; do
  curl -fsS "$BASE_URL/api/$locale/tours/$TOUR_ID/" >/dev/null
  echo "$locale tour detail OK"
done

curl -fsS "$BASE_URL/api/ru/attractions/?country=Казахстан" >/dev/null
echo "attractions country filter OK"

PAYMENT_CODE="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE_URL/api/en/payments/finikpay/webhook/")"
if [[ "$PAYMENT_CODE" != "404" ]]; then
  echo "Expected removed payment endpoint to return 404, got $PAYMENT_CODE" >&2
  exit 1
fi

echo "smoke checks OK"

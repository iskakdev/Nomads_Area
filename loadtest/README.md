# Nomads Area load test

Run the generator from a VPS separate from the application server. The test
uses only a read-only tour detail endpoint and treats redirects, throttling and
server errors as failures.

## Production preparation

Configure Django to use the shared Redis cache and temporarily raise only the
anonymous read limit:

```env
CACHE_URL=redis://127.0.0.1:6379/1
CACHE_KEY_PREFIX=nomads-area
API_CACHE_TIMEOUT=60
DRF_ANON_THROTTLE_RATE=1000000/minute
```

Restart Gunicorn and verify that repeated requests return `200`. Do not change
`DRF_FORMS_THROTTLE_RATE`; POST forms are outside this test.

## Run

Install k6 on the load-generator VPS, copy this directory there, then run:

```bash
TARGET_URL=https://www.nomadsarea.com/api/en/tours/54/ \
ALLOW_PRODUCTION=yes \
VUS_LOW=10 \
VUS_HIGH=50 \
./loadtest/run.sh
```

Increase `VUS_HIGH` in separate runs: `10`, `25`, `50`, `100`, pausing at
least 30 seconds between runs. Stop when p99 exceeds 1.5 seconds, any 5xx
appears, workers time out, CPU stays above 90%, swap grows, or PostgreSQL
connections approach their limit.

The JSON summary is saved under `loadtest/results/`.

## Server monitoring

```bash
sudo journalctl -u nomadsarea -f
```

```bash
watch -n 1 'uptime; free -h; ss -s'
```

```bash
watch -n 2 "sudo -u postgres psql -Atc \"
SELECT state || ': ' || count(*)
FROM pg_stat_activity
GROUP BY state
ORDER BY state;
\""
```

After a production test, restore the normal anonymous rate and restart
Gunicorn. Keep the shared Redis cache enabled.

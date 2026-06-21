# Nomads Area — developer handoff

Этот документ нужен следующему разработчику, чтобы быстро понять текущее состояние проекта, правила работы и критичные места. Не храните здесь секреты, токены, пароли и реальные ключи.

## Repositories and production paths

Backend:

- GitHub: `iskakdev/Nomads_Area`
- Production path: `/root/Nomads_Area`
- Django project path: `/root/Nomads_Area/nomads_area`
- Virtualenv: `/root/Nomads_Area/venv`
- Main service: `nomadsarea`
- Celery service: `nomadsarea-celery`

Frontend:

- GitHub: `kubanych-js/nomads-area`
- Production path: `/root/nomads-area`
- Process manager: PM2
- PM2 process: `nomads-frontend`

Production domain:

- Public site: `https://www.nomadsarea.com`
- Backend API is exposed under `/api/...` through Nginx.

## Current backend stack

- Django 5.2.x
- Django REST Framework
- PostgreSQL
- Redis cache
- Celery
- django-modeltranslation for RU/EN/ES/FR/DE model fields
- django-jazzmin admin
- Optional Sentry, disabled until `SENTRY_DSN` is set
- Optional S3-compatible media storage, disabled until `USE_S3_STORAGE=True`

## Dependency files

There is one canonical backend dependency list:

- `nomads_area/requirements.txt`

The repository-root file exists only as a deploy convenience:

- `requirements.txt` contains `-r nomads_area/requirements.txt`

This allows both commands to work:

```bash
cd /root/Nomads_Area
pip install -r requirements.txt
```

```bash
cd /root/Nomads_Area/nomads_area
pip install -r requirements.txt
```

When adding backend dependencies, update only `nomads_area/requirements.txt`.

## Required production environment

Production env file is on the server:

```bash
/root/Nomads_Area/nomads_area/.env
```

Important variables:

```dotenv
DEBUG=False
SECRET_KEY=...
ALLOWED_HOSTS=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
CACHE_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=https://www.nomadsarea.com,https://nomadsarea.com
```

`DEBUG` must stay `False` in production. If it becomes `True`, Django can expose debug pages with internal settings and stack traces.

## Health and smoke checks

Public health endpoints:

```bash
curl -fsS https://www.nomadsarea.com/api/healthz/
curl -fsS https://www.nomadsarea.com/api/readyz/
```

Full smoke check:

```bash
cd /root/Nomads_Area
bash scripts/smoke_check.sh
```

Expected output includes:

```text
ru tour detail OK
en tour detail OK
es tour detail OK
fr tour detail OK
de tour detail OK
attractions country filter OK
smoke checks OK
```

## Backend deploy

```bash
cd /root/Nomads_Area
git pull --ff-only origin main

source venv/bin/activate
pip install -r requirements.txt

cd nomads_area
python manage.py migrate
python manage.py check

sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
sudo systemctl is-active nomadsarea nomadsarea-celery

cd /root/Nomads_Area
bash scripts/smoke_check.sh
```

## Frontend deploy

```bash
cd /root/nomads-area
git pull --ff-only origin main

rm -rf .next
pnpm build

pm2 restart nomads-frontend --update-env
pm2 save
```

## Backup and restore

Manual database backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_database.sh
```

Manual media backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_media.sh
```

Install automatic systemd timers:

```bash
cd /root/Nomads_Area
bash scripts/install_backup_timers.sh
```

Default schedule:

- DB backup daily at 03:15
- Media backup daily at 03:35
- Backup retention: 14 days

Check timers:

```bash
systemctl list-timers 'nomads-backup-*' --no-pager
journalctl -u nomads-backup-database.service -n 100 --no-pager
journalctl -u nomads-backup-media.service -n 100 --no-pager
```

Check database restore:

```bash
cd /root/Nomads_Area
bash scripts/restore_database_check.sh /var/backups/nomads-area/db-....dump
```

The restore check creates a temporary PostgreSQL database, restores the dump, validates that public tables exist, then drops the temporary database.

## Optional Sentry setup

Sentry is optional and does nothing until `SENTRY_DSN` is set.

Add to `.env`:

```dotenv
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

Then:

```bash
sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
```

Use `SENTRY_TRACES_SAMPLE_RATE=0.0` initially. It sends errors without performance tracing. Raise to `0.05` or `0.1` only when performance data is needed.

## Optional S3/CDN media setup

S3-compatible storage is optional and disabled by default.

Add to `.env` only when the bucket/CDN is ready:

```dotenv
USE_S3_STORAGE=True
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_REGION_NAME=...
AWS_S3_ENDPOINT_URL=...
AWS_S3_CUSTOM_DOMAIN=cdn.example.com
AWS_LOCATION=media
```

Then:

```bash
cd /root/Nomads_Area/nomads_area
source /root/Nomads_Area/venv/bin/activate
python manage.py check
sudo systemctl restart nomadsarea
```

Do not turn on S3 until media migration is planned. Existing local files will not magically move to S3.

## Important business logic

### Active tours

If a tour is inactive, frontend should stop showing it after cache/revalidation, but backend must also reject booking attempts. Backend validation is the final safety layer.

### Bookings

Booking creation validates:

- tour exists;
- tour is active;
- selected tour date belongs to the selected tour;
- extra services belong to the selected tour;
- group tour seats are available;
- duplicate request fingerprints are handled.

### Attractions

Attraction should be one record connected to many tours, not duplicated per tour.

Correct shape:

```text
Attraction
  ├── private tour A
  ├── group tour B
  └── private tour C
```

Country filtering exists for attractions:

```text
/api/ru/attractions/?country=Казахстан
/api/ru/attractions/?country=Kazakhstan
/api/ru/attractions/?country=<country_id>
```

### Quiz branching

Quiz branching must stop after the selected branch. A selected option with `next_question` should lead only to that branch. Other branches should not appear after a concrete branch has been selected.

## Caching rule

The frontend cache/revalidate policy was intentionally left as-is after the latest discussion. Do not change frontend cache behavior casually.

Backend still protects critical actions. Example: even if a stale frontend page shows an inactive tour, backend must reject booking.

## Known operational gotchas

- `https://www.nomadsarea.com/healthz/` may hit frontend/redirects depending on Nginx. Use `/api/healthz/` and `/api/readyz/` for backend health.
- `/api/not-existing-debug-check/` can be interpreted as a locale route. Use `/api/ru/not-existing-debug-check/` to test a real backend 404.
- `DEBUG=False` must be verified after deploy:

```bash
cd /root/Nomads_Area/nomads_area
grep -n '^DEBUG=' .env
curl -sS -i https://www.nomadsarea.com/api/ru/not-existing-debug-check/ | head -40
```

Expected: `404 Not Found`, no Django traceback page.

- Do not run destructive DB commands on production without a fresh backup.
- Do not run mass POST load tests on production. They create real leads/bookings/notifications.

## Tests

Local/full backend tests:

```bash
cd /home/iskhak/PycharmProjects/Nomads_Area
source .venv/bin/activate
python nomads_area/manage.py test nomads_area_app
```

Expected latest count was 39 tests. If PostgreSQL test DB already exists, Django asks whether to delete it; answer `yes` only for local/test DB.

Non-DB checks:

```bash
python nomads_area/manage.py check
python nomads_area/manage.py makemigrations --check --dry-run
python -m compileall nomads_area/nomads_area nomads_area/nomads_area_app
bash -n scripts/*.sh
```

## GitHub Actions

CI workflow was intentionally not committed because pushing workflow files requires a GitHub token with `workflow` scope. The project owner said they will handle this part.

Do not ask for tokens in chat. If CI is added, use a short-lived token with limited repository permissions and workflow scope, or add the workflow through GitHub UI.

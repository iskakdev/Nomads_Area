# Nomads Area — operations checklist

Документ для безопасной эксплуатации production. Не храните здесь пароли, токены, SMTP-ключи и доступы.

## 1. Backend deploy

```bash
cd /root/Nomads_Area
git pull --ff-only origin main

source venv/bin/activate
cd nomads_area

python manage.py migrate
python manage.py check

sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
sudo systemctl is-active nomadsarea nomadsarea-celery
```

## 2. Frontend deploy

```bash
cd /root/nomads-area
git pull --ff-only origin main

rm -rf .next
pnpm build

pm2 restart nomads-frontend --update-env
pm2 save
```

## 3. Database backup

Создавайте backup перед миграциями и крупными изменениями данных.

Ручной backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_database.sh
```

По умолчанию backup хранится в `/var/backups/nomads-area`, старые DB backup старше 14 дней удаляются.

Проверка восстановления backup:

```bash
cd /root/Nomads_Area
bash scripts/restore_database_check.sh /var/backups/nomads-area/db-....dump
```

Скрипт создаёт временную PostgreSQL базу, восстанавливает dump, проверяет наличие таблиц и удаляет временную базу.

## 4. Media backup

Файлы из `MEDIA_ROOT` нужно бэкапить отдельно от PostgreSQL.

Ручной backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_media.sh
```

По умолчанию media backup хранится в `/var/backups/nomads-area`, старые media backup старше 14 дней удаляются.

## 5. Automatic backups

Установить systemd timers:

```bash
cd /root/Nomads_Area
bash scripts/install_backup_timers.sh
```

Расписание:

- DB backup: каждый день в 03:15
- Media backup: каждый день в 03:35

Проверить timers:

```bash
systemctl list-timers 'nomads-backup-*' --no-pager
journalctl -u nomads-backup-database.service -n 100 --no-pager
journalctl -u nomads-backup-media.service -n 100 --no-pager
```

## 6. Media storage / CDN

Сейчас media может храниться на сервере. Для роста проекта лучше вынести media в S3-compatible storage + CDN, чтобы сервер не был единственной точкой хранения фотографий и видео.

Backend уже поддерживает opt-in режим. В `.env`:

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

Если `AWS_S3_CUSTOM_DOMAIN` задан, API будет отдавать media URL через CDN-домен.

После изменения env:

```bash
cd /root/Nomads_Area/nomads_area
source /root/Nomads_Area/venv/bin/activate
python manage.py check
sudo systemctl restart nomadsarea
```

## 7. Error monitoring

Для Sentry достаточно добавить DSN в `.env`:

```dotenv
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

После изменения env:

```bash
sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
```

`SENTRY_TRACES_SAMPLE_RATE=0.0` означает: ошибки отправляются, performance tracing выключен. Если потом понадобится performance monitoring, можно поднять до `0.05` или `0.1`.

## 8. Smoke checks after deploy

```bash
for locale in ru en es fr de; do
  curl -fsS "https://www.nomadsarea.com/api/$locale/tours/54/" >/dev/null \
    && echo "$locale OK" \
    || echo "$locale FAIL"
done
```

```bash
curl -fsS "https://www.nomadsarea.com/api/ru/attractions/?country=Казахстан" >/dev/null \
  && echo "Attractions filter OK"
```

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://www.nomadsarea.com/api/en/payments/finikpay/webhook/
```

Ожидаемо: `404`, потому что онлайн-платежи удалены.

Или одной командой:

```bash
cd /root/Nomads_Area
bash scripts/smoke_check.sh
```

## 9. Load-test rules

Не запускать массовый POST на production. Он создаёт реальные брони/лиды/уведомления.

Для честного GET-теста:

- запускать нагрузку с отдельной VPS;
- заранее проверить, что throttle не превращает тест в поток `429`;
- мониторить `journalctl`, RAM, CPU, PostgreSQL connections;
- прекращать тест при `5xx`, worker timeout, росте swap или p99 выше 2–3 секунд.

Пример wrk:

```bash
/usr/bin/wrk -t2 -c10 -d30s --latency \
  https://www.nomadsarea.com/api/en/tours/54/
```

## 10. Admin data safety

- Если тур выключен через `Активен`, backend не должен принимать новую бронь на этот тур.
- Достопримечательность должна быть одной записью, связанной с несколькими турами, а не дублями.
- Если меняются вопросы квиза, проверяйте ветвление: выбранная ветка не должна показывать вопросы из другой ветки.

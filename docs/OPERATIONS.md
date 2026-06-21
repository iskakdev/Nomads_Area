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

```bash
cd /root/Nomads_Area/nomads_area
source /root/Nomads_Area/venv/bin/activate

DB_NAME=$(python manage.py shell -c \
  'from django.conf import settings; print(settings.DATABASES["default"]["NAME"])' \
  | tail -1)

BACKUP="/var/lib/postgresql/nomads-$(date +%F-%H%M).dump"

sudo -u postgres pg_dump -Fc "$DB_NAME" -f "$BACKUP"
sudo cp "$BACKUP" /root/
sudo ls -lh "$BACKUP" /root/$(basename "$BACKUP")
```

Restore проверять сначала на staging:

```bash
sudo -u postgres createdb nomads_restore_check
sudo -u postgres pg_restore -d nomads_restore_check /path/to/backup.dump
```

## 4. Media backup

Файлы из `MEDIA_ROOT` нужно бэкапить отдельно от PostgreSQL.

Проверить путь:

```bash
cd /root/Nomads_Area/nomads_area
source /root/Nomads_Area/venv/bin/activate
python manage.py shell -c 'from django.conf import settings; print(settings.MEDIA_ROOT)'
```

Минимальный архив:

```bash
tar -czf /root/nomads-media-$(date +%F-%H%M).tar.gz -C /root/Nomads_Area/nomads_area media
```

Для роста проекта лучше вынести media в объектное хранилище/CDN. Тогда сервер не будет единственной точкой хранения фотографий и видео.

## 5. Smoke checks after deploy

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

## 6. Load-test rules

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

## 7. Admin data safety

- Если тур выключен через `Активен`, backend не должен принимать новую бронь на этот тур.
- Достопримечательность должна быть одной записью, связанной с несколькими турами, а не дублями.
- Если меняются вопросы квиза, проверяйте ветвление: выбранная ветка не должна показывать вопросы из другой ветки.

#!/usr/bin/env bash
# Boot Redis + Celery worker/beat + API inside one container (HF Spaces friendly).
set -e

echo "[spaces] starting redis…"
redis-server --daemonize yes --save "" --appendonly no

echo "[spaces] init db…"
python -m app.cli init-db || true

# Optionally seed an admin user from env (ADMIN_EMAIL / ADMIN_PASSWORD)
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
  python -m app.cli create-user --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD" --admin || true
fi

echo "[spaces] starting celery worker…"
celery -A app.core.celery_app.celery worker -l info -P solo &

echo "[spaces] starting celery beat…"
celery -A app.core.celery_app.celery beat -l info &

echo "[spaces] starting API on :${PORT:-7860}…"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}"

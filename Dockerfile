# Single-container image for Hugging Face Spaces (and quick demos).
# Runs Redis + Celery worker + Celery beat + the FastAPI API in one container on port 7860.
# For real deployments use docker-compose.yml (separate services) instead.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    DATABASE_URL=sqlite+pysqlite:////app/storage/jobhunter.db \
    REDIS_URL=redis://localhost:6379/0 \
    CELERY_BROKER_URL=redis://localhost:6379/1 \
    CELERY_RESULT_BACKEND=redis://localhost:6379/2 \
    STORAGE_DIR=/app/storage

RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-server build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend/ /app/
COPY deploy/spaces-start.sh /app/spaces-start.sh
RUN chmod +x /app/spaces-start.sh && mkdir -p /app/storage

EXPOSE 7860
CMD ["/app/spaces-start.sh"]

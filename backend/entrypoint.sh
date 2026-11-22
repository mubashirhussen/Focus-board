#!/bin/sh
set -e

echo "[FocusBoard] Running production container initialization..."

# 1. Run database migrations
echo "[FocusBoard] Checking database and applying Alembic migrations..."
python -m scripts.run_migrations || {
    echo "[FocusBoard] Warning: Alembic upgrade encountered an issue or already up to date. Proceeding to startup..."
}

# 2. Start Uvicorn production server
echo "[FocusBoard] Starting Uvicorn production server on port ${PORT:-8000} with ${WORKERS:-2} workers..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${WORKERS:-2}"

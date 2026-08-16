#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server (ENV=${ENV:-local})..."
if [ "$ENV" = "local" ] || [ -z "$ENV" ]; then
    echo "Live-reload enabled (ENV=local)."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Live-reload disabled (ENV=${ENV})."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi

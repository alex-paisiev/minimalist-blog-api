#!/bin/sh
set -e

if [ "$APP_ENV" != "production" ]; then
    echo "[entrypoint] Non-production environment — seeding database..."
    python /app/scripts/seed.py
fi

exec "$@"

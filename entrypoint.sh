#!/bin/bash
# =============================================================================
# Docker entrypoint — runs before the main CMD
# =============================================================================
set -e

echo "==> Waiting for PostgreSQL to be ready..."
until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(os.environ['DATABASE_URL'])
    print('PostgreSQL is ready.')
except Exception as e:
    print(f'Not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
    echo "    PostgreSQL not ready yet — retrying in 2s..."
    sleep 2
done

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Starting application..."
exec "$@"
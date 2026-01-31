#!/bin/bash
set -e

echo "Waiting for database to be ready..."

# DB ?곌껐 ?湲?(理쒕? 30珥?
for i in {1..30}; do
    if python -c "
import pymysql
import os
from urllib.parse import urlparse

url = urlparse(os.environ.get('DATABASE_URL', ''))
try:
    conn = pymysql.connect(
        host=url.hostname,
        port=url.port or 3306,
        user=url.username,
        password=url.password,
        database=url.path[1:] if url.path else None
    )
    conn.close()
    print('Database is ready!')
    exit(0)
except Exception as e:
    print(f'Waiting... {e}')
    exit(1)
" 2>/dev/null; then
        break
    fi
    echo "Attempt $i/30: Database not ready, waiting..."
    sleep 1
done

echo "Running database migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

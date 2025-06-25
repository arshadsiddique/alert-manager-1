#!/bin/bash
set -e

echo "🚀 Starting Grafana-Jira Alert Manager Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import sys
import time
import psycopg2
from app.core.config import settings

def wait_for_db():
    for i in range(60):
        try:
            conn = psycopg2.connect(settings.DATABASE_URL)
            conn.close()
            print('✅ Database is ready!')
            return
        except psycopg2.OperationalError:
            print(f'⏳ Database not ready yet... ({i+1}/60)')
            time.sleep(1)
    print('❌ Database connection timeout')
    sys.exit(1)

wait_for_db()
"

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Start the FastAPI server
echo "🎯 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
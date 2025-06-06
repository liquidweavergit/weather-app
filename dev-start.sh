#!/bin/bash
set -e

echo "🚀 Starting Temperature Display App in Development Mode"
echo "📁 Working directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "📦 FastAPI version: $(python -c 'import fastapi; print(fastapi.__version__)')"

# Wait for database if DATABASE_URL is set
if [ ! -z "$DATABASE_URL" ]; then
    echo "⏳ Waiting for database connection..."
    python -c "
import asyncpg
import asyncio
import os
import time

async def wait_for_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        for i in range(30):
            try:
                conn = await asyncpg.connect(db_url)
                await conn.close()
                print('✅ Database connection successful')
                return
            except Exception as e:
                print(f'⏳ Waiting for database... ({i+1}/30)')
                time.sleep(2)
        print('❌ Database connection failed after 60 seconds')
    else:
        print('ℹ️  No DATABASE_URL set, skipping database check')

asyncio.run(wait_for_db())
"
fi

# Run database migrations if they exist
if [ -d "migrations" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head || echo "⚠️ Migration failed or no migrations to run"
fi

echo "🌟 Starting development server with hot reload..."
echo "📡 Server will be available at http://localhost:8000"
echo "📚 API docs will be available at http://localhost:8000/docs"
echo "🔄 Hot reload is enabled - changes will be reflected automatically"
echo

# Start the development server
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir /app \
    --reload-exclude "*.pyc" \
    --reload-exclude "__pycache__" \
    --reload-exclude ".git" \
    --reload-exclude "logs" \
    --reload-exclude "data" \
    --log-level debug 
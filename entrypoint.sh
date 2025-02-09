#!/bin/sh

set -e

echo "Применение миграций..."
alembic upgrade head

echo "Запуск Uvicorn..."
exec uvicorn app:app --host 0.0.0.0 --port 8000

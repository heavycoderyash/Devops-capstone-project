#!/bin/sh
# Container entrypoint.
# RUN_MIGRATIONS=true  (default, docker compose): migrate then serve.
# RUN_MIGRATIONS=false (Kubernetes): a Helm hook Job runs migrations once, so
#                      replicas don't race each other on startup.
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'

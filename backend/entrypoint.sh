#!/bin/sh
# =============================================================================
# SkillForge AI — Backend Container Entrypoint
# Sequence:
#   1. Validate required production environment variables
#   2. Wait for PostgreSQL to become reachable
#   3. Run Alembic database migrations
#   4. Start Uvicorn application server
# =============================================================================

set -e  # Exit immediately on any error

echo "=========================================="
echo "  SkillForge AI — Backend Starting Up"
echo "=========================================="

# ---------------------------------------------------------------------------
# 1. Validate required environment variables in production
# ---------------------------------------------------------------------------
if [ "$APP_ENV" = "production" ]; then
    echo "[entrypoint] APP_ENV=production — validating required variables..."

    if [ -z "$SECRET_KEY" ]; then
        echo "[entrypoint] ERROR: SECRET_KEY is not set. Refusing to start in production." >&2
        exit 1
    fi

    if [ -z "$DATABASE_URL" ]; then
        echo "[entrypoint] ERROR: DATABASE_URL is not set. Refusing to start in production." >&2
        exit 1
    fi

    echo "[entrypoint] Required environment variables present."
else
    echo "[entrypoint] APP_ENV=${APP_ENV:-development} — running in development mode."
fi

# ---------------------------------------------------------------------------
# 2. Wait for PostgreSQL to become reachable
#    Uses pg_isready if DATABASE_URL is a PostgreSQL URL, otherwise skips.
# ---------------------------------------------------------------------------
if echo "$DATABASE_URL" | grep -q "postgresql"; then
    echo "[entrypoint] PostgreSQL DATABASE_URL detected — waiting for database to be ready..."

    # Extract host and port from DATABASE_URL
    # Format: postgresql+psycopg2://user:pass@host:port/dbname  OR  postgresql://user:pass@host:port/dbname
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+)[:/].*|\1|')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')
    DB_PORT=${DB_PORT:-5432}

    MAX_RETRIES=30
    RETRY_INTERVAL=2
    RETRIES=0

    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; do
        RETRIES=$((RETRIES + 1))
        if [ "$RETRIES" -ge "$MAX_RETRIES" ]; then
            echo "[entrypoint] ERROR: PostgreSQL at $DB_HOST:$DB_PORT did not become ready after $MAX_RETRIES attempts." >&2
            exit 1
        fi
        echo "[entrypoint] Waiting for PostgreSQL at $DB_HOST:$DB_PORT... (attempt $RETRIES/$MAX_RETRIES)"
        sleep "$RETRY_INTERVAL"
    done

    echo "[entrypoint] PostgreSQL is ready at $DB_HOST:$DB_PORT."
else
    echo "[entrypoint] Non-PostgreSQL DATABASE_URL detected — skipping PostgreSQL readiness check."
fi

# ---------------------------------------------------------------------------
# 3. Run Alembic database migrations
# ---------------------------------------------------------------------------
echo "[entrypoint] Running Alembic migrations (alembic upgrade head)..."

if ! alembic upgrade head; then
    echo "[entrypoint] ERROR: Alembic migration failed. Container will not start." >&2
    exit 1
fi

echo "[entrypoint] Migrations completed successfully."

# ---------------------------------------------------------------------------
# 4. Start FastAPI with Uvicorn — bound to 0.0.0.0 so Docker can reach it
# ---------------------------------------------------------------------------
PORT="${PORT:-8000}"
echo "[entrypoint] Starting Uvicorn on 0.0.0.0:${PORT} ..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers 1 \
    --log-level info

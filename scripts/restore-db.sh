#!/bin/bash
# BudgetFlow Database Restore Script
#
# Restores the budget_flow database from a pg_dump SQL backup file.
# Drops and recreates the database before restoring (clean slate).
#
# Usage:
#   bash scripts/restore-db.sh <backup-file.sql>
#
# For non-interactive use (e.g., tests):
#   echo y | bash scripts/restore-db.sh <backup-file.sql>
#
# Environment variables:
#   DB_PASSWORD         PostgreSQL password (from .env)
#   BUDGET_DB_NAME      Database name        (default: budget_flow)
#   BUDGET_DB_USER      Database user        (default: postgres)
#   BUDGET_DB_HOST      Database host        (default: localhost)
#   BUDGET_DB_PORT      Database port        (default: 5432)

set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "[restore] ERROR: No backup file specified."
    echo "[restore] Usage: bash scripts/restore-db.sh <backup-file.sql>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "[restore] ERROR: File not found: $BACKUP_FILE"
    exit 1
fi

DB_NAME="${BUDGET_DB_NAME:-budget_flow}"
DB_USER="${BUDGET_DB_USER:-postgres}"
DB_HOST="${BUDGET_DB_HOST:-localhost}"
DB_PORT="${BUDGET_DB_PORT:-5432}"
POSTGRES_CONTAINER="${BUDGET_POSTGRES_CONTAINER:-budget-flow-postgres}"
export PGPASSWORD="${DB_PASSWORD:-}"

# Determine how to run psql commands
run_psql() {
    local DB="$1"; shift
    if command -v psql > /dev/null 2>&1; then
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB" "$@"
    elif command -v docker > /dev/null 2>&1; then
        docker exec -i -e PGPASSWORD="${DB_PASSWORD:-}" "$POSTGRES_CONTAINER" \
            psql -U "$DB_USER" -d "$DB" "$@"
    else
        echo "[restore] ERROR: Neither psql nor docker found in PATH." >&2
        return 1
    fi
}

BACKUP_SIZE="$(wc -c < "$BACKUP_FILE")"

echo "[restore] ============================================"
echo "[restore] BudgetFlow Database Restore"
echo "[restore] ============================================"
echo "[restore] Target database : ${DB_NAME} @ ${DB_HOST}:${DB_PORT}"
echo "[restore] Backup file     : ${BACKUP_FILE}"
echo "[restore] Backup size     : ${BACKUP_SIZE} bytes"
echo "[restore] ============================================"
echo ""
printf "[restore] WARNING: This will DROP and recreate '%s'. All current data will be lost. Continue? [y/N] " "$DB_NAME"
read -r CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "[restore] Aborted — database was not modified."
    exit 0
fi

echo ""
echo "[restore] Dropping database '${DB_NAME}'..."
run_psql postgres \
    -c "DROP DATABASE IF EXISTS ${DB_NAME};" \
    -c "CREATE DATABASE ${DB_NAME};" \
    > /dev/null

echo "[restore] Restoring from backup..."
run_psql "$DB_NAME" < "$BACKUP_FILE" > /dev/null

# Sanity check: count users rows
USER_COUNT="$(run_psql "$DB_NAME" -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "?")"

echo ""
echo "[restore] SUCCESS — database '${DB_NAME}' restored."
echo "[restore] Users table row count: ${USER_COUNT}"

#!/bin/bash
# BudgetFlow Database Backup Script
#
# Creates a timestamped pg_dump backup of the budget_flow database.
# Enforces a 7-day retention policy (keeps last 7 scheduled backups).
#
# Usage:
#   bash scripts/backup-db.sh [--db-name NAME] [--output-dir DIR]
#
# Environment variables (with defaults):
#   DB_PASSWORD         PostgreSQL password (from .env)
#   BUDGET_DB_NAME      Database name        (default: budget_flow)
#   BUDGET_DB_USER      Database user        (default: postgres)
#   BUDGET_DB_HOST      Database host        (default: localhost)
#   BUDGET_DB_PORT      Database port        (default: 5432)
#   BUDGET_BACKUP_DIR   Output directory     (default: ./backups)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Defaults (overridable via env or flags) ---
DB_NAME="${BUDGET_DB_NAME:-budget_flow}"
DB_USER="${BUDGET_DB_USER:-postgres}"
DB_HOST="${BUDGET_DB_HOST:-localhost}"
DB_PORT="${BUDGET_DB_PORT:-5432}"
BACKUP_DIR="${BUDGET_BACKUP_DIR:-$REPO_ROOT/backups}"
RETAIN_COUNT=7

# --- Parse optional flags ---
while [ "$#" -gt 0 ]; do
    case "$1" in
        --db-name)    DB_NAME="$2";    shift 2 ;;
        --output-dir) BACKUP_DIR="$2"; shift 2 ;;
        *)
            echo "[backup] Unknown argument: $1"
            echo "[backup] Usage: bash backup-db.sh [--db-name NAME] [--output-dir DIR]"
            exit 1
            ;;
    esac
done

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/budget_flow_${TIMESTAMP}.sql"

echo "[backup] Starting backup of '${DB_NAME}' on ${DB_HOST}:${DB_PORT}..."
echo "[backup] Output: ${BACKUP_FILE}"

# Determine how to run pg_dump:
#   1. Direct binary (pg_dump in PATH) — preferred when running inside postgres container
#   2. Via docker exec — fallback when running from host machine without pg_dump installed
run_pg_dump() {
    if command -v pg_dump > /dev/null 2>&1; then
        # pg_dump is directly available
        PGPASSWORD="${DB_PASSWORD:-}" pg_dump \
            -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    elif command -v docker > /dev/null 2>&1; then
        # Fall back to docker exec into the postgres container
        POSTGRES_CONTAINER="${BUDGET_POSTGRES_CONTAINER:-budget-flow-postgres}"
        docker exec -e PGPASSWORD="${DB_PASSWORD:-}" "$POSTGRES_CONTAINER" \
            pg_dump -U "$DB_USER" "$DB_NAME"
    else
        echo "[backup] ERROR: Neither pg_dump nor docker found in PATH." >&2
        return 1
    fi
}

if run_pg_dump > "$BACKUP_FILE" 2>/tmp/budget_backup_err; then
    SIZE="$(wc -c < "$BACKUP_FILE")"
    echo "[backup] SUCCESS — ${SIZE} bytes written"
else
    ERR="$(cat /tmp/budget_backup_err)"
    echo "[backup] FAILED — ${ERR}"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# --- Retention policy: keep last RETAIN_COUNT scheduled backups ---
# Pattern budget_flow_[0-9]* matches YYYYMMDD_HHMMSS files only,
# NOT pre-stop backups (budget_flow_prestop_*), so those are preserved separately.
echo "[backup] Applying ${RETAIN_COUNT}-day retention..."

EXISTING=$(ls -1 "${BACKUP_DIR}"/budget_flow_[0-9]*.sql 2>/dev/null | wc -l | tr -d ' ')

if [ "$EXISTING" -gt "$RETAIN_COUNT" ]; then
    DELETE_COUNT=$(( EXISTING - RETAIN_COUNT ))
    ls -1 "${BACKUP_DIR}"/budget_flow_[0-9]*.sql | sort | head -n "$DELETE_COUNT" | while read -r OLD_FILE; do
        echo "[backup] Removing old backup: $(basename "$OLD_FILE")"
        rm -f "$OLD_FILE"
    done
fi

REMAINING=$(ls -1 "${BACKUP_DIR}"/budget_flow_[0-9]*.sql 2>/dev/null | wc -l | tr -d ' ')
echo "[backup] Done — ${REMAINING}/${RETAIN_COUNT} scheduled backups in ${BACKUP_DIR}"

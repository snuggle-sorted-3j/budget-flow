#!/bin/bash
# BudgetFlow Custom PostgreSQL Entrypoint
#
# Wraps the official postgres:15-alpine docker-entrypoint.sh to add:
#   - SIGTERM/SIGINT signal trapping
#   - Automatic pg_dump backup before graceful shutdown
#
# Backups are written to /backups (bind-mounted from ./backups on the host).
# File naming: budget_flow_prestop_YYYYMMDD_HHMMSS.sql

set -e

BACKUP_DIR="/backups"
PGUSER="${POSTGRES_USER:-postgres}"
PGDATABASE="${POSTGRES_DB:-budget_flow}"

mkdir -p "$BACKUP_DIR"

# Run pg_dump backup before shutdown
do_backup() {
    local TS
    TS="$(date +%Y%m%d_%H%M%S)"
    local FILE="${BACKUP_DIR}/budget_flow_prestop_${TS}.sql"
    echo "[entrypoint] Container stopping — creating pre-stop backup..."
    if pg_dump -U "$PGUSER" "$PGDATABASE" > "$FILE" 2>/tmp/pg_dump_err; then
        local SIZE
        SIZE="$(wc -c < "$FILE")"
        echo "[entrypoint] Backup OK → $FILE (${SIZE} bytes)"
    else
        echo "[entrypoint] WARNING: backup failed — $(cat /tmp/pg_dump_err)"
        rm -f "$FILE"
    fi
}

# SIGTERM handler: backup, then forward signal to postgres child
_term() {
    echo "[entrypoint] Caught SIGTERM"
    do_backup
    if [ -n "$POSTGRES_PID" ]; then
        kill -TERM "$POSTGRES_PID" 2>/dev/null || true
        wait "$POSTGRES_PID"
    fi
}

# SIGINT handler: backup, then forward signal to postgres child
_int() {
    echo "[entrypoint] Caught SIGINT"
    do_backup
    if [ -n "$POSTGRES_PID" ]; then
        kill -INT "$POSTGRES_PID" 2>/dev/null || true
        wait "$POSTGRES_PID"
    fi
}

trap '_term' TERM
trap '_int' INT

# Start the official postgres entrypoint in the background
# "$@" passes CMD arguments through (e.g., "postgres")
/usr/local/bin/docker-entrypoint.sh "$@" &
POSTGRES_PID=$!

# Wait for postgres — keeps this shell alive to handle signals
wait "$POSTGRES_PID"
EXIT_CODE=$?
exit $EXIT_CODE

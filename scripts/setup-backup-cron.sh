#!/bin/bash
# BudgetFlow Backup Cron Setup
#
# Installs a daily midnight cron job that runs backup-db.sh.
# Idempotent — running this script multiple times is safe.
#
# Usage:
#   bash scripts/setup-backup-cron.sh
#
# To remove the cron job:
#   crontab -l | grep -v "budget-flow-backup" | crontab -

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup-db.sh"

if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "[cron-setup] ERROR: backup-db.sh not found at ${BACKUP_SCRIPT}"
    exit 1
fi

# Cron entry runs at midnight daily
CRON_SCHEDULE="0 0 * * *"
CRON_LOG="/tmp/budget_flow_backup.log"
CRON_CMD="bash ${BACKUP_SCRIPT} >> ${CRON_LOG} 2>&1"
CRON_MARKER="budget-flow-backup"

echo "[cron-setup] BudgetFlow Backup Cron Installer"
echo "[cron-setup] Schedule : daily at midnight (${CRON_SCHEDULE})"
echo "[cron-setup] Script   : ${BACKUP_SCRIPT}"
echo "[cron-setup] Log      : ${CRON_LOG}"
echo ""

# Read current crontab (empty string if none)
CURRENT_CRONTAB="$(crontab -l 2>/dev/null || true)"

# Idempotency check — skip if already installed
if echo "$CURRENT_CRONTAB" | grep -q "$CRON_MARKER"; then
    echo "[cron-setup] Cron job already installed — nothing to do."
    echo ""
    echo "[cron-setup] Current matching cron entry:"
    echo "$CURRENT_CRONTAB" | grep "$CRON_MARKER" || true
    exit 0
fi

# Append new entry with marker comment
(
    echo "$CURRENT_CRONTAB"
    echo "# ${CRON_MARKER} — added by setup-backup-cron.sh"
    echo "${CRON_SCHEDULE} ${CRON_CMD}"
) | crontab -

echo "[cron-setup] SUCCESS — cron job installed."
echo ""
echo "[cron-setup] To verify:"
echo "   crontab -l | grep budget-flow-backup"
echo ""
echo "[cron-setup] To run a manual backup now:"
echo "   bash ${BACKUP_SCRIPT}"
echo ""
echo "[cron-setup] To remove the cron job:"
echo "   crontab -l | grep -v budget-flow-backup | crontab -"

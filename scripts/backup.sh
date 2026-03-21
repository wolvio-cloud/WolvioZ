#!/usr/bin/env bash
# scripts/backup.sh
# Backs up Open WebUI data (chat history, users, settings) to /opt/backups/wolvio-z
# Add to cron: 0 3 * * * /opt/wolvio-z/scripts/backup.sh >> /var/log/wolvio-backup.log 2>&1

set -euo pipefail

BACKUP_DIR="/opt/backups/wolvio-z"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEST="$BACKUP_DIR/webui_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "[$TIMESTAMP] Starting backup..."

# Backup the Open WebUI Docker volume
docker run --rm \
  -v wolvio-z_open_webui_data:/data:ro \
  -v "$BACKUP_DIR":/backup \
  alpine \
  tar czf "/backup/webui_$TIMESTAMP.tar.gz" -C /data .

echo "[$TIMESTAMP] Backup saved: $DEST"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "webui_*.tar.gz" -mtime +7 -delete
echo "[$TIMESTAMP] Old backups pruned."

#!/usr/bin/env bash
# scripts/backup.sh
# Backs up Open WebUI data (chat history, users, settings) and config files.
# .env is NOT backed up here — store secrets separately (password manager / secret vault).
# Add to cron: 0 3 * * * /opt/wolvio-z/scripts/backup.sh >> /var/log/wolvio-backup.log 2>&1

set -euo pipefail

WORKDIR="/opt/wolvio-z"
BACKUP_DIR="/opt/backups/wolvio-z"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
WEBUI_DEST="$BACKUP_DIR/webui_$TIMESTAMP.tar.gz"
CONFIG_DEST="$BACKUP_DIR/configs_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "[$TIMESTAMP] Starting backup..."

# ── 1. Open WebUI volume (chat history, users, settings) ────────────────────
docker run --rm \
  -v wolvio-z_open_webui_data:/data:ro \
  -v "$BACKUP_DIR":/backup \
  alpine \
  tar czf "/backup/webui_$TIMESTAMP.tar.gz" -C /data .

# Integrity check — fail loudly rather than silently keep a corrupt archive
if ! tar -tzf "$WEBUI_DEST" > /dev/null 2>&1; then
  echo "[$TIMESTAMP] ✗ INTEGRITY CHECK FAILED: $WEBUI_DEST is corrupt. Removing."
  rm -f "$WEBUI_DEST"
  exit 1
fi
echo "[$TIMESTAMP] WebUI backup OK: $WEBUI_DEST ($(du -sh "$WEBUI_DEST" | cut -f1))"

# ── 2. Config files (excludes .env — store secrets separately) ───────────────
tar czf "$CONFIG_DEST" \
  -C "$WORKDIR" \
  --exclude='.env' \
  docker-compose.yml litellm_config.yaml Caddyfile .env.example scripts/ \
  2>/dev/null

if ! tar -tzf "$CONFIG_DEST" > /dev/null 2>&1; then
  echo "[$TIMESTAMP] ✗ INTEGRITY CHECK FAILED: $CONFIG_DEST is corrupt. Removing."
  rm -f "$CONFIG_DEST"
  exit 1
fi
echo "[$TIMESTAMP] Config backup OK: $CONFIG_DEST ($(du -sh "$CONFIG_DEST" | cut -f1))"

# ── 3. Prune old backups (keep last 7 days) ───────────────────────────────────
find "$BACKUP_DIR" -name "webui_*.tar.gz"   -mtime +7 -delete
find "$BACKUP_DIR" -name "configs_*.tar.gz" -mtime +7 -delete
echo "[$TIMESTAMP] Old backups pruned (>7 days)."

# ── 4. Summary ────────────────────────────────────────────────────────────────
TOTAL=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "[$TIMESTAMP] Backup complete. Total backup dir size: $TOTAL"

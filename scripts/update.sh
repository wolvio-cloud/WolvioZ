#!/usr/bin/env bash
# scripts/update.sh — Pull latest images and configs, rolling-restart services.
# Usage: bash /opt/wolvio-z/scripts/update.sh
# Override branch with: DEPLOY_BRANCH=my-branch bash scripts/update.sh

set -euo pipefail

WORKDIR="/opt/wolvio-z"
BRANCH="${DEPLOY_BRANCH:-main}"

cd "$WORKDIR"

echo "========================================================"
echo "  Wolvio Z — Update"
echo "========================================================"

# ─── 1. Pull latest configs from git ─────────────────────────────────────────
echo ""
echo "▶ Pulling latest configs from branch: $BRANCH"
if git fetch origin "$BRANCH" 2>/dev/null; then
  git checkout "origin/$BRANCH" -- \
    docker-compose.yml litellm_config.yaml Caddyfile scripts/ 2>/dev/null && \
    chmod +x scripts/*.sh && \
    echo "  Configs updated." || \
    echo "  ⚠  Checkout failed — using existing configs."
else
  echo "  ⚠  Could not reach GitHub — using existing configs."
fi

# ─── 2. Pull latest images ────────────────────────────────────────────────────
echo ""
echo "▶ Pulling latest Docker images..."
docker compose pull

# ─── 3. Rolling restart (dependency order: cache → gateway → ui → proxy) ─────
echo ""
echo "▶ Rolling restart..."
for service in redis litellm open-webui caddy; do
  echo "  Updating $service..."
  docker compose up -d --no-deps "$service"
  # Brief pause to allow the container to initialise before the next one starts
  sleep 8
done

# ─── 4. Final status ──────────────────────────────────────────────────────────
echo ""
echo "▶ Status after update:"
docker compose ps

echo ""
echo "  Update complete. Run scripts/healthcheck.sh to verify."

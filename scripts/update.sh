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

_wait_healthy() {
  local svc="$1"
  local max=60  # seconds
  local elapsed=0
  echo "    Waiting for $svc to be healthy..."
  while [[ $elapsed -lt $max ]]; do
    local state
    state=$(docker compose ps --format '{{.Health}}' "$svc" 2>/dev/null | head -1)
    if [[ "$state" == "healthy" ]]; then
      echo "    ✓ $svc is healthy"
      return 0
    fi
    sleep 5
    (( elapsed += 5 ))
  done
  echo "    ⚠  $svc did not become healthy within ${max}s — proceeding anyway"
  return 0
}

for service in redis litellm open-webui caddy; do
  echo "  Updating $service..."
  docker compose up -d --no-deps "$service"
  _wait_healthy "$service"
done

# ─── 4. Final status ──────────────────────────────────────────────────────────
echo ""
echo "▶ Status after update:"
docker compose ps

echo ""
echo "  Update complete. Run scripts/healthcheck.sh to verify."

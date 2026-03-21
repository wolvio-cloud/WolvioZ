#!/usr/bin/env bash
# scripts/healthcheck.sh — Verify all Wolvio Z services are healthy.
# Usage: bash /opt/wolvio-z/scripts/healthcheck.sh

set -euo pipefail

WORKDIR="/opt/wolvio-z"
cd "$WORKDIR"

echo "========================================================"
echo "  Wolvio Z — Health Check"
echo "========================================================"

# ─── 1. Container status ─────────────────────────────────────────────────────
echo ""
echo "▶ Container status:"
docker compose ps

# ─── 2. LiteLLM internal health ──────────────────────────────────────────────
echo ""
echo "▶ LiteLLM health:"
docker compose exec -T litellm curl -sf http://localhost:4000/health 2>/dev/null \
  | python3 -m json.tool 2>/dev/null \
  || echo "  ✗ LiteLLM not responding — check: docker compose logs litellm"

# ─── 3. Available models ─────────────────────────────────────────────────────
echo ""
echo "▶ Models available:"
MASTER_KEY=$(grep '^LITELLM_MASTER_KEY=' .env 2>/dev/null | cut -d= -f2- | tr -d '"' || echo "")
if [[ -n "$MASTER_KEY" ]]; then
  docker compose exec -T litellm curl -sf \
    -H "Authorization: Bearer $MASTER_KEY" \
    http://localhost:4000/v1/models 2>/dev/null \
    | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [m['id'] for m in data.get('data', [])]
    print(f'  {len(models)} models available:')
    for m in models:
        print(f'    ✓ {m}')
except Exception as e:
    print(f'  Could not parse model list: {e}')
" 2>/dev/null || echo "  ✗ Could not fetch model list"
else
  echo "  ⚠  LITELLM_MASTER_KEY not found in .env"
fi

# ─── 4. Open WebUI reachability ──────────────────────────────────────────────
echo ""
echo "▶ Open WebUI reachability:"
SERVER_IP=$(hostname -I | awk '{print $1}')
if curl -sf --max-time 5 "http://$SERVER_IP/" > /dev/null 2>&1; then
  echo "  ✓ Reachable at http://$SERVER_IP"
else
  echo "  ✗ Not reachable on port 80 — Caddy may be down or still starting"
fi

# ─── 5. Disk usage ───────────────────────────────────────────────────────────
echo ""
echo "▶ Disk:"
df -h / | awk 'NR==2 {printf "  /: %s used (%s of %s, %s free)\n", $3, $2, $2, $4}'
echo -n "  Backups: "
du -sh /opt/backups/wolvio-z 2>/dev/null || echo "(none yet)"

# ─── 6. Memory ───────────────────────────────────────────────────────────────
echo ""
echo "▶ Memory:"
free -h | awk 'NR==2 {printf "  RAM: %s used / %s total (%s free)\n", $3, $2, $4}'

# ─── 7. Recent errors ────────────────────────────────────────────────────────
echo ""
echo "▶ Recent Caddy logs (last 5 lines):"
docker compose logs caddy --tail 5 --no-log-prefix 2>/dev/null || echo "  (Caddy not running)"

echo ""
echo "========================================================"

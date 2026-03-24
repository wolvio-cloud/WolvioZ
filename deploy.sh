#!/usr/bin/env bash
# deploy.sh — Wolvio Z full deployment
# First-time install on a fresh server:
#   curl -fsSL https://raw.githubusercontent.com/wolvio-cloud/WolvioZ/main/deploy.sh | bash
# Re-deploy / update on existing server:
#   bash /opt/wolvio-z/deploy.sh

set -euo pipefail

WORKDIR="/opt/wolvio-z"
REPO="https://github.com/wolvio-cloud/WolvioZ.git"
# Override with: DEPLOY_BRANCH=my-branch bash deploy.sh
BRANCH="${DEPLOY_BRANCH:-main}"

echo "========================================================"
echo "  Wolvio Z — Deploy"
echo "========================================================"

# ─── 1. Dependencies ─────────────────────────────────────────────────────────
echo ""
echo "▶ Checking dependencies..."

if ! command -v docker &>/dev/null; then
  echo "  Installing Docker..."
  curl -fsSL https://get.docker.com | bash
fi

if ! docker compose version &>/dev/null 2>&1; then
  echo "  Installing Docker Compose plugin..."
  apt-get install -y docker-compose-plugin
fi

if ! command -v git &>/dev/null; then
  apt-get install -y git
fi

echo "  Docker: $(docker --version)"
echo "  Compose: $(docker compose version)"

# ─── 2. Pull latest configs ───────────────────────────────────────────────────
echo ""
echo "▶ Setting up project directory: $WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

_git_ok=false
if [[ -d .git ]]; then
  echo "  Repo exists — fetching latest from branch: $BRANCH"
  if git fetch origin "$BRANCH" 2>/dev/null; then
    _git_ok=true
  else
    echo "  ⚠  Could not reach GitHub — using existing local files."
  fi
else
  echo "  Initialising git repo..."
  git init
  git remote add origin "$REPO" 2>/dev/null || git remote set-url origin "$REPO"
  if git fetch origin "$BRANCH" 2>/dev/null; then
    _git_ok=true
  else
    echo "  ⚠  Could not reach GitHub — local files only."
  fi
fi

if [[ "$_git_ok" == true ]]; then
  git checkout "origin/$BRANCH" -- \
    docker-compose.yml \
    litellm_config.yaml \
    Caddyfile \
    .gitignore \
    .env.example \
    scripts/ 2>/dev/null || true
  chmod +x scripts/*.sh
  echo "  Configs updated from GitHub."
else
  for f in docker-compose.yml litellm_config.yaml Caddyfile; do
    if [[ ! -f "$f" ]]; then
      echo "  ✗ Missing required file: $f"
      echo "    Clone the repo to $WORKDIR or set DEPLOY_BRANCH and ensure GitHub is reachable."
      exit 1
    fi
  done
  echo "  Using existing local config files."
fi

# ─── 3. Validate .env ────────────────────────────────────────────────────────
echo ""
echo "▶ Checking .env..."

if [[ ! -f .env ]]; then
  echo "  .env not found — creating from template..."
  cat > .env << 'ENVEOF'
# !! Fill in your real values, then re-run deploy.sh !!
LITELLM_MASTER_KEY=sk-REPLACE-ME
WEBUI_SECRET_KEY=REPLACE-ME
OPENAI_API_KEY=sk-REPLACE-ME
ANTHROPIC_API_KEY=sk-ant-REPLACE-ME
GEMINI_API_KEY=AIza-REPLACE-ME
GROQ_API_KEY=gsk_REPLACE-ME
REDIS_PASSWORD=REPLACE-ME
# DOMAIN=ai.yourdomain.com   # Uncomment and set for HTTPS
ENVEOF
  echo ""
  echo "  ⚠  .env created with placeholders."
  echo "     Fill in all values, then re-run:"
  echo "     nano $WORKDIR/.env && bash $WORKDIR/deploy.sh"
  exit 1
fi

if grep -q 'REPLACE-ME' .env; then
  echo ""
  echo "  ⚠  .env still has REPLACE-ME placeholders."
  echo "     Fill in all values and re-run:"
  echo "     nano $WORKDIR/.env"
  exit 1
fi

# Ensure REDIS_PASSWORD is present (added in v2)
if ! grep -q '^REDIS_PASSWORD=' .env; then
  echo ""
  echo "  ⚠  REDIS_PASSWORD is missing from .env."
  echo "     Add it with: echo \"REDIS_PASSWORD=\$(openssl rand -hex 24)\" >> $WORKDIR/.env"
  exit 1
fi

echo "  .env looks good."

# ─── 4. Firewall ─────────────────────────────────────────────────────────────
echo ""
echo "▶ Applying firewall rules..."
bash scripts/firewall.sh

# ─── 5. Snapshot current state for rollback reference ────────────────────────
echo ""
echo "▶ Capturing rollback snapshot..."
docker compose images 2>/dev/null > /tmp/wolvio-rollback-images.txt || true
cp docker-compose.yml /tmp/wolvio-compose-rollback.yml 2>/dev/null || true
echo "  Saved to /tmp/wolvio-rollback-images.txt (use if deploy fails)"

# ─── 6. Start the stack ───────────────────────────────────────────────────────
echo ""
echo "▶ Starting Wolvio Z stack..."
docker compose down --remove-orphans 2>/dev/null || true
docker compose pull
docker compose up -d

# ─── 7. Wait for healthy ──────────────────────────────────────────────────────
echo ""
echo "▶ Waiting for services to be healthy (up to 120s)..."
_healthy=false
for i in $(seq 1 24); do
  sleep 5
  if ! docker compose ps 2>/dev/null | grep -qiE 'starting|restarting'; then
    _healthy=true
    break
  fi
  echo "  ... still starting (${i}×5s)"
done

echo ""
echo "▶ Container status:"
docker compose ps

if [[ "$_healthy" == false ]]; then
  echo ""
  echo "  ⚠  Stack did not stabilise in 120s. Check logs:"
  echo "     docker compose logs --tail 50"
  echo "  Previous images: /tmp/wolvio-rollback-images.txt"
  exit 1
fi

# ─── 8. Health checks ─────────────────────────────────────────────────────────
echo ""
echo "▶ Health checks:"

echo ""
echo "  -- LiteLLM /health --"
docker compose exec -T litellm curl -sf http://localhost:4000/health 2>/dev/null \
  | python3 -m json.tool 2>/dev/null \
  || echo "  LiteLLM health endpoint not yet ready (check: docker compose logs litellm)"

echo ""
echo "  -- Models available --"
MASTER_KEY=$(grep '^LITELLM_MASTER_KEY=' .env | cut -d= -f2-)
docker compose exec -T litellm curl -sf \
  -H "Authorization: Bearer $MASTER_KEY" \
  http://localhost:4000/v1/models 2>/dev/null \
  | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [m['id'] for m in data.get('data', [])]
    print(f'  Found {len(models)} models:')
    for m in models:
        print(f'    • {m}')
except:
    print('  Could not parse model list')
" 2>/dev/null || echo "  (model list not yet available)"

# ─── 9. Set up daily backup cron ─────────────────────────────────────────────
echo ""
echo "▶ Setting up daily backup cron..."
CRON_JOB="0 3 * * * /opt/wolvio-z/scripts/backup.sh >> /var/log/wolvio-backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v 'wolvio-z/scripts/backup'; echo "$CRON_JOB") | crontab -
echo "  Daily backup scheduled at 3am."

# ─── 10. Done ─────────────────────────────────────────────────────────────────
DOMAIN_VAL=$(grep '^DOMAIN=' .env | cut -d= -f2- | tr -d '"' 2>/dev/null || echo "")
SERVER_IP_VAL=$(hostname -I | awk '{print $1}')

echo ""
echo "========================================================"
echo "  Wolvio Z is running!"
echo ""
if [[ -n "$DOMAIN_VAL" ]]; then
  echo "  Open WebUI  → https://$DOMAIN_VAL"
else
  echo "  Open WebUI  → http://$SERVER_IP_VAL"
  echo "  (Set DOMAIN=yourdomain.com in .env for HTTPS)"
fi
echo ""
echo "  LiteLLM API → internal only (docker network)"
echo ""
echo "  Models: claude-opus-4, claude-sonnet-4, claude-haiku-4 (Claude 4 generation)"
echo "          gpt-4o, gpt-4o-mini, gemini-2.5-flash, gemini-2.0-flash-lite,"
echo "          llama-3.3-70b, llama-3.1-8b, qwen3-32b"
echo ""
echo "  First run: open the URL above and create an admin account."
echo "  Health:    bash /opt/wolvio-z/scripts/healthcheck.sh"
echo "  Update:    bash /opt/wolvio-z/scripts/update.sh"
echo "========================================================"

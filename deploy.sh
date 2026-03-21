#!/usr/bin/env bash
# deploy.sh — Wolvio Z full MVP deploy
# Run as root on the DigitalOcean server:
#   curl -fsSL https://raw.githubusercontent.com/wolvio-cloud/WolvioZ/claude/setup-wolvio-docker-oMgtd/deploy.sh | bash
# Or: bash /opt/wolvio-z/deploy.sh

set -euo pipefail

WORKDIR="/opt/wolvio-z"
REPO="https://github.com/wolvio-cloud/WolvioZ.git"
BRANCH="claude/setup-wolvio-docker-oMgtd"

echo "========================================================"
echo "  Wolvio Z — MVP Deploy"
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
  echo "  Repo exists — fetching latest..."
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
  echo "  Configs updated from GitHub."
else
  # Verify required files exist locally before continuing
  for f in docker-compose.yml litellm_config.yaml Caddyfile; do
    if [[ ! -f "$f" ]]; then
      echo "  ✗ Missing required file: $f"
      echo "    Ensure the repo was cloned to $WORKDIR before running this script."
      exit 1
    fi
  done
  echo "  Using existing local config files."
fi

# ─── 3. Write .env ────────────────────────────────────────────────────────────
echo ""
echo "▶ Checking .env..."

if [[ ! -f .env ]]; then
  echo "  .env not found — creating from template..."
  cat > .env << 'ENVEOF'
# !! Fill in your real values below !!
LITELLM_MASTER_KEY=sk-REPLACE-ME
WEBUI_SECRET_KEY=REPLACE-ME
OPENAI_API_KEY=sk-REPLACE-ME
ANTHROPIC_API_KEY=sk-ant-REPLACE-ME
GEMINI_API_KEY=AIza-REPLACE-ME
GROQ_API_KEY=gsk_REPLACE-ME
REDIS_URL=redis://redis:6379
# DOMAIN=ai.yourdomain.com   # Uncomment and set for HTTPS
SERVER_IP=159.65.153.81
ENVEOF
  echo ""
  echo "  ⚠️  .env created with placeholders."
  echo "     Edit it now, then re-run this script:"
  echo "     nano $WORKDIR/.env"
  exit 1
fi

# Check for unfilled placeholders
if grep -q 'REPLACE-ME' .env; then
  echo ""
  echo "  ⚠️  .env still has REPLACE-ME placeholders."
  echo "     Fill in all values and re-run:"
  echo "     nano $WORKDIR/.env"
  exit 1
fi

echo "  .env looks good."

# ─── 4. Firewall ─────────────────────────────────────────────────────────────
echo ""
echo "▶ Applying firewall rules..."
chmod +x scripts/firewall.sh
bash scripts/firewall.sh

# ─── 5. Start the stack ───────────────────────────────────────────────────────
echo ""
echo "▶ Starting Wolvio Z stack..."
chmod +x scripts/backup.sh

docker compose down --remove-orphans 2>/dev/null || true
docker compose pull
docker compose up -d

echo ""
echo "  Waiting 25s for all services to become healthy..."
sleep 25

# ─── 6. Health checks ─────────────────────────────────────────────────────────
echo ""
echo "▶ Health checks:"

echo ""
echo "  -- Container status --"
docker compose ps

echo ""
echo "  -- LiteLLM /health --"
curl -sf http://localhost:4000/health 2>/dev/null | python3 -m json.tool 2>/dev/null || \
  curl -s http://localhost:4000/health 2>/dev/null || echo "  LiteLLM not yet ready"

echo ""
echo "  -- Models available --"
MASTER_KEY=$(grep '^LITELLM_MASTER_KEY=' .env | cut -d= -f2-)
MODEL_LIST=$(curl -s -H "Authorization: Bearer $MASTER_KEY" http://localhost:4000/v1/models 2>/dev/null)
echo "$MODEL_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [m['id'] for m in data.get('data', [])]
    print(f'  Found {len(models)} models:')
    for m in models:
        print(f'    • {m}')
except:
    print('  Could not parse model list')
" 2>/dev/null || echo "$MODEL_LIST"

# ─── 7. Set up daily backup cron ─────────────────────────────────────────────
echo ""
echo "▶ Setting up daily backup cron..."
CRON_JOB="0 3 * * * /opt/wolvio-z/scripts/backup.sh >> /var/log/wolvio-backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v 'wolvio-z/scripts/backup'; echo "$CRON_JOB") | crontab -
echo "  Daily backup scheduled at 3am."

# ─── 8. Done ─────────────────────────────────────────────────────────────────
DOMAIN_VAL=$(grep '^DOMAIN=' .env | cut -d= -f2- | tr -d '"' || echo "")
SERVER_IP_VAL=$(grep '^SERVER_IP=' .env | cut -d= -f2- | tr -d '"' || echo "159.65.153.81")

echo ""
echo "========================================================"
echo "  Wolvio Z is running!"
echo ""
if [[ -n "$DOMAIN_VAL" ]]; then
  echo "  Open WebUI  → https://$DOMAIN_VAL"
else
  echo "  Open WebUI  → http://$SERVER_IP_VAL"
  echo "  (Add DOMAIN=yourdomain.com to .env for HTTPS)"
fi
echo ""
echo "  LiteLLM API → http://localhost:4000 (internal only)"
echo ""
echo "  9 models available:"
echo "    OpenAI    : gpt-4o, gpt-4o-mini"
echo "    Anthropic : claude-3-5-sonnet, claude-3-haiku"
echo "    Gemini    : gemini-2.0-flash, gemini-1.5-pro"
echo "    Groq      : llama-3.3-70b, llama-3.1-8b, mixtral-8x7b"
echo ""
echo "  First run: open the URL above, create an admin account."
echo "========================================================"

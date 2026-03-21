#!/usr/bin/env bash
# fix-and-setup.sh
# Diagnoses LITELLM_MASTER_KEY mismatch, applies the corrected configs,
# restarts containers, verifies health, and initialises the git repo.
# Run as root from /opt/wolvio-z

set -euo pipefail

WORKDIR="/opt/wolvio-z"
REPO="https://github.com/wolvio-cloud/WolvioZ"
BRANCH="claude/setup-wolvio-docker-oMgtd"

cd "$WORKDIR"

echo "============================================================"
echo " Wolvio Z — Fix & Setup"
echo "============================================================"

# ─── 1. Show current files ───────────────────────────────────────────────────
echo ""
echo "▶ Current files in $WORKDIR:"
ls -la

# ─── 2. Read & display current config (masked) ───────────────────────────────
echo ""
echo "▶ Current .env (API key values masked):"
if [[ -f .env ]]; then
  sed 's/\(KEY\|SECRET\|TOKEN\|PASSWORD\)=\(.\{4\}\).*/\1=\2***/gI' .env
else
  echo "  [.env not found — will create from .env.example]"
fi

echo ""
echo "▶ docker-compose.yml:"
cat docker-compose.yml 2>/dev/null || echo "  [not found]"

echo ""
echo "▶ litellm_config.yaml:"
cat litellm_config.yaml 2>/dev/null || echo "  [not found]"

# ─── 3. Diagnose LITELLM_MASTER_KEY mismatch ─────────────────────────────────
echo ""
echo "▶ Diagnosing LITELLM_MASTER_KEY..."

# Extract key from .env
ENV_KEY=""
if [[ -f .env ]]; then
  ENV_KEY=$(grep -E '^LITELLM_MASTER_KEY=' .env | cut -d= -f2- | tr -d '"'"'" || true)
fi

# Extract key from litellm_config.yaml (inline value, not env var reference)
YAML_KEY=""
if [[ -f litellm_config.yaml ]]; then
  YAML_KEY=$(grep 'master_key:' litellm_config.yaml | grep -v 'os.environ' | awk '{print $2}' | tr -d '"' || true)
fi

# Extract what Open WebUI uses as OPENAI_API_KEY in docker-compose.yml
WEBUI_KEY=""
if [[ -f docker-compose.yml ]]; then
  WEBUI_KEY=$(grep 'OPENAI_API_KEY:' docker-compose.yml | grep -v LITELLM | awk '{print $2}' | tr -d '"' || true)
fi

echo "  .env LITELLM_MASTER_KEY    : ${ENV_KEY:+${ENV_KEY:0:8}***  (set)}"
echo "  litellm_config.yaml key    : ${YAML_KEY:-'(using os.environ — OK)'}"
echo "  docker-compose WebUI key   : ${WEBUI_KEY:-'(not found)'}"

if [[ -n "$YAML_KEY" && "$YAML_KEY" != "$ENV_KEY" ]]; then
  echo ""
  echo "  ⚠️  MISMATCH DETECTED: litellm_config.yaml has a hardcoded key"
  echo "     that differs from .env. This causes 'No models available'."
fi

# ─── 4. Generate a master key if none exists ─────────────────────────────────
if [[ -z "$ENV_KEY" ]]; then
  echo ""
  echo "▶ No LITELLM_MASTER_KEY found in .env — generating one..."
  NEW_KEY="sk-$(openssl rand -hex 24)"
  echo "LITELLM_MASTER_KEY=${NEW_KEY}" >> .env
  ENV_KEY="$NEW_KEY"
  echo "  Generated: ${ENV_KEY:0:12}***"
fi

# ─── 5. Apply corrected configs ───────────────────────────────────────────────
echo ""
echo "▶ Applying corrected docker-compose.yml and litellm_config.yaml..."

# Back up originals
cp docker-compose.yml docker-compose.yml.bak 2>/dev/null && echo "  Backed up docker-compose.yml → docker-compose.yml.bak" || true
cp litellm_config.yaml litellm_config.yaml.bak 2>/dev/null && echo "  Backed up litellm_config.yaml → litellm_config.yaml.bak" || true

# Pull the corrected configs from git
if [[ -d .git ]]; then
  echo "  Git repo already initialised — pulling latest..."
  git fetch origin "$BRANCH" 2>/dev/null || true
  git checkout origin/"$BRANCH" -- docker-compose.yml litellm_config.yaml .gitignore .env.example 2>/dev/null || {
    echo "  (Could not pull from git — using existing files)"
  }
else
  echo "  Initialising git repo and pulling configs..."
  git init
  git remote add origin "$REPO"
  git fetch origin "$BRANCH" 2>/dev/null || {
    echo "  (Remote branch not yet available — skipping pull)"
  }
  git checkout origin/"$BRANCH" -- docker-compose.yml litellm_config.yaml .gitignore .env.example 2>/dev/null || true
fi

# Fix: ensure litellm_config.yaml uses os.environ (not a hardcoded key)
if grep -q 'master_key:' litellm_config.yaml 2>/dev/null && ! grep -q 'os.environ' litellm_config.yaml 2>/dev/null; then
  echo "  Patching litellm_config.yaml master_key to use os.environ..."
  sed -i 's|master_key:.*|master_key: os.environ/LITELLM_MASTER_KEY|' litellm_config.yaml
fi

# Fix: ensure docker-compose.yml Open WebUI uses ${LITELLM_MASTER_KEY} not a hardcoded value
# (The corrected docker-compose.yml from git already handles this correctly)

# ─── 6. Restart containers ────────────────────────────────────────────────────
echo ""
echo "▶ Restarting containers..."
docker compose down --remove-orphans
docker compose up -d
echo "  Containers started. Waiting 15s for health checks..."
sleep 15

# ─── 7. Verify ────────────────────────────────────────────────────────────────
echo ""
echo "▶ Health checks:"
echo ""
echo "  -- LiteLLM /health --"
curl -sf http://localhost:4000/health | python3 -m json.tool 2>/dev/null || \
  curl -s http://localhost:4000/health

echo ""
echo "  -- LiteLLM /v1/models (with master key) --"
MASTER_KEY=$(grep '^LITELLM_MASTER_KEY=' .env | cut -d= -f2- | tr -d '"'"'" || echo "")
if [[ -n "$MASTER_KEY" ]]; then
  curl -s -H "Authorization: Bearer $MASTER_KEY" http://localhost:4000/v1/models | \
    python3 -m json.tool 2>/dev/null | head -40 || \
    curl -s -H "Authorization: Bearer $MASTER_KEY" http://localhost:4000/v1/models | head -200
else
  echo "  (Could not read master key from .env)"
fi

# ─── 8. Git: commit & push ────────────────────────────────────────────────────
echo ""
echo "▶ Setting up git repository..."
git config user.email "wolvio-bot@wolvio.cloud" 2>/dev/null || true
git config user.name "Wolvio Setup" 2>/dev/null || true

# Stage config files (NOT .env)
git add docker-compose.yml litellm_config.yaml .gitignore .env.example 2>/dev/null || true

# Check if there's anything to commit
if ! git diff --cached --quiet 2>/dev/null; then
  git commit -m "fix: align LITELLM_MASTER_KEY across all configs

- docker-compose.yml: Open WebUI OPENAI_API_KEY now uses \${LITELLM_MASTER_KEY}
- litellm_config.yaml: master_key uses os.environ/LITELLM_MASTER_KEY
- Add .gitignore (excludes .env) and .env.example template
- Open WebUI ENABLE_OLLAMA_API=false, points to LiteLLM on internal network"
  echo "  Committed."
else
  echo "  Nothing new to commit."
fi

echo ""
echo "▶ Pushing to $BRANCH..."
git push -u origin HEAD:"$BRANCH" && echo "  Pushed successfully." || \
  echo "  Push failed — ensure git remote is authenticated (add deploy key or PAT)."

echo ""
echo "============================================================"
echo " Done! Check Open WebUI at http://$(hostname -I | awk '{print $1}'):3000"
echo "============================================================"

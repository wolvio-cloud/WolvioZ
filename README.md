# Wolvio Z

Self-hosted AI chat stack for a single server. One command to deploy, all models ready.

**Stack:** Open WebUI → LiteLLM → Redis cache → Caddy reverse proxy

```
Browser → Caddy (:80/443) → Open WebUI → LiteLLM → OpenAI / Anthropic / Gemini / Groq
                                                    ↕
                                                  Redis
```

---

## Models included

| Name | Provider | Use case |
|------|----------|----------|
| `gpt-4o` | OpenAI | Best quality |
| `gpt-4o-mini` | OpenAI | Fast + cheap |
| `claude-3-5-sonnet` | Anthropic | Best reasoning |
| `claude-3-haiku` | Anthropic | Fast Anthropic |
| `gemini-2.5-flash` | Google | Multimodal |
| `gemini-2.0-flash-lite` | Google | Lightweight |
| `llama-3.3-70b` | Groq | Fast open model |
| `llama-3.1-8b` | Groq | Ultra-fast |
| `qwen3-32b` | Groq | Multilingual |

Provider fallbacks are configured automatically (e.g. `gpt-4o` → `gpt-4o-mini`).

---

## Quick start

### 1. Deploy (fresh server)

```bash
curl -fsSL https://raw.githubusercontent.com/wolvio-cloud/WolvioZ/main/deploy.sh | bash
```

This installs Docker, clones the repo to `/opt/wolvio-z`, and creates a `.env` template.

### 2. Fill in your API keys

```bash
nano /opt/wolvio-z/.env
```

```env
LITELLM_MASTER_KEY=sk-...        # generate: openssl rand -hex 32
WEBUI_SECRET_KEY=...             # generate: openssl rand -hex 32
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
REDIS_PASSWORD=...               # generate: openssl rand -hex 24

# Optional — set to enable HTTPS via Let's Encrypt:
# DOMAIN=ai.yourdomain.com
```

### 3. Start

```bash
bash /opt/wolvio-z/deploy.sh
```

Open the server IP in your browser and create your admin account.

---

## HTTPS

Set `DOMAIN=ai.yourdomain.com` in `.env` and point your DNS A record to the server.
Caddy provisions a Let's Encrypt certificate automatically on first request.

---

## Operations

| Task | Command |
|------|---------|
| Health check | `bash /opt/wolvio-z/scripts/healthcheck.sh` |
| Update stack | `bash /opt/wolvio-z/scripts/update.sh` |
| Manual backup | `bash /opt/wolvio-z/scripts/backup.sh` |
| View logs | `docker compose logs -f [service]` |
| Restart service | `docker compose restart [service]` |
| Stop everything | `docker compose down` |

Services: `redis`, `litellm`, `open-webui`, `caddy`

### Backups

Backups run daily at 3am (set up by `deploy.sh`). They are stored in `/opt/backups/wolvio-z/` and kept for 7 days.

- `webui_TIMESTAMP.tar.gz` — chat history, users, settings
- `configs_TIMESTAMP.tar.gz` — docker-compose, litellm config, Caddyfile

> `.env` is **not** backed up automatically. Store your secrets in a password manager.

---

## Project structure

```
.
├── docker-compose.yml      # All services
├── litellm_config.yaml     # Model list, routing, cache config
├── Caddyfile               # Reverse proxy + security headers
├── deploy.sh               # One-command install/re-deploy
├── .env.example            # Template — copy to .env
└── scripts/
    ├── healthcheck.sh      # Verify all services + models
    ├── update.sh           # Rolling update (no downtime)
    ├── backup.sh           # Data + config backup
    └── firewall.sh         # UFW rules (auto-applied by deploy.sh)
```

---

## Requirements

- Ubuntu 22.04+ (or any Debian-based Linux)
- 2 GB RAM minimum (4 GB recommended)
- Ports 80 and 443 open
- API keys for the providers you want to use (you can leave unused ones as placeholders)

---

## Updating a single service

```bash
cd /opt/wolvio-z
docker compose pull litellm
docker compose up -d --no-deps litellm
```

Or run `scripts/update.sh` for a full rolling update.

---

## LiteLLM API

The LiteLLM proxy is not exposed to the host — it's internal to the Docker network only.
To call it directly (e.g. for debugging):

```bash
docker compose exec litellm curl -s \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  http://localhost:4000/v1/models
```

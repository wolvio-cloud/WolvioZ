#!/usr/bin/env bash
# scripts/firewall.sh
# Hardens the DigitalOcean server with UFW.
# Allows: SSH (22), HTTP (80), HTTPS (443)
# Blocks: direct access to LiteLLM (4000) and Open WebUI (3000) from outside
# Run as root.

set -euo pipefail

echo "▶ Setting up UFW firewall..."

# Reset to defaults (non-interactive)
ufw --force reset

# Default: deny all incoming, allow all outgoing
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (don't lock yourself out!)
ufw allow 22/tcp comment "SSH"

# Allow HTTP + HTTPS (Caddy)
ufw allow 80/tcp  comment "HTTP"
ufw allow 443/tcp comment "HTTPS"

# Explicitly block direct container ports from external access
# (docker-compose already doesn't expose them, but belt-and-suspenders)
ufw deny 3000/tcp comment "Block direct Open WebUI"
ufw deny 4000/tcp comment "Block direct LiteLLM"

# Enable firewall
ufw --force enable

echo ""
echo "▶ UFW status:"
ufw status verbose

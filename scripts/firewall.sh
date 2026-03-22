#!/usr/bin/env bash
# scripts/firewall.sh
# Hardens the server with UFW.
# Allows:  SSH (22, rate-limited), HTTP (80), HTTPS (443)
# Blocks:  direct access to internal container ports
#
# WARNING: This script resets all UFW rules before applying new ones.
# If you have custom rules for other services on this server, back them up
# first with: ufw status numbered > /tmp/ufw-backup.txt
# Run as root.

set -euo pipefail

echo "▶ Setting up UFW firewall..."

# Reset to a clean slate (non-interactive)
ufw --force reset

# Default policy: deny all inbound, allow all outbound
ufw default deny incoming
ufw default allow outgoing

# SSH — rate-limited to block brute-force (max 6 attempts per 30 seconds per IP)
ufw limit 22/tcp comment "SSH (rate-limited)"

# HTTP + HTTPS — served by Caddy
ufw allow 80/tcp  comment "HTTP"
ufw allow 443/tcp comment "HTTPS"
ufw allow 443/udp comment "HTTP/3 QUIC"

# Belt-and-suspenders blocks for container ports
# (docker-compose uses 'expose' not 'ports', so these are never host-bound,
#  but explicit deny rules prevent confusion and catch misconfigs)
ufw deny 8080/tcp comment "Block direct Open WebUI"
ufw deny 4000/tcp comment "Block direct LiteLLM"

# Enable the firewall
ufw --force enable

echo ""
echo "▶ UFW status:"
ufw status verbose

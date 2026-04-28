#!/usr/bin/env bash
set -euo pipefail

# Enable HTTPS with Let's Encrypt using certbot nginx plugin.
# Requires domain DNS A record pointing to the server.
# Usage:
#   SERVER_HOST=47.98.235.65 DOMAIN=example.com EMAIL=you@example.com ROOT_SSH_KEY=~/.ssh/id_ed25519_deploy ./scripts/enable_https_certbot.sh

SERVER_HOST="${SERVER_HOST:-}"
SERVER_PORT="${SERVER_PORT:-22}"
ROOT_USER="${ROOT_USER:-root}"
ROOT_SSH_KEY="${ROOT_SSH_KEY:-}"
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"

if [[ -z "$SERVER_HOST" || -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "Missing required env vars: SERVER_HOST, DOMAIN, EMAIL"
  exit 1
fi

SSH_OPTS=(-p "$SERVER_PORT")
if [[ -n "$ROOT_SSH_KEY" ]]; then
  SSH_OPTS+=( -i "$ROOT_SSH_KEY" )
fi

ssh "${SSH_OPTS[@]}" "$ROOT_USER@$SERVER_HOST" "
set -e
if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y certbot python3-certbot-nginx
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y certbot python3-certbot-nginx
elif command -v yum >/dev/null 2>&1; then
  yum install -y epel-release || true
  yum install -y certbot python3-certbot-nginx || yum install -y certbot
else
  echo 'Unsupported package manager. Install certbot manually.'
  exit 1
fi

certbot --nginx -d '$DOMAIN' --non-interactive --agree-tos -m '$EMAIL' --redirect
systemctl reload nginx || service nginx reload
certbot certificates
"

echo "HTTPS enabled. Verify at: https://$DOMAIN"

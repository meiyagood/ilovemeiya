#!/usr/bin/env bash
set -euo pipefail

# Enable HTTPS with Let's Encrypt using acme.sh + nginx.
# Requires domain DNS A record pointing to the server.
# Usage:
#   SERVER_HOST=47.98.235.65 DOMAIN=example.com EMAIL=you@example.com ROOT_SSH_KEY=~/.ssh/id_ed25519_deploy ./scripts/enable_https_certbot.sh

SERVER_HOST="${SERVER_HOST:-}"
SERVER_PORT="${SERVER_PORT:-22}"
ROOT_USER="${ROOT_USER:-root}"
ROOT_SSH_KEY="${ROOT_SSH_KEY:-}"
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"
INCLUDE_WWW="${INCLUDE_WWW:-1}"

if [[ -z "$SERVER_HOST" || -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "Missing required env vars: SERVER_HOST, DOMAIN, EMAIL"
  exit 1
fi

if ! command -v dig >/dev/null 2>&1; then
  echo "dig command not found. Install dnsutils/bind tools first."
  exit 1
fi

A_MAIN="$(dig +short "$DOMAIN" A | tail -n 1 || true)"
if [[ "$A_MAIN" != "$SERVER_HOST" ]]; then
  echo "DNS not ready: $DOMAIN -> ${A_MAIN:-<empty>}, expected $SERVER_HOST"
  exit 1
fi

DOMAIN_ARGS=( -d "$DOMAIN" )
SERVER_NAMES="$DOMAIN"
if [[ "$INCLUDE_WWW" == "1" ]]; then
  A_WWW="$(dig +short "www.$DOMAIN" A | tail -n 1 || true)"
  if [[ "$A_WWW" != "$SERVER_HOST" ]]; then
    echo "DNS not ready: www.$DOMAIN -> ${A_WWW:-<empty>}, expected $SERVER_HOST"
    exit 1
  fi
  DOMAIN_ARGS+=( -d "www.$DOMAIN" )
  SERVER_NAMES="$DOMAIN www.$DOMAIN"
fi

SSH_OPTS=(-p "$SERVER_PORT")
if [[ -n "$ROOT_SSH_KEY" ]]; then
  SSH_OPTS+=( -i "$ROOT_SSH_KEY" )
fi

ssh "${SSH_OPTS[@]}" "$ROOT_USER@$SERVER_HOST" "
set -e
if [[ ! -d /root/.acme.sh ]]; then
  curl -fsSL https://get.acme.sh | sh -s email='$EMAIL'
fi

/root/.acme.sh/acme.sh --set-default-ca --server letsencrypt
if ! /root/.acme.sh/acme.sh --issue --webroot /usr/share/nginx/html ${DOMAIN_ARGS[*]} --keylength ec-256; then
  echo 'acme.sh issue step skipped or failed; trying to continue with existing certificate files'
fi

mkdir -p /etc/nginx/ssl/$DOMAIN
/root/.acme.sh/acme.sh --install-cert -d '$DOMAIN' \
  --ecc \
  --fullchain-file /etc/nginx/ssl/$DOMAIN/fullchain.cer \
  --key-file /etc/nginx/ssl/$DOMAIN/$DOMAIN.key

cat >/etc/nginx/conf.d/$DOMAIN.conf <<'EOF'
server {
    listen 80;
    listen [::]:80;
  server_name __SERVER_NAMES__;
    root /usr/share/nginx/html;

    location /.well-known/acme-challenge/ {
        allow all;
    }

    location / {
      return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
  server_name __SERVER_NAMES__;
    root /usr/share/nginx/html;
    index index.html;

  ssl_certificate     /etc/nginx/ssl/__DOMAIN__/fullchain.cer;
  ssl_certificate_key /etc/nginx/ssl/__DOMAIN__/__DOMAIN__.key;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
      try_files \$uri \$uri/ /index.html;
    }
}
EOF

  sed -i \"s|__SERVER_NAMES__|$SERVER_NAMES|g\" /etc/nginx/conf.d/$DOMAIN.conf
  sed -i \"s|__DOMAIN__|$DOMAIN|g\" /etc/nginx/conf.d/$DOMAIN.conf

nginx -t
systemctl reload nginx || service nginx reload
"

echo "HTTPS enabled. Verify at: https://$DOMAIN"

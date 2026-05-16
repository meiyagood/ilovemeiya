#!/usr/bin/env bash
set -euo pipefail

# Usage:
# SERVER_HOST=47.98.235.65 SERVER_USER=deploy SSH_KEY_PATH=~/.ssh/id_ed25519_deploy ./scripts/setup_nginx_backend_proxy.sh

SERVER_HOST="${SERVER_HOST:-}"
SERVER_USER="${SERVER_USER:-deploy}"
SERVER_PORT="${SERVER_PORT:-22}"
SSH_KEY_PATH="${SSH_KEY_PATH:-}"

if [[ -z "$SERVER_HOST" ]]; then
  echo "Missing SERVER_HOST"
  exit 1
fi

SSH_OPTS=(-p "$SERVER_PORT")
if [[ -n "$SSH_KEY_PATH" ]]; then
  SSH_OPTS+=( -i "$SSH_KEY_PATH" )
fi

read -r -d '' SNIPPET <<'EOF' || true
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /admin {
    proxy_pass http://127.0.0.1:8000/admin;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /uploads/ {
    proxy_pass http://127.0.0.1:8000/uploads/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
EOF

echo "This script prints nginx snippet. Add it inside your active server block."
echo
printf '%s\n' "$SNIPPET"
echo

echo "Opening nginx -T summary from server for reference..."
ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" "sudo nginx -T | grep -E 'server_name|listen|root' -n | sed -n '1,120p'"

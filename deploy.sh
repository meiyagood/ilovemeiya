#!/usr/bin/env bash
set -euo pipefail

# Manual deploy helper for static personal site
# Usage:
#   SERVER_HOST=47.98.235.65 SERVER_USER=root SERVER_WEB_ROOT=/usr/share/nginx/html ./deploy.sh
# Optional:
#   SERVER_PORT=22

SERVER_HOST="${SERVER_HOST:-}"
SERVER_USER="${SERVER_USER:-deploy}"
SERVER_PORT="${SERVER_PORT:-22}"
SERVER_WEB_ROOT="${SERVER_WEB_ROOT:-}"
SSH_KEY_PATH="${SSH_KEY_PATH:-}"
BACKUP_SUBDIR="${BACKUP_SUBDIR:-.deploy-backups}"

if [[ -z "$SERVER_HOST" || -z "$SERVER_WEB_ROOT" ]]; then
  echo "Missing required env vars: SERVER_HOST, SERVER_WEB_ROOT"
  exit 1
fi

FILES=(
  "index.html"
  "travel.html"
  "reading.html"
  "french.html"
  "vibe.html"
  "social.html"
)

for f in "${FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required file: $f"
    exit 1
  fi
done

echo "Creating backup on server..."
SSH_OPTS=(-p "$SERVER_PORT")
SCP_OPTS=(-P "$SERVER_PORT")
if [[ -n "$SSH_KEY_PATH" ]]; then
  SSH_OPTS+=( -i "$SSH_KEY_PATH" )
  SCP_OPTS+=( -i "$SSH_KEY_PATH" )
fi

TS="$(date +%F-%H%M%S)"
REMOTE_BACKUP_DIR="$SERVER_WEB_ROOT/$BACKUP_SUBDIR/$TS"

ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" \
  "mkdir -p '$REMOTE_BACKUP_DIR'; cd '$SERVER_WEB_ROOT' || exit 1; \
   for f in ${FILES[*]}; do [[ -f \"$f\" ]] && cp -a \"$f\" '$REMOTE_BACKUP_DIR'/; done"

echo "Uploading files..."
scp "${SCP_OPTS[@]}" "${FILES[@]}" "$SERVER_USER@$SERVER_HOST:$SERVER_WEB_ROOT/"

echo "Reloading nginx..."
ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" \
  "sudo /usr/sbin/nginx -t && (sudo /bin/systemctl reload nginx || sudo /usr/sbin/service nginx reload)"

echo "Done: http://$SERVER_HOST/"

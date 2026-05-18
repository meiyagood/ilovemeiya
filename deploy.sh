#!/usr/bin/env bash
set -euo pipefail

# Manual deploy helper for static personal site
# Usage:
#   SERVER_HOST=47.98.235.65 SERVER_USER=root SERVER_WEB_ROOT=/usr/share/nginx/html ./deploy.sh
# Optional:
#   SERVER_PORT=22
#   MILESTONE_WEBHOOK_URL=https://api.example.com/api/milestones/travel-sync
#   MILESTONE_WEBHOOK_TOKEN=your_token

SERVER_HOST="${SERVER_HOST:-}"
SERVER_USER="${SERVER_USER:-deploy}"
SERVER_PORT="${SERVER_PORT:-22}"
SERVER_WEB_ROOT="${SERVER_WEB_ROOT:-}"
SSH_KEY_PATH="${SSH_KEY_PATH:-}"
BACKUP_SUBDIR="${BACKUP_SUBDIR:-.deploy-backups}"
MILESTONE_WEBHOOK_URL="${MILESTONE_WEBHOOK_URL:-}"
MILESTONE_WEBHOOK_TOKEN="${MILESTONE_WEBHOOK_TOKEN:-}"
MILESTONE_WEBHOOK_TIMEOUT="${MILESTONE_WEBHOOK_TIMEOUT:-12}"
BACKEND_DIR="${BACKEND_DIR:-/home/deploy/une-vie-backend}"
BACKEND_SERVICE="${BACKEND_SERVICE:-une-vie-backend}"
DEPLOY_BACKEND="${DEPLOY_BACKEND:-false}"

if [[ -z "$SERVER_HOST" || -z "$SERVER_WEB_ROOT" ]]; then
  echo "Missing required env vars: SERVER_HOST, SERVER_WEB_ROOT"
  exit 1
fi

FILES=(
  "index.html"
  "news.html"
  "travel.html"
  "reading.html"
  "french.html"
  "vibe.html"
  "social.html"
  "style.css"
)

ASSET_DIRS=(
  "media"
  "icons"
)

for f in "${FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required file: $f"
    exit 1
  fi
done

for d in "${ASSET_DIRS[@]}"; do
  if [[ ! -d "$d" ]]; then
    echo "Missing asset directory: $d"
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
  for f in ${FILES[*]}; do if [ -f \"\$f\" ]; then cp -a \"\$f\" '$REMOTE_BACKUP_DIR'/; fi; done"

echo "Uploading files..."
scp "${SCP_OPTS[@]}" "${FILES[@]}" "$SERVER_USER@$SERVER_HOST:$SERVER_WEB_ROOT/"

echo "Uploading asset directories..."
for d in "${ASSET_DIRS[@]}"; do
  scp -r "${SCP_OPTS[@]}" "$d" "$SERVER_USER@$SERVER_HOST:$SERVER_WEB_ROOT/"
done

echo "Reloading nginx..."
ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" \
  "sudo /usr/sbin/nginx -t && (sudo /bin/systemctl reload nginx || sudo /usr/sbin/service nginx reload)"

# ── Backend deploy (opt-in via DEPLOY_BACKEND=true) ──────────────────────
if [[ "$DEPLOY_BACKEND" == "true" ]]; then
  echo "Uploading backend Python files..."
  scp -r "${SCP_OPTS[@]}" backend/app/ "$SERVER_USER@$SERVER_HOST:$BACKEND_DIR/"
  scp "${SCP_OPTS[@]}" backend/requirements.txt "$SERVER_USER@$SERVER_HOST:$BACKEND_DIR/"

  echo "Restarting backend service (${BACKEND_SERVICE})..."
  # Uses root SSH to run systemctl (deploy user needs sudo or use root key)
  ROOT_SSH_OPTS=("${SSH_OPTS[@]}")
  ssh "${ROOT_SSH_OPTS[@]}" "root@$SERVER_HOST" \
    "cd '$BACKEND_DIR' && \
     .venv/bin/pip install -q -r requirements.txt && \
     /bin/systemctl restart '$BACKEND_SERVICE' && \
     echo 'Backend restarted OK'"
fi

if [[ -n "$MILESTONE_WEBHOOK_URL" ]]; then
  PHOTO_COUNT="$(grep -o 'class="js-lazy-photo"' travel.html | wc -l | tr -d ' ')"
  PHOTO_LIST_JSON="$(grep -o 'src="media/[^"]*"' travel.html | sed -E 's/src="([^"]*)"/"\1"/' | paste -sd, -)"
  if [[ -z "$PHOTO_LIST_JSON" ]]; then
    PHOTO_LIST_JSON=""
  fi

  PAYLOAD=$(cat <<EOF
{"event":"travel_photos_updated","page":"travel.html","milestone":"Nice","photo_count":${PHOTO_COUNT:-0},"photos":[${PHOTO_LIST_JSON}],"deployed_url":"http://$SERVER_HOST/travel.html","deployed_at":"$TS"}
EOF
)

  echo "Notifying milestone webhook..."
  CURL_ARGS=(
    --fail --silent --show-error
    --max-time "$MILESTONE_WEBHOOK_TIMEOUT"
    -X POST "$MILESTONE_WEBHOOK_URL"
    -H "Content-Type: application/json"
    -d "$PAYLOAD"
  )
  if [[ -n "$MILESTONE_WEBHOOK_TOKEN" ]]; then
    CURL_ARGS+=( -H "Authorization: Bearer $MILESTONE_WEBHOOK_TOKEN" )
  fi

  curl "${CURL_ARGS[@]}"
  echo "Milestone webhook notified."
fi

echo "Done: http://$SERVER_HOST/"

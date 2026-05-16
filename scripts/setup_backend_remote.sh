#!/usr/bin/env bash
set -euo pipefail

# Usage:
# SERVER_HOST=47.98.235.65 SERVER_USER=deploy SSH_KEY_PATH=~/.ssh/id_ed25519_deploy ./scripts/setup_backend_remote.sh

SERVER_HOST="${SERVER_HOST:-}"
SERVER_USER="${SERVER_USER:-deploy}"
SERVER_PORT="${SERVER_PORT:-22}"
SSH_KEY_PATH="${SSH_KEY_PATH:-}"

if [[ -z "$SERVER_HOST" ]]; then
  echo "Missing SERVER_HOST"
  exit 1
fi

SSH_OPTS=(-p "$SERVER_PORT")
SCP_OPTS=(-P "$SERVER_PORT")
if [[ -n "$SSH_KEY_PATH" ]]; then
  SSH_OPTS+=( -i "$SSH_KEY_PATH" )
  SCP_OPTS+=( -i "$SSH_KEY_PATH" )
fi

REMOTE_DIR="/home/$SERVER_USER/une-vie-backend"

echo "Preparing remote directories..."
ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" "mkdir -p '$REMOTE_DIR'"

echo "Uploading backend files..."
scp -r "${SCP_OPTS[@]}" backend/app "$SERVER_USER@$SERVER_HOST:$REMOTE_DIR/"
scp "${SCP_OPTS[@]}" backend/requirements.txt "$SERVER_USER@$SERVER_HOST:$REMOTE_DIR/"

if [[ -f backend/.env ]]; then
  scp "${SCP_OPTS[@]}" backend/.env "$SERVER_USER@$SERVER_HOST:$REMOTE_DIR/.env"
fi

echo "Installing Python env + dependencies on remote..."
ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" "cd '$REMOTE_DIR' && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

echo "Installing systemd service..."
scp "${SCP_OPTS[@]}" scripts/une-vie-backend.service "$SERVER_USER@$SERVER_HOST:/tmp/une-vie-backend.service"
ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" "sudo mv /tmp/une-vie-backend.service /etc/systemd/system/une-vie-backend.service && sudo systemctl daemon-reload && sudo systemctl enable --now une-vie-backend"

echo "Done. Check status:"
ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" "sudo systemctl status --no-pager une-vie-backend | sed -n '1,20p'"

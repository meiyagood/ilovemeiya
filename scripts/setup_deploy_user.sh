#!/usr/bin/env bash
set -euo pipefail

# Idempotent setup for a non-root deploy user on the target server.
# Usage:
#   SERVER_HOST=47.98.235.65 ROOT_SSH_KEY=~/.ssh/id_ed25519_deploy DEPLOY_PUBKEY_PATH=~/.ssh/id_ed25519_deploy.pub ./scripts/setup_deploy_user.sh

SERVER_HOST="${SERVER_HOST:-}"
SERVER_PORT="${SERVER_PORT:-22}"
ROOT_USER="${ROOT_USER:-root}"
ROOT_SSH_KEY="${ROOT_SSH_KEY:-}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"
SERVER_WEB_ROOT="${SERVER_WEB_ROOT:-/usr/share/nginx/html}"
DEPLOY_PUBKEY_PATH="${DEPLOY_PUBKEY_PATH:-$HOME/.ssh/id_ed25519_deploy.pub}"

if [[ -z "$SERVER_HOST" ]]; then
  echo "Missing required env var: SERVER_HOST"
  exit 1
fi
if [[ ! -f "$DEPLOY_PUBKEY_PATH" ]]; then
  echo "Public key not found: $DEPLOY_PUBKEY_PATH"
  exit 1
fi

SSH_OPTS=(-p "$SERVER_PORT")
if [[ -n "$ROOT_SSH_KEY" ]]; then
  SSH_OPTS+=( -i "$ROOT_SSH_KEY" )
fi

DEPLOY_PUBKEY="$(cat "$DEPLOY_PUBKEY_PATH")"

ssh "${SSH_OPTS[@]}" "$ROOT_USER@$SERVER_HOST" "
set -e
id -u '$DEPLOY_USER' >/dev/null 2>&1 || useradd -m -s /bin/bash '$DEPLOY_USER'
mkdir -p /home/$DEPLOY_USER/.ssh
chmod 700 /home/$DEPLOY_USER/.ssh
touch /home/$DEPLOY_USER/.ssh/authorized_keys
chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys
chown -R $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/.ssh
if ! grep -qxF '$DEPLOY_PUBKEY' /home/$DEPLOY_USER/.ssh/authorized_keys; then
  echo '$DEPLOY_PUBKEY' >> /home/$DEPLOY_USER/.ssh/authorized_keys
fi
mkdir -p '$SERVER_WEB_ROOT'
chown -R $DEPLOY_USER:$DEPLOY_USER '$SERVER_WEB_ROOT'
find '$SERVER_WEB_ROOT' -type d -exec chmod 755 {} \\\;
find '$SERVER_WEB_ROOT' -type f -exec chmod 644 {} \\\;
cat >/etc/sudoers.d/$DEPLOY_USER-nginx <<EOF
Defaults:$DEPLOY_USER !requiretty
$DEPLOY_USER ALL=(root) NOPASSWD:/usr/sbin/nginx -t,/bin/systemctl reload nginx,/usr/sbin/service nginx reload
EOF
chmod 440 /etc/sudoers.d/$DEPLOY_USER-nginx
visudo -cf /etc/sudoers.d/$DEPLOY_USER-nginx
"

echo "Deploy user setup completed: $DEPLOY_USER@$SERVER_HOST"

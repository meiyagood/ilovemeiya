#!/usr/bin/env bash
# =============================================================
# deploy.sh — 部署 Flask 后台到阿里云服务器
# 用法：
#   SERVER_HOST=47.98.235.65 SERVER_USER=root ./deploy.sh
# 可选：
#   SERVER_PORT=22（默认22）
#   SSH_KEY_PATH=~/.ssh/id_rsa
# =============================================================
set -euo pipefail

# ── 配置项（可通过环境变量覆盖）──────────────────────────────
SERVER_HOST="${SERVER_HOST:-47.98.235.65}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PORT="${SERVER_PORT:-22}"
SSH_KEY_PATH="${SSH_KEY_PATH:-}"
BACKEND_DIR="${BACKEND_DIR:-/root/ilovemeiyawebsite/backend}"
ADMIN_PORT="${ADMIN_PORT:-8001}"

# ── SSH / SCP 参数拼装 ────────────────────────────────────────
SSH_OPTS=(-p "$SERVER_PORT" -o StrictHostKeyChecking=no)
if [[ -n "$SSH_KEY_PATH" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY_PATH")
fi

echo "🚀  开始部署到 $SERVER_USER@$SERVER_HOST ..."

# ── 在服务器上远程执行部署逻辑 ────────────────────────────────
ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" bash -s << REMOTE
set -euo pipefail

# 1. 进入项目后台目录
echo "📂  进入 $BACKEND_DIR ..."
cd "$BACKEND_DIR"

# 2. 拉取最新代码
echo "📥  git pull ..."
git pull

# 3. 安装/更新依赖
echo "📦  pip install ..."
pip3 install -q -r requirements.txt

# 4. 检查并清理旧进程（占用 $ADMIN_PORT 端口）
OLD_PID=\$(lsof -ti :$ADMIN_PORT 2>/dev/null || true)
if [[ -n "\$OLD_PID" ]]; then
  echo "🔪  终止旧进程 PID \$OLD_PID ..."
  kill -9 \$OLD_PID
  sleep 1
fi

# 5. 后台重新启动服务
echo "▶️   启动 admin_app.py ..."
nohup python3 admin_app.py > admin_app.log 2>&1 &
NEW_PID=\$!
sleep 2

# 验证启动成功
if kill -0 \$NEW_PID 2>/dev/null; then
  echo "✅  服务已启动，PID=\$NEW_PID，端口 $ADMIN_PORT"
  echo "📄  日志：$BACKEND_DIR/admin_app.log"
else
  echo "❌  启动失败，请查看日志："
  tail -20 admin_app.log
  exit 1
fi
REMOTE

echo ""
echo "🎉  部署完成！后台地址：http://$SERVER_HOST:$ADMIN_PORT/une-vie-admin/login"


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

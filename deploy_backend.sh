#!/usr/bin/env bash
# =============================================================
# deploy_backend.sh — 部署 Flask 后台到阿里云服务器
# 用法：
#   ./deploy_backend.sh
# 可选环境变量：
#   SERVER_HOST=47.98.235.65
#   SERVER_USER=root
#   SERVER_PORT=22
#   SSH_KEY_PATH=~/.ssh/id_rsa
#   BACKEND_DIR=/root/ilovemeiyawebsite/backend
#   ADMIN_PORT=8001
# =============================================================
set -euo pipefail

SERVER_HOST="${SERVER_HOST:-47.98.235.65}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PORT="${SERVER_PORT:-22}"
SSH_KEY_PATH="${SSH_KEY_PATH:-}"
BACKEND_DIR="${BACKEND_DIR:-/root/ilovemeiyawebsite/backend}"
ADMIN_PORT="${ADMIN_PORT:-8001}"

SSH_OPTS=(-p "$SERVER_PORT" -o StrictHostKeyChecking=no)
if [[ -n "$SSH_KEY_PATH" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY_PATH")
fi

echo "🚀  开始部署到 $SERVER_USER@$SERVER_HOST ..."

ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" \
  BACKEND_DIR="$BACKEND_DIR" ADMIN_PORT="$ADMIN_PORT" \
  bash -s << 'REMOTE'
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

# 4. 检查并清理旧进程（占用端口）
OLD_PID=$(lsof -ti :"$ADMIN_PORT" 2>/dev/null || true)
if [[ -n "$OLD_PID" ]]; then
  echo "🔪  终止旧进程 PID $OLD_PID ..."
  kill -9 "$OLD_PID"
  sleep 1
fi

# 5. 后台重新启动服务
echo "▶️   启动 admin_app.py ..."
nohup python3 admin_app.py > admin_app.log 2>&1 &
NEW_PID=$!
sleep 2

if kill -0 "$NEW_PID" 2>/dev/null; then
  echo "✅  服务已启动，PID=$NEW_PID，端口 $ADMIN_PORT"
  echo "📄  日志：$BACKEND_DIR/admin_app.log"
else
  echo "❌  启动失败，请查看日志："
  tail -20 admin_app.log
  exit 1
fi
REMOTE

echo ""
echo "🎉  部署完成！后台地址：http://$SERVER_HOST:$ADMIN_PORT/une-vie-admin/login"

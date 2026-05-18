#!/bin/bash
# Une vie pensée 后端 - 快速启动脚本

set -e

echo "========================================"
echo "🚀 Une vie pensée 后端启动助手"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR"

echo "📁 项目路径: $BACKEND_DIR"
echo ""

# 检查 Python 版本
echo "🐍 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3，请先安装 Python 3.10 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "📦 创建虚拟环境..."
    cd "$BACKEND_DIR"
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
else
    echo "✅ 虚拟环境已存在"
fi

echo ""
echo "📦 激活虚拟环境..."
source "$BACKEND_DIR/venv/bin/activate"
echo "✅ 虚拟环境已激活"

echo ""
echo "📥 安装依赖..."
cd "$BACKEND_DIR"
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet -r requirements.txt
echo "✅ 依赖安装完成"

echo ""
echo "🗄️  初始化数据库..."
if [ ! -f "$BACKEND_DIR/data.db" ]; then
    python init_db.py
    echo "✅ 数据库初始化完成"
else
    echo "✅ 数据库已存在"
    read -p "是否重新初始化数据库? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$BACKEND_DIR/data.db"
        python init_db.py
        echo "✅ 数据库已重新初始化"
    fi
fi

echo ""
echo "========================================"
echo "✨ 启动信息"
echo "========================================"
echo ""
echo "服务器地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo "ReDoc: http://localhost:8000/redoc"
echo ""
echo "默认管理员:"
echo "  用户名: admin"
echo "  密码: change-me"
echo ""
echo "⚠️  重要: 部署到生产环境前必须修改默认密码！"
echo ""
echo "========================================"
echo ""

# 启动服务器
echo "🚀 正在启动 FastAPI 服务器..."
echo "按 Ctrl+C 停止服务"
echo ""

cd "$BACKEND_DIR"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

"""
Flask 后台管理应用
独立运行于 port 8001，提供 /une-vie-admin 网页后台。
FastAPI 主服务（port 8000）负责 JSON API；本应用负责服务端渲染的管理界面。

运行方式：
    python admin_app.py
或通过 Nginx 反代 /une-vie-admin -> localhost:8001
"""

from __future__ import annotations

import os
from datetime import timedelta
from functools import wraps

import secrets

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# ──────────────────────────────────────────────────────────
# 应用初始化
# ──────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "app"),   # admin.html 在 backend/app/
    static_folder=os.path.join(BASE_DIR, "app", "static"),
)

# Session 签名密钥（必须在生产环境中通过环境变量设置）
app.secret_key = os.getenv("SESSION_SECRET_KEY", "default-fallback-key-please-change")
app.permanent_session_lifetime = timedelta(hours=24)

# 后台通行密码（单密码极简模式）
ADMIN_PASSPHRASE: str | None = os.getenv("ADMIN_PASSPHRASE")

# ──────────────────────────────────────────────────────────
# 登录保护装饰器
# ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


# ──────────────────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────────────────

@app.route("/une-vie-admin")
@login_required
def admin_dashboard():
    """后台主页——未登录时自动跳转到登录页。"""
    return render_template("admin_dashboard.html", posts=[])


@app.route("/une-vie-admin/login", methods=["GET"])
def admin_login():
    """登录页面——已登录时直接跳转到后台。"""
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")


@app.route("/une-vie-admin/login", methods=["POST"])
def admin_login_post():
    """处理登录表单。使用 secrets.compare_digest 防止时序攻击。"""
    input_passphrase = request.form.get("passphrase", "")

    if not ADMIN_PASSPHRASE:
        flash("后台未配置 ADMIN_PASSPHRASE 环境变量，无法登录。", "error")
        return redirect(url_for("admin_login"))

    if secrets.compare_digest(input_passphrase, ADMIN_PASSPHRASE):
        session["is_admin"] = True
        session.permanent = True
        return redirect(url_for("admin_dashboard"))

    flash("密码错误，请重新输入。", "error")
    return redirect(url_for("admin_login"))


@app.route("/une-vie-admin/logout", methods=["POST"])
def admin_logout():
    """清除 session 并跳转到登录页。"""
    session.clear()
    flash("已安全退出后台。", "info")
    return redirect(url_for("admin_login"))


# ──────────────────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("ADMIN_PORT", 8001))
    debug = os.getenv("ENV", "development") == "development"
    print(f"🔑 Admin UI running at http://localhost:{port}/une-vie-admin")
    app.run(host="0.0.0.0", port=port, debug=debug)

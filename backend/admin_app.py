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
import sys
from datetime import timedelta
from functools import wraps

import secrets

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_cors import CORS

# 将 backend/ 加入路径，以便导入 app 包（models, database）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal, engine
from app.models import Base, Quote

# 确保表存在（仅建新表，不删旧表）
Base.metadata.create_all(bind=engine, checkfirst=True)

# ──────────────────────────────────────────────────────────
# 应用初始化
# ──────────────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "app", "templates"),
    static_folder=os.path.join(BASE_DIR, "app", "static"),
)

# 允许前台域名跨域访问 /api/* 接口
CORS(app, resources={r"/api/*": {"origins": ["https://zaoanmeiya.com", "http://zaoanmeiya.com", "http://localhost:*"]}})

# Session 签名密钥（必须在生产环境中通过环境变量设置）
app.secret_key = os.getenv("SESSION_SECRET_KEY", "default-fallback-key-please-change")
app.permanent_session_lifetime = timedelta(hours=24)

# 后台通行密码（单密码极简模式）
ADMIN_PASSPHRASE: str | None = os.getenv("ADMIN_PASSPHRASE")


# ──────────────────────────────────────────────────────────
# 数据库辅助
# ──────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
# 后台主页
# ──────────────────────────────────────────────────────────

@app.route("/une-vie-admin")
@login_required
def admin_dashboard():
    """后台主页——未登录时自动跳转到登录页。"""
    from app.models import DailyLog
    db = SessionLocal()
    try:
        posts  = db.query(DailyLog).order_by(DailyLog.id.desc()).all()
        quotes = db.query(Quote).order_by(Quote.created_at.desc()).all()
    finally:
        db.close()
    return render_template("admin_dashboard.html", posts=posts, quotes=quotes)


# ──────────────────────────────────────────────────────────
# 登录 / 退出
# ──────────────────────────────────────────────────────────

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
# Quote 路由：Focus & Milestone 语录管理
# ──────────────────────────────────────────────────────────

@app.route("/une-vie-admin/quote/add", methods=["POST"])
@login_required
def quote_add():
    """添加新语录。表单字段：content（必填）、source（可选）。"""
    content = request.form.get("content", "").strip()
    source = request.form.get("source", "").strip()

    if not content:
        flash("语录内容不能为空。", "error")
        return redirect(url_for("admin_dashboard") + "#miniapp")

    db = SessionLocal()
    try:
        quote = Quote(content=content, source=source, is_current=False)
        db.add(quote)
        db.commit()
        flash(f"语录已添加：{content[:40]}…" if len(content) > 40 else f"语录已添加：{content}", "success")
    except Exception as e:
        db.rollback()
        flash(f"添加失败：{e}", "error")
    finally:
        db.close()

    return redirect(url_for("admin_dashboard") + "#miniapp")


@app.route("/une-vie-admin/quote/toggle/<int:quote_id>", methods=["POST"])
@login_required
def quote_toggle(quote_id: int):
    """
    将指定语录设为前台激活（is_current=True），
    同时将其他所有语录的 is_current 设为 False，保证唯一性。
    支持 JSON（AJAX）和表单（form）两种请求方式。
    """
    db = SessionLocal()
    try:
        target = db.query(Quote).filter(Quote.id == quote_id).first()
        if not target:
            if request.is_json:
                return jsonify({"ok": False, "error": "语录不存在"}), 404
            flash("语录不存在。", "error")
            return redirect(url_for("admin_dashboard") + "#miniapp")

        # 清空所有 is_current，再激活目标
        db.query(Quote).update({"is_current": False})
        target.is_current = True
        db.commit()

        if request.is_json:
            return jsonify({"ok": True, "active_id": quote_id})

        flash(f"「{target.content[:30]}」已设为今日展示。", "success")
    except Exception as e:
        db.rollback()
        if request.is_json:
            return jsonify({"ok": False, "error": str(e)}), 500
        flash(f"操作失败：{e}", "error")
    finally:
        db.close()

    return redirect(url_for("admin_dashboard") + "#miniapp")


@app.route("/une-vie-admin/quote/delete/<int:quote_id>", methods=["POST"])
@login_required
def quote_delete(quote_id: int):
    """删除指定语录。"""
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            flash("语录不存在。", "error")
        else:
            db.delete(quote)
            db.commit()
            flash("语录已删除。", "success")
    except Exception as e:
        db.rollback()
        flash(f"删除失败：{e}", "error")
    finally:
        db.close()

    return redirect(url_for("admin_dashboard") + "#miniapp")


# ──────────────────────────────────────────────────────────
# 公开 API：前台获取当前激活语录
# ──────────────────────────────────────────────────────────

@app.route("/api/quote/current")
def api_quote_current():
    """返回当前激活语录（JSON），供前台 vibe.html 动态加载。"""
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.is_current == True).first()
        if quote:
            return jsonify(quote.to_dict())
        return jsonify({"content": "今日语录：真正的秩序，从自我观察开始。", "source": ""})
    finally:
        db.close()


# ──────────────────────────────────────────────────────────
# Post 路由：动态管理
# ──────────────────────────────────────────────────────────

@app.route("/une-vie-admin/post/create", methods=["POST"])
@login_required
def post_create():
    """发布新动态，写入 DailyLog 表。"""
    from app.models import DailyLog
    content  = request.form.get("content", "").strip()
    title    = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()

    if not content:
        flash("内容不能为空。", "error")
        return redirect(url_for("admin_dashboard"))

    db = SessionLocal()
    try:
        log = DailyLog(title=title, content=content, category=category, is_published=True)
        db.add(log)
        db.commit()
        flash("动态已发布！", "success")
    except Exception as e:
        db.rollback()
        flash(f"发布失败：{e}", "error")
    finally:
        db.close()

    return redirect(url_for("admin_dashboard"))


@app.route("/une-vie-admin/post/<int:post_id>/delete", methods=["POST"])
@login_required
def post_delete(post_id: int):
    """删除指定动态。"""
    from app.models import DailyLog
    db = SessionLocal()
    try:
        post = db.query(DailyLog).filter(DailyLog.id == post_id).first()
        if post:
            db.delete(post)
            db.commit()
            flash("动态已删除。", "success")
        else:
            flash("动态不存在。", "error")
    except Exception as e:
        db.rollback()
        flash(f"删除失败：{e}", "error")
    finally:
        db.close()
    return redirect(url_for("admin_dashboard"))


# ──────────────────────────────────────────────────────────
# Miniapp 路由：小程序其他配置（占位）
# ──────────────────────────────────────────────────────────

@app.route("/une-vie-admin/miniapp/save", methods=["POST"])
@login_required
def miniapp_save():
    flash("小程序配置已保存。", "success")
    return redirect(url_for("admin_dashboard") + "#miniapp")


@app.route("/api/posts")
def api_posts():
    """返回已发布动态列表（JSON），供前台 vibe.html 动态加载。"""
    from app.models import DailyLog
    db = SessionLocal()
    try:
        logs = (
            db.query(DailyLog)
            .filter(DailyLog.is_published == True)
            .order_by(DailyLog.posted_at.desc())
            .limit(20)
            .all()
        )
        return jsonify([l.to_dict() for l in logs])
    finally:
        db.close()


# ──────────────────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("ADMIN_PORT", 8001))
    debug = os.getenv("ENV", "development") == "development"
    print(f"🔑 Admin UI running at http://localhost:{port}/une-vie-admin")
    app.run(host="0.0.0.0", port=port, debug=debug)

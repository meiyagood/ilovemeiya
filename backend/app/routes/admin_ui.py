"""
后台管理 Web 界面路由
提供 /une-vie-admin 网页后台，使用 session cookie 认证。
认证逻辑：timing-safe 比对环境变量中的用户名/密码。
"""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..config import ADMIN_PASSWORD, ADMIN_USERNAME

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["Admin UI"])

_SESSION_KEY = "admin_authenticated"


def _is_authenticated(request: Request) -> bool:
    return request.session.get(_SESSION_KEY) is True


# ──────────────────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────────────────

@router.get("/une-vie-admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """后台主页——未登录时重定向到登录页。"""
    if not _is_authenticated(request):
        return RedirectResponse(url="/une-vie-admin/login", status_code=302)
    return templates.TemplateResponse("admin.html", {"request": request})


# ──────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────

@router.get("/une-vie-admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    """登录页面——已登录时直接跳转到后台。"""
    if _is_authenticated(request):
        return RedirectResponse(url="/une-vie-admin", status_code=302)
    return templates.TemplateResponse(
        "admin_login.html", {"request": request, "error": None}
    )


@router.post("/une-vie-admin/login", response_class=HTMLResponse)
def admin_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """处理登录表单提交。使用 timing-safe 比对防止时序攻击。"""
    valid_user = secrets.compare_digest(username, ADMIN_USERNAME)
    valid_pass = secrets.compare_digest(password, ADMIN_PASSWORD)

    if valid_user and valid_pass:
        request.session[_SESSION_KEY] = True
        return RedirectResponse(url="/une-vie-admin", status_code=303)

    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": "用户名或密码错误"},
        status_code=401,
    )


# ──────────────────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────────────────

@router.post("/une-vie-admin/logout")
def admin_logout(request: Request):
    """清除 session 并跳转到登录页。"""
    request.session.clear()
    return RedirectResponse(url="/une-vie-admin/login", status_code=303)

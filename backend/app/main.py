"""
主应用入口文件
初始化 FastAPI 应用并配置所有中间件和路由
"""

from __future__ import annotations

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .auth import verify_admin
from .config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    CORS_ORIGINS,
    STATIC_DIR,
    UPLOAD_DIR,
)
from .database import Base, engine
from .routes import (
    public_router,
    articles_router,
    albums_router,
    daily_logs_router,
    categories_router,
    admin_router,
    news_router,
)


# ──────────────────────────────────────────────────────────
# 启动和关闭事件
# ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动和关闭事件处理
    """
    # 启动事件
    print("🚀 Starting Une vie pensée CMS API...")
    Base.metadata.create_all(bind=engine)
    _ensure_schema_compatibility()
    print("✅ Database initialized")
    
    yield
    
    # 关闭事件
    print("🛑 Shutting down Une vie pensée CMS API...")


def _ensure_schema_compatibility() -> None:
    """
    轻量级数据库迁移检查
    确保数据库表结构与当前模型兼容
    """
    with engine.begin() as conn:
        # 检查并添加缺失的列（如果需要）
        # 这可以根据需要进行扩展
        pass


# ──────────────────────────────────────────────────────────
# FastAPI 应用初始化
# ──────────────────────────────────────────────────────────

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ──────────────────────────────────────────────────────────
# 注册路由
# ──────────────────────────────────────────────────────────

# 公开 API
app.include_router(public_router)

# 管理员 API（通用）
app.include_router(admin_router)

# 资源 API（需要认证）
app.include_router(articles_router)
app.include_router(albums_router)
app.include_router(daily_logs_router)
app.include_router(categories_router)
app.include_router(news_router)


# ──────────────────────────────────────────────────────────
# 管理员 HTML 面板
# ──────────────────────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/", response_class=HTMLResponse)
def admin_panel(_: str = Depends(verify_admin)):
    """服务管理后台 HTML 页面（需要 HTTP Basic 认证）"""
    admin_html = Path(__file__).parent / "admin.html"
    return admin_html.read_text(encoding="utf-8")


# ──────────────────────────────────────────────────────────
# 根路由
# ──────────────────────────────────────────────────────────

@app.get("/")
def root():
    """API 根路由"""
    return {
        "service": "Une vie pensée CMS API",
        "version": APP_VERSION,
        "docs": "/docs",
        "docs_alternative": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



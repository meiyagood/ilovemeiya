"""
路由模块
包含所有 API 端点的定义
"""

from .public import router as public_router
from .articles import router as articles_router
from .albums import router as albums_router
from .daily_logs import router as daily_logs_router
from .categories import router as categories_router
from .admin import router as admin_router

__all__ = [
    "public_router",
    "articles_router",
    "albums_router",
    "daily_logs_router",
    "categories_router",
    "admin_router",
]

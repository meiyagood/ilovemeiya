"""
配置管理模块
管理应用的所有环境变量和配置参数
"""

from __future__ import annotations

import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# 数据库配置
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 应用配置
APP_TITLE = "Une vie pensée CMS API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
一个思考的人生 - 融合个人摄影展示与哲学思考的 minimal 风格网站后端

API 文档可在 `/docs` 查看（Swagger UI）或 `/redoc` 查看（ReDoc）
"""

# CORS 配置
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,https://www.zaoanmeiya.com").split(",") if o.strip()] or ["*"]

# 管理员认证
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")

# JWT 配置（可选，如需升级认证）
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# 文件上传配置
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MEDIA_DIR = Path(__file__).resolve().parent / "static" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 环境标识
ENV = os.getenv("ENV", "development")
DEBUG = ENV == "development"

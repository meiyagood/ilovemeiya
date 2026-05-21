"""
数据库模型定义
使用 SQLAlchemy ORM 定义所有数据库表结构
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# ──────────────────────────────────────────────────────────
# 用户与认证
# ──────────────────────────────────────────────────────────

class User(Base):
    """管理员用户模型 - 用于后台登录和权限管理"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 用户信息
    full_name: Mapped[str] = mapped_column(String(200), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    avatar_url: Mapped[str] = mapped_column(String(500), default="")
    
    # 权限和状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ──────────────────────────────────────────────────────────
# 分类和标签
# ──────────────────────────────────────────────────────────

class Category(Base):
    """内容分类模型 - 用于组织文章和相册"""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    name_cn: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(50), default="")
    color: Mapped[str] = mapped_column(String(10), default="#000000")
    layout_type: Mapped[str] = mapped_column(String(30), default="list")
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    articles: Mapped[list[Article]] = relationship("Article", back_populates="category")
    albums: Mapped[list[Album]] = relationship("Album", back_populates="category")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name_fr": self.name_fr,
            "name_cn": self.name_cn,
            "slug": self.slug,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "layout_type": self.layout_type,
            "order": self.order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }



# ──────────────────────────────────────────────────────────
# 文章与哲学随想
# ──────────────────────────────────────────────────────────

class Article(Base):
    """文章/哲学随想模型 - 支持 Markdown 格式"""
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    
    # 内容
    summary: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")  # Markdown 格式
    
    # 元数据
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    cover_url: Mapped[str] = mapped_column(String(500), default="")
    tags: Mapped[str] = mapped_column(String(500), default="")  # 逗号分隔的标签
    
    # 发布状态
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)  # 精选文章
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关系
    category: Mapped[Optional[Category]] = relationship("Category", back_populates="articles")

    def to_dict(self, include_content: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "summary": self.summary,
            "category_id": self.category_id,
            "category": self.category.to_dict() if self.category else None,
            "cover_url": self.cover_url,
            "tags": [t.strip() for t in self.tags.split(",") if t.strip()],
            "is_published": self.is_published,
            "featured": self.featured,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
        if include_content:
            data["content"] = self.content
        return data


# ──────────────────────────────────────────────────────────
# 相册与照片
# ──────────────────────────────────────────────────────────

class Album(Base):
    """相册模型 - 用于组织摄影作品"""
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    title_cn: Mapped[str] = mapped_column(String(200), default="")
    
    # 描述
    description_fr: Mapped[str] = mapped_column(Text, default="")
    description_cn: Mapped[str] = mapped_column(Text, default="")
    
    # 元数据
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    cover_url: Mapped[str] = mapped_column(String(500), default="")
    
    # 状态
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_count: Mapped[int] = mapped_column(Integer, default=0)  # 缓存照片数量
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    category: Mapped[Optional[Category]] = relationship("Category", back_populates="albums")
    photos: Mapped[list[Photo]] = relationship(
        "Photo",
        back_populates="album",
        cascade="all, delete-orphan",
        order_by="Photo.order",
    )

    def to_dict(self, include_photos: bool = False) -> dict:
        data = {
            "id": self.id,
            "title_fr": self.title_fr,
            "title_cn": self.title_cn,
            "description_fr": self.description_fr,
            "description_cn": self.description_cn,
            "category_id": self.category_id,
            "category": self.category.to_dict() if self.category else None,
            "cover_url": self.cover_url,
            "is_published": self.is_published,
            "photo_count": self.photo_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_photos:
            data["photos"] = [photo.to_dict() for photo in self.photos]
        return data


# ──────────────────────────────────────────────────────────
# 日常随笔与日志
# ──────────────────────────────────────────────────────────

class DailyLog(Base):
    """日常日志/随笔模型 - 记录碎片化的思考或短句"""
    __tablename__ = "daily_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 内容
    title: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 主要内容
    
    # 作者信息
    author: Mapped[str] = mapped_column(String(100), default="美芽")
    
    # 状态
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    mood: Mapped[str] = mapped_column(String(50), default="")  # 心情标签：calm, thoughtful, happy 等
    
    # 时间戳
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)  # 发布时间（用于排序和显示）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        posted_str = self.posted_at.strftime("%Y.%m.%d %H:%M") if self.posted_at else ""
        if self.title:
            posted_str += f" {self.author}《{self.title}》"
        else:
            posted_str += f" {self.author}"
        
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "is_published": self.is_published,
            "mood": self.mood,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "posted_display": posted_str,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Photo(Base):
    """照片模型 - 属于某个相册"""
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), nullable=False, index=True)
    
    # 图片信息
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(500), default="")
    
    # 元数据
    title: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")  # 可以包含哲学寄语
    photographer_note: Mapped[str] = mapped_column(Text, default="")  # 摄影师的话
    
    # 拍摄信息
    taken_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    location: Mapped[str] = mapped_column(String(300), default="")
    
    # 排序
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    album: Mapped[Album] = relationship("Album", back_populates="photos")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "album_id": self.album_id,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "title": self.title,
            "description": self.description,
            "photographer_note": self.photographer_note,
            "taken_at": self.taken_at.isoformat() if self.taken_at else None,
            "location": self.location,
            "order": self.order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ──────────────────────────────────────────────────────────
# Focus & Milestone 小程序
# ──────────────────────────────────────────────────────────

class Quote(Base):
    """
    哲学语录 / 日常反思，用于 Focus & Milestone 小程序展示。
    is_current=True 的条目显示在前台手机 Mockup 中；同一时刻只有一条激活。
    """
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(200), default="")  # 来源/作者
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "is_current": self.is_current,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

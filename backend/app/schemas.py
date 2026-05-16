"""
Pydantic 数据验证和序列化模型
用于 API 请求和响应的数据校验
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field


# ──────────────────────────────────────────────────────────
# 用户认证相关 Schema
# ──────────────────────────────────────────────────────────

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    full_name: str = ""
    bio: str = ""
    avatar_url: str = ""


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=100)


# ──────────────────────────────────────────────────────────
# 分类 Schema
# ──────────────────────────────────────────────────────────

class CategoryBase(BaseModel):
    name_fr: str = Field(min_length=1, max_length=200)
    name_cn: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=220)
    description: str = ""
    icon: str = ""
    color: str = "#000000"
    layout_type: str = "list"
    order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name_fr: Optional[str] = None
    name_cn: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    layout_type: Optional[str] = None
    order: Optional[int] = None


class CategoryOut(CategoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────
# 文章 Schema
# ──────────────────────────────────────────────────────────

class ArticleBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    slug: str = Field(min_length=1, max_length=320)
    summary: str = ""
    content: str = ""
    category_id: Optional[int] = None
    cover_url: str = ""
    tags: str = ""
    is_published: bool = False
    featured: bool = False


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    cover_url: Optional[str] = None
    tags: Optional[str] = None
    is_published: Optional[bool] = None
    featured: Optional[bool] = None


class ArticleOut(ArticleBase):
    id: int
    category: Optional[CategoryOut] = None
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────
# 相册 Schema
# ──────────────────────────────────────────────────────────

class AlbumBase(BaseModel):
    title_fr: str = Field(min_length=1, max_length=200)
    title_cn: str = ""
    description_fr: str = ""
    description_cn: str = ""
    category_id: Optional[int] = None
    cover_url: str = ""
    is_published: bool = False


class AlbumCreate(AlbumBase):
    pass


class AlbumUpdate(BaseModel):
    title_fr: Optional[str] = None
    title_cn: Optional[str] = None
    description_fr: Optional[str] = None
    description_cn: Optional[str] = None
    category_id: Optional[int] = None
    cover_url: Optional[str] = None
    is_published: Optional[bool] = None


class AlbumOut(AlbumBase):
    id: int
    category: Optional[CategoryOut] = None
    photo_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlbumWithPhotos(AlbumOut):
    photos: list[PhotoOut] = []


# ──────────────────────────────────────────────────────────
# 照片 Schema
# ──────────────────────────────────────────────────────────

class PhotoBase(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    caption_fr: str = ""
    caption_cn: str = ""
    order: int = 0


class PhotoCreate(PhotoBase):
    pass


class PhotoUpdate(BaseModel):
    url: Optional[str] = None
    caption_fr: Optional[str] = None
    caption_cn: Optional[str] = None
    order: Optional[int] = None


class PhotoOut(PhotoBase):
    id: int
    album_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────
# 新闻 Schema
# ──────────────────────────────────────────────────────────

class NewsItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    date: str = Field(min_length=1, max_length=20)
    summary_cn: str = ""
    content_cn: str = ""
    content_en: str = ""
    image_path: str = ""
    image_caption: str = ""
    is_public: bool = False


class NewsItemCreate(NewsItemBase):
    pass


class NewsItemUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    summary_cn: Optional[str] = None
    content_cn: Optional[str] = None
    content_en: Optional[str] = None
    image_path: Optional[str] = None
    image_caption: Optional[str] = None
    is_public: Optional[bool] = None


class NewsItemOut(NewsItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────
# 日常日志 Schema
# ──────────────────────────────────────────────────────────

class DailyLogBase(BaseModel):
    title: str = ""
    content: str = Field(min_length=1)
    author: str = Field(default="美芽", max_length=100)
    mood: str = ""
    is_published: bool = True


class DailyLogCreate(DailyLogBase):
    pass


class DailyLogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    mood: Optional[str] = None
    is_published: Optional[bool] = None


class DailyLogOut(DailyLogBase):
    id: int
    posted_at: datetime
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def posted_display(self) -> str:
        s = self.posted_at.strftime("%Y.%m.%d") if self.posted_at else ""
        return f"{s} {self.author}" if self.author else s

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────
# 文件上传 Schema
# ──────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """文件上传响应"""
    url: str
    filename: str
    size: int
    mime_type: str

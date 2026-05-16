"""
公开 API 路由
用户可访问，无需认证
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Album, Article, DailyLog, Category
from ..schemas import AlbumOut, AlbumWithPhotos, ArticleOut, DailyLogOut, CategoryOut

router = APIRouter(prefix="/api/public", tags=["Public"])


# ──────────────────────────────────────────────────────────
# 健康检查
# ──────────────────────────────────────────────────────────

@router.get("/health")
def health_check() -> dict[str, str]:
    """API 健康检查"""
    return {"status": "ok", "service": "Une vie pensée CMS API"}


# ──────────────────────────────────────────────────────────
# 分类 API
# ──────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    """获取所有分类列表"""
    categories = db.query(Category).order_by(Category.order.asc(), Category.name_fr.asc()).all()
    return categories


@router.get("/categories/{slug}", response_model=CategoryOut)
def get_category(slug: str, db: Session = Depends(get_db)):
    """按 slug 获取分类详情"""
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# ──────────────────────────────────────────────────────────
# 文章 API
# ──────────────────────────────────────────────────────────

@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    skip: int = 0,
    limit: int = 10,
    category_slug: str | None = None,
    db: Session = Depends(get_db),
):
    """
    获取已发布的文章列表
    
    - skip: 跳过的记录数（分页）
    - limit: 返回的最大记录数
    - category_slug: 按分类 slug 过滤
    """
    query = db.query(Article).filter(Article.is_published == True)
    
    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)
    
    articles = query.order_by(Article.published_at.desc()).offset(skip).limit(limit).all()
    return articles


@router.get("/articles/{slug}", response_model=ArticleOut)
def get_article(slug: str, db: Session = Depends(get_db)):
    """获取文章详情（包括完整内容）"""
    article = db.query(Article).filter(Article.slug == slug, Article.is_published == True).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # 增加浏览次数
    article.view_count += 1
    db.commit()
    
    return article


@router.get("/articles/featured", response_model=list[ArticleOut])
def get_featured_articles(limit: int = 5, db: Session = Depends(get_db)):
    """获取精选文章"""
    articles = (
        db.query(Article)
        .filter(Article.is_published == True, Article.featured == True)
        .order_by(Article.published_at.desc())
        .limit(limit)
        .all()
    )
    return articles


# ──────────────────────────────────────────────────────────
# 相册 API
# ──────────────────────────────────────────────────────────

@router.get("/albums", response_model=list[AlbumOut])
def list_albums(db: Session = Depends(get_db)):
    """获取所有已发布的相册列表"""
    albums = db.query(Album).filter(Album.is_published == True).order_by(Album.created_at.desc()).all()
    return albums


@router.get("/albums/{album_id}", response_model=AlbumWithPhotos)
def get_album(album_id: int, db: Session = Depends(get_db)):
    """获取相册及其所有照片"""
    album = db.query(Album).filter(Album.id == album_id, Album.is_published == True).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    return album


# ──────────────────────────────────────────────────────────
# 日志 API
# ──────────────────────────────────────────────────────────

@router.get("/daily-logs", response_model=list[DailyLogOut])
def list_daily_logs(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    获取已发布的日常日志列表（时间倒序排列）
    
    - skip: 跳过的记录数
    - limit: 返回的最大记录数
    """
    logs = (
        db.query(DailyLog)
        .filter(DailyLog.is_published == True)
        .order_by(DailyLog.posted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return logs


@router.get("/daily-logs/latest", response_model=list[DailyLogOut])
def get_latest_daily_logs(limit: int = 5, db: Session = Depends(get_db)):
    """获取最新的日常日志"""
    logs = (
        db.query(DailyLog)
        .filter(DailyLog.is_published == True)
        .order_by(DailyLog.posted_at.desc())
        .limit(limit)
        .all()
    )
    return logs


@router.get("/daily-logs/{log_id}", response_model=DailyLogOut)
def get_daily_log(log_id: int, db: Session = Depends(get_db)):
    """获取单条日常日志"""
    log = db.query(DailyLog).filter(DailyLog.id == log_id, DailyLog.is_published == True).first()
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    return log

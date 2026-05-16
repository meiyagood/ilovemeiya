"""
文章 API 路由
管理员操作：CRUD 文章/哲学随想
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..database import get_db
from ..models import Article, Category
from ..schemas import ArticleCreate, ArticleOut, ArticleUpdate

router = APIRouter(prefix="/api/articles", tags=["Articles"])


# ──────────────────────────────────────────────────────────
# 列表（管理员）
# ──────────────────────────────────────────────────────────

@router.get("", response_model=list[ArticleOut])
def list_articles(
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """列出所有文章（管理员）"""
    return db.query(Article).order_by(Article.created_at.desc()).all()


@router.post("", response_model=ArticleOut, status_code=201)
def create_article(
    payload: ArticleCreate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """创建新文章"""
    # 检查 slug 是否唯一
    if db.query(Article).filter(Article.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail="Article slug already exists")
    
    # 验证分类是否存在
    if payload.category_id:
        category = db.query(Category).filter(Category.id == payload.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    article = Article(**payload.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.put("/{article_id}", response_model=ArticleOut)
def update_article(
    article_id: int,
    payload: ArticleUpdate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """更新文章"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    data = payload.model_dump(exclude_unset=True)
    
    # 检查 slug 唯一性
    if "slug" in data:
        existing = db.query(Article).filter(
            Article.slug == data["slug"], Article.id != article_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Article slug already exists")
    
    # 验证分类
    if "category_id" in data and data["category_id"]:
        category = db.query(Category).filter(Category.id == data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    for key, value in data.items():
        setattr(article, key, value)
    
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}")
def delete_article(
    article_id: int,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """删除文章"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    db.delete(article)
    db.commit()
    return {"ok": True, "message": "Article deleted successfully"}


@router.get("/{article_id}", response_model=ArticleOut)
def get_article_detail(
    article_id: int,
    db: Session = Depends(get_db),
):
    """获取文章详情（管理员和公开）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

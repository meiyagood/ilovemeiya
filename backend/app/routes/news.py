"""
新闻 API 路由
管理员操作：CRUD 新闻条目
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..database import get_db
from ..models import NewsItem
from ..schemas import NewsItemCreate, NewsItemOut, NewsItemUpdate

router = APIRouter(prefix="/api/news", tags=["News"])


@router.get("/public", response_model=list[NewsItemOut])
def list_public_news(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """获取公开新闻列表（仅 is_public=True）"""
    return (
        db.query(NewsItem)
        .filter(NewsItem.is_public == True)  # noqa: E712
        .order_by(NewsItem.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("", response_model=list[NewsItemOut])
def list_news(
    skip: int = 0,
    limit: int = 50,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """获取新闻列表（管理端，包含草稿）"""
    return db.query(NewsItem).order_by(NewsItem.date.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=NewsItemOut, status_code=201)
def create_news(
    payload: NewsItemCreate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """创建新闻条目"""
    item = NewsItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{news_id}", response_model=NewsItemOut)
def update_news(
    news_id: int,
    payload: NewsItemUpdate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """更新新闻条目"""
    item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{news_id}")
def delete_news(
    news_id: int,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """删除新闻条目"""
    item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/{news_id}/toggle")
def toggle_news_public(
    news_id: int,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """切换新闻公开状态"""
    item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    item.is_public = not item.is_public
    db.commit()
    db.refresh(item)
    return item

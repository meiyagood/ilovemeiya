"""
分类 API 路由
管理员操作：CRUD 分类
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..database import get_db
from ..models import Category, Article, Album
from ..schemas import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
):
    """获取所有分类"""
    return db.query(Category).order_by(Category.id).all()


# ──────────────────────────────────────────────────────────
# 分类 CRUD
# ──────────────────────────────────────────────────────────

@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """创建新分类"""
    # 检查 slug 是否唯一
    if db.query(Category).filter(Category.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail="Category slug already exists")
    
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """更新分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    data = payload.model_dump(exclude_unset=True)
    
    # 检查 slug 唯一性
    if "slug" in data:
        existing = db.query(Category).filter(
            Category.slug == data["slug"], Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Category slug already exists")
    
    for key, value in data.items():
        setattr(category, key, value)
    
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """删除分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 将该分类下的文章和相册的分类设为 NULL
    db.query(Article).filter(Article.category_id == category_id).update(
        {Article.category_id: None}
    )
    db.query(Album).filter(Album.category_id == category_id).update(
        {Album.category_id: None}
    )
    
    db.delete(category)
    db.commit()
    return {"ok": True, "message": "Category deleted successfully"}


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    """获取分类详情"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

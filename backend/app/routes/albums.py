"""
相册与照片 API 路由
管理员操作：CRUD 相册和照片
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..database import get_db
from ..models import Album, Photo, Category
from ..schemas import (
    AlbumCreate,
    AlbumOut,
    AlbumUpdate,
    AlbumWithPhotos,
    PhotoCreate,
    PhotoOut,
    PhotoUpdate,
)

router = APIRouter(prefix="/api/albums", tags=["Albums"])


# ──────────────────────────────────────────────────────────
# 相册 CRUD
# ──────────────────────────────────────────────────────────

@router.post("", response_model=AlbumOut, status_code=201)
def create_album(
    payload: AlbumCreate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """创建新相册"""
    # 验证分类
    if payload.category_id:
        category = db.query(Category).filter(Category.id == payload.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    album = Album(**payload.model_dump())
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@router.put("/{album_id}", response_model=AlbumOut)
def update_album(
    album_id: int,
    payload: AlbumUpdate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """更新相册"""
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    data = payload.model_dump(exclude_unset=True)
    
    # 验证分类
    if "category_id" in data and data["category_id"]:
        category = db.query(Category).filter(Category.id == data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    for key, value in data.items():
        setattr(album, key, value)
    
    db.commit()
    db.refresh(album)
    return album


@router.delete("/{album_id}")
def delete_album(
    album_id: int,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """删除相册（及其所有照片）"""
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    db.delete(album)  # 级联删除相关照片
    db.commit()
    return {"ok": True, "message": "Album deleted successfully"}


# ──────────────────────────────────────────────────────────
# 照片 CRUD
# ──────────────────────────────────────────────────────────

@router.post("/{album_id}/photos", response_model=PhotoOut, status_code=201)
def create_photo(
    album_id: int,
    payload: PhotoCreate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """在相册中添加照片"""
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    photo = Photo(album_id=album_id, **payload.model_dump())
    db.add(photo)
    
    # 更新相册照片计数
    album.photo_count = db.query(Photo).filter(Photo.album_id == album_id).count() + 1
    
    db.commit()
    db.refresh(photo)
    return photo


@router.put("/photos/{photo_id}", response_model=PhotoOut)
def update_photo(
    photo_id: int,
    payload: PhotoUpdate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """更新照片"""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(photo, key, value)
    
    db.commit()
    db.refresh(photo)
    return photo


@router.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: int,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """删除照片"""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    album_id = photo.album_id
    db.delete(photo)
    
    # 更新相册照片计数
    album = db.query(Album).filter(Album.id == album_id).first()
    if album:
        album.photo_count = db.query(Photo).filter(Photo.album_id == album_id).count()
    
    db.commit()
    return {"ok": True, "message": "Photo deleted successfully"}


@router.get("/{album_id}", response_model=AlbumWithPhotos)
def get_album_with_photos(album_id: int, db: Session = Depends(get_db)):
    """获取相册及其所有照片"""
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return album

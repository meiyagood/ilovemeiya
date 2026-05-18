"""
管理员 API 路由
需要认证，提供内容管理功能
"""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..config import ALLOWED_IMAGE_EXTENSIONS, MAX_FILE_SIZE_BYTES, UPLOAD_DIR
from ..database import get_db
from ..schemas import UploadResponse

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ──────────────────────────────────────────────────────────
# 文件上传
# ──────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    上传图片文件
    
    - 支持格式: jpg, jpeg, png, gif, webp
    - 最大文件大小: 10MB
    """
    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {ALLOWED_IMAGE_EXTENSIONS}",
        )
    
    # 读取文件内容并检查大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size (10MB)",
        )
    
    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # 返回文件信息
    return UploadResponse(
        url=f"/uploads/{unique_filename}",
        filename=unique_filename,
        size=len(content),
        mime_type=file.content_type or "application/octet-stream",
    )


@router.delete("/upload/{filename}")
def delete_file(
    filename: str,
    _: str = Depends(verify_admin),
):
    """删除已上传的文件"""
    file_path = UPLOAD_DIR / filename
    
    # 安全检查：确保文件在上传目录内
    try:
        file_path.resolve().relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return {"ok": True, "message": "File deleted successfully"}
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


# ──────────────────────────────────────────────────────────
# 系统信息
# ──────────────────────────────────────────────────────────

@router.get("/info")
def get_admin_info(_: str = Depends(verify_admin)):
    """获取管理员面板信息"""
    return {
        "service": "Une vie pensée CMS API",
        "version": "1.0.0",
        "upload_dir": str(UPLOAD_DIR),
        "max_file_size_mb": 10,
    }

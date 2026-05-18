"""
日常日志 API 路由
管理员操作：CRUD 日常随笔和日志
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..database import get_db
from ..models import DailyLog
from ..schemas import DailyLogCreate, DailyLogOut, DailyLogUpdate

router = APIRouter(prefix="/api/daily-logs", tags=["Daily Logs"])


# ──────────────────────────────────────────────────────────
# 日志 CRUD
# ──────────────────────────────────────────────────────────

@router.post("", response_model=DailyLogOut, status_code=201)
def create_daily_log(
    payload: DailyLogCreate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """创建新的日常日志"""
    log = DailyLog(**payload.model_dump())
    log.date = log.posted_at  # keep legacy `date` column in sync
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.put("/{log_id}", response_model=DailyLogOut)
def update_daily_log(
    log_id: int,
    payload: DailyLogUpdate,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """更新日常日志"""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(log, key, value)
    if 'posted_at' in data:
        log.date = log.posted_at  # keep legacy `date` column in sync
    
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{log_id}")
def delete_daily_log(
    log_id: int,
    _: str = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """删除日常日志"""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    
    db.delete(log)
    db.commit()
    return {"ok": True, "message": "Daily log deleted successfully"}


@router.get("/{log_id}", response_model=DailyLogOut)
def get_daily_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
):
    """获取日常日志详情"""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    return log


@router.get("", response_model=list[DailyLogOut])
def list_daily_logs(
    skip: int = 0,
    limit: int = 20,
    published_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    获取日常日志列表
    
    - skip: 跳过的记录数
    - limit: 返回的最大记录数
    - published_only: 仅返回已发布的日志
    """
    query = db.query(DailyLog)
    
    if published_only:
        query = query.filter(DailyLog.is_published == True)
    
    logs = query.order_by(DailyLog.posted_at.desc()).offset(skip).limit(limit).all()
    return logs

"""
认证和授权模块
处理管理员认证、权限验证和令牌管理
"""

from __future__ import annotations

import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import ADMIN_USERNAME, ADMIN_PASSWORD
from .database import get_db
from .models import User
from .security import verify_password, verify_token

security = HTTPBasic()
bearer_scheme = HTTPBearer(auto_error=False)


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    验证 HTTP Basic 认证的管理员凭证
    
    Args:
        credentials: HTTP Basic 认证凭证
        
    Returns:
        管理员用户名
        
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    # 使用 timing-safe 比较防止时序攻击
    is_valid_user = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_valid_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)

    if not (is_valid_user and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def verify_admin_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    验证 JWT 令牌认证的管理员用户
    
    Args:
        credentials: Bearer 令牌凭证
        db: 数据库会话
        
    Returns:
        管理员用户对象
        
    Raises:
        HTTPException: 认证失败时抛出 401 或 403 错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an admin",
        )
    
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前认证的用户（无需管理员权限）
    
    Args:
        credentials: Bearer 令牌凭证
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user

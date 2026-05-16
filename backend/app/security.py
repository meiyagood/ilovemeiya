"""
安全认证模块
处理密码哈希、验证和认证令牌
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError

from .config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对密码进行加密哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    
    Args:
        data: 要编码的数据字典
        expires_delta: 过期时间间隔，默认使用配置值
        
    Returns:
        JWT 令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    验证 JWT 令牌
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        解码后的令牌数据，如果无效返回 None
    """
    try:
        payload = decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except (ExpiredSignatureError, InvalidTokenError):
        return None

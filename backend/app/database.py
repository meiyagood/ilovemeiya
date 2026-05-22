import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 优先使用现有配置，如果没有则默认使用本地 SQLite 数据库
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.sqlite")

# 针对 SQLite 数据库的特殊连接配置
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

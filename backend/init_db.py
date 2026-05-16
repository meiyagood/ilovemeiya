#!/usr/bin/env python3
"""
数据库初始化脚本
创建数据库表并初始化默认数据
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from app.database import engine, Base
from app.models import User, Category, Article, Album, Photo, DailyLog
from app.security import hash_password


def init_database():
    """初始化数据库表"""
    print("🔨 正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")


def create_default_admin():
    """创建默认管理员用户"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # 检查是否已存在管理员
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("ℹ️  管理员用户已存在，跳过创建")
            return
        
        # 创建默认管理员
        admin = User(
            username="admin",
            email="admin@zaoanmeiya.com",
            hashed_password=hash_password("change-me"),  # ⚠️ 请立即修改此密码！
            full_name="Une vie pensée",
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        print("✅ 默认管理员用户创建成功")
        print("⚠️  默认用户名: admin")
        print("⚠️  默认密码: change-me")
        print("⚠️  请立即修改管理员密码！")
    except Exception as e:
        db.rollback()
        print(f"❌ 创建管理员失败: {e}")
    finally:
        db.close()


def create_sample_categories():
    """创建示例分类"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # 检查是否已存在分类
        if db.query(Category).count() > 0:
            print("ℹ️  分类已存在，跳过创建")
            return
        
        categories = [
            Category(
                name_fr="哲学随想",
                name_cn="哲学随想",
                slug="philosophy",
                description="关于生活、思考和人生的哲学性文章",
                icon="💭",
                color="#2C3E50",
                order=1,
            ),
            Category(
                name_fr="摄影展示",
                name_cn="摄影展示",
                slug="photography",
                description="个人摄影作品展示",
                icon="📷",
                color="#34495E",
                order=2,
            ),
            Category(
                name_fr="旅行记录",
                name_cn="旅行记录",
                slug="travel",
                description="旅行途中的所见所思",
                icon="✈️",
                color="#7F8C8D",
                order=3,
            ),
            Category(
                name_fr="日常碎片",
                name_cn="日常碎片",
                slug="daily",
                description="日常生活中的思考片段",
                icon="📝",
                color="#95A5A6",
                order=4,
            ),
        ]
        
        for cat in categories:
            db.add(cat)
        
        db.commit()
        print("✅ 示例分类创建成功")
    except Exception as e:
        db.rollback()
        print(f"❌ 创建分类失败: {e}")
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 50)
    print("🚀 Une vie pensée CMS - 数据库初始化")
    print("=" * 50)
    
    try:
        init_database()
        create_default_admin()
        create_sample_categories()
        
        print("\n" + "=" * 50)
        print("✅ 初始化完成！")
        print("=" * 50)
        print("\n接下来：")
        print("1. 修改管理员密码（用户名: admin）")
        print("2. 运行应用: uvicorn app.main:app --reload")
        print("3. 访问 API 文档: http://localhost:8000/docs")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

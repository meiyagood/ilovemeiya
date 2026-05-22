"""
migrate.py — 一次性数据库迁移脚本
在服务器上执行：python3 migrate.py

作用：为现有 vibe.db 追加新字段，不删除任何现有数据。
字段已存在时静默跳过，安全幂等。
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "vibe.db")


def add_column(cursor, table: str, column: str, col_type: str, default: str = "''"):
    """尝试为表添加新列，字段已存在时静默跳过。"""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}")
        print(f"  ✅ {table}.{column} 添加成功")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"  ⏭  {table}.{column} 已存在，跳过")
        else:
            raise


def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在：{DB_PATH}")
        return

    print(f"🔗 连接数据库：{DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("\n📋 迁移 daily_logs 表...")
    add_column(cur, "daily_logs", "category", "VARCHAR(50)",  default="''")

    # 确保 quotes 表字段完整（防止旧版本缺字段）
    print("\n📋 迁移 quotes 表...")
    add_column(cur, "quotes", "source",     "VARCHAR(200)", default="''")
    add_column(cur, "quotes", "is_current", "BOOLEAN",      default="0")

    conn.commit()
    conn.close()
    print("\n🎉 迁移完成，数据库已更新。")


if __name__ == "__main__":
    main()

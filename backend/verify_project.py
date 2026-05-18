#!/usr/bin/env python3
"""
项目结构验证脚本
检查所有必要的文件和目录是否正确创建
"""

import os
import sys
from pathlib import Path

def check_project_structure():
    """检查项目结构"""
    backend_dir = Path(__file__).resolve().parent
    
    print("\n" + "=" * 60)
    print("🔍 Une vie pensée 后端项目结构检查")
    print("=" * 60 + "\n")
    
    required_files = {
        "app/__init__.py": "应用包初始化",
        "app/config.py": "配置管理模块",
        "app/database.py": "数据库连接配置",
        "app/models.py": "SQLAlchemy 数据库模型",
        "app/schemas.py": "Pydantic 验证模型",
        "app/security.py": "密码和认证安全模块",
        "app/auth.py": "认证和授权逻辑",
        "app/main.py": "FastAPI 应用入口",
        "app/routes/__init__.py": "路由包初始化",
        "app/routes/public.py": "公开 API 路由",
        "app/routes/admin.py": "管理员 API 路由",
        "app/routes/articles.py": "文章 API 路由",
        "app/routes/albums.py": "相册 API 路由",
        "app/routes/daily_logs.py": "日志 API 路由",
        "app/routes/categories.py": "分类 API 路由",
        "requirements.txt": "Python 依赖列表",
        "init_db.py": "数据库初始化脚本",
        "README.md": "项目文档",
    }
    
    missing_files = []
    created_files = []
    
    for filepath, description in required_files.items():
        full_path = backend_dir / filepath
        status = "✅" if full_path.exists() else "❌"
        print(f"{status} {filepath:<35} - {description}")
        
        if full_path.exists():
            created_files.append(filepath)
        else:
            missing_files.append(filepath)
    
    print("\n" + "=" * 60)
    print(f"✅ 已创建文件: {len(created_files)}/{len(required_files)}")
    print("=" * 60)
    
    if missing_files:
        print(f"\n⚠️  缺失文件:")
        for f in missing_files:
            print(f"   - {f}")
        return False
    else:
        print("\n✅ 所有必要文件已正确创建！")
        return True


def check_python_syntax():
    """检查 Python 文件的语法"""
    print("\n" + "=" * 60)
    print("🐍 检查 Python 语法")
    print("=" * 60 + "\n")
    
    backend_dir = Path(__file__).resolve().parent
    app_dir = backend_dir / "app"
    
    python_files = list(app_dir.glob("**/*.py"))
    errors = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, str(py_file), 'exec')
            print(f"✅ {py_file.relative_to(backend_dir)}")
        except SyntaxError as e:
            print(f"❌ {py_file.relative_to(backend_dir)}: {e}")
            errors.append((py_file, e))
    
    if errors:
        print(f"\n⚠️  发现 {len(errors)} 个语法错误")
        return False
    else:
        print("\n✅ 所有 Python 文件语法正确！")
        return True


def print_quick_start():
    """打印快速开始指南"""
    print("\n" + "=" * 60)
    print("🚀 快速开始")
    print("=" * 60 + "\n")
    
    steps = [
        ("1. 创建虚拟环境", "python3 -m venv venv"),
        ("2. 激活虚拟环境 (Linux/Mac)", "source venv/bin/activate"),
        ("2. 激活虚拟环境 (Windows)", "venv\\Scripts\\activate"),
        ("3. 安装依赖", "pip install -r requirements.txt"),
        ("4. 初始化数据库", "python init_db.py"),
        ("5. 启动开发服务器", "uvicorn app.main:app --reload"),
        ("6. 访问 API 文档", "http://localhost:8000/docs"),
    ]
    
    for description, command in steps:
        print(f"  {description}")
        print(f"  $ {command}\n")


def main():
    """主函数"""
    structure_ok = check_project_structure()
    syntax_ok = check_python_syntax()
    
    print_quick_start()
    
    print("=" * 60)
    print("📊 项目状态总结")
    print("=" * 60)
    print(f"✅ 项目结构: {'完整' if structure_ok else '不完整'}")
    print(f"✅ 代码质量: {'正常' if syntax_ok else '有问题'}")
    print("\n✨ 项目已准备就绪，可以开始开发了！\n")
    
    return 0 if (structure_ok and syntax_ok) else 1


if __name__ == "__main__":
    sys.exit(main())

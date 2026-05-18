# 🌿 Une vie pensée - 项目后端 API

一个融合了个人摄影展示与哲学思考的 minimal 风格网站的 Python FastAPI 后端系统。

**现场网站**: https://www.zaoanmeiya.com/

## 📋 项目概述

"Une vie pensée" 意为"一个思考的人生"。该项目提供了一个现代化的 CMS 后端系统，支持：

- 📝 **文章管理**：哲学随想和长文章（支持 Markdown）
- 📷 **摄影相册**：组织和展示摄影作品  
- 🎯 **每日日志**：记录碎片化的思考和灵感
- 🏷️ **分类系统**：灵活的内容分类和组织
- 🔐 **认证管理**：安全的管理员认证和权限控制

## 🏗️ 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py              # 配置管理（环境变量、常量）
│   ├── database.py            # 数据库连接和会话管理
│   ├── models.py              # SQLAlchemy ORM 模型
│   ├── schemas.py             # Pydantic 验证和序列化模型
│   ├── security.py            # 密码哈希和 JWT 认证
│   ├── auth.py                # 认证逻辑和依赖
│   ├── main.py                # FastAPI 应用入口
│   ├── routes/                # API 路由模块
│   │   ├── __init__.py
│   │   ├── public.py          # 公开 API（无需认证）
│   │   ├── admin.py           # 管理员 API（文件上传等）
│   │   ├── articles.py        # 文章 CRUD API
│   │   ├── albums.py          # 相册和照片 CRUD API
│   │   ├── daily_logs.py      # 日志 CRUD API
│   │   └── categories.py      # 分类 CRUD API
│   ├── static/                # 静态文件
│   └── templates/             # HTML 模板（可选）
├── uploads/                   # 用户上传的文件
├── data.db                    # SQLite 数据库文件
├── requirements.txt           # Python 依赖
├── init_db.py                 # 数据库初始化脚本
└── README.md                  # 项目文档
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # 在 Windows 上: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 创建数据库表和默认数据
python init_db.py
```

输出示例：
```
==================================================
🚀 Une vie pensée CMS - 数据库初始化
==================================================
🔨 正在创建数据库表...
✅ 数据库表创建成功
✅ 默认管理员用户创建成功
⚠️  默认用户名: admin
⚠️  默认密码: change-me
✅ 示例分类创建成功

==================================================
✅ 初始化完成！
==================================================
```

### 3. 启动开发服务器

```bash
# 方式一：直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式二：使用 Python 模块
python -m uvicorn app.main:app --reload

# 方式三：使用 main.py 直接运行
python app/main.py
```

服务器将在 `http://localhost:8000` 启动

### 4. 访问 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API 文档

### 认证方式

**HTTP Basic Auth**（用于传统表单登录）：
```bash
curl -u admin:change-me http://localhost:8000/api/admin/info
```

**JWT Bearer Token**（可选升级）：
```bash
Authorization: Bearer <token>
```

### 公开 API（无需认证）

#### 文章 API
- `GET /api/public/articles` - 获取已发布文章列表
- `GET /api/public/articles/{slug}` - 获取文章详情
- `GET /api/public/articles/featured` - 获取精选文章

#### 相册 API
- `GET /api/public/albums` - 获取相册列表
- `GET /api/public/albums/{album_id}` - 获取相册及照片

#### 日志 API
- `GET /api/public/daily-logs` - 获取日常日志列表
- `GET /api/public/daily-logs/latest` - 获取最新日志

#### 分类 API
- `GET /api/public/categories` - 获取所有分类

### 管理员 API（需要认证）

#### 文件上传
```bash
POST /api/admin/upload
- 支持格式: .jpg, .jpeg, .png, .gif, .webp
- 最大大小: 10MB
```

#### 文章管理
```bash
POST   /api/articles          # 创建文章
PUT    /api/articles/{id}     # 更新文章  
DELETE /api/articles/{id}     # 删除文章
GET    /api/articles/{id}     # 获取文章详情
```

#### 相册管理
```bash
POST   /api/albums            # 创建相册
PUT    /api/albums/{id}       # 更新相册
DELETE /api/albums/{id}       # 删除相册
POST   /api/albums/{id}/photos     # 添加照片
PUT    /api/albums/photos/{id}     # 更新照片
DELETE /api/albums/photos/{id}     # 删除照片
```

#### 日志管理
```bash
POST   /api/daily-logs        # 创建日志
PUT    /api/daily-logs/{id}   # 更新日志
DELETE /api/daily-logs/{id}   # 删除日志
```

#### 分类管理
```bash
POST   /api/categories        # 创建分类
PUT    /api/categories/{id}   # 更新分类
DELETE /api/categories/{id}   # 删除分类
```

## 🗄️ 数据库模型

### User（用户）
```python
- id: int (主键)
- username: str (唯一)
- email: str (唯一)
- hashed_password: str
- full_name: str
- bio: str
- is_active: bool
- is_admin: bool
- created_at: datetime
```

### Category（分类）
```python
- id: int
- name_fr: str
- name_cn: str
- slug: str (唯一)
- description: str
- icon: str
- color: str
- layout_type: str
- order: int
```

### Article（文章）
```python
- id: int
- title: str
- slug: str (唯一)
- content: str (Markdown)
- summary: str
- category_id: int (外键)
- cover_url: str
- tags: str (逗号分隔)
- is_published: bool
- featured: bool
- view_count: int
- created_at: datetime
- published_at: datetime (可选)
```

### Album（相册）
```python
- id: int
- title_fr: str
- title_cn: str
- description_fr: str
- description_cn: str
- category_id: int (外键)
- cover_url: str
- is_published: bool
- photo_count: int
- created_at: datetime
```

### Photo（照片）
```python
- id: int
- album_id: int (外键)
- image_url: str
- thumbnail_url: str
- title: str
- description: str
- photographer_note: str
- taken_at: datetime (可选)
- location: str
- order: int
- created_at: datetime
```

### DailyLog（日常日志）
```python
- id: int
- title: str
- content: str
- author: str
- mood: str
- is_published: bool
- posted_at: datetime
- created_at: datetime
```

## 🔐 安全性

### 密码安全
- 使用 **bcrypt** 进行密码哈希
- 支持时序安全的密码比较（防止时序攻击）

### 认证
- HTTP Basic Auth：用于管理员登录
- JWT Token：可选升级方案

### CORS
可通过 `CORS_ORIGINS` 环境变量配置允许的源：
```bash
CORS_ORIGINS="http://localhost:3000,https://www.zaoanmeiya.com"
```

## ⚙️ 环境配置

创建 `.env` 文件（可选）：

```bash
# 数据库
DATABASE_PATH=/path/to/data.db

# 认证
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# CORS
CORS_ORIGINS=http://localhost:3000,https://www.zaoanmeiya.com

# JWT（如需启用）
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# 环境
ENV=development
LOG_LEVEL=INFO
```

## 📦 生产部署

### 使用 Gunicorn

```bash
pip install gunicorn

# 启动服务
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY init_db.py .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建镜像
docker build -t une-vie-pensee-api .

# 运行容器
docker run -p 8000:8000 -e ADMIN_PASSWORD=secure-password une-vie-pensee-api
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name www.zaoanmeiya.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🧪 开发和测试

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试
pytest tests/ -v
```

### 代码格式化

```bash
# 安装工具
pip install black flake8 mypy

# 格式化代码
black app/

# 代码检查
flake8 app/
mypy app/
```

## 🐛 常见问题

**Q: 如何修改管理员密码？**
```python
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

db = SessionLocal()
user = db.query(User).filter(User.username == "admin").first()
user.hashed_password = hash_password("new-password")
db.commit()
```

**Q: 如何添加新的管理员用户？**
```python
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

db = SessionLocal()
new_admin = User(
    username="newadmin",
    email="newadmin@example.com",
    hashed_password=hash_password("password"),
    is_admin=True
)
db.add(new_admin)
db.commit()
```

**Q: 如何导出数据库？**
```bash
# SQLite 可直接复制 data.db 文件
cp data.db data.db.backup
```

## 📞 技术支持

- GitHub Issues: [提交问题]
- 电子邮件: [contact@zaoanmeiya.com]

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**最后更新**: 2026年5月16日  
**版本**: 1.0.0  
**作者**: Une vie pensée Team

Use HTTP Basic credentials from `ADMIN_USERNAME` and `ADMIN_PASSWORD`.

## API Summary

- `GET /api/health`
- `GET /api/articles`
- `POST /api/articles` (admin)
- `PUT /api/articles/{id}` (admin)
- `DELETE /api/articles/{id}` (admin)
- `GET /api/albums`
- `POST /api/albums` (admin)
- `PUT /api/albums/{id}` (admin)
- `DELETE /api/albums/{id}` (admin)
- `GET /api/albums/{album_id}/photos`
- `POST /api/albums/{album_id}/photos` (admin)
- `PUT /api/photos/{id}` (admin)
- `DELETE /api/photos/{id}` (admin)
- `POST /api/uploads` (admin)

## Notes

- Read endpoints are public by default.
- Write endpoints require admin auth.
- Uploaded files are served from `/uploads/<filename>`.

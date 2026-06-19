# Jarvis — 暑期个人学习助手平台

一个基于 Django 5.0 的个人学习管理平台，集成内容抓取、AI 对话、目标追踪、身心健康记录等功能。

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Django 5.0 |
| 前端 | HTMX + Django Templates |
| 数据库 | PostgreSQL 15 (PgVector) |
| 缓存/队列 | Redis 7 + Celery |
| ASGI 服务器 | Daphne |
| LLM | DeepSeek API / OpenAI API |
| 容器化 | Docker 29 + docker-compose |

## 项目结构

```
D:\Jarvis project\
├── config/                 # Django 项目配置
│   ├── settings/
│   │   ├── base.py         # 基础配置 (PostgreSQL, Celery, CORS)
│   │   ├── dev.py          # 开发环境配置 (DEBUG=True)
│   │   └── prod.py         # 生产环境配置 (安全加固)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                   # 核心业务 App
│   ├── accounts/           # 用户认证与偏好 (User, UserPreference, etc.)
│   ├── content/            # 内容抓取与推荐 (Creator, ProcessedContent, etc.)
│   ├── goals/              # 目标与进度追踪 (Goal, GoalProgress)
│   ├── wellness/           # 身心健康跟踪 (WellnessRecord)
│   ├── trajectory/         # 成长轨迹记录 (TrajectoryEvent)
│   ├── chat/               # AI 对话 (Conversation, Message)
│   ├── dashboard/          # Dashboard 首页 (DashboardLayout)
│   └── userprofile/        # 用户主页 (UserProfile)
├── infra/                  # 基础设施 App
│   ├── eventbus/           # 事件总线 (Event)
│   └── llm/                # LLM 服务 (LLMCallLog)
├── docker-compose.yml      # 容器编排 (PostgreSQL + Redis + Web + Celery)
├── Dockerfile              # Python 3.12 应用镜像
├── requirements.txt        # Python 依赖
└── manage.py               # Django 管理入口
```

## 快速开始

### 前置要求

- Python 3.12+
- Docker 29+ (PostgreSQL + Redis)

### 本地开发

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 安装依赖
.venv\Scripts\pip install -r requirements.txt

# 3. 启动 PostgreSQL 和 Redis
docker compose up -d db redis

# 4. 执行数据库迁移
.venv\Scripts\python manage.py migrate

# 5. 运行开发服务器
.venv\Scripts\python manage.py runserver
```

### Docker 全栈启动

```bash
docker compose up --build
```

## 环境变量

复制 `.env.example` 为 `.env` 并根据需要修改：

```env
SECRET_KEY=your-secret-key-here
DB_NAME=jarvis
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:8000
```

## 数据模型总览 (18 个模型)

| App | 模型 | 说明 |
|-----|------|------|
| accounts | User | 自定义用户模型 (继承 AbstractUser) |
| accounts | UserPreference | 用户偏好 (学习标签、每日时长) |
| accounts | FavoriteCreator | 收藏的 UP 主 |
| accounts | MonitorTopic | AI 监控关键词 |
| accounts | UserSettings | 推送/隐私设置 |
| content | Creator | 内容创作者 |
| content | RawContent | 原始抓取内容 |
| content | ProcessedContent | 处理后标准内容 (含生命周期管理) |
| content | ContentEmbedding | 768 维向量嵌入 |
| goals | Goal | 学习目标 |
| goals | GoalProgress | 目标进度记录 |
| wellness | WellnessRecord | 身心健康日记录 |
| trajectory | TrajectoryEvent | 成长轨迹事件 |
| chat | Conversation | AI 对话会话 |
| chat | Message | 对话消息 |
| dashboard | DashboardLayout | 首页布局配置 |
| eventbus | Event | 事件总线记录 |
| llm | LLMCallLog | LLM 调用日志 |

## 开发中...

本项目处于 Phase 1 骨架搭建阶段。后续将逐步添加：
- Phase 2: 用户认证系统 (django-allauth)
- Phase 3: 内容抓取管线 (Celery)
- Phase 4: AI 对话集成 (DeepSeek API)
- Phase 5: Dashboard 可视化

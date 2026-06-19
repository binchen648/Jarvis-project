# Summer Project Phase 1 — 项目骨架搭建

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 搭建个人学习助手平台的 Django 项目骨架，包含完整的目录结构、配置拆分、容器化环境和基础模型注册。

**Architecture:** Django 5.0 + HTMX 单体应用，settings 拆分为 base/dev/prod 三环境，8 个 App + 2 个基础设施独立目录，PostgreSQL 15 + Redis 7 容器化，Celery 异步任务队列。

**Tech Stack:** Python 3.12, Django 5.0, PostgreSQL 15, Redis 7, Celery, Daphne, Docker Compose

**项目路径:** `D:\Jarvis project`

---

### Task 1: 初始化 Django 项目与目录结构

**Files:**
- Create: `D:\Jarvis project\manage.py`
- Create: `D:\Jarvis project\requirements.txt`
- Create: `D:\Jarvis project\.env.example`
- Create: `D:\Jarvis project\.gitignore`
- Create: `D:\Jarvis project\README.md`
- Create: `D:\Jarvis project\config\__init__.py`
- Create: `D:\Jarvis project\config\settings\__init__.py`
- Create: `D:\Jarvis project\config\settings\base.py`
- Create: `D:\Jarvis project\config\settings\dev.py`
- Create: `D:\Jarvis project\config\settings\prod.py`
- Create: `D:\Jarvis project\config\urls.py`
- Create: `D:\Jarvis project\config\wsgi.py`
- Create: `D:\Jarvis project\config\asgi.py`

**Step 1: 创建 Python 虚拟环境**

```powershell
Set-Location -LiteralPath "D:\Jarvis project"
python -m venv .venv
```

Expected: `.venv/` 目录创建成功

**Step 2: 创建项目目录结构**

```powershell
New-Item -ItemType Directory -Path "D:\Jarvis project\config\settings" -Force
```

**Step 3: 创建 manage.py**

使用 Django 5.0 标准 manage.py 模板，设置默认 settings 模块为 `config.settings.dev`。

**Step 4: 创建 config/settings/base.py**

配置：
- SECRET_KEY 从环境变量读取
- DEBUG = False
- ALLOWED_HOSTS = []
- INSTALLED_APPS 包含基础 django 应用
- DATABASES 使用 PostgreSQL（配置从环境变量读取，含 PgVector 扩展）
- 国际化：zh-cn 时区 Asia/Shanghai
- STATIC_ROOT / MEDIA_ROOT 配置
- Celery 配置预留
- CORS 配置预留

**Step 5: 创建 config/settings/dev.py**

继承 base：
- DEBUG = True
- ALLOWED_HOSTS = ["*"]
- 数据库使用 docker-compose 中的 PostgreSQL
- CORS 开发模式允许所有来源

**Step 6: 创建 config/settings/prod.py**

继承 base：
- DEBUG = False
- 安全配置（SECURE_SSL_REDIRECT 等）
- 生产数据库配置

**Step 7: 创建 config/urls.py / wsgi.py / asgi.py**

Django 5.0 标准路由和 ASGI/WSGI 入口。

**Step 8: 创建 requirements.txt**

```text
django>=5.0,<5.1
psycopg2-binary>=2.9
daphne>=4.0
channels>=4.0
celery>=5.3
redis>=5.0
python-decouple>=3.8
django-allauth>=0.60
django-cors-headers>=4.0
```

**Step 9: 安装依赖**

```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

Expected: 所有包安装成功，无报错

**Step 10: 创建 .env.example**

```env
SECRET_KEY=django-insecure-...
DB_NAME=jarvis
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

**Step 11: 创建 .gitignore**

Python/Django 标准 gitignore（含 .env、.venv/、__pycache__、*.pyc、media/、static/ 等）。

**Step 12: 验证**

Run: `.\.venv\Scripts\python manage.py runserver --help`
Expected: Django 5.0 帮助信息正常显示

---

### Task 2: 创建 8 个核心 App + 2 个基础设施

**Files:**
- Create: `D:\Jarvis project\apps\__init__.py`
- Create: `D:\Jarvis project\apps\accounts\__init__.py`
- Create: `D:\Jarvis project\apps\accounts\models.py`
- Create: `D:\Jarvis project\apps\accounts\views.py`
- Create: `D:\Jarvis project\apps\accounts\urls.py`
- Create: `D:\Jarvis project\apps\accounts\admin.py`
- Create: `D:\Jarvis project\apps\accounts\apps.py`
- Create: `D:\Jarvis project\apps\accounts\templates\accounts\base.html`
- Create: `D:\Jarvis project\apps\content\` (同上结构)
- Create: `D:\Jarvis project\apps\goals\` (同上结构)
- Create: `D:\Jarvis project\apps\wellness\` (同上结构)
- Create: `D:\Jarvis project\apps\trajectory\` (同上结构)
- Create: `D:\Jarvis project\apps\chat\` (同上结构)
- Create: `D:\Jarvis project\apps\dashboard\` (同上结构)
- Create: `D:\Jarvis project\apps\userprofile\` (同上结构)
- Create: `D:\Jarvis project\infra\__init__.py`
- Create: `D:\Jarvis project\infra\eventbus\__init__.py`
- Create: `D:\Jarvis project\infra\eventbus\engine.py`
- Create: `D:\Jarvis project\infra\llm\__init__.py`
- Create: `D:\Jarvis project\infra\llm\service.py`

**Step 1: 创建 apps 和 infra 目录**

```powershell
$apps = @("accounts","content","goals","wellness","trajectory","chat","dashboard","userprofile")
foreach ($app in $apps) {
    New-Item -ItemType Directory -Path "D:\Jarvis project\apps\$app\templates\$app" -Force
    New-Item -ItemType Directory -Path "D:\Jarvis project\apps\$app\migrations" -Force
}
New-Item -ItemType Directory -Path "D:\Jarvis project\infra\eventbus" -Force
New-Item -ItemType Directory -Path "D:\Jarvis project\infra\llm" -Force
```

**Step 2: 每个 App 创建标准骨架文件**

每个 App 包含：
- `__init__.py` — 空文件
- `apps.py` — AppConfig 定义，设置 verbose_name（中文）
- `models.py` — 写入架构文档中的模型定义（仅 accounts 和 userprofile 有模型，其他 App 留占位）
- `views.py` — 基础 view（返回 HTMX 模板）
- `urls.py` — 空 urlpatterns
- `admin.py` — 注册模型
- `templates/<app>/` — 基础模板

**Step 3: 基础设施 stub**

- `infra/eventbus/engine.py` — EventBus 类占位，含注释说明接口设计
- `infra/llm/service.py` — LLMService 类占位，含注释说明接口设计

**Step 4: 注册所有 App 到 settings**

在 `config/settings/base.py` 的 INSTALLED_APPS 中添加所有 app 路径：
```python
INSTALLED_APPS = [
    ...
    'apps.accounts',
    'apps.content',
    'apps.goals',
    'apps.wellness',
    'apps.trajectory',
    'apps.chat',
    'apps.dashboard',
    'apps.userprofile',
    'infra.eventbus',
    'infra.llm',
]
```

**Step 5: 编写 accounts 和 userprofile 的初始模型**

根据架构文档完整实现：

accounts 模型：
- `User` — 继承 `AbstractUser`（django-allauth 兼容）
- `UserPreference` — 学习领域标签、每日学习时长、活跃时间段
- `FavoriteCreator` — name, platform, profile_url, user (FK)
- `MonitorTopic` — keyword, push_frequency, user (FK)
- `UserSettings` — push_enabled, privacy, user (OneToOne)

userprofile 模型：
- `UserInterestProfile` — user (OneToOne), interests_embedding (VectorField 768d), preferred_categories (ArrayField), preferred_content_types (ArrayField), active_learning_skills (ArrayField), preferred_time_slots, avg_session_duration, disliked_categories, blocked_creators

**Step 6: 运行 `python manage.py check` 验证配置**

Run: `.\.venv\Scripts\python manage.py check`
Expected: 零错误

**Step 7: 创建初始 migration**

Run: `.\.venv\Scripts\python manage.py makemigrations accounts userprofile`
Run: `.\.venv\Scripts\python manage.py migrate`
Expected: 迁移成功，无错误

---

### Task 3: 容器化环境配置

**Files:**
- Create: `D:\Jarvis project\docker-compose.yml`
- Create: `D:\Jarvis project\Dockerfile`
- Create: `D:\Jarvis project\.dockerignore`

**Step 1: 创建 docker-compose.yml**

```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: jarvis
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A config worker -l info
    depends_on: [db, redis]
    env_file: .env

volumes:
  pgdata:
```

**Step 2: 创建 Dockerfile**

基于 python:3.12-slim 的多阶段构建。

**Step 3: 创建 .dockerignore**

**Step 4: 创建 Celery 配置**

`config/celery.py` — Celery 应用实例，自动发现所有 App 的 tasks.py。
`config/__init__.py` — 确保 Celery 应用在 Django 启动时加载。

**Step 5: 启动容器验证**

Run: `docker compose up -d db redis`
Expected: PostgreSQL 5432 端口监听，Redis 6379 端口监听

验证连接：
```powershell
docker compose ps
docker compose logs db --tail 10
```

---

### Task 4: 初始化数据库并验证

**Step 1: 创建 .env 文件**

从 .env.example 复制到 .env，生成随机 SECRET_KEY：
```powershell
Copy-Item -Path "D:\Jarvis project\.env.example" -Destination "D:\Jarvis project\.env"
```

**Step 2: 运行 `python manage.py check`**

Run: `.\.venv\Scripts\python manage.py check`
Expected: 零错误、零警告

**Step 3: 运行 migration**

Run: `.\.venv\Scripts\python manage.py migrate`
Expected: 所有表创建成功，无错误

**Step 4: 创建超级用户**

Run: `.\.venv\Scripts\python manage.py createsuperuser`
留空邮箱或输入 binchen0648@gmail.com

**Step 5: 验证 runserver**

Run: `.\.venv\Scripts\python manage.py runserver`
Expected: 开发服务器在 8000 端口启动

**Step 6: 验证 admin 页面**

浏览器访问 `http://localhost:8000/admin/`
Expected: Django admin 页面正常加载，所有已注册模型可见

---

### Task 5: 验证与审查

**Files:**
- Modify: `D:\Jarvis project\README.md`

**Step 1: LSP 诊断**

Run LSP diagnostics on all changed files。
Expected: 零错误、零警告

**Step 2: 运行自动审查**

触发 `review-work` 5 Agent 全面审查：
- Goal Verification: Phase 1 目标是否全部达成
- QA Execution: 实际启动验证
- Code Quality: 代码结构与规范
- Security: 配置安全性
- Context Mining: 是否遗漏上下文

**Step 3: 更新 README.md**

写入完整的 Phase 1 项目说明：
- 项目简介
- 技术栈
- 快速启动指南
- 目录结构说明
- 开发环境配置步骤

---

### 执行顺序与依赖关系

```
Task 1 (初始化项目)
  └── Task 2 (App 骨架)
       └── Task 3 (容器化)
            └── Task 4 (数据库验证)
                 └── Task 5 (审查文档)
```

每个 Task 完成后自动触发代码审查，审查通过才进入下一 Task。

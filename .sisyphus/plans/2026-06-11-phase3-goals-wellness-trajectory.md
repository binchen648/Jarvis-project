# Phase 3 — goals / wellness / trajectory App 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成暑期学习助手平台 Phase3 剩余 3 个 App（goals / wellness / trajectory）的完整交付，包括数据模型、视图层、HTMX 模板、Celery 任务、测试覆盖，并通过生产就绪审查。

**设计哲学（来自用户确认）:** 陪伴型助手，人性优先。deadline 软提醒、记录宽松、建议可静默、节点需用户确认。所有提醒类 Celery 任务采用「存库待拉取」模式，不主动推送。

**技术栈:** Django 5.0 + HTMX 2.0 + PostgreSQL 15 + Celery + Redis + PgVector

**参考实现:** `apps/content/` (models.py / views.py / urls.py / tasks.py / tests.py 模式)

---

## Task 1: goals — Goal 模型升级

**文件:**
- 修改: `apps/goals/models.py` — 给 Goal 添加字段
- 新建: `apps/goals/migrations/0002_goal_type_fields.py`
- 验证: `python manage.py check`

**改动内容:**
```python
# 在 Goal 模型中新增字段
goal_type = models.CharField(
    max_length=20,
    choices=[("duration","时长型"),("count","计数型"),("completion","完成型"),("habit","习惯型"),("custom","自定义")],
    default="custom", verbose_name="目标类型"
)
target_value = models.FloatField(null=True, blank=True, verbose_name="目标值")
target_unit = models.CharField(max_length=20, blank=True, verbose_name="目标单位")
category = models.CharField(
    max_length=10,
    choices=[("daily","每日"),("weekly","每周"),("custom","自定义周期")],
    default="daily", verbose_name="周期类别"
)
is_recurring = models.BooleanField(default=False, verbose_name="是否循环")
```

**人性化原则:** deadline 字段保留但设为可空，Celery 任务仅做温和提醒，不过期标记。

---

## Task 2: goals — GoalSession 模型新建

**文件:**
- 修改: `apps/goals/models.py` — 新增 GoalSession
- 新建: `apps/goals/migrations/0003_goalsession.py`

**模型定义:**
```python
class GoalSession(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=CASCADE, related_name="goal_sessions")
    goal = models.ForeignKey(Goal, on_delete=SET_NULL, null=True, blank=True, verbose_name="关联目标")
    date = models.DateField(auto_now_add=True, verbose_name="记录日期")
    duration_minutes = models.IntegerField(verbose_name="学习时长(分钟)")
    note = models.TextField(blank=True, verbose_name="备注")
    content_ref = models.ForeignKey("content.ProcessedContent", null=True, blank=True, on_delete=SET_NULL, verbose_name="关联内容")
```

**人性化原则:** goal 可空，允许用户不绑定目标自由记录。

---

## Task 3: goals — 视图层

**文件:**
- 新建: `apps/goals/views.py` — 5 个视图函数

**视图清单:**

| 视图 | URL | 方法 | 说明 |
|------|-----|------|------|
| `goal_list` | `/goals/` | GET | 列出用户所有 Goal，含进度概览 |
| `goal_create` | `/goals/create/` | GET+POST | Django Form 创建 Goal |
| `goal_detail` | `/goals/<id>/` | GET | 目标详情 + 关联的 GoalSession 列表 |
| `goal_edit` | `/goals/<id>/edit/` | GET+POST | 编辑目标 |
| `update_status` | `/goals/<id>/status/` | POST | HTMX 一键切换状态 |
| `log_session` | `/goals/session/log/` | GET+POST | 记录一条学习会话 |

**人性化原则:** `update_status` 让用户手动确认完成/放弃，系统不自动标记。

---

## Task 4: goals — URL 路由

**文件:**
- 新建: `apps/goals/urls.py`
- 修改: `config/urls.py` — 添加 `path('goals/', include('apps.goals.urls'))`

```python
app_name = "goals"
urlpatterns = [
    path("", views.goal_list, name="goal_list"),
    path("create/", views.goal_create, name="goal_create"),
    path("<int:pk>/", views.goal_detail, name="goal_detail"),
    path("<int:pk>/edit/", views.goal_edit, name="goal_edit"),
    path("<int:pk>/status/", views.update_status, name="update_status"),
    path("session/log/", views.log_session, name="log_session"),
]
```

---

## Task 5: goals — HTMX 模板

**文件:**
- 新建: `templates/goals/goal_list.html`
- 新建: `templates/goals/goal_detail.html`
- 新建: `templates/goals/goal_form.html`
- 新建: `templates/goals/goal_session_form.html`

**模式:** 继承 `base.html`，使用 content app 模板风格（卡片式列表、HTMX POST 交互）。

---

## Task 6: goals — Celery 任务

**文件:**
- 新建: `apps/goals/tasks.py`

**任务清单:**

```python
@shared_task(bind=True, time_limit=300, soft_time_limit=270, max_retries=3)
def check_goal_deadlines(self):
    """每日检查即将到期的目标，生成温和提醒。
    人性化原则：不过期标记，仅创建提醒记录，用户拉取查看。
    """

@shared_task(bind=True, time_limit=600, soft_time_limit=540, max_retries=3)
def aggregate_daily_sessions(self):
    """每日汇总用户学习时长，更新 GoalProgress。
    调度: 每天 00:30
    """
```

---

## Task 7: goals — 测试

**文件:**
- 修改: `apps/goals/tests.py`

**测试覆盖:**
- Goal 模型字段创建
- GoalSession 创建（含 goal 可空测试）
- 视图 GET 状态码 200（需 login）
- 视图 POST 创建/更新
- Celery 任务调用

---

## Task 8: wellness — HealthSuggestion 模型 & Admin

**文件:**
- 修改: `apps/wellness/models.py` — 新增 HealthSuggestion
- 修改: `apps/wellness/admin.py` — 注册 HealthSuggestion

```python
class HealthSuggestion(models.Model):
    user = ForeignKey("accounts.User", on_delete=CASCADE, related_name="health_suggestions")
    suggestion_type = CharField(
        max_length=20,
        choices=[("break","休息"),("eye","护眼"),("posture","坐姿"),("exercise","运动"),("sleep","睡眠")],
        verbose_name="建议类型"
    )
    content = TextField(verbose_name="建议内容")
    trigger_reason = CharField(max_length=100, verbose_name="触发原因")
    is_read = BooleanField(default=False, verbose_name="已读")
    created_at = DateTimeField(auto_now_add=True)
```

---

## Task 9: wellness — 视图、URL、模板

**文件:**
- 修改: `apps/wellness/views.py`
- 新建: `apps/wellness/urls.py`
- 新建: `templates/wellness/suggestion_list.html`
- 新建: `templates/wellness/record_form.html`
- 修改: `config/urls.py` — 添加 wellness/ 路由

**视图:**
| 视图 | URL | 说明 |
|------|-----|------|
| `suggestion_list` | `/wellness/suggestions/` | 列出未读建议，HTMX 局部刷新 |
| `dismiss_suggestion` | `/wellness/suggestions/<id>/dismiss/` | POST 标记已读 |
| `record_create` | `/wellness/record/` | 记录今日心情/睡眠/运动 |

---

## Task 10: wellness — Celery 任务 & 测试

**文件:**
- 新建: `apps/wellness/tasks.py`
- 修改: `apps/wellness/tests.py`

```python
@shared_task(bind=True, time_limit=300, soft_time_limit=270, max_retries=3)
def generate_health_suggestions(self):
    """每 2 小时检查用户学习模式，生成健康建议。
    人性化原则：仅创建建议记录存库，用户拉取查看，不推送。
    规则：连续学习>120分钟→休息提醒；22:00后→睡眠提醒。
    """
```

---

## Task 11: trajectory — 4 个模型新建

**文件:**
- 修改: `apps/trajectory/models.py`

**模型清单:**
```python
class SkillNode(models.Model):
    """技能节点 — 预置图谱"""
    name = CharField(max_length=200, unique=True)
    category = CharField(max_length=50)
    difficulty = IntegerField(choices=[(1,"入门"),(2,"初级"),(3,"中级"),(4,"高级"),(5,"专家")])
    estimated_hours = IntegerField()
    prerequisites = ManyToManyField("self", symmetrical=False, blank=True)
    recommended_content = ManyToManyField("content.ProcessedContent", blank=True)
    learner_count = IntegerField(default=0)
    avg_completion_rate = FloatField(null=True, blank=True)

class UserLearningProgress(models.Model):
    """用户技能进度"""
    user = ForeignKey("accounts.User", on_delete=CASCADE, related_name="learning_progress")
    skill = ForeignKey(SkillNode, on_delete=CASCADE)
    status = CharField(max_length=20, choices=[("not_started","未开始"),("learning","学习中"),("completed","已完成"),("struggling","有困难")], default="not_started")

class LearningPath(models.Model):
    """个性化路径"""
    user = ForeignKey("accounts.User", on_delete=CASCADE, related_name="learning_paths")
    title = CharField(max_length=200)
    goal_description = TextField(blank=True)
    is_active = BooleanField(default=True)

class PathNode(models.Model):
    """路径节点"""
    path = ForeignKey(LearningPath, on_delete=CASCADE, related_name="nodes")
    skill = ForeignKey(SkillNode, null=True, on_delete=SET_NULL)
    order = IntegerField()
    status = CharField(max_length=20, choices=[("pending","待开始"),("in_progress","进行中"),("completed","已完成")], default="pending")
    estimated_minutes = IntegerField(default=0)
```

**人性化原则:** 节点完成需用户手动确认（`complete_node` POST 视图），系统不自动推进。

---

## Task 12: trajectory — 视图、URL、模板

**文件:**
- 修改: `apps/trajectory/views.py`
- 新建: `apps/trajectory/urls.py`
- 新建: `templates/trajectory/skill_graph.html`
- 新建: `templates/trajectory/path_list.html`
- 新建: `templates/trajectory/path_detail.html`
- 修改: `config/urls.py` — 添加 trajectory/ 路由

**视图:**
| 视图 | URL | 说明 |
|------|-----|------|
| `skill_graph` | `/trajectory/skills/` | 技能图谱浏览(按category分组) |
| `path_list` | `/trajectory/paths/` | 用户学习路径列表 |
| `path_detail` | `/trajectory/paths/<id>/` | 路径详细节点列表 |
| `complete_node` | `/trajectory/nodes/<id>/complete/` | POST 手动确认完成节点 |

---

## Task 13: trajectory — Celery 任务 & 测试

**文件:**
- 新建: `apps/trajectory/tasks.py`
- 修改: `apps/trajectory/tests.py`

```python
@shared_task(bind=True, time_limit=300, soft_time_limit=270, max_retries=3)
def update_skill_stats(self):
    """每日更新 SkillNode 的 learner_count / avg_completion_rate。"""

@shared_task(bind=True, time_limit=600, soft_time_limit=540, max_retries=3)
def check_path_progress(self):
    """每日检查路径进度，生成温和提示记录。"""
```

---

## Task 14: 跨 App 整合

**文件:**
- 修改: `config/urls.py` — 注册 3 个 App 路由
- 修改: `config/celery.py` — 注册新增 Celery Beat 定时任务

**Celery Beat 新增:**
```python
"check-goal-deadlines": {
    "task": "apps.goals.tasks.check_goal_deadlines",
    "schedule": crontab(hour=8, minute=0),  # daily 08:00
},
"aggregate-daily-sessions": {
    "task": "apps.goals.tasks.aggregate_daily_sessions",
    "schedule": crontab(hour=0, minute=30),  # daily 00:30
},
"generate-health-suggestions": {
    "task": "apps.wellness.tasks.generate_health_suggestions",
    "schedule": 7200.0,  # every 2 hours
},
"update-skill-stats": {
    "task": "apps.trajectory.tasks.update_skill_stats",
    "schedule": crontab(hour=3, minute=0),  # daily 03:00
},
"check-path-progress": {
    "task": "apps.trajectory.tasks.check_path_progress",
    "schedule": crontab(hour=8, minute=30),  # daily 08:30
},
```

---

## 执行策略

### 总原则
- **不自行编写代码** — 每 App 派发独立 `deep` category 子 Agent
- **并行执行** — goals / wellness / trajectory 三个 App 可并行
- **每个子 Agent prompt 必须包含**: TASK / EXPECTED OUTCOME / MUST DO / MUST NOT DO / CONTEXT（参考文件路径）

### App 内执行顺序（子 Agent 内部）
1. 模型 → migration
2. Admin 注册
3. 视图 + URL
4. 模板
5. Celery 任务
6. 测试

### 验证顺序（Step 5）
1. `lsp_diagnostics` 检查所有修改文件
2. `python manage.py check` 零错误
3. `python manage.py test apps.goals apps.wellness apps.trajectory --keepdb`
4. `review-work` 5 Agent 全面审查
5. Oracle 深度架构审查
6. 生产就绪 Checklist 逐项检查

---

## 文件改动总清单

### 修改文件
| 文件 | 变更 |
|------|------|
| `apps/goals/models.py` | Goal 新增 5 字段 + GoalSession 模型 |
| `apps/goals/admin.py` | 注册 GoalSession |
| `apps/goals/tests.py` | 全面测试 |
| `apps/wellness/models.py` | 新增 HealthSuggestion |
| `apps/wellness/admin.py` | 注册 HealthSuggestion |
| `apps/wellness/tests.py` | 全面测试 |
| `apps/trajectory/models.py` | 新增 4 模型 |
| `apps/trajectory/admin.py` | 注册 4 模型 |
| `apps/trajectory/tests.py` | 全面测试 |
| `config/urls.py` | 添加 3 个 App 路由 |
| `config/celery.py` | 添加 5 个 Beat 任务 |

### 新建文件
| 文件 | 归属 |
|------|------|
| `apps/goals/urls.py` | goals |
| `apps/goals/views.py` | goals |
| `apps/goals/tasks.py` | goals |
| `templates/goals/goal_list.html` | goals |
| `templates/goals/goal_detail.html` | goals |
| `templates/goals/goal_form.html` | goals |
| `templates/goals/goal_session_form.html` | goals |
| `apps/wellness/urls.py` | wellness |
| `apps/wellness/views.py` | wellness |
| `apps/wellness/tasks.py` | wellness |
| `templates/wellness/suggestion_list.html` | wellness |
| `templates/wellness/record_form.html` | wellness |
| `apps/trajectory/urls.py` | trajectory |
| `apps/trajectory/views.py` | trajectory |
| `apps/trajectory/tasks.py` | trajectory |
| `templates/trajectory/skill_graph.html` | trajectory |
| `templates/trajectory/path_list.html` | trajectory |
| `templates/trajectory/path_detail.html` | trajectory |

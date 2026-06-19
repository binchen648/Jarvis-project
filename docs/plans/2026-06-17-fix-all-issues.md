# Jarvis Dashboard + Agent V2 + Memory Timeline + AI Surface 修复计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 Jarvis 项目所有未修复问题：Dashboard 变量名 bug、Agent V2 双列布局、Memory Timeline 页面、AI Surface 完整实现。

**Architecture:** 4 个独立任务并行执行：
1. Dashboard bug: 1 行变量名修复
2. Agent V2: 重写 `templates/chat/conversation_detail.html` 为双列布局，新增 API 端点聚合右侧面板数据
3. Memory Timeline: 新建 `apps/memory/` app，复用 `TrajectoryEvent` 模型
4. AI Surface: 完善 `templates/base.html` 中 AI Surface 的 5 种类型 + Pulse 动画

**Tech Stack:** Django 5.0, HTMX, Tailwind CSS, SQLite (demo), Django Templates

---

## 任务分解

### 任务 1: Dashboard 变量名 Bug 修复

**Files:**
- Modify: `templates/dashboard/home.html:363`

**Steps:**
1. 将 `kpi_ai_confidence_pct` 替换为 `ai_confidence_pct`
2. 验证：`lsp_diagnostics` 检查 home.html

---

### 任务 2: Agent V2 双列布局

**Files:**
- Modify: `apps/chat/views.py` — 新增 `agent_state` 视图函数
- Create: `apps/chat/urls.py` 或修改现有 URL 配置 — 新增 `/chat/agent/<uuid>/` 路由
- Modify: `templates/chat/conversation_detail.html` — 重写为双列布局
- Modify: `apps/chat/consumers.py` — 确保 WebSocket 消息格式兼容双列布局

**Steps:**
1. 创建 `agent_state` 视图：聚合 conversation metadata、recent messages、tools used、memory hints
2. 新增 URL 路由
3. 重写模板为双列布局（左：对话流，右：Active State 面板）
4. 确保 HTMX 轮询或 WebSocket 更新右侧面板

---

### 任务 3: Memory Timeline 页面

**Files:**
- Create: `apps/memory/__init__.py`
- Create: `apps/memory/apps.py`
- Create: `apps/memory/models.py` — 无新模型，仅导出 `TrajectoryEvent`
- Create: `apps/memory/views.py` — `timeline_view` 和 `detail_view`
- Create: `apps/memory/urls.py`
- Create: `apps/memory/templates/memory/timeline.html`
- Create: `apps/memory/templates/memory/detail.html`
- Modify: `config/urls.py` — 注册 memory app URL
- Modify: `config/settings/base.py` — 添加 `'apps.memory'` 到 INSTALLED_APPS

**Steps:**
1. `python manage.py startapp memory` 在 apps/ 目录下
2. models.py 中导入并重新导出 `TrajectoryEvent`
3. views.py 中实现 timeline_view（分页列表）和 detail_view（单条详情）
4. templates 按 mockup 设计
5. URL 配置
6. 注册 app

---

### 任务 4: AI Surface 完善

**Files:**
- Modify: `templates/base.html` — 完善 AI Surface 的 5 种类型 + Pulse 动画

**Steps:**
1. 在现有 AI Surface 骨架上添加 5 种 Surface 类型的切换逻辑
2. 添加 CSS 动画（Pulse、Expand/Collapse）
3. 添加 JavaScript 自动轮换逻辑（根据时间/用户行为切换类型）
4. 确保 Jarvis Core 脉冲动画（紫色→蓝色渐变旋转）

---

## 执行顺序

```
Phase 1: 任务 1 (Dashboard bug) — 5 分钟，独立
Phase 2: 任务 2 + 任务 3 + 任务 4 — 并行执行
Phase 3: R4b 集成一致性审查
Phase 4: R5/R5b/R6 验收
```

## 关键约束

- 遵循 `docs/design-system.md` 的颜色/字体/间距/动效规范
- 所有模板变量名必须与 views.py 一致
- Agent V2 右侧面板数据通过新建 API 端点获取
- Memory Timeline 复用 `TrajectoryEvent` 模型
- AI Surface 必须包含 5 种类型 + Pulse 动画

## 验收标准

- [ ] Dashboard 渲染无变量名错误
- [ ] Agent 页面双列布局匹配 mockup
- [ ] Memory Timeline 页面可访问（`/memory/timeline/`）
- [ ] AI Surface 在所有页面显示且带脉冲动画
- [ ] 所有修改文件 `lsp_diagnostics` 无 error

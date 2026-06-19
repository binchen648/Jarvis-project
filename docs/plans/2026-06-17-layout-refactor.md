# Layout System v1.0 Refactoring Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 按照 Layout System v1.0.md 重构 Jarvis 项目的全局布局系统（5 个模板文件）。

**Architecture:** CSS Variables + CSS Grid 12列 双驱动布局。Sidebar 240px fixed → Topbar 48px sticky → Content `calc(100vw-240px)`。所有页面使用统一 CSS Grid 12 列布局，禁用 flex-wrap 伪 grid、max-w-*、container 和 h-[xxx]。

**Tech Stack:** Django 5.0 Templates, Tailwind CSS (via CSS Variables), CSS Grid

---

## 设计令牌参考

**最终规格（design-system.md 值 + Layout System v1.0.md 结构）:**
```
--sidebar-width:        240px
--sidebar-collapsed:    64px
--topbar-height:        48px
--content-max-width:    1200px
--card-radius:          8px     (--radius-md)
--card-padding:         20px    (--space-5)
--card-border:          1px solid rgba(255,255,255,0.06)
--card-bg:              rgba(15,15,25,0.85)
--card-backdrop-blur:   16px
--card-height-metric:   96px
--card-height-panel:    320px
--card-height-timeline: 400px
```

**Spacing Token 白名单:** 4/8/12/16/20/24/32/40/48/64px

**禁止使用:**
- `max-w-4xl`, `max-w-5xl`, `max-w-6xl`
- `container` class
- `flex-wrap` 冒充 grid
- `h-[xxx]` 任意高度

---

### Task 1: Refactor base.html — Global Layout Shell

**Files:**
- Modify: `templates/base.html`

**Goal:** 更新 :root CSS Variables + 重构 Sidebar/Topbar/Content 布局

**具体要求:**
1. 更新 `:root` CSS 变量区块，设置精确的 layout tokens:
   - `--sidebar-width: 240px`
   - `--sidebar-collapsed: 64px`
   - `--topbar-height: 48px`
   - `--content-max-width: 1200px`
   - `--card-radius: 8px`
   - `--card-padding: 20px`
2. Sidebar: `width: var(--sidebar-width)`, `position: fixed`, `height: 100vh`, `z-index: 100`
3. Sidebar collapsed: `width: var(--sidebar-collapsed)`
4. Topbar: `height: var(--topbar-height)`, `position: sticky`, `top: 0`, `z-index: 50`
5. Content: `margin-left: var(--sidebar-width)`, `padding: var(--space-8)`, `max-width: var(--content-max-width)`, `min-width: 960px`
6. Content 容器使用 CSS Grid: `grid-template-columns: repeat(12, 1fr)`, `gap: 24px`
7. AI Surface: 继续浮动在右下角
8. 保留全部 Jinja2 block 结构（`{% block content %}`, `{% block extra_js %}` 等）

---

### Task 2: Refactor dashboard/home.html — Dashboard Grid

**Files:**
- Modify: `templates/dashboard/home.html`

**Goal:** 将 Dashboard 改为 12-column CSS Grid 布局

**Grid Spec:**
- Welcome Header: `grid-column: span 12`
- Metrics 4 cards: 每卡 `grid-column: span 3`（4×3=12）
- Today's Plan: `grid-column: span 12`
- Goal Progress: `grid-column: span 6`
- Memory Timeline: `grid-column: span 6`

**Card Spec:**
- 所有卡片: `border-radius: var(--card-radius)`, `padding: var(--card-padding)`
- Metric Card: `min-height: 96px`
- Panel Card: `min-height: 320px`

**必须:**
- 移除所有 `max-w-*` 和 `container` 类
- 移除所有 `h-[xxx]` 任意高度
- 移除 `flex-wrap` 伪 grid 布局
- 保留所有 Django template 变量不变
- 更新间距使用 spacing tokens

---

### Task 3: Refactor conversation_detail.html — Agent Grid

**Files:**
- Modify: `templates/chat/conversation_detail.html`

**Goal:** 将 Agent 页面改为 8+4 CSS Grid 布局

**Grid Spec:**
- Conversation (left): `grid-column: span 8`
- Context Sidebar (right): `grid-column: span 4`
- 整个容器: `display: grid; grid-template-columns: repeat(12, 1fr); gap: 24px`

**Must DO:**
- 保留全部 WebSocket JS 逻辑不变
- 保留全部 HTMX 属性（hx-get, hx-trigger, hx-swap, hx-indicator）
- 保留 typing indicator, input form, send button
- 右侧面板卡片标准化（padding/radius/bg 符合 card spec）
- 移除 `h-[calc(100vh-8rem)]`, `-m-6` 等 hack 样式

---

### Task 4: Refactor memory/timeline.html + detail.html — Memory Grid

**Files:**
- Modify: `templates/memory/timeline.html`
- Modify: `templates/memory/detail.html`

**Goal:** 将 Memory Timeline 改为 12-column CSS Grid 布局

**Grid Spec (timeline):**
- Top Summary/Stats: `grid-column: span 12`
- Memory Filters (left): `grid-column: span 3`
- Timeline (right): `grid-column: span 9`
- 容器: `display: grid; grid-template-columns: repeat(12, 1fr); gap: 24px`

**detail.html:**
- 单列 card 布局，使用 card spec
- `max-width: 800px; margin: 0 auto;` 居中（不在禁止列表内）

---

### 执行顺序

```
Task 1 (base.html) → Phase 1: 全局变量 + Layout Shell
  ↓
Task 2 (home.html) → Phase 2: Dashboard Grid
  ↓ (可并行)
Task 3 (conversation_detail.html) → Phase 3: Agent Grid
  ↓ (可并行)
Task 4 (timeline.html + detail.html) → Phase 4: Memory Grid
  ↓
验证: lsp_diagnostics + 页面渲染检查
```

### 验收标准

- [ ] base.html sidebar width=240px, topbar height=48px
- [ ] 所有页面使用 `display: grid; grid-template-columns: repeat(12, 1fr)`
- [ ] 无 `max-w-4xl/5xl/6xl` / `container` / `flex-wrap` 冒充 grid / `h-[xxx]`
- [ ] 所有卡片 radius=8px, padding=20px
- [ ] HTMX/WebSocket 功能完整保留
- [ ] `lsp_diagnostics` 无 error

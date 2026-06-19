# Jarvis Design System

> **Personal AI Operating System**
> 不是聊天机器人，是个人 AI 操作系统。

---

## 1. 品牌定位

### 核心理念

Jarvis 不是"另一个 AI 聊天窗口"。它是用户数字生活的**副驾驶操作系统**——管理目标、追踪学习、调度健康、主动提醒、跨会话记忆。

### 品牌关键词

```
智能        · 不 intrusive
高效        · 不 冰冷
陪伴        · 不 话痨
掌控        · 不 复杂
```

### 设计哲学

| 原则 | 说明 |
|------|------|
| **Glanceable** | 一瞥即可获取关键信息，无需阅读 |
| **Proactive** | 系统主动推送有价值信息，而非被动等待 |
| **Spatial** | 信息有层级、有呼吸、有节奏 |
| **Terminal-Inspired** | 保留命令行的高效感，但不牺牲视觉 |
| **AI-First** | 每个界面都预设 AI 参与，而非事后附加 |

### 竞品参考与差异化

| 参考 | 借鉴什么 | 避免什么 |
|------|---------|---------|
| **Linear** | 极简信息密度、暗色 mastery、surgical spacing | 太冷、太企业 |
| **Arc** | 侧边栏优先、圆润 UI、空间层次感 | 过度动画、太浏览器 |
| **LobeChat** | Glassmorphism、渐变强调、未来感 | 太 chat-centric、信息密度低 |
| **Raycast** | 命令面板、键盘优先、紧凑效率 | 太开发工具感、缺少视觉温暖 |

---

## 2. Design System 结构

```
Theme Tokens
├── Colors
│   ├── Semantic Colors (primary/accent/success/warning/error)
│   ├── Surface Colors (bg/card/sidebar/dialog)
│   ├── Content Colors (text/icon/border)
│   └── Chart Colors (8-color palette)
├── Typography
│   ├── Font Family
│   ├── Type Scale
│   ├── Font Weights
│   └── Line Height
├── Spacing
│   ├── 4px Grid
│   └── Component Spacing
├── Motion
│   ├── Duration Tokens
│   ├── Easing Curves
│   └── Micro-interactions
├── Shadows
│   └── Elevation Levels
└── Radius
    └── Border Radius Scale
```

---

## 3. 色彩体系

### 主色调 (Dark Theme First)

```css
/* ── Brand Core ── */
--jarvis-blue:         #4F8CFF;    /* 主色 — 信任、智能 */
--jarvis-purple:       #8B5CF6;    /* 强调 — Agent 交互、AI Surface */
--jarvis-cyan:         #06B6D4;    /* 信息 — 主动推送、Memory Pulse */
--jarvis-teal:         #14B8A6;    /* 成功 — 目标完成、Summary Pulse */

/* ── Surface ── */
--surface-bg:          #0A0A0F;    /* 主背景 — 深空黑 */
--surface-sidebar:     #0F0F16;    /* 侧边栏 — 微亮 */
--surface-card:        #14141E;    /* 卡片 — 第二层 */
--surface-dialog:      #1A1A28;    /* 对话框 — 最亮层 */
--surface-hover:       #1E1E30;    /* 悬停状态 */

/* ── Content ── */
--text-primary:        #F1F1F6;    /* 主文字 — 高亮白 */
--text-secondary:      #9191A8;    /* 次要文字 */
--text-tertiary:       #5C5C72;    /* 辅助文字 */
--text-placeholder:    #3A3A4E;    /* 占位符 */

/* ── Border ── */
--border-default:      #1E1E30;    /* 默认边框 */
--border-hover:        #2E2E44;    /* 悬停边框 */

/* ── Semantic ── */
--color-success:       #22C55E;    /* 成功 */
--color-warning:       #F59E0B;    /* 警告 */
--color-error:         #EF4444;    /* 错误 */
--color-info:          #4F8CFF;    /* 信息 */
```

### Light Theme (未来扩展)

Light 主题保持相同的色相，反转亮度：

```css
--surface-bg:          #F8F8FC;
--surface-card:        #FFFFFF;
--text-primary:        #0A0A0F;
--text-secondary:      #5C5C72;
```

### 模块色彩标识

每个核心模块有专属强调色，用于侧边栏图标和状态指示：

| 模块 | 色值 | 色相 |
|------|------|------|
| Dashboard | `#4F8CFF` | 蓝 |
| Agent/Chat | `#8B5CF6` | 紫 |
| Goals | `#F59E0B` | 琥珀 |
| Memory | `#06B6D4` | 青 |
| Wellness | `#22C55E` | 绿 |
| Content | `#EC4899` | 粉 |

---

## 4. Typography

### Font Family

```css
/* 主字体 — 无衬线，数字友好 */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* 等宽 — 用于代码、数据、时间戳 */
--font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;

/* 展示 — 仅用于 hero/branding 场景 */
--font-display: 'SF Pro Display', 'Inter Display', sans-serif;
```

### Type Scale

```css
--text-xs:     0.75rem;    /* 12px — 标签、时间戳、辅助信息 */
--text-sm:     0.875rem;   /* 14px — 正文次要 */
--text-base:   1rem;       /* 16px — 正文 */
--text-lg:     1.125rem;   /* 18px — 小标题 */
--text-xl:     1.25rem;    /* 20px — 卡片标题 */
--text-2xl:    1.5rem;     /* 24px — 页面标题 */
--text-3xl:    1.875rem;   /* 30px — 大标题 */
--text-4xl:    2.25rem;    /* 36px — Hero */
```

### Font Weights

```css
--weight-normal:  400;     /* 正文 */
--weight-medium:  500;     /* 强调正文 */
--weight-semibold: 600;    /* 小标题 */
--weight-bold:    700;     /* 标题 */
```

### Line Height

```css
--leading-tight:    1.25;  /* 标题 */
--leading-normal:   1.5;   /* 正文 */
--leading-relaxed:  1.75;  /* 长文 */
```

---

## 5. Spacing

### 4px 网格系统

```css
--space-1:  0.25rem;    /*  4px */
--space-2:  0.5rem;     /*  8px */
--space-3:  0.75rem;    /* 12px */
--space-4:  1rem;       /* 16px */
--space-5:  1.25rem;    /* 20px */
--space-6:  1.5rem;     /* 24px */
--space-8:  2rem;       /* 32px */
--space-10: 2.5rem;     /* 40px */
--space-12: 3rem;       /* 48px */
--space-16: 4rem;       /* 64px */
```

### Layout Tokens

```css
--sidebar-width:        240px;
--sidebar-collapsed:    64px;
--topbar-height:        48px;
--content-max-width:    1200px;
--panel-min-width:      320px;
--input-height:         40px;
--button-height:        36px;
```

### Component Spacing

| 组件 | 内边距 | 间距 |
|------|--------|------|
| Card | `--space-5` (20px) | — |
| Sidebar Item | `--space-2` y `--space-4` x | — |
| Dialog Content | `--space-6` | — |
| Form Fields | — | `--space-4` 垂直 |
| Button | `--space-2` y `--space-4` x | — |
| List Items | `--space-3` y | `--space-1` gap |

---

## 6. Border Radius

```css
--radius-none:   0;
--radius-sm:     4px;      /* 按钮、输入框 */
--radius-md:     8px;      /* 卡片 */
--radius-lg:     12px;     /* 对话框 */
--radius-xl:     16px;     /* 大卡片 */
--radius-full:   9999px;   /* Avatar、标签 */
```

---

## 7. Shadows

```css
--shadow-sm:     0 1px 2px rgba(0, 0, 0, 0.3);
--shadow-md:     0 4px 12px rgba(0, 0, 0, 0.4);
--shadow-lg:     0 8px 24px rgba(0, 0, 0, 0.5);
--shadow-xl:     0 16px 48px rgba(0, 0, 0, 0.6);
--shadow-glow:   0 0 20px rgba(79, 140, 255, 0.15);  /* 主色光晕 */
```

---

## 8. AI Surface — 统一 AI 交互层

> AI Surface 是 Jarvis 区别于"聊天机器人"的核心设计。AI 不是藏在 `/agent/` 页面里的一个对话窗口，而是**悬浮在所有页面之上**的智能层。

### 设计定位

AI Surface 是操作系统级的 AI 伴侣层。用户在任何页面都能感知到 AI 的存在，但 AI 不抢占内容焦点。

```
┌─────────────────────────────────────────────────────┐
│  Sidebar  │  Main Content Area                      │
│           │                                         │
│           │  ┌─────────────────────────────────┐    │
│           │  │  Dashboard content              │    │
│           │  │                                 │    │
│           │  └─────────────────────────────────┘    │
│           │                                         │
│  ┌──────┐ │                                         │
│  │  ✦   │ │  ← AI Surface (浮动在右下)              │
│  └──────┘ │                                         │
└───────────┴─────────────────────────────────────────┘
```

### Jarvis Pulse — 品牌心跳

AI Surface 的入口图标不是静态的。它永远在呼吸。

```
 ┌─────────────────────┐
 │                     │
 │         ✦           │  ← Jarvis Core Icon
 │    (呼吸光晕)        │  ← Pulse Glow
 │                     │
 └─────────────────────┘
     右下角 · 44×44 · 圆形
```

#### Pulse 状态机

| 状态 | 触发 | 光晕色 | 动画 | 频率 |
|------|------|--------|------|:----:|
| **Idle (呼吸)** | 默认 | `--jarvis-purple` @ 15% 透明度 | 微弱缩放 + 透明度呼吸 | 4s 周期 |
| **Thinking** | Agent 正在推理 | `--jarvis-purple` @ 40% 透明度 | 快速脉冲（节奏感） | 1.2s 周期 |
| **Goal Alert** | 目标即将到期 | `--jarvis-purple` → 全亮 | 醒目脉冲 + 微光晕 | 0.8s 周期 |
| **Memory Reminder** | 触发记忆回调 | `--jarvis-cyan` 青色呼吸 | 平静水面涟漪 | 2s 周期 |
| **Summary Ready** | 日报/周报就绪 | `--jarvis-teal` 碧绿 | 渐变呼吸 | 3s 周期 |
| **Error** | AI 服务异常 | `--color-error` 红色 | 缓慢闪烁 | 2s 周期 |

```css
/* ── Pulse Animations ── */
@keyframes pulse-idle {
    0%, 100% { opacity: 0.15; transform: scale(1); }
    50%      { opacity: 0.25; transform: scale(1.05); }
}
@keyframes pulse-thinking {
    0%, 100% { opacity: 0.3; transform: scale(1); box-shadow: 0 0 12px rgba(139, 92, 246, 0.15); }
    50%      { opacity: 0.6; transform: scale(1.08); box-shadow: 0 0 24px rgba(139, 92, 246, 0.3); }
}
@keyframes pulse-alert {
    0%, 100% { opacity: 0.5; transform: scale(1); box-shadow: 0 0 16px rgba(139, 92, 246, 0.2); }
    50%      { opacity: 1;   transform: scale(1.12); box-shadow: 0 0 36px rgba(139, 92, 246, 0.5); }
}
@keyframes pulse-memory {
    0%, 100% { opacity: 0.2; transform: scale(1); box-shadow: 0 0 8px rgba(6, 182, 212, 0.1); }
    50%      { opacity: 0.5; transform: scale(1.06); box-shadow: 0 0 20px rgba(6, 182, 212, 0.3); }
}
```

#### 品牌价值

用户不需要看屏幕内容——只需余光扫到右下角的脉冲颜色和节奏，就知道：

```
脉动紫色 = Jarvis 正在为你思考
青色涟漪 = Jarvis 记起了重要的事
红色闪烁 = Jarvis 需要你的注意
```

**这是品牌的超级记忆点。** 就像 Mac 的睡眠呼吸灯、Pixel 的 Always-On Display、Tesla 的灯光秀——一个微小的动画，成为整个产品的灵魂。

---

### 5 种 Surface 形态

| 形态 | 触发时机 | 内容 | 用户操作 |
|------|---------|------|---------|
| **Morning Briefing** | 每天首次打开 | 今日目标、昨日回顾、健康建议 | 滑动忽略 / 点击展开 |
| **Evening Summary** | 21:00 或关闭前 | 今日完成汇总、明日预览 | 查看 / 关闭 |
| **Smart Suggestion** | AI 检测到可优化项 | "你已连续学习 2 小时，休息一下？" | 采纳 / 忽略 |
| **Goal Alert** | 目标到期或异常 | "LeetCode 每日一题今日还未完成" | 去完成 / 稍后 |
| **Memory Reminder** | 相关记忆触发 | "你 3 天前学过 Python 异步，要复习吗？" | 查看记忆 / 关闭 |

### 视觉规范

```css
/* ── Surface Container ── */
--ai-surface-bg:            rgba(139, 92, 246, 0.08);  /* Jarvis Purple @ 8% */
--ai-surface-border:        rgba(139, 92, 246, 0.25);  /* Jarvis Purple @ 25% */
--ai-surface-glow:          0 0 24px rgba(139, 92, 246, 0.12);
--ai-surface-glow-hover:    0 0 32px rgba(139, 92, 246, 0.2);

--ai-surface-radius:        12px;
--ai-surface-padding:       16px 20px;
--ai-surface-max-width:     420px;

/* ── Surface Icon ── */
--ai-surface-icon:          'sparkles';     /* Heroicons sparkles */
--ai-surface-icon-size:     20px;
--ai-surface-icon-color:    #8B5CF6;        /* Jarvis Purple */

/* ── Surface Typography ── */
--ai-surface-title-size:    0.875rem;       /* 14px semibold */
--ai-surface-body-size:     0.8125rem;      /* 13px normal */
--ai-surface-meta-size:     0.75rem;        /* 12px tertiary */
```

### 行为规范

| 行为 | 规则 |
|------|------|
| **位置** | 固定在右下角，距边缘 24px |
| **堆叠** | 最多同时显示 3 条，按优先级排序（Alert > Briefing > Suggestion > Reminder > Summary） |
| **消除** | 用户点击"稍后"或滑动关闭后，同类 Surface 30 分钟内不重复 |
| **入口** | 收拢状态显示为 Sparkle 图标（Jarvis Purple + glow），点击展开当前最高优先级 Surface |
| **动画** | 从右下角滑入 + 透明度渐入，200ms ease-out |
| **DnD** | 不打扰模式：22:00-07:00 仅显示 Goal Alert（紧急） |

### Surface 层级

```
Priority 1: Goal Alert       — 🔴 必须立即处理
Priority 2: Smart Suggestion — 🟡 建议但非紧急
Priority 3: Memory Reminder  — 🔵 有价值但可稍后
Priority 4: Morning Briefing — 🟢 每日例行
Priority 5: Evening Summary  — 🟢 每日例行
```

### 代码结构（未来实现）

```
templates/
└── components/
    └── ai_surface.html        ← Surface 容器（浮动定位 + 优先级排序）
    ├── ai_surface_briefing.html
    ├── ai_surface_summary.html
    ├── ai_surface_suggestion.html
    ├── ai_surface_alert.html
    └── ai_surface_reminder.html
```

---

## 9. Motion Design

### Duration Tokens

```css
--duration-instant:  0ms;
--duration-fast:    100ms;    /* hover、tap */
--duration-normal:  200ms;    /* 面板切换、展开 */
--duration-slow:    300ms;    /* 页面过渡、对话框 */
--duration-glass:   500ms;    /* 玻璃态模糊过渡 */
```

### Easing Curves

```css
--ease-out:       cubic-bezier(0.16, 1, 0.3, 1);     /* 出场 — Linear 风格 */
--ease-in-out:    cubic-bezier(0.65, 0, 0.35, 1);     /* 前后一致 */
--ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1);  /* 弹性 — 仅用于趣味元素 */
--ease-glass:     cubic-bezier(0.4, 0, 0.2, 1);        /* 玻璃态过渡 */
```

### Micro-interactions

| 元素 | 触发 | 动画 | 时长 | 缓动 |
|------|------|------|:----:|:----:|
| 侧边栏 Item | hover | 背景淡入 + 左侧指示条滑动 | 100ms | ease-out |
| 侧边栏 Item | active | 缩放 0.97 | 100ms | ease-out |
| Card | hover | 上移 2px + shadow 增强 | 200ms | ease-out |
| Button | hover | 背景亮度变化 | 100ms | ease-out |
| Button | click | 缩放 0.95 | 100ms | ease-out |
| 对话框 | open | 透明度 0→1 + 上移 8→0 | 200ms | ease-out |
| 对话框 | close | 透明度 1→0 + 下移 0→8 | 150ms | ease-in-out |
| AI 回复 | streaming | 逐字 fadeIn | 20ms/字 | ease-out |
| 面板切换 | 路由变化 | 透明度 + 平移 16px | 200ms | ease-out |
| 通知出现 | 主动推送 | 从顶部滑入 | 300ms | ease-out |
| 玻璃态 | mount | 背景模糊 0→12px | 500ms | ease-glass |

---

## 9. 页面信息架构

```
Application Shell
├── Sidebar (240px)
│   ├── Logo + App Name
│   ├── ───
│   ├── Dashboard           [icon: grid]          ← 首页
│   ├── Agent               [icon: sparkles]      ← AI 对话
│   ├── Memory              [icon: brain]         ← 记忆时间线
│   ├── Goals               [icon: target]        ← 学习目标
│   ├── Wellness            [icon: heart]         ← 健康
│   ├── ───
│   ├── Content             [icon: book-open]     ← 推荐内容
│   ├── Trajectory          [icon: git-branch]    ← 学习路径
│   └── ───
│   ├── Settings             [icon: gear]
│   └── User Avatar + Name
│
├── Topbar (48px)
│   ├── Breadcrumb / Page Title
│   ├── ─── (spacer)
│   ├── Global Search (Cmd+K)
│   ├── Notification Bell
│   └── ───
│
└── Main Content Area
    └── [Render by route]
```

### 路由与页面映射

| Path | 页面 | Layout |
|------|------|--------|
| `/` | Dashboard | 面板网格 |
| `/agent/` | Agent 对话 | 对话全屏 |
| `/agent/:id/` | 具体对话 | 对话全屏 |
| `/memory/` | 记忆时间线 | 全宽时间线 |
| `/goals/` | 目标列表 | 卡片网格 |
| `/goals/:id/` | 目标详情 | 左侧详情 + 右侧 timeline |
| `/wellness/` | 健康面板 | 面板网格 |
| `/wellness/suggestions/` | 健康建议 | 列表 |
| `/content/feed/` | 推荐列表 | 卡片列表 |
| `/trajectory/` | 学习路径 | 图谱布局 |
| `/settings/` | 设置 | 左侧导航 + 右侧内容 |

---

## 10. 核心 Wireframes

> 以下为 ASCII wireframe，视觉设计以 Design Tokens 为准。

### 10.1 Dashboard

```
┌─────────────────────────────────────────────────────────┐
│ sidebar  │  Dashboard                        Cmd+K  🔔  │
│          ├──────────────────────────────────────────────┤
│ ┌───┐    │ ┌──────┐ ┌──────┐ ┌──────┐                    │
│ │   │    │ │Today │ │Goals │ │Streak│                    │
│ │ D │    │ │45min │ │ 3/5  │ │ 12d  │                    │
│ │ A │    │ └──────┘ └──────┘ └──────┘                    │
│ │ G │    │                                                 │
│ │   │    │ ┌────────────────────────────────────────┐    │
│ │ M │    │ │  Weekly Activity                       │    │
│ │ E │    │ │  ▃▄▆▇▅▃▄  CSS bar chart               │    │
│ │ M │    │ └────────────────────────────────────────┘    │
│ │   │    │                                                 │
│ │ G │    │ ┌────────────┐ ┌────────────────────────┐    │
│ │ O │    │ │ Expiring   │ │ Recent Chats           │    │
│ │   │    │ │ LeetCode 2d│ │ ─ How to learn Python  │    │
│ │ W │    │ └────────────┘ └────────────────────────┘    │
│ └───┘    └──────────────────────────────────────────────┘
```

### 10.2 Agent / Chat

```
┌─────────────────────────────────────────────────────────┐
│ sidebar  │  Agent                                Cmd+K  │
│          ├──────────────────────────────────────────────┤
│          │ ┌────────────────────────────────────────┐  │
│          │ │ today, 14:30                          │  │
│          │ │ ┌──────────────────────────────────┐  │  │
│          │ │ │ user: 帮我规划本周学习计划       │  │  │
│          │ │ └──────────────────────────────────┘  │  │
│          │ │ ┌──────────────────────────────────┐  │  │
│          │ │ │ agent: 好的，我先查看你的      │  │  │
│          │ │ │ 目标和当前进度...               │  │  │
│          │ │ │                                │  │  │
│          │ │ │ 🔍 思考中 (2/3)               │  │  │
│          │ │ │ ┌─ tool_call ──────────────┐  │  │  │
│          │ │ │ │ 📊 使用: get_goal_progress│  │  │  │
│          │ │ │ └──────────────────────────┘  │  │  │
│          │ │ │                                │  │  │
│          │ │ │ 根据你的目标，我建议...      │  │  │
│          │ │ └──────────────────────────────────┘  │  │
│          │ └────────────────────────────────────────┘  │
│          │                                                 │
│          │ ┌────────────────────────────────────────┐  │
│          │ │ › 输入消息...                        │  │
│          │ └────────────────────────────────────────┘  │
│          │   [tool: auto] [model: chat]        发送 ↵  │
│          └──────────────────────────────────────────────┘
```

### 10.3 Memory Timeline

```
┌─────────────────────────────────────────────────────────┐
│ sidebar  │  Memory                              Cmd+K  │
│          ├──────────────────────────────────────────────┤
│          │  Search memory...                    [filter] │
│          │                                                 │
│          │  2026-06-15  Monday                            │
│          │  ┌────────────────────────────────────────┐  │
│          │  │ 🎯 完成 LeetCode 每日一题 (L2)       │  │
│          │  │ 📚 学习 Python 异步编程 2h (L2)      │  │
│          │  │ 💬 和 Jarvis 讨论学习计划 (L2)       │  │
│          │  └────────────────────────────────────────┘  │
│          │                                                 │
│          │  2026-06-14  Sunday                            │
│          │  ┌────────────────────────────────────────┐  │
│          │  │ 🧘 休息日 - 学习 30min (L2)           │  │
│          │  └────────────────────────────────────────┘  │
│          │                                                 │
│          │  [Load more...]                                │
│          └──────────────────────────────────────────────┘
```

### 10.4 Global Command Palette (Cmd+K)

```
┌─────────────────────────────────────────────────────────┐
│  › 搜索目标、记忆、命令...                               │
│                                                         │
│  Recent                                                  │
│  ┌────────────────────────────────────────────────┐    │
│  │ 📄 查看 Dashboard                             │    │
│  │ 💬 继续上次对话「Python 学习计划」            │    │
│  │ 🎯 新建学习目标                               │    │
│  │ 📊 查看本周学习统计                           │    │
│  └────────────────────────────────────────────────┘    │
│                                                         │
│  Quick Actions                                           │
│  ┌────────────────────────────────────────────────┐    │
│  │  /new-goal       新建学习目标                 │    │
│  │  /log-session    记录学习                     │    │
│  │  /memory-search  搜索记忆                     │    │
│  │  /agent          打开 Agent 对话              │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 11. 实现计划

### Phase 1: Design Token → Tailwind Config

| 文件 | 内容 |
|------|------|
| `tailwind.config.js` | 更新 theme.extend 的 colors / fontFamily / borderRadius / spacing |
| `templates/base.html` | 更新 `<style>` 中的 CSS 变量，替换已有的 DaisyUI theme |

### Phase 2: Layout Shell

| 组件 | 说明 |
|------|------|
| `Sidebar.svelte` / HTML partial | 侧边栏组件（图标 + 标签 + 模块色彩标识） |
| `Topbar.svelte` / HTML partial | 顶栏组件（Cmd+K 入口 + 通知） |
| `CommandPalette.svelte` / HTML partial | 全局命令面板 |

### Phase 3: 模块页面按新 Design System 重构

| 页面 | 优先级 |
|------|:------:|
| Agent (Chat) 页面重构 | P0 |
| Dashboard 重构 | P0 |
| Memory Timeline 页面 | P1 |
| Goals 页面重构 | P1 |
| Wellness 页面重构 | P2 |

---

> **Next**: 确认 Design System 方案后，开始 Phase 1 编码。

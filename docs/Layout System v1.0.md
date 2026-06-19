# Jarvis Design System

## Layout System v1.0

---

# 1. Layout Philosophy

Jarvis 不是传统 SaaS 管理后台。

设计目标：

* AI First
* Information Dense
* Focus Driven
* Dashboard + Agent Workspace

布局原则：

1. Sidebar 固定
2. Content 自适应扩展
3. Grid 驱动布局
4. 页面共享统一模板
5. 卡片尺寸标准化

---

# 2. Global Layout

Desktop ≥ 1440px

┌──────── Sidebar ────────┬──────── Content ────────┐
│                         │                         │
│                         │                         │
│                         │                         │
└─────────────────────────┴─────────────────────────┘

Sidebar Width:
256px

Content:
width: calc(100vw - 256px)

Content Padding:
32px

Content Max Width:
1600px

Content Min Width:
960px

---

# 3. Breakpoints

Desktop XL:
≥ 1600px

Desktop:
1440px - 1599px

Laptop:
1280px - 1439px

Tablet:
768px - 1279px

Mobile:
<768px

---

# 4. Grid System

Desktop:

12 Columns

Gap:
24px

Tablet:

8 Columns

Gap:
16px

Mobile:

4 Columns

Gap:
12px

---

# 5. Sidebar Specification

Width:
256px

Collapsed Width:
72px

Position:
fixed

Height:
100vh

Z-index:
100

Sections:

* Dashboard
* Agent
* Goals
* Wellness
* Content
* Trajectory
* Settings

Avatar:
Bottom Fixed

---

# 6. Top Bar

Height:
64px

Contains:

* Search
* Notifications
* User Avatar

Position:
sticky

Top:
0

Z-index:
50

---

# 7. Card System

All content lives inside cards.

Card Radius:
16px

Card Padding:
24px

Border:
1px solid rgba(255,255,255,0.06)

Background:
rgba(15,15,25,0.85)

Backdrop Blur:
16px

---

# 8. Card Heights

Metric Card:
96px

Status Card:
120px

Panel Card:
320px

Timeline Card:
400px

Conversation Card:
Auto Height

Agent Tool Card:
80px

Memory Card:
96px

---

# 9. Dashboard Template

Grid:
12 Columns

Welcome Header:
span 12

Metrics:
4 cards

each span 3

Layout:

3 + 3 + 3 + 3

Today Plan:
span 12

Goal Progress:
span 6

Memory Timeline:
span 6

Recent Activity:
span 12

---

# 10. Agent Template

Grid:
12 Columns

Layout:

Conversation:
span 8

Context Sidebar:
span 4

Conversation Area:

* Messages
* Tool Cards
* Input

Context Sidebar:

* Active Goal
* Relevant Memory
* Today Focus
* Recent Tool Usage

---

# 11. Memory Template

Grid:
12 Columns

Top Summary:
span 12

Memory Filters:
span 3

Timeline:
span 9

Timeline Card Height:
Auto

Memory Summary:
span 12

---

# 12. Goals Template

Grid:
12 Columns

Goal Health:
span 3

Progress:
span 3

Confidence:
span 3

Momentum:
span 3

Goal List:
span 8

AI Suggestions:
span 4

---

# 13. Wellness Template

Grid:
12 Columns

Mood Trend:
span 8

Health Snapshot:
span 4

Recent Check-ins:
span 12

---

# 14. Empty State

所有空状态统一规范：

Icon
↓

Title
↓

Description
↓

Primary Action

Example:

🧠

No Memories Yet

Start learning and Jarvis will build your memory timeline.

[Start Learning]

---

# 15. Floating AI Surface

Position:
Bottom Right

Size:
64px

Z-index:
200

Maximum Active Cards:
3

Priority:

Goal Alert

>

Smart Suggestion

>

Memory Reminder

>

Morning Briefing

>

Evening Summary

Agent 页面：

Surface 自动缩小

Memory 页面：

Surface 完全展开

---

# 16. Spacing Scale

4px

8px

12px

16px

24px

32px

48px

64px

禁止使用任意间距值。

统一使用 Spacing Token。

---

# 17. Implementation Rules

禁止：

max-w-4xl

max-w-5xl

max-w-6xl

container

flex-wrap 模拟 Grid

任意高度 h-[xxx]

---

必须：

CSS Grid

12 Column Layout

Layout Token

Page Template

统一 Card Height

---

# Layout Golden Rule

所有页面必须遵循：

Sidebar
→ Content
→ Grid
→ Card

禁止页面自行定义布局逻辑。

# Dashboard 高保真稿 V2 — Jarvis Design System

> Personal AI Operating System
> 基于 `docs/design-system.md` 视觉语言 · 六项体验重构

---

## 布局结构

```
┌──────────────────────────────────────────────────────────────────────┐
│ Sidebar  │  Topbar                              Jarvis Core  🔔 ▸  │
│ 240px    ├──────────────────────────────────────────────────────────┤
│          │                                                          │
│ ✦ Jarvis │                                                          │
│ ───────  │  Good Morning, Alex                         Jun 16     │
│ ☐ Dash   │                                                          │
│ ✦ Agent  │  今天最重要的目标：                                      │
│ 🧠 Memory│  LeetCode 92 — 两数之和                                   │
│ 🎯 Goals │  预计完成：35 分钟                                         │
│ ❤️ Health│  Jarvis 建议：18:30 开始学习，今日精力高峰                │
│ ───────  │                                       ┌────────────┐    │
│ 📚 Con.  │                                       │  ◉  AI Core │    │
│ 🗺 Traj.  │                                       │  动态紫蓝球  │    │
│ ───────  │                                       └────────────┘    │
│ ⚙ Set.   │                                                          │
│          │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ 👤 Alex  │  │Focus     │ │Goal      │ │Memory    │ │AI        │   │
│          │  │82%       │ │Health    │ │Growth    │ │Confidence│   │
│          │  │▲ +5%     │ │3正常 1风险│ │+12条  │ │87%       │   │
│          │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│          │                                                          │
│          │  ┌──────────────────────────────────────────────────┐   │
│          │  │  Today's Plan                        2/3 done   │   │
│          │  │                                                    │   │
│          │  │  ☐ ① LeetCode 92                         35min   │   │
│          │  │    ├─ 难度: Medium  🎯 今日必完成                  │   │
│          │  │    └─ 🔗 /goals/leetcode-92                       │   │
│          │  │                                                    │   │
│          │  │  ☐ ② 阅读 ReAct Agent 笔记               20min   │   │
│          │  │    ├─ 上次: 3天前  🧠 需要复习                   │   │
│          │  │    └─ 🔗 /memory/react-agent                      │   │
│          │  │                                                    │   │
│          │  │  ☐ ③ 更新 Wellness 记录                   5min   │   │
│          │  │    └─ 🔗 /wellness/record                        │   │
│          │  └──────────────────────────────────────────────────┘   │
│          │                                                          │
│          │  ┌──────────────┐  ┌──────────────────────────────┐    │
│          │  │ Goal Progress │  │ Memory Timeline              │    │
│          │  │              │  │                              │    │
│          │  │ Goal A       │  │ 🧠 复习 ReAct Agent笔记     │    │
│          │  │ ██████░░ 60% │  │    1h ago → /memory         │    │
│          │  │              │  │ 📚 学习 Python 异步编程     │    │
│          │  │ Goal B       │  │    2h ago → /memory         │    │
│          │  │ ████████░80%│  │                              │    │
│          │  │              │  │ → 查看完整 Timeline          │    │
│          │  │ Goal C       │  └──────────────────────────────┘    │
│          │  │ ███░░░░░ 30% │                                      │
│          │  └──────────────┘                                      │
│          │                                          ✦  ← Pulse   │
│          │                                          (AI Surface)  │
└──────────┴──────────────────────────────────────────────────────────┘
```

---

## 组件分解

### 1. Welcome + AI Briefing (原问题 1)

```
Good Morning, Alex                         --text-xl weight-semibold
                                     Jun 16  --text-tertiary

今天最重要的目标：
LeetCode 92 — 两数之和                     --text-base weight-medium
预计完成：35 分钟                           --text-sm secondary
Jarvis 建议：18:30 开始学习，今日精力高峰    --text-sm --jarvis-cyan
                                              ↑ AI 分析标记
```

**关键改动**: 不再是静态问候，而是 AI 已经分析过你今天的数据后给出的**行动简报**。

---

### 2. 四张 KPI 卡 (原问题 2)

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Today    │  │ Goal     │  │ Memory   │  │ AI       │
│ Focus    │  │ Health   │  │ Growth   │  │Confidence│
│   82%    │  │  3正常   │  │  +12条   │  │   87%    │
│  ▲ +5%   │  │  1风险   │  │  本周    │  │  稳定    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
  jarvis-blue  琥珀/红双色    jarvis-cyan   jarvis-purple
```

**关键改动**: 从通用指标(时长/目标数/连续天数)改为 **Jarvis 专属指标**(专注度/目标健康度/记忆成长/AI 置信度)。

---

### 3. Today's Plan — 行动台 (原问题 3)

```
┌──────────────────────────────────────────────────────────────────┐
│  Today's Plan                                    2/3 done      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ☐ ① LeetCode 92                                35min    │  │
│  │    ├─ 难度: Medium  🎯 今日必完成                          │  │
│  │    └─ 🔗 /goals/leetcode-92                               │  │
│  │                                                             │  │
│  │  ☑ ② 阅读 ReAct Agent 笔记                       20min    │  │  ← 已完成
│  │    ├─ 上次: 3天前  🧠 需要复习                            │  │
│  │    └─ 🔗 /memory/react-agent                               │  │
│  │                                                             │  │
│  │  ☐ ③ 更新 Wellness 记录                           5min    │  │
│  │    └─ 🔗 /wellness/record                                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  每项可点击 → 直接跳转到对应页面                                  │
│  已完成项显示 ☑ + 划线                                            │
│  空状态: "Jarvis 正在分析你的目标，稍后为你生成计划"               │
└──────────────────────────────────────────────────────────────────┘
```

---

### 4. Goal Progress + Memory Timeline (原问题 4)

```
┌──────────────────────────┐  ┌──────────────────────────────────┐
│  Goal Progress           │  │  Memory Timeline                 │
│                          │  │                                  │
│  Goal A: 系统设计         │  │  🧠 复习 ReAct Agent 笔记      │
│  ████████████░░░░  70%   │  │     1h ago → /memory            │
│  ─────────────────────   │  │                                  │
│  Goal B: LeetCode 150    │  │  📚 学习 Python 异步编程        │
│  ████████████████  90%   │  │     2h ago → /memory            │
│  ─────────────────────   │  │                                  │
│  Goal C: 项目实战         │  │  💬 讨论学习计划                │
│  ██████░░░░░░░░░░  30%   │  │     昨天 → /memory              │
│                          │  │                                  │
│  进度条: jarvis-purple    │  │  → 查看完整 Timeline            │
│  高风险: 红色              │  │     (jarvis-cyan link)          │
└──────────────────────────┘  └──────────────────────────────────┘

```

**关键改动**: 从"周学习时长柱状图"改为"目标进度时间线"——用户关心成果而非时长。

---

### 5. Jarvis Core — 品牌视觉锚点 (原问题 5)

```
位置: Topbar 右侧

          ◉
      ╱       ╲
   Memory   Goals
      ╲       ╱
       Agent

尺寸: 32×32px 圆形
颜色: 动态紫蓝渐变 (--jarvis-purple → --jarvis-blue)
动画: 缓慢自旋 + 微呼吸 (8s cycle)
交互: 悬停显示 "Jarvis AI Core | v1.0"
意义: 用户看到这个球就知道 "这是 Jarvis"
```

**设计规范**:

```css
.jarvis-core {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #8B5CF6, #4F8CFF);
    animation: core-breathe 8s ease-in-out infinite;
    cursor: pointer;
}

@keyframes core-breathe {
    0%, 100% { transform: rotate(0deg) scale(1); box-shadow: 0 0 12px rgba(139, 92, 246, 0.2); }
    25%      { transform: rotate(90deg) scale(1.02); box-shadow: 0 0 20px rgba(79, 140, 255, 0.3); }
    50%      { transform: rotate(180deg) scale(1); box-shadow: 0 0 12px rgba(139, 92, 246, 0.2); }
    75%      { transform: rotate(270deg) scale(1.02); box-shadow: 0 0 20px rgba(6, 182, 212, 0.3); }
    100%     { transform: rotate(360deg) scale(1); box-shadow: 0 0 12px rgba(139, 92, 246, 0.2); }
}
```

---

### 6. AI Surface 增强 (原问题 6)

```
空闲状态:
     ✦
    紫色微呼吸 (4s 周期)
    --jarvis-purple @ 15% opacity

有普通提醒:
    ✦ ✦
    双层紫色脉冲 (2s 周期)
    内层 solid / 外层 glow

高优先级 (Goal at Risk):
    ✦ ✦ ✦
    紫 → 红色脉冲 (1s 周期)
    内层 --jarvis-purple → --color-error
    外层 glow 增强 #EF444420 → #EF444450

点击展开 Surface 面板:
    ┌─────────────────────┐
    │ 📋 Goal at Risk      │
    │ LeetCode 92 今日截止 │
    │ [去完成] [稍后]      │
    └─────────────────────┘
```

**关键改动**: 从单层呼吸 → 双层脉冲 → 三色渐变，让用户通过 Pulse 状态就能判断优先级。

---

## 色彩映射总结

| 组件 | 主色 | 强调色 |
|------|:----:|:------:|
| Jarvis Core | `#8B5CF6→#4F8CFF` 渐变 | — |
| Welcome Briefing | `--text-primary` | `--jarvis-cyan` (AI 建议) |
| Focus KPI | `--jarvis-blue` | `--color-success` (涨幅) |
| Goal Health KPI | `--jarvis-purple` | `--color-error` (风险计数) |
| Memory Growth KPI | `--jarvis-cyan` | — |
| AI Confidence KPI | `--jarvis-purple` | — |
| Today's Plan | `--text-primary` | `--jarvis-purple` (优先级) |
| Goal Progress | `--jarvis-purple` | `--color-error` (高风险) |
| Memory Timeline | `--jarvis-cyan` | — |
| AI Surface Idle | `--jarvis-purple` 15% | — |
| AI Surface Alert | `--jarvis-purple→--color-error` | — |

---

> **确认 V2 方案后，继续出 Agent 高保真稿和 Memory Timeline 高保真稿。**

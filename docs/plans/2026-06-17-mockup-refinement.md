# Mockup Refinement Plan — Dashboard + Memory

**Goal:** 严格按 mockup-dashboard.md 和 mockup-memory.md 实现高保真视觉

**Architecture:** 3 个独立任务并行执行:
- Task A: base.html — Jarvis Core orb + AI Surface 三态脉冲
- Task B: dashboard/home.html — 补全视觉细节
- Task C: memory/timeline.html + views.py — 重写 Memory 页面

---

### Task A: Jarvis Core + AI Surface (base.html)

**File:** `templates/base.html`

**添加 Jarvis Core orb (mockup §5):**
```css
.jarvis-core {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #8B5CF6, #4F8CFF);
    animation: core-breathe 8s ease-in-out infinite;
    cursor: pointer;
}
@keyframes core-breathe {
    0%, 100% { transform: rotate(0deg) scale(1); box-shadow: 0 0 12px rgba(139,92,246,0.2); }
    25%      { transform: rotate(90deg) scale(1.02); box-shadow: 0 0 20px rgba(79,140,255,0.3); }
    50%      { transform: rotate(180deg) scale(1); box-shadow: 0 0 12px rgba(139,92,246,0.2); }
    75%      { transform: rotate(270deg) scale(1.02); box-shadow: 0 0 20px rgba(6,182,212,0.3); }
    100%     { transform: rotate(360deg) scale(1); box-shadow: 0 0 12px rgba(139,92,246,0.2); }
}
```
- 位置: Topbar 右侧（通知铃旁边）
- 悬停: "Jarvis AI Core | v1.0" tooltip

**AI Surface 三态脉冲 (mockup §6):**
- Idle: 紫色微呼吸 4s, --jarvis-purple @15% opacity
- Alert: 紫→红脉冲 1s, 双层内外光晕
- 实现 data-pulse 状态属性切换

---

### Task B: Dashboard 视觉补全 (home.html)

**File:** `templates/dashboard/home.html`

1. Today's Plan 子详情（每项显示难度标签、链接、状态标记）
2. 已完成项用 ☑ + line-through
3. Memory Timeline 链接从 `trajectory:skill_graph` 改为 `memory:timeline`
4. 空状态对齐 mockup 格式
5. KPI 卡颜色验证（mockup §色彩映射）

---

### Task C: Memory Timeline 重写

**Files:**
- Modify: `apps/memory/views.py`
- Modify: `templates/memory/timeline.html`

**分类映射:**
```
learning  → 🧠 Learning     (--jarvis-blue)
achievement → 🎯 Goal       (--jarvis-purple)
reflection → 💬 Chat        (--jarvis-purple)
milestone → 📝 Agent Note   (--jarvis-cyan)
❤️ Health  → 来自 wellness 数据（--color-success）
```

**5 种卡片样式**: 每个卡片左侧 2px 彩色边框、emoji 图标、标题、时间、子详情

**日分割线**: "Today — Jun 16", "Yesterday — Jun 15", "Jun 14, 2026"

**Memory Stats**: 底部固定，显示本周 + 总计 + 各类别计数

**空状态**: 含 CTA 按钮 💬 去和 Agent 对话 + 🎯 创建第一个目标

**"Load more"**: 替换当前分页为加载更多按钮

---

### 执行与验收

3 个任务并行派发，完成后通过 R4b 集成审查 + 截图对比 mockup 验证。

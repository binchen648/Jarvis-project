# Pulse Orb + AI Surface Stack — Integration Architecture

## 数据流

```
SurfaceEvent (来自 eventbus / 手动创建)
  ↓
/api/core-status/ 聚合 pending 事件
  ↓  state 映射规则:
     pending_alerts > 0 → alert
     active_tool != ""  → executing  
     surface_count > 0  → reminder
     其他               → idle
  ↓
Orb 显示状态 + 颜色 + 动画
  ↓
点击 Orb → Surface Stack (按优先级排序的卡片列表)
  ↓
点击卡片 → ActionRegistry.execute(action, source)
  ↓
Agent / Goal / Memory
```

## 需要改动的

| # | 文件 | 改动 | 工作量 |
|---|------|------|--------|
| 1 | `apps/dashboard/views.py` | `core_status`: 改进 state 映射 + 添加 `pending_alerts` | ~10行 |
| 2 | `templates/base.html` | Surface Stack 替换当前空 overlay，卡片可点击执行 Action | ~50行 |

## Phase 1 — API state 映射

```python
# 在 core_status() 中添加:
state = "idle"
pending_alerts = SurfaceEvent.objects.filter(user=user, status="pending").count()

if pending_alerts > 0:
    state = "alert"
elif active_tool:
    state = "executing"
elif surface_count > 0:
    state = "reminder"
# else idle
```

## Phase 2 — Surface Stack

点击 Orb → 显示 Surface 卡片堆叠，每张卡片：
- 左侧色条（按 type 区分颜色）
- 图标 + 标题 + 描述
- 操作按钮：「Discuss」「Create Goal」「Dismiss」

操作按钮调用 `POST /api/actions/execute`。

## Phase 3 — Action Launcher

Surface 卡片配置：
```python
# payload 中包含 action 信息
{
    "action": "discuss",           # ActionRegistry action_id
    "source": {"type":"memory","id":12},
    "label": "Review Now",
    "icon": "stars"
}
```

前端点击按钮 → `POST /api/actions/execute` → 跳转/提示。

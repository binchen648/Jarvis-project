# Phase 4 — 贾维斯人格画像与记忆系统

## 1. Event Store（事件流）

基于已有 `infra/eventbus/Event` 升级：

```python
# 变更: Event 增加 user FK，统一所有用户行为事件
Event.user    = ForeignKey(User, null=True)  # 新增
Event.type    = "goal_session.created"       # 命名空间.动作
Event.payload = {"duration": 45, "goal_id": 3}
```

所有 App 通过 `emit_event(type, user, payload)` 统一写入，不再直接操作 Event 模型。

事件类型举例：
```
goal_session.created    wellness.recorded
goal.status_changed     content.bookmarked
chat.message.sent       trajectory.node_completed
```

## 2. Knowledge Graph（知识图谱）

基于已有 SkillNode M2M 关系扩展：

| 模型 | 说明 | 数据来源 |
|------|------|---------|
| SkillNode (已有) | 技能节点 + prerequisites + recommended_content | 预置 |
| UserLearningProgress (已有) | 用户技能进度 | 自动 |
| UserInterest (新建) | 用户兴趣标签 + 强度值 | 从 Event 聚合 |
| UserContentInteraction (新建) | 用户对内容的 bookmark/read/block | Event 写入 |

```python
class UserInterest(models.Model):
    user = FK(User)
    tag = CharField(max_length=50)        # "AI Agent", "Python"
    weight = FloatField(default=1.0)       # 兴趣强度 0-10
    source = CharField()                    # "goal" / "session" / "chat"
    last_updated = DateTimeField()
```

## 3. Persona Builder（定期压缩）

UserPersona 模型 + Celery 定时任务：

```python
class UserPersona(models.Model):
    user = OneToOneField(User)
    # LLM 生成的紧凑画像（~300 tokens）
    persona_summary = TextField(blank=True)
    # 结构化事实（用户主动告知的）
    facts = JSONField(default=list)
    # 兴趣图谱快照
    interests = JSONField(default=list)
    # 画像版本号、更新时间
    version = IntegerField(default=0)
    last_built_at = DateTimeField(null=True)
```

构建流程（Celery 每日/按需触发）：
```
1. 从 Event Store 拉取近 N 天事件
2. 从 Knowledge Graph 拉取用户兴趣/技能
3. 组装成一条 prompt → LLM 输出 ~300t 画像摘要
4. 更新 facts：从对话中提取的显式事实
5. 更新 interests：从 events 聚合兴趣标签加权
```

## 4. Memory Retrieval（按需召回）

每次对话开始时调用的服务：

```
Input:  user + 当前页面 + 对话历史(前N条)
          │
          ▼
    ┌──────────────────┐
    │ MemoryRetrieval  │
    ├──────────────────┤
    │ 1. Facts         │ ← UserPersona.facts 中命中相关事实
    │ 2. Persona       │ ← UserPersona.persona_summary
    │ 3. Graph Nodes   │ ← UserInterest + SkillNode 相关节点
    │ 4. Today Context  │ ← 今日学习/健康摘要
    └────────┬─────────┘
             ▼
    System Prompt 注入：
    [人格设定] + [画像摘要] + [相关事实] + [今日状态] + [对话历史]
    总计 ~800 tokens
```

触发方式：Chat WebSocket Consumer 建立时调用，结果拼进 system prompt。

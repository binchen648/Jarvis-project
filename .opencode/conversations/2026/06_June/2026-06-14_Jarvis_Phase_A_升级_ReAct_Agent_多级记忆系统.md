# Jarvis Phase A 升级 — ReAct Agent + 多级记忆系统

**保存时间**: 2026-06-14 14:36:00 | **对话时长**: 4h29m | **标签**: #Django #Python #Agent #架构升级

---

## 摘要

完成了 Jarvis 暑期项目的 Phase A 架构升级：将 LLM 模块从简单 Q&A 升级为 Hermes-inspired ReAct Agent 架构。新增 MemoryEntry 多级记忆模型（L1/L2/L3 + FTS5 搜索）、memory_service 全文检索服务、工具注册系统（5 个内置工具）、ReAct Agent Loop（含保护机制）、重构 System Prompt 为 Agent-aware 模式、重构 Chat Consumer 对接 Agent。迁移文件已创建，Django check 零问题。

---

## 需求与决策

| 需求 | 决策 | 原因 |
|------|------|------|
| 了解 Hermes Agent 是什么 | 调研并分析其核心能力：ReAct Loop、多级记忆、技能自创、子代理并行 | 用户想了解该框架 |
| 分析对 Jarvis 架构的升级价值 | 提出 6 大升级方向，制定 Phase A-D 路线图 | 用户项目是 Django 学习平台 |
| 执行 Phase A 升级 | ReAct Agent Loop + 多级记忆系统 + System Prompt 重构 | 最低风险、最高价值 |
| 集成方式选择 | 原生 Python/Django 实现，不安装外部 Hermes Agent | 避免 Windows 兼容性和额外依赖 |
| 复杂处理专员流程 | 完整流程（Step 0-5），含 R1-R6 审查 | 用户明确要求 |
| 子代理派遣超时 | 改用手动实现（子代理连续 3 次超时 30 分钟） | 效率考量 |
| 补上遗漏审查 | 自行完成 R4b + R5b + R6 审查报告 | 承认流程违规并补救 |

---

## 代码改动

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `infra/llm/models.py` | 修改 (+58 行) | 新增 MemoryEntry 模型 (L1/L2/L3 + 索引 + expires_at) |
| `infra/llm/memory_service.py` | 新增 (376 行) | 6 个函数: L1 画像, L2 上下文, FTS5 搜索, 存储, 过期清理, 统计 |
| `infra/llm/tools.py` | 新增 (582 行) | Tool 数据类 + ToolRegistry + 5 个内置工具 |
| `infra/llm/agent.py` | 新增 (383 行) | ReAct Agent Loop, 保护机制 (10 轮/60s/三级降级) |
| `infra/llm/system_prompt.py` | 重构 (107→215 行) | +_build_tools_section, +_build_react_instructions, 向后兼容 |
| `infra/llm/memory_retrieval.py` | 重构 | 调用 memory_service，保留 UserPersona 回退 |
| `infra/llm/persona_builder.py` | 重构 | build_persona 写入 MemoryEntry, get_persona_context 优先 memory_service |
| `apps/chat/consumers.py` | 重构 | Agent.run() 替代 LLMService.stream_chat(), 新增 _ws_send_callback |
| `infra/llm/migrations/0003_memoryentry.py` | 新增 | MemoryEntry 建表迁移 |
| `config/settings/base.py` | 修改 (+1 行) | django.contrib.postgres 加入 INSTALLED_APPS |

---

## 关键文件

- `infra/llm/models.py` — MemoryEntry 模型，L1/L2/L3 三级记忆 + expires_at 生命周期
- `infra/llm/memory_service.py` — 记忆存储服务，6 个函数覆盖 CRUD + FTS5 搜索
- `infra/llm/tools.py` — 工具注册系统，Tool 数据类 + Registry + 5 个内置工具
- `infra/llm/agent.py` — ReAct Agent Loop，含 max_iterations=10, timeout=60s, retry→skip→terminate
- `infra/llm/system_prompt.py` — 系统提示组装，支持工具描述 + ReAct 指令注入
- `apps/chat/consumers.py` — WebSocket 消费者，对接 Agent.run() + 推送中间状态

---

## 待办事项

- [x] 新增 MemoryEntry 模型
- [x] 新增 memory_service.py（6 个函数）
- [x] 新增 tools.py（工具注册 + 5 个内置工具）
- [x] 新增 agent.py（ReAct Agent Loop）
- [x] 重构 system_prompt.py
- [x] 重构 memory_retrieval.py
- [x] 重构 persona_builder.py
- [x] 重构 consumers.py 对接 Agent
- [x] 创建数据库迁移
- [x] Django check 零问题
- [ ] admin.py 注册 MemoryEntry（⚠️ Context Mining 发现）
- [ ] search_memories N+1 更新优化（建议 Phase B）

---

## 备注

### 踩过的坑
1. **子代理连续超时**：Task 4/6/7 子代理各超时 30 分钟，原因是 Django 项目文件复杂、子代理花大量时间在文件读取上。改为手动实现。
2. **Django 迁移路径**：`makemigrations` 使用 app label `llm` 而非 `infra.llm`。
3. **Pyright Q 对象类型推断**：Django 的 `Q` 对象运算符 `&`/`|` 不被 pyright 识别，用 `NOQA` 注释解决。
4. **consumers.py 两次 connect 定义**：编辑时误将 `_ws_send_callback` 插入到 `connect` 之前，导致文件有两个 `connect` 定义，最终重写整个文件解决。

### 技术决策
- 使用**查询时 SearchVector**（非存储 SearchVectorField），Phase B 再升级
- Agent 使用**非流式推理** + `send_callback` 推送中间状态，避免 2 次 API 调用
- 所有重构保持**向后兼容**：memory_retrieval/persona_builder 在 memory_service 不可用时回退到 UserPersona
- system_prompt.py 在不传 `tools_metadata` 时回退到原有行为

### 已知风险
- ⚠️ `search_memories` 每行单独 `update` access_count，数据量大时性能下降
- ⚠️ admin.py 未注册 MemoryEntry 模型

### 上线步骤
```bash
cd "D:\Jarvis project"
docker compose up -d db redis
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py runserver
```

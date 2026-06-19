# Phase 4 缺口修补计划

## Gap 1: LLM 画像注入 builder

当前 `build_persona()` 只用规则摘要。改为：
```
_collect_signals() → 有 API Key → summarize_to_persona() → UserPersona
                  → 无 API Key → _generate_summary() (规则) → UserPersona
```
修改文件: infra/llm/persona_builder.py (build_persona 函数)

## Gap 2: 事件覆盖补齐

新增 signal handlers:
- Goal post_save → GOAL_CREATED / GOAL_STATUS_CHANGED
- Message (chat) post_save → CHAT_MESSAGE_SENT
- 修改文件: infra/eventbus/signals.py, event_types.py

## Gap 3: System Prompt Token 预算

`assemble_system_prompt()` 输出前做截断：
- persona_summary > 300 tokens → 截断
- interests > 6 条 → 截断
- 总计 ~800 tokens 封顶
- 修改文件: infra/llm/system_prompt.py, memory_retrieval.py

## Gap 4: Chat 事件反馈

`ChatConsumer._save_message()` 保存 user 消息后 emit CHAT_MESSAGE_SENT
修改文件: apps/chat/consumers.py

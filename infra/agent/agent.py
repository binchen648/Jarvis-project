"""ReAct Agent Loop — 将 Jarvis 从 Q&A 升级为可执行工具的 Agent。

ReAct (Reasoning + Acting) 循环:
1. 系统提示注入记忆(L1+L2) + 工具描述 + ReAct 格式指令
2. LLM 生成: 要么直接回答(最终答案), 要么调用工具(tool_call)
3. 如果是工具调用: 执行工具 → 获取结果 → 反馈 LLM → 继续
4. 最多 MAX_ITERATIONS=10 轮，超时自动终止

用法:
    agent = Agent(user=request.user)
    result = await agent.run("帮我制定 Python 学习计划")
    print(result.content)  # Agent 的最终回答
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from django.utils import timezone

logger = logging.getLogger(__name__)

MAX_ITERATIONS_DEFAULT = 10
TIMEOUT_SECONDS_DEFAULT = 60


@dataclass
class AgentResult:
    """Agent 执行结果。"""
    content: str
    tool_calls: int = 0
    iterations: int = 0
    tokens_used: int = 0
    thinking_steps: list = field(default_factory=list)

    def __bool__(self):
        return bool(self.content)


class Agent:
    """ReAct Agent — 执行 Reason + Act 循环。

    保护机制:
    - MAX_ITERATIONS: 防止无限工具调用循环
    - TIMEOUT: 防止长时间无响应
    - Tool error 三级降级: retry(1次) → skip → terminate
    """

    MAX_ITERATIONS = MAX_ITERATIONS_DEFAULT
    TIMEOUT_SECONDS = TIMEOUT_SECONDS_DEFAULT

    def __init__(
        self,
        user,
        conversation_id: Optional[int] = None,
        send_callback=None,
        max_iterations: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        self.user = user
        self.conversation_id = conversation_id
        self.send_callback = send_callback  # async callable(event_dict)
        self.max_iterations = max_iterations or self.MAX_ITERATIONS
        self.timeout = timeout or self.TIMEOUT_SECONDS
        self.messages: list[dict] = []
        self._tool_call_count = 0

    async def run(self, user_message: str) -> AgentResult:
        """运行 ReAct Agent 循环。

        流程:
        1. 组装系统提示 (Persona + Context + Tools + ReAct Instructions)
        2. 添加用户消息到对话历史
        3. 进入循环: 调用 LLM → 判断响应 → 执行工具或返回最终答案
        4. 发送 thinking/tool_call/tool_result 中间状态到前端

        Args:
            user_message: 用户输入消息

        Returns:
            AgentResult 包含最终内容和执行统计
        """
        self.messages = []
        self._tool_call_count = 0
        thinking_steps = []
        total_tokens_used = 0

        # Step 2: 发送初始 thinking 事件
        if self.send_callback:
            await self.send_callback({
                'type': 'thinking',
                'content': '正在分析你的问题...',
                'step': 0,
            })

        # Step 3: 添加用户消息
        self.messages.append({'role': 'user', 'content': user_message})

        # Step 4: ReAct 循环
        iteration = 0
        try:
            while iteration < self.max_iterations:
                iteration += 1

                # 4a: 发送 thinking 事件
                progress_text = f"正在分析... ({iteration}/{self.max_iterations})"
                if self.send_callback:
                    await self.send_callback({
                        'type': 'thinking',
                        'content': progress_text,
                        'step': iteration,
                    })

                # 4b: 调用 LLM (流式 — chunk 已在同步线程中实时推送到前端)
                try:
                    llm_response, chunk_tokens = await asyncio.wait_for(
                        self._llm_call(), timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning("LLM call timeout at iteration %d", iteration)
                    thinking_steps.append({
                        'step': iteration, 'type': 'timeout',
                        'content': 'LLM 调用超时'
                    })
                    continue
                except Exception as e:
                    logger.error("LLM call failed at iteration %d: %s", iteration, e)
                    thinking_steps.append({
                        'step': iteration, 'type': 'error',
                        'content': 'LLM 调用失败'
                    })
                    break

                # Accumulate token usage from this iteration
                total_tokens_used += chunk_tokens

                # 4c: 解析响应
                if self._looks_like_tool_call(llm_response):
                    # Tool call 分支
                    tool_name, tool_args = self._parse_tool_call(llm_response)
                    tool_call_id = f"call_{iteration}"

                    thinking_steps.append({
                        'step': iteration, 'type': 'tool_call',
                        'content': f'调用工具: {tool_name}'
                    })

                    if self.send_callback:
                        await self.send_callback({
                            'type': 'tool_call',
                            'tool': tool_name,
                            'tool_call_id': tool_call_id,
                            'status': 'running',
                        })

                    # 4d: 执行工具
                    tool_result = await self._execute_tool_with_fallback(
                        tool_name, tool_args, tool_call_id
                    )

                    thinking_steps.append({
                        'step': iteration, 'type': 'tool_result',
                        'content': tool_result.get('error', '') if 'error' in tool_result
                                   else f'{tool_name} 执行完成'
                    })

                    if self.send_callback:
                        await self.send_callback({
                            'type': 'tool_result',
                            'tool': tool_name,
                            'tool_call_id': tool_call_id,
                            'status': 'done',
                        })

                    # 4e: 将工具结果反馈给 LLM
                    self.messages.append({
                        'role': 'assistant',
                        'content': '',  # OpenAI 格式: tool_calls 在 message 中
                        'tool_calls': [{
                            'id': tool_call_id,
                            'type': 'function',
                            'function': {
                                'name': tool_name,
                                'arguments': json.dumps(tool_args, ensure_ascii=False),
                            }
                        }] if not tool_result.get('error') else []
                    })
                    self.messages.append({
                        'role': 'tool',
                        'tool_call_id': tool_call_id,
                        'content': json.dumps(tool_result, ensure_ascii=False),
                    })

                else:
                    # 最终答案分支 — 循环结束
                    content = self._extract_final_answer(llm_response)
                    thinking_steps.append({
                        'step': iteration, 'type': 'final_answer',
                        'content': '生成最终回答'
                    })
                    return AgentResult(
                        content=content,
                        tool_calls=self._tool_call_count,
                        iterations=iteration,
                        tokens_used=total_tokens_used,
                        thinking_steps=thinking_steps,
                    )

        except asyncio.TimeoutError:
            thinking_steps.append({
                'step': 0, 'type': 'timeout',
                'content': 'Agent 运行超时'
            })

        # 超时保护 — 返回友好提示
        return AgentResult(
            content='抱歉，我花了太长时间处理这个问题，请稍后再试。',
            tool_calls=self._tool_call_count,
            iterations=iteration,
            tokens_used=total_tokens_used,
            thinking_steps=thinking_steps,
        )

    # ── 内部方法 ──────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        """组装系统提示: Persona + Context + Tools + ReAct 指令。"""
        from infra.agent.system_prompt import assemble_system_prompt

        memory_context = {}
        try:
            from infra.memory.memory_service import get_level1_profile, get_level2_context
            profile = get_level1_profile(self.user)
            ctx = get_level2_context(self.user)

            memory_context = {
                'persona_summary': profile.get('summary', ''),
                'facts': [f for f in profile.get('facts', [])],
                'interests': profile.get('interests', []),
                'today_context': '',
                'relevance_hints': '',
            }
            # 构建今日上下文
            today_parts = []
            if ctx.get('goals'):
                today_parts.append(f"进行中目标{len(ctx['goals'])}个")
            if ctx.get('skills'):
                today_parts.append(f"学习中技能{len(ctx['skills'])}个")
            memory_context['today_context'] = '，'.join(today_parts) if today_parts else ''
        except Exception:
            logger.warning("Failed to build memory context for agent")

        # 获取工具定义 (OpenAI format)
        from tools.tools import get_openai_tools
        tools_raw = get_openai_tools()
        # Unwrap from OpenAI nested format to flat format for system_prompt builder
        tools = [t["function"] for t in tools_raw]

        return assemble_system_prompt(memory_context, tools_metadata=tools)

    async def _llm_call(self) -> tuple[str, int]:
        """调用 DeepSeek API (流式, 通过 to_thread 包装)。

        在同步线程中逐块迭代 stream_chat，通过 run_coroutine_threadsafe
        将每个 chunk 实时推送到主事件循环，再经由 send_callback 发送到前端。

        Returns:
            tuple[str, int]: (content, tokens_used)
        """
        from infra.llm.llm_service import LLMService

        system_prompt = self._build_system_prompt()
        svc = LLMService()

        all_messages = []
        if system_prompt:
            all_messages.append({'role': 'system', 'content': system_prompt})
        all_messages.extend(self.messages)

        # 捕获主事件循环，供同步线程中的 run_coroutine_threadsafe 使用
        loop = asyncio.get_running_loop()

        def sync_stream(loop):
            """在同步线程中迭代流式 chunk，实时推送到主事件循环"""
            full_content = ""
            tokens_used = 0
            for event in svc.stream_chat(
                messages=all_messages, system_prompt=None,
                max_tokens=4000, temperature=0.7,
            ):
                if event.get('chunk'):
                    chunk_text = event['chunk']
                    full_content += chunk_text
                    if self.send_callback:
                        asyncio.run_coroutine_threadsafe(
                            self.send_callback({'type': 'chunk', 'content': chunk_text}),
                            loop,
                        )
                if event.get('done'):
                    tokens_used = event.get('tokens_used', 0)
                    if not full_content and event.get('content'):
                        full_content = event['content']
                    break
            return full_content, tokens_used

        return await asyncio.to_thread(sync_stream, loop)

    @staticmethod
    def _looks_like_tool_call(response: str) -> bool:
        """判断响应是否包含工具调用。

        判断逻辑:
        1. 检查响应是否以 JSON 对象开头（避免自然语言误匹配）
        2. 检查 OpenAI 原生 tool_calls 格式: {"tool_calls": [...]}
        3. 检查文本降级格式: 出现 "function_call" 或 "tool_calls"
        """
        response_stripped = response.strip()
        if not response_stripped.startswith('{'):
            return False
        if 'tool_calls' in response:
            return True
        if 'function_call' in response:
            return True
        return False

    @staticmethod
    def _parse_tool_call(response: str) -> tuple:
        """解析工具调用, 返回 (tool_name, tool_args_dict)。

        支持两种格式:
        - OpenAI 原生: {"tool_calls": [{"function": {"name": ..., "arguments": ...}}]}
        - 文本降级: {"type": "function_call", "name": ..., "arguments": {}}
        """
        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return '', {}

        # 原生 OpenAI 格式
        if 'tool_calls' in data and data['tool_calls']:
            tc = data['tool_calls'][0]
            func = tc.get('function', {})
            name = func.get('name', '')
            try:
                args = json.loads(func.get('arguments', '{}'))
            except (json.JSONDecodeError, TypeError):
                args = {}
            return name, args

        # 文本降级格式
        if data.get('type') == 'function_call':
            return data.get('name', ''), data.get('arguments', {})

        # 直接 function_call 格式
        if 'function_call' in data:
            fc = data['function_call']
            return fc.get('name', ''), fc.get('arguments', {})

        # ReAct action 格式: {"action": "tool_name", "arguments": {...}}
        if data.get('action'):
            return data['action'], data.get('arguments', {})

        return '', {}

    @staticmethod
    def _extract_final_answer(response: str) -> str:
        """从 LLM 响应中提取最终答案。

        如果响应是纯文本，直接返回。
        如果响应是 JSON（但无 tool_calls），提取 content 字段。
        """
        try:
            data = json.loads(response)
            if 'content' in data and 'tool_calls' not in data:
                return data['content']
        except (json.JSONDecodeError, TypeError):
            pass
        return response

    async def _execute_tool_with_fallback(
        self,
        tool_name: str,
        tool_args: dict,
        tool_call_id: str,
        max_retries: int = 1,
    ) -> dict:
        """执行工具，支持降级策略: retry → skip → terminate。"""
        from tools.tools import call_tool
        from asyncio import to_thread

        # 第 0 次: 正常执行
        try:
            result = await to_thread(call_tool, tool_name, user=self.user, **tool_args)
            if 'error' not in result:
                self._tool_call_count += 1
            return result
        except Exception as e:
            logger.warning("Tool %s failed (attempt 1): %s", tool_name, e)

        # 第 1 次: 重试
        if max_retries > 0:
            try:
                result = await to_thread(call_tool, tool_name, user=self.user, **tool_args)
                if 'error' not in result:
                    self._tool_call_count += 1
                return result
            except Exception as e:
                logger.warning("Tool %s retry failed: %s", tool_name, e)

        # 第 2 次: 跳过，返回友好提示
        return {
            'tool': tool_name,
            'error': f'工具 {tool_name} 执行失败，已自动跳过',
            'skipped': True,
        }

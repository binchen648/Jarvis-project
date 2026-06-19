import json
import logging

from django.core.cache import cache

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 10000
WS_RATE_LIMIT = 20  # max messages per window
WS_RATE_WINDOW = 60  # seconds


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat with Jarvis.

    Phase A 升级: 使用 ReAct Agent 替代直接 LLM 流式调用。
    Agent 每轮推理通过 _ws_send_callback 推送中间状态 (thinking/tool_call/tool_result)。
    """

    async def connect(self):
        try:
            self.user = self.scope['user']
        except KeyError:
            logger.exception("connect: no user in scope")
            await self.close()
            return

        if not self.user.is_authenticated:
            await self.close()
            return

        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        self.conversation = None
        self.system_prompt = ""

        # Load or create conversation
        try:
            self.conversation = await self._get_or_create_conversation()
        except Exception as exc:
            logger.exception("connect: _get_or_create_conversation failed: %s", exc)
            await self.close()
            return

        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'connected',
            'conversation_id': self.conversation.id,
            'conversation_title': self.conversation.title,
        }))

    async def disconnect(self, close_code):
        pass

    async def _ws_send_callback(self, event_dict: dict):
        """Agent 的 send_callback 回调 — 将 Agent 中间状态发送到 WebSocket。"""
        try:
            if event_dict.get('type') == 'thinking':
                await self.send(text_data=json.dumps({
                    'type': 'thinking',
                    'content': event_dict.get('content', ''),
                    'step': event_dict.get('step', 0),
                }))
            elif event_dict.get('type') == 'tool_call':
                await self.send(text_data=json.dumps({
                    'type': 'tool_call',
                    'tool': event_dict.get('tool', ''),
                    'tool_call_id': event_dict.get('tool_call_id', ''),
                    'status': event_dict.get('status', 'running'),
                }))
            elif event_dict.get('type') == 'tool_result':
                await self.send(text_data=json.dumps({
                    'type': 'tool_result',
                    'tool': event_dict.get('tool', ''),
                    'tool_call_id': event_dict.get('tool_call_id', ''),
                    'status': event_dict.get('status', 'done'),
                }))
        except Exception:
            pass  # Don't fail the whole agent if callback fails

    async def receive(self, text_data):
        # ── JSON parse guard ─────────────────────────────────────
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error', 'content': '无效的消息格式',
            }))
            return

        msg_type = data.get('type', 'message')

        if msg_type == 'message':
            content = data.get('content', '').strip()
            if not content:
                return

            # ── Rate limit guard (Redis-based, per-user) ────────
            try:
                key = f"rate_limit:ws:{self.user.id}"
                count = cache.incr(key)
                if count == 1:
                    cache.expire(key, WS_RATE_WINDOW)
                if count > WS_RATE_LIMIT:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'content': '发送太快了，请稍后再试。',
                    }))
                    return
            except Exception:
                pass  # Fail open if Redis is unavailable

            # ── Length limit guard ──────────────────────────────
            if len(content) > MAX_MESSAGE_LENGTH:
                await self.send(text_data=json.dumps({
                    'type': 'error', 'content': f'消息长度不能超过{MAX_MESSAGE_LENGTH}字。',
                }))
                return

            # Save user message
            user_msg = await self._save_message('user', content)

            # Echo back the user message
            await self.send(text_data=json.dumps({
                'type': 'user_message',
                'id': user_msg.id,
                'content': user_msg.content,
                'timestamp': user_msg.created_at.isoformat(),
            }))

            # ── Run ReAct Agent Loop ────────────────────────────
            try:
                from infra.agent.agent import Agent
                agent = Agent(
                    user=self.user,
                    conversation_id=self.conversation.id,
                    send_callback=self._ws_send_callback,
                )
                # Load conversation history for context
                history = await self._get_conversation_history()
                agent.messages = history

                result = await agent.run(content)

                # Save assistant response
                assistant_msg = await self._save_message(
                    'assistant',
                    result.content,
                    tokens_used=result.tokens_used,  # type: ignore[arg-type]
                )

                await self.send(text_data=json.dumps({
                    'type': 'done',
                'id': assistant_msg.id,  # type: ignore[union-attr]
                'content': result.content,
            }))
            except Exception as e:
                logger.error("Agent execution failed: %s", e)
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'content': '抱歉，AI 服务暂时不可用。',
                }))

        elif msg_type == 'title_update':
            title = data.get('title', '').strip()
            if title:
                await self._update_title(title)

    @database_sync_to_async
    def _get_or_create_conversation(self):
        from .models import Conversation
        if self.conversation_id:
            try:
                conv = Conversation.objects.get(
                    pk=self.conversation_id, user=self.user
                )
                if not conv.title:
                    conv.title = f"对话 {conv.created_at.strftime('%m/%d %H:%M')}"
                    conv.save(update_fields=['title'])
                return conv
            except Conversation.DoesNotExist:
                pass
        from django.utils import timezone
        now = timezone.now()
        conv = Conversation.objects.create(
            user=self.user,
            title=f"对话 {now.strftime('%m/%d %H:%M')}",
        )
        return conv

    @database_sync_to_async
    def _build_system_prompt(self):
        try:
            from infra.memory.retrieval import retrieve_chat_context
            from infra.agent.system_prompt import assemble_system_prompt
            context = retrieve_chat_context(self.user)
            return assemble_system_prompt(context)
        except Exception as e:
            logger.warning("Failed to build system prompt: %s", e)
            from infra.agent.system_prompt import PERSONA_SYSTEM
            return PERSONA_SYSTEM

    @database_sync_to_async
    def _save_message(self, role, content, tokens_used=None):
        from .models import Message
        return Message.objects.create(
            conversation=self.conversation,
            role=role, content=content, tokens_used=tokens_used,
        )

    @database_sync_to_async
    def _get_conversation_history(self):
        from .models import Message
        messages = Message.objects.filter(
            conversation=self.conversation
        ).order_by('created_at')[:20]
        return [
            {'role': m.role, 'content': m.content} for m in messages
        ]

    @database_sync_to_async
    def _update_title(self, title):
        self.conversation.title = title
        self.conversation.save(update_fields=['title'])

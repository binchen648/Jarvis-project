"""LLM Service — unified API client for DeepSeek (or compatible).

Provides:
- Streaming and non-streaming chat completions
- Automatic retry with exponential backoff
- Token counting and cost tracking via LLMCallLog
- Graceful fallback when API is not configured

Usage:
    service = LLMService()
    for chunk in service.stream_chat(messages):
        yield chunk
"""

import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service for chat completions. Supports streaming and non-streaming."""

    def __init__(self):
        self.api_key = self._get_api_key()
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        self.timeout = 30

    def _get_api_key(self):
        """Get API key from settings."""
        from django.conf import settings
        return getattr(settings, 'DEEPSEEK_API_KEY', '')

    @property
    def available(self):
        """Check if API is configured."""
        return bool(self.api_key)

    def chat(self, messages, system_prompt=None, max_tokens=2000, temperature=0.7):
        """Non-streaming chat completion with retry.

        Retries on transient failures (connection, timeout, 5xx, 429)
        with exponential backoff (1s, 2s, 4s). Max 3 attempts.
        No retry on non-retryable 4xx errors.

        Args:
            messages: List of dicts with 'role' and 'content'
            system_prompt: Optional system message (will be prepended)
            max_tokens: Max tokens in response
            temperature: 0-1, higher = more creative

        Returns:
            dict with 'content' (str), 'tokens_used' (int), 'duration_ms' (int)
            On failure: {'content': fallback_msg, 'tokens_used': 0, 'duration_ms': 0}
        """
        import requests

        max_attempts = 3
        start = time.time()

        for attempt in range(max_attempts):
            try:
                if not self.available:
                    return self._fallback_response("API 未配置，请设置 DEEPSEEK_API_KEY")

                all_messages = []
                if system_prompt:
                    all_messages.append({"role": "system", "content": system_prompt})
                all_messages.extend(messages)

                resp = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": all_messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False,
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                duration = int((time.time() - start) * 1000)

                result = {
                    'content': data['choices'][0]['message']['content'],
                    'tokens_used': data['usage']['total_tokens'],
                    'duration_ms': duration,
                }
                self._log_call(result, True)
                return result

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0
                if status in (429,) or status >= 500:
                    # Retry on rate limit and server errors
                    if attempt < max_attempts - 1:
                        delay = 2 ** attempt  # 1s, 2s, 4s
                        time.sleep(delay)
                        continue
                # Don't retry other 4xx — fall through to error handling
                duration = int((time.time() - start) * 1000)
                self._log_call({'content': str(e), 'tokens_used': 0, 'duration_ms': duration}, False, str(e))
                return self._fallback_response("抱歉，AI 服务暂时不可用，请稍后再试。")

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_attempts - 1:
                    delay = 2 ** attempt  # 1s, 2s, 4s
                    time.sleep(delay)
                    continue
                duration = int((time.time() - start) * 1000)
                self._log_call({'content': str(e), 'tokens_used': 0, 'duration_ms': duration}, False, str(e))
                return self._fallback_response("抱歉，AI 服务暂时不可用，请稍后再试。")

            except Exception as e:
                # Unknown error — don't retry
                duration = int((time.time() - start) * 1000)
                self._log_call({'content': str(e), 'tokens_used': 0, 'duration_ms': duration}, False, str(e))
                return self._fallback_response("抱歉，AI 服务暂时不可用，请稍后再试。")

        # All retries exhausted
        duration = int((time.time() - start) * 1000)
        self._log_call({'content': 'Max retries exceeded', 'tokens_used': 0, 'duration_ms': duration}, False, 'Max retries exceeded')
        return self._fallback_response("抱歉，AI 服务暂时不可用，请稍后再试。")

    def stream_chat(self, messages, system_prompt=None, max_tokens=2000, temperature=0.7):
        """Streaming chat completion. Generator.

        Yields:
            dict with 'chunk' (str) and 'done' (bool)
            Final yield sets 'done': True with full response
        """
        if not self.available:
            yield {'chunk': 'AI 服务未配置（DEEPSEEK_API_KEY）', 'done': True, 'content': '', 'tokens_used': 0}
            return

        start = time.time()
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        full_content = ""
        try:
            import requests
            resp = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": all_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
                timeout=self.timeout,
                stream=True,
            )
            resp.raise_for_status()

            for line in resp.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_content += content
                                yield {'chunk': content, 'done': False}
                        except json.JSONDecodeError:
                            continue

            duration = int((time.time() - start) * 1000)
            tokens_used = len(full_content) // 2  # rough estimate
            self._log_call({'content': full_content, 'tokens_used': tokens_used, 'duration_ms': duration}, True)
            yield {'chunk': '', 'done': True, 'content': full_content, 'tokens_used': tokens_used}

        except Exception as e:
            logger.error("LLM streaming failed: %s", e)
            duration = int((time.time() - start) * 1000)
            self._log_call({'content': str(e), 'tokens_used': 0, 'duration_ms': duration}, False, str(e))
            if not full_content:
                yield {'chunk': '抱歉，AI 服务暂时不可用。', 'done': True, 'content': '', 'tokens_used': 0}
            else:
                yield {'chunk': '', 'done': True, 'content': full_content, 'tokens_used': len(full_content) // 2}

    def _log_call(self, result, success, error=""):
        """Log LLM API call to LLMCallLog."""
        try:
            from .models import LLMCallLog
            LLMCallLog.objects.create(
                model_name=self.model,
                prompt_tokens=result.get('tokens_used', 0) // 2,
                completion_tokens=result.get('tokens_used', 0) // 2,
                total_tokens=result.get('tokens_used', 0),
                cost=0.0,  # Calculated later
                duration_ms=result.get('duration_ms', 0),
                success=success,
                error_message=error,
            )
        except Exception as e:
            logger.warning("Failed to log LLM call: %s", e)

    def _fallback_response(self, message):
        """Return a fallback response when API is unavailable."""
        return {'content': message, 'tokens_used': 0, 'duration_ms': 0}


def summarize_to_persona(user_signals: dict) -> str:
    """Use LLM to generate a compact persona summary from raw signals.

    This is the LLM-based version of persona_builder._generate_summary().
    Falls back to rule-based if API is not available.
    """
    from infra.memory.persona_builder import _generate_summary

    svc = LLMService()
    if not svc.available:
        return _generate_summary(user_signals)

    interests = user_signals.get('interests', [])
    if interests and isinstance(interests[0], dict):
        interest_tags = [i['tag'] for i in interests[:5]]
    else:
        interest_tags = [str(i) for i in interests[:5]]

    recent_goals = user_signals.get('recent_goals', [])[:3]

    prompt = (
        f"你是一个用户画像分析师。根据以下用户数据，生成一段极其紧凑的中文画像摘要（不超过200字）。\n"
        f"要求：自然流畅，不要罗列数据，描述用户的学习习惯、兴趣、状态。\n\n"
        f"用户近7天数据：\n"
        f"- 学习总时长：{user_signals.get('total_minutes_7d', 0)}分钟\n"
        f"- 日均学习：{user_signals.get('avg_daily_minutes', 0)}分钟\n"
        f"- 兴趣标签：{', '.join(interest_tags)}\n"
        f"- 完成技能数：{user_signals.get('completed_skills', 0)}个\n"
        f"- 进行中技能：{user_signals.get('learning_skills', 0)}个\n"
        f"- 当前目标：{'; '.join(recent_goals)}"
    )

    result = svc.chat(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.3,
    )
    return result.get('content', _generate_summary(user_signals))

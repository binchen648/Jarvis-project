"""Tool Registry — 工具注册与调用系统，支持 OpenAI Function Calling 格式及文本降级模式。

提供：
- Tool 数据类：定义工具名称、描述、参数 Schema 和执行函数
- ToolRegistry：注册、查询、批量导出（OpenAI format / text）
- 全局单例：模块级便捷函数
- 5 个内置工具：获取用户画像、搜索记忆、今日上下文、技能进度、内容搜索

用法：
    from infra.llm.tools import get_openai_tools, call_tool

    # OpenAI 格式（function calling）
    tools = get_openai_tools()

    # 文本降级格式
    desc = get_text_descriptions()

    # 执行工具
    result = call_tool("get_user_profile", user=request.user)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 1. Tool 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class Tool:
    """工具定义。

    Attributes:
        name: 工具名称，如 "get_user_profile"
        description: 工具描述（供 LLM 理解用途）
        parameters: JSON Schema 格式的参数定义
        execute: 执行函数，签名 (user, **kwargs) -> dict
        requires_user: 是否需要 user 参数（默认 True）
    """
    name: str
    description: str
    parameters: dict
    execute: Callable[..., dict]
    requires_user: bool = True


# ═══════════════════════════════════════════════════════════════
# 2. ToolRegistry 类
# ═══════════════════════════════════════════════════════════════

class ToolRegistry:
    """工具注册中心。"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册一个工具。"""
        if tool.name in self._tools:
            logger.warning("工具 '%s' 重复注册，将覆盖已有定义", tool.name)
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """按名称获取工具。"""
        return self._tools.get(name)

    def list_all(self) -> list[Tool]:
        """返回所有已注册工具列表。"""
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict]:
        """返回 OpenAI Function Calling 格式的工具定义列表。

        格式:
            {
                "type": "function",
                "function": {
                    "name": ...,
                    "description": ...,
                    "parameters": {"type": "object", "properties": ..., "required": [...]}
                }
            }
        """
        result = []
        for tool in self._tools.values():
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters.get("properties", {}),
                        "required": tool.parameters.get("required", []),
                    },
                },
            })
        return result

    def to_text_descriptions(self) -> str:
        """返回纯文本格式的工具描述（用于不支持 function calling 的降级模式）。

        格式:
            ## 可用工具

            ### get_user_profile
            描述：获取用户的学习画像...
            参数：无

            ### search_memories
            描述：搜索跨会话记忆...
            参数：query（必需）- 搜索关键词
        """
        if not self._tools:
            return "暂无可用工具。"

        lines = ["## 可用工具\n"]
        for tool in self._tools.values():
            lines.append(f"### {tool.name}")
            lines.append(f"描述：{tool.description}")

            props = tool.parameters.get("properties", {})
            required = tool.parameters.get("required", [])
            if props:
                lines.append("参数：")
                for param_name, param_schema in props.items():
                    req_flag = "（必需）" if param_name in required else "（可选）"
                    desc = param_schema.get("description", "")
                    lines.append(f"- {param_name}{req_flag}：{desc}")
            else:
                lines.append("参数：无")
            lines.append("")  # blank line between tools

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 3. 全局单例及便捷函数
# ═══════════════════════════════════════════════════════════════

_registry = ToolRegistry()


def register_tool(tool: Tool) -> None:
    """注册工具到全局注册表。"""
    _registry.register(tool)


def get_tool(name: str) -> Tool | None:
    """从全局注册表按名称获取工具。"""
    return _registry.get(name)


def get_all_tools() -> list[Tool]:
    """获取全局注册表中所有工具。"""
    return _registry.list_all()


def get_openai_tools() -> list[dict]:
    """获取 OpenAI Function Calling 格式的所有工具定义。"""
    return _registry.to_openai_tools()


def get_text_descriptions() -> str:
    """获取纯文本格式的所有工具描述（用于降级模式）。"""
    return _registry.to_text_descriptions()


def call_tool(name: str, user=None, **kwargs) -> dict:
    """便捷函数：按名称调用工具并返回结果。

    Args:
        name: 工具名称
        user: 用户实例（工具需要时必传）
        **kwargs: 工具参数

    Returns:
        工具执行结果 dict，失败时返回 {"error": ...}
    """
    tool = _registry.get(name)
    if tool is None:
        return {"error": f"未知工具：{name}"}

    # ── Schema Validation ────────────────────────────────────────
    params = tool.parameters.get('properties', {})
    required = tool.parameters.get('required', [])

    # 1. Check required params present
    for param_name in required:
        if param_name not in kwargs:
            return {"error": f"validation_error: 缺少必要参数 '{param_name}'"}

    # 2. Basic type check and coercion
    validated_args = {}
    for param_name, value in kwargs.items():
        if param_name not in params:
            continue  # silently ignore unknown params
        param_schema = params[param_name]
        param_type = param_schema.get('type', 'string')

        if param_type == 'string' and not isinstance(value, str):
            validated_args[param_name] = str(value)
        elif param_type == 'integer' and not isinstance(value, int):
            try:
                validated_args[param_name] = int(value)
            except (TypeError, ValueError):
                return {"error": f"validation_error: 参数 '{param_name}' 应为整数，收到 {type(value).__name__}"}
        elif param_type == 'number' and not isinstance(value, (int, float)):
            try:
                validated_args[param_name] = float(value)
            except (TypeError, ValueError):
                return {"error": f"validation_error: 参数 '{param_name}' 应为数字，收到 {type(value).__name__}"}
        else:
            validated_args[param_name] = value

    # ── Execute ──────────────────────────────────────────────────
    try:
        if tool.requires_user:
            if user is None:
                return {"error": f"工具 '{name}' 需要 user 参数"}
            return tool.execute(user, **validated_args)
        return tool.execute(**validated_args)
    except Exception as e:
        logger.exception("调用工具 '%s' 时发生异常", name)
        return {"error": f"工具 '{name}' 执行失败：{e}"}


# ═══════════════════════════════════════════════════════════════
# 4. 内置工具实现
# ═══════════════════════════════════════════════════════════════

# ── 4a. get_user_profile ──────────────────────────────────────

def _execute_get_user_profile(user, **kwargs) -> dict:
    """获取用户的学习画像、兴趣标签、近期目标和学习偏好。"""
    try:
        from infra.memory.memory_service import get_level1_profile, get_level2_context

        profile = get_level1_profile(user)
        context = get_level2_context(user)
        return {
            "profile": profile,
            "context": context,
        }
    except ImportError:
        # memory_service 尚未创建时的降级行为：读取 UserPersona + MemoryEntry
        return _fallback_get_user_profile(user)
    except Exception as e:
        logger.exception("获取用户画像失败")
        return {"error": f"获取用户画像失败：{e}"}


def _fallback_get_user_profile(user) -> dict:
    """降级方案：直接从数据库读取用户画像。"""
    try:
        from infra.llm.models import UserPersona

        persona = UserPersona.objects.get(user=user)
        return {
            "profile": {
                "summary": persona.persona_summary,
                "facts": persona.facts[:8],
                "interests": persona.interests[:6],
            },
            "context": {},
        }
    except UserPersona.DoesNotExist:
        return {"profile": {}, "context": {}, "note": "尚未构建用户画像"}
    except Exception as e:
        return {"error": f"获取用户画像失败：{e}"}


# ── 4b. search_memories ───────────────────────────────────────

def _execute_search_memories(user, **kwargs) -> dict:
    """搜索跨会话记忆，检索用户过去的学习记录、偏好和已知信息。"""
    query = kwargs.get("query", "")
    if not query:
        return {"error": "搜索关键词不能为空"}

    try:
        from infra.memory.memory_service import search_memories

        results = search_memories(user, query, limit=10)
        return {
            "query": query,
            "results": results,
            "count": len(results),
        }
    except ImportError:
        # memory_service 尚未创建时的降级行为：从 MemoryEntry 直接搜索
        return _fallback_search_memories(user, query)
    except Exception as e:
        logger.exception("搜索记忆失败")
        return {"error": f"搜索记忆失败：{e}"}


def _fallback_search_memories(user, query: str) -> dict:
    """降级方案：直接从 MemoryEntry 按关键词搜索。"""
    try:
        from django.db.models import Q
        from infra.llm.models import MemoryEntry

        results = list(
            MemoryEntry.objects.filter(
                user=user,
                is_active=True,
            ).filter(
                Q(content__icontains=query)
                | Q(metadata__icontains=query)
            ).order_by("-weight", "-created_at")[:10]
        )

        return {
            "query": query,
            "results": [
                {
                    "id": m.id,
                    "level": m.level,
                    "memory_type": m.memory_type,
                    "content": m.content,
                    "weight": m.weight,
                }
                for m in results
            ],
            "count": len(results),
        }
    except Exception as e:
        return {"error": f"搜索记忆失败：{e}"}


# ── 4c. get_today_context ─────────────────────────────────────

def _execute_get_today_context(user, **kwargs) -> dict:
    """获取用户今日的学习活动摘要和身心状态。"""
    try:
        from django.db.models import Sum, Count
        from django.utils import timezone

        today = timezone.localdate()
        result: dict[str, Any] = {}

        # 今日学习总时长
        try:
            from apps.goals.models import GoalSession

            agg = GoalSession.objects.filter(user=user, date=today).aggregate(
                total=Sum("duration_minutes"),
                count=Count("id"),
            )
            result["total_minutes"] = agg["total"] or 0
            result["sessions_count"] = agg["count"] or 0
        except Exception:
            logger.warning("获取 GoalSession 数据失败")
            result["total_minutes"] = 0
            result["sessions_count"] = 0

        # 今日心情
        try:
            from apps.wellness.models import WellnessRecord

            record = WellnessRecord.objects.filter(
                user=user, record_date=today
            ).first()
            if record and record.mood_score:
                mood_map = {1: "很差", 2: "较差", 3: "一般", 4: "良好", 5: "很好"}
                result["mood"] = {
                    "score": record.mood_score,
                    "label": mood_map.get(record.mood_score, "未知"),
                }
            else:
                result["mood"] = None
        except Exception:
            logger.warning("获取 WellnessRecord 数据失败")
            result["mood"] = None

        # 活跃目标数
        try:
            from apps.goals.models import Goal

            active_count = Goal.objects.filter(user=user, status="active").count()
            result["active_goals"] = active_count
        except Exception:
            logger.warning("获取 Goal 数据失败")
            result["active_goals"] = 0

        return result

    except Exception as e:
        logger.exception("获取今日上下文失败")
        return {"error": f"获取今日上下文失败：{e}"}


# ── 4d. get_skill_progress ────────────────────────────────────

def _execute_get_skill_progress(user, **kwargs) -> dict:
    """获取用户的技能学习进度。"""
    category = kwargs.get("category", "")

    try:
        from django.db.models import Count
        from apps.trajectory.models import UserLearningProgress, SkillNode

        # 基础查询
        qs = UserLearningProgress.objects.filter(user=user).select_related("skill")

        if category:
            qs = qs.filter(skill__category=category)

        # 按状态和分类聚合
        progress_list = list(qs)

        # 按状态统计
        status_counts: dict[str, int] = {}
        for p in progress_list:
            status_counts[p.status] = status_counts.get(p.status, 0) + 1

        # 按分类统计
        category_counts: dict[str, dict] = {}
        for p in progress_list:
            cat = p.skill.category
            if cat not in category_counts:
                category_counts[cat] = {"total": 0, "completed": 0, "learning": 0}
            category_counts[cat]["total"] += 1
            if p.status == "completed":
                category_counts[cat]["completed"] += 1
            elif p.status == "learning":
                category_counts[cat]["learning"] += 1

        # 详情列表（简洁版）
        details = []
        for p in progress_list[:20]:
            details.append({
                "skill_name": p.skill.name,
                "category": p.skill.category,
                "difficulty": p.skill.difficulty,
                "status": p.status,
                "predicted_completion_days": p.predicted_completion_days,
            })

        return {
            "total_skills": len(progress_list),
            "by_status": status_counts,
            "by_category": category_counts,
            "details": details,
            "filter_category": category or "全部",
        }

    except Exception as e:
        logger.exception("获取技能进度失败")
        return {"error": f"获取技能进度失败：{e}"}


# ── 4e. search_content ────────────────────────────────────────

def _execute_search_content(user, **kwargs) -> dict:
    """搜索已处理的学习内容。"""
    query = kwargs.get("query", "")
    category = kwargs.get("category", "")

    if not query:
        return {"error": "搜索关键词不能为空"}

    try:
        from django.db.models import Q
        from apps.content.models import ProcessedContent

        # 构建搜索条件
        q = Q(title__icontains=query) | Q(tags__overlap=[query])

        # 可选分类筛选
        if category:
            contents = list(
                ProcessedContent.objects.filter(q, content_type=category)  # noqa: PGH003
                .select_related("creator")
                .order_by("-quality_score", "-published_at")[:20]
            )
        else:
            contents = list(
                ProcessedContent.objects.filter(q)
                .select_related("creator")
                .order_by("-quality_score", "-published_at")[:20]
            )

        results = []
        for c in contents:
            results.append({
                "id": c.pk,
                "title": c.title,
                "url": c.url,
                "content_type": c.content_type,
                "tags": c.tags,
                "ai_summary": c.ai_summary[:200] if c.ai_summary else "",
                "quality_score": c.quality_score,
                "creator": c.creator.name if c.creator else "",
                "duration_minutes": c.duration_minutes,
            })

        return {
            "query": query,
            "category": category or "全部",
            "results": results,
            "count": len(results),
        }

    except Exception as e:
        logger.exception("搜索内容失败")
        return {"error": f"搜索内容失败：{e}"}


# ═══════════════════════════════════════════════════════════════
# 5. 注册内置工具
# ═══════════════════════════════════════════════════════════════

# 注册在文件末尾执行，避免模块级循环导入

register_tool(Tool(
    name="get_user_profile",
    description="获取用户的学习画像、兴趣标签、近期目标和学习偏好",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    execute=_execute_get_user_profile,
    requires_user=True,
))

register_tool(Tool(
    name="search_memories",
    description="搜索跨会话记忆，检索用户过去的学习记录、偏好和已知信息",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词，如「Python 异步编程」",
            },
        },
        "required": ["query"],
    },
    execute=_execute_search_memories,
    requires_user=True,
))

register_tool(Tool(
    name="get_today_context",
    description="获取用户今日的学习活动摘要和身心状态",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    execute=_execute_get_today_context,
    requires_user=True,
))

register_tool(Tool(
    name="get_skill_progress",
    description="获取用户的技能学习进度，支持按分类筛选",
    parameters={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "技能分类名称，留空查询全部。例如：编程、数学、英语",
            },
        },
        "required": [],
    },
    execute=_execute_get_skill_progress,
    requires_user=True,
))

register_tool(Tool(
    name="search_content",
    description="搜索已处理的学习内容，支持标题和标签匹配",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词，如「机器学习入门」",
            },
            "category": {
                "type": "string",
                "description": "内容分类筛选（可选）。例如：video、article、podcast",
            },
        },
        "required": ["query"],
    },
    execute=_execute_search_content,
    requires_user=True,
))


# ═══════════════════════════════════════════════════════════════
# __all__ 导出
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # 数据类
    "Tool",
    # 注册表
    "ToolRegistry",
    # 全局函数
    "register_tool",
    "get_tool",
    "get_all_tools",
    "get_openai_tools",
    "get_text_descriptions",
    "call_tool",
]

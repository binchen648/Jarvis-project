"""System Prompt Assembly — builds the system prompt for each chat session.

Assembly logic:
    [人格设定] (fixed, ~100t)
    + [用户画像] (from Persona, ~200t)
    + [实时上下文] (today + page, ~150t)
    + [对话历史] (last N messages)
"""

import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

MAX_PROMPT_TOKENS = 800  # soft cap

def _truncate(text, max_chars):
    """Truncate text to approximate token budget (1 token ≈ 2 chars for Chinese)."""
    if not text or len(text) <= max_chars * 2:
        return text
    return text[:max_chars * 2] + "..."

# ── Layer 1: 人格设定 (固定) ──────────────────────────────

PERSONA_SYSTEM = """你是贾维斯（Jarvis），一个温暖而高效的个人学习助手。

【核心原则】
- 简洁直接：不说废话，不假装人类，不刻意情感化
- 关注成长：以帮助用户学习和进步为最高优先级
- 尊重边界：不替用户做决定，只提供信息和视角
- 数据驱动：基于对用户学习习惯和目标的了解给出建议

【能力范围】
- 解答学习问题，提供学习建议
- 帮助规划学习目标和路径
- 分析学习数据，反馈学习状态
- 关心身心健康，适时提醒
- 推荐适合用户的内容"""


# ── Layer 2: 用户画像 (动态注入) ──────────────────────────

def _build_persona_section(context: dict) -> str:
    """Build persona section from MemoryRetrieval context."""
    parts = []

    summary = context.get('summary') or context.get('persona_summary', '')
    if summary:
        parts.append(f"【用户概况】{_truncate(summary, 300)}")

    if context.get('interests'):
        tags = [i['tag'] if isinstance(i, dict) else i for i in context['interests'][:6]]
        parts.append(f"【兴趣领域】{'、'.join(tags)}")

    return "\n".join(parts)


# ── Layer 3: 实时上下文 (动态注入) ─────────────────────────

def _build_context_section(context: dict) -> str:
    """Build real-time context section."""
    parts = []

    if context.get('today_context'):
        parts.append(f"【今日状态】{context['today_context']}")

    if context.get('relevance_hints'):
        parts.append(f"【当前场景】{context['relevance_hints']}")

    if context.get('facts'):
        facts = context['facts']
        safe_facts = []
        for f in (facts[:5] if isinstance(facts, list) else []):
            text = f.get('content', str(f)) if isinstance(f, dict) else str(f)
            safe_facts.append(_truncate(text, 100))
        if safe_facts:
            parts.append(f"【关于用户】{'；'.join(safe_facts)}")

    return "\n".join(parts)


# ── Layer 4: 工具描述 (动态注入) ───────────────────────────

def _build_tools_section(tools_metadata: list[dict]) -> str:
    """Build tools description section from tool metadata list.

    Args:
        tools_metadata: list of dicts, each with 'name', 'description', 'parameters'

    Returns:
        str: Formatted Chinese tool description text
    """
    if not tools_metadata:
        return ""

    lines = ["【可用工具】"]
    for i, tool in enumerate(tools_metadata, 1):
        name = tool.get("name", f"tool_{i}")
        desc = tool.get("description", "")
        params = tool.get("parameters", {})

        # Format parameters
        param_lines = []
        if isinstance(params, dict) and "properties" in params:
            props = params["properties"]
            required = set(params.get("required", []) or [])
            for pname, pinfo in props.items():
                ptype = pinfo.get("type", "string")
                pdesc = pinfo.get("description", "")
                flag = "（必填）" if pname in required else "（可选）"
                param_lines.append(f"    - {pname} ({ptype}){flag}: {pdesc}")
        elif isinstance(params, list):
            for p in params:
                pname = p.get("name", "")
                ptype = p.get("type", "string")
                flag = "（必填）" if p.get("required") else "（可选）"
                pdesc = p.get("description", "")
                param_lines.append(f"    - {pname} ({ptype}){flag}: {pdesc}")

        lines.append(f"\n{i}. {name}: {desc}")
        if param_lines:
            lines.append("   参数:")
            lines.extend(param_lines)
        else:
            lines.append("   参数: 无")

    return "\n".join(lines)


# ── Layer 5: ReAct 响应格式指令 ───────────────────────────

def _build_react_instructions() -> str:
    """Build ReAct-format response instructions in Chinese.

    Returns:
        str: Instruction text describing the Thinking→Action→Observation→Answer loop
    """
    return (
        "\n【响应格式】\n"
        "请遵循以下推理与调用格式：\n"
        "\n"
        "【思考】分析用户意图，判断是否需要使用工具。\n"
        "【行动】如需使用工具，调用格式为：\n"
        '  {"action": "工具名称", "arguments": {"参数名": "参数值"}}\n'
        "【观察】等待工具返回结果，分析输出内容。\n"
        "【回答】根据观察结果给出最终回复。\n"
        "\n"
        "【工具调用规则】\n"
        "- 每次调用仅使用一个工具，等待返回后再决定下一步\n"
        "- 同一推理链最多进行 10 轮（思考→行动→观察）\n"
        "- 若无合适工具可用，直接回答用户，不要编造工具调用\n"
        "- 工具名称和参数名必须严格匹配【可用工具】中定义的名称\n"
        "\n"
        "【降级模式】\n"
        "如果原生 function calling / tool calling 机制不可用，请按以下纯文本 JSON 格式输出工具调用：\n"
        "```json\n"
        "{\n"
        '  "type": "function_call",\n'
        '  "name": "工具名称",\n'
        '  "arguments": {\n'
        '    "参数名": "参数值"\n'
        "  }\n"
        "}\n"
        "```\n"
        "请将上述 JSON 块放在单独一行，系统将自动解析并执行。\n"
        "无论何种模式，最终回答必须以【回答】开头。"
    )


# ── Public API ────────────────────────────────────────────

def assemble_system_prompt(memory_context: dict, tools_metadata: list[dict] | None = None) -> str:
    """Assemble the full system prompt for a chat session.

    Assembly layers:
        [人格设定] (fixed PERSONA_SYSTEM)
        [用户画像] (_build_persona_section)
        [实时上下文] (_build_context_section)
        [可用工具] (_build_tools_section, conditional)
        [响应格式] (_build_react_instructions, conditional)
        [使用说明] (fixed closing note)

    Args:
        memory_context: dict from memory_retrieval.retrieve_chat_context()
        tools_metadata: optional list of tool metadata dicts.
                        Each dict: {'name': str, 'description': str, 'parameters': dict}

    Returns:
        str: Complete system prompt (~800 tokens without tools, larger with tools)
    """
    sections = [
        PERSONA_SYSTEM,
        "",
        _build_persona_section(memory_context),
        "",
        _build_context_section(memory_context),
    ]

    # Layer 4: Available tools (only when tools_metadata is provided)
    if tools_metadata:
        tool_section = _build_tools_section(tools_metadata)
        if tool_section:
            sections.extend(["", tool_section])

    # Layer 5: ReAct format instructions (only when tools are available)
    if tools_metadata:
        sections.extend(["", _build_react_instructions()])

    # Instruction for how to use this context
    sections.append(
        "\n【使用说明】\n"
        "以上信息基于用户数据自动生成，用于帮助你更好地理解用户。\n"
        "如果与当前对话无关，请忽略。用户明确提到的话题优先于画像信息。"
    )

    full_prompt = "\n".join(sections)

    # Token budget enforcement: truncate if over soft cap
    estimated_tokens = len(full_prompt) // 2
    if estimated_tokens > MAX_PROMPT_TOKENS:
        max_chars = MAX_PROMPT_TOKENS * 2
        full_prompt = full_prompt[:max_chars]
        logger.warning(
            "System prompt truncated to ~%d chars (%d tokens budget)",
            max_chars, MAX_PROMPT_TOKENS,
        )

    return full_prompt

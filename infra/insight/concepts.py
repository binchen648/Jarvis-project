from dataclasses import dataclass
from typing import Optional


@dataclass
class ConceptMeta:
    concept: str
    category: str
    type: str


TERM_INDEX: dict[str, ConceptMeta] = {
    "mcp": ConceptMeta("AI Agent", "Developer Tool", "Protocol"),
    "cursor": ConceptMeta("AI Agent", "Developer Tool", "Code Editor"),
    "codex": ConceptMeta("AI Agent", "Developer Tool", "AI Assistant"),
    "claude code": ConceptMeta("AI Agent", "Developer Tool", "CLI Tool"),
    "autogpt": ConceptMeta("AI Agent", "Developer Tool", "Framework"),
    "langgraph": ConceptMeta("AI Agent", "Developer Tool", "Framework"),
    "crewai": ConceptMeta("AI Agent", "Developer Tool", "Framework"),
    "react agent": ConceptMeta("AI Agent", "Architecture", "Pattern"),
    "multi agent": ConceptMeta("AI Agent", "Architecture", "Pattern"),
    "tool use": ConceptMeta("AI Agent", "Capability", "Pattern"),
    "function calling": ConceptMeta("AI Agent", "Capability", "Pattern"),
    "python": ConceptMeta("Python Web", "Language", "General"),
    "django": ConceptMeta("Python Web", "Backend", "Framework"),
    "fastapi": ConceptMeta("Python Web", "Backend", "Framework"),
    "flask": ConceptMeta("Python Web", "Backend", "Framework"),
    "react": ConceptMeta("Frontend", "Frontend", "Framework"),
    "vue": ConceptMeta("Frontend", "Frontend", "Framework"),
    "javascript": ConceptMeta("Frontend", "Frontend", "Language"),
    "typescript": ConceptMeta("Frontend", "Frontend", "Language"),
    "leetcode": ConceptMeta("Algorithms", "Practice", "Platform"),
    "algorithm": ConceptMeta("Algorithms", "Core", "Concept"),
    "data structure": ConceptMeta("Algorithms", "Core", "Concept"),
    "docker": ConceptMeta("DevOps", "Infrastructure", "Container"),
    "kubernetes": ConceptMeta("DevOps", "Infrastructure", "Orchestrator"),
    "git": ConceptMeta("Developer Experience", "Tool", "VCS"),
    "github": ConceptMeta("Developer Experience", "Platform", "VCS"),
    "vscode": ConceptMeta("Developer Experience", "Tool", "Editor"),
}


def lookup(term: str) -> Optional[ConceptMeta]:
    return TERM_INDEX.get(term.lower().strip())


def extract_from_text(text: str) -> list[ConceptMeta]:
    found = []
    text_lower = text.lower()
    for term, meta in TERM_INDEX.items():
        if term in text_lower:
            found.append(meta)
    return found

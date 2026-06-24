from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class ConceptMeta:
    concept: str
    category: str
    type: str


# Term → regex patterns + ConceptMeta
# Uses re.search() with word boundaries to avoid substring match issues
# Each term has aliases for different formats (spaces, hyphens, etc.)
TERM_PATTERNS: list[tuple[re.Pattern, ConceptMeta]] = [
    # ── AI Agent Ecosystem ──
    (re.compile(r'\bmcp\b', re.IGNORECASE), ConceptMeta("AI Agent", "Developer Tool", "Protocol")),
    (re.compile(r'\bcursor\b', re.IGNORECASE), ConceptMeta("AI Agent", "Developer Tool", "Code Editor")),
    (re.compile(r'\bcodex\b', re.IGNORECASE), ConceptMeta("AI Agent", "Developer Tool", "AI Assistant")),
    (re.compile(r'(?:claude.code|claude-code|claudecode)', re.IGNORECASE), ConceptMeta("AI Agent", "Developer Tool", "CLI Tool")),
    (re.compile(r'\bautogpt\b', re.IGNORECASE), ConceptMeta("AI Agent", "Developer Tool", "Framework")),
    (re.compile(r'\blanggraph\b', re.IGNORECASE), ConceptMeta("AI Agent", "Developer Tool", "Framework")),
    (re.compile(r'\bcrewai\b', re.IGNORECASE), ConceptMeta("AI Agent", "Developer Tool", "Framework")),
    (re.compile(r'(?:react.agent|react-agent)', re.IGNORECASE), ConceptMeta("AI Agent", "Architecture", "Pattern")),
    (re.compile(r'(?:multi.agent|multi-agent|multiagent)', re.IGNORECASE), ConceptMeta("AI Agent", "Architecture", "Pattern")),
    (re.compile(r'\btool.use\b', re.IGNORECASE), ConceptMeta("AI Agent", "Capability", "Pattern")),
    (re.compile(r'\bfunction.calling\b', re.IGNORECASE), ConceptMeta("AI Agent", "Capability", "Pattern")),
    
    # ── Python Web ──
    (re.compile(r'\bpython\b', re.IGNORECASE), ConceptMeta("Python Web", "Language", "General")),
    (re.compile(r'\bdjango\b', re.IGNORECASE), ConceptMeta("Python Web", "Backend", "Framework")),
    (re.compile(r'\bfastapi\b', re.IGNORECASE), ConceptMeta("Python Web", "Backend", "Framework")),
    (re.compile(r'\bflask\b', re.IGNORECASE), ConceptMeta("Python Web", "Backend", "Framework")),
    
    # ── Frontend ──
    (re.compile(r'\breact\b', re.IGNORECASE), ConceptMeta("Frontend", "Frontend", "Framework")),
    (re.compile(r'\bvue\b', re.IGNORECASE), ConceptMeta("Frontend", "Frontend", "Framework")),
    (re.compile(r'\bjavascript\b', re.IGNORECASE), ConceptMeta("Frontend", "Frontend", "Language")),
    (re.compile(r'\btypescript\b', re.IGNORECASE), ConceptMeta("Frontend", "Frontend", "Language")),
    
    # ── Algorithms ──
    (re.compile(r'\bleetcode\b', re.IGNORECASE), ConceptMeta("Algorithms", "Practice", "Platform")),
    (re.compile(r'\balgorithm\b', re.IGNORECASE), ConceptMeta("Algorithms", "Core", "Concept")),
    (re.compile(r'\bdata.structure\b', re.IGNORECASE), ConceptMeta("Algorithms", "Core", "Concept")),
    
    # ── DevOps ──
    (re.compile(r'\bdocker\b', re.IGNORECASE), ConceptMeta("DevOps", "Infrastructure", "Container")),
    (re.compile(r'\bkubernetes\b', re.IGNORECASE), ConceptMeta("DevOps", "Infrastructure", "Orchestrator")),
    (re.compile(r'\bgit\b', re.IGNORECASE), ConceptMeta("Developer Experience", "Tool", "VCS")),
    (re.compile(r'\bgithub\b', re.IGNORECASE), ConceptMeta("Developer Experience", "Platform", "VCS")),
    (re.compile(r'\bvscode\b', re.IGNORECASE), ConceptMeta("Developer Experience", "Tool", "Editor")),
]


def extract_from_text(text: str) -> set[ConceptMeta]:
    """Extract concepts from text using regex matching.
    
    Returns a SET (deduplicated) — each concept appears at most once per text.
    """
    found = set()
    for pattern, meta in TERM_PATTERNS:
        if pattern.search(text):
            found.add(meta)
    return found

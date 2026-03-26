"""Step 2b: Behavior Typing — assign behavior_type before schema mapping.

This is a semantic buffer layer: it stabilizes the mapping input
by assigning behavior_type (semantic category) before schema mapping.
"""
from __future__ import annotations
import logging
import re
from typing import Optional
from agentic_mindset.compiler.schemas import (
    CanonicalBehavior,
    BehaviorType,
)

logger = logging.getLogger(__name__)


TYPING_SYSTEM = """You are classifying canonical behaviors into semantic types.

Each behavior must be assigned exactly ONE type:
- core_principle: foundational belief that drives all other behavior (e.g., "clarity is supreme value")
- decision_policy: how this person approaches decisions (e.g., "commits at 70% information")
- communication: how they communicate interpersonally (e.g., "direct to the point of bluntness")
- conflict: how they handle conflict (e.g., "destroys rivals completely")
- emotional: emotional patterns and triggers (e.g., "baseline calm, erupts when blocked")
- drive: what they are motivated by (e.g., "legacy over profit")
- execution: how they get things done (e.g., "personally leads from the front")

Choose the most central type — the one that best describes the BEHAVIOR, not the person."""


TYPING_USER = """Classify each canonical behavior into a behavior_type.

Output format:
```yaml
typing_results:
  - canonical_id: cb-001
    behavior_type: communication
    note: brief reasoning
  - canonical_id: cb-002
    behavior_type: decision_policy
    note: ...
```"""


def build_typing_prompt(canonicals: list[CanonicalBehavior]) -> str:
    lines = ["Canonical behaviors:\n"]
    for cb in canonicals:
        lines.append(f"- id: {cb.id}")
        lines.append(f"  canonical_form: {cb.canonical_form}")
        lines.append(f"  status: {cb.status.value}")
        lines.append(f"  variants: {', '.join(v.text[:60] for v in cb.variants[:3])}")
        lines.append("")
    return "\n".join(lines)


def type_behaviors(canonicals: list[CanonicalBehavior], llm) -> list[CanonicalBehavior]:
    """Run Step 2b: assign behavior_type to each canonical behavior."""
    from agentic_mindset.compiler.llm import LLMClient
    if not isinstance(llm, LLMClient):
        raise TypeError("llm must be an LLMClient instance")

    if not canonicals:
        return canonicals

    prompt = build_typing_prompt(canonicals)
    try:
        result = llm.complete_structured(prompt, system=TYPING_SYSTEM)
    except RuntimeError:
        # Fallback: try to extract behavior types from free-form explanation response
        raw = llm.complete(prompt, system=TYPING_SYSTEM)
        results_map = _parse_typing_from_text(raw, canonicals)
    else:
        # Handle result being a list (markdown format) or string
        results_map = {}
        if isinstance(result, dict):
            typing_list = result.get("typing_results", [])
        elif isinstance(result, list):
            typing_list = result
        else:
            typing_list = []

        for r in typing_list:
            if isinstance(r, dict) and "canonical_id" in r:
                results_map[r["canonical_id"]] = BehaviorType(r["behavior_type"])

    for cb in canonicals:
        if cb.id in results_map:
            cb.behavior_type = results_map[cb.id]

    return canonicals


# ---------------------------------------------------------------------------
# Fallback parser for free-form explanation-style LLM responses
# ---------------------------------------------------------------------------

import re
from typing import Optional


# All valid behavior type keywords (order matters — most specific first)
_VALID_TYPES = ["core_principle", "decision_policy", "communication", "conflict", "emotional", "drive", "execution"]


def _parse_typing_from_text(raw: str, canonicals: list[CanonicalBehavior]) -> dict[str, BehaviorType]:
    """Extract behavior_type assignments from a free-form LLM explanation.

    Handles MiniMax-style responses where the model explains its reasoning
    instead of returning structured YAML/JSON.

    Strategy:
    1. Try to find each canonical ID in the response and look for a type keyword nearby
    2. If no canonical IDs are found, scan the entire response for type keywords
       and assign them to canonicals in order (best-effort alignment)
    """
    result: dict[str, BehaviorType] = {}
    raw_lower = raw.lower()

    # First pass: try to find canonical IDs and their associated type keywords
    ids_found = 0
    for cb in canonicals:
        cb_id = cb.id.lower()
        cb_pos = raw_lower.find(cb_id)
        if cb_pos == -1:
            cb_pos = raw_lower.find(cb_id.replace("-", ""))

        if cb_pos == -1:
            continue

        ids_found += 1
        window_start = max(0, cb_pos - 100)
        window_end = min(len(raw), cb_pos + 200)
        window = raw_lower[window_start:window_end]

        found_type: Optional[str] = None
        for bt_keyword in _VALID_TYPES:
            if re.search(r'\b' + bt_keyword + r'\b', window):
                found_type = bt_keyword
                break

        if found_type:
            result[cb.id] = BehaviorType(found_type)

    # Second pass: if no canonical IDs were found, scan entire response for type keywords
    # and assign them to canonicals in order (one type per canonical)
    if ids_found == 0:
        logger.warning(
            "typer: no canonical IDs found in LLM response; "
            "falling back to positional type keyword scan. "
            "Response preview: %s",
            raw[:300],
        )
        type_positions: list[tuple[int, str]] = []  # (position, type_keyword)
        for bt_keyword in _VALID_TYPES:
            pos = 0
            while True:
                pos = raw_lower.find(bt_keyword, pos)
                if pos == -1:
                    break
                type_positions.append((pos, bt_keyword))
                pos += 1

        # Sort by position and assign to canonicals in order
        type_positions.sort(key=lambda x: x[0])
        for i, cb in enumerate(canonicals):
            if i < len(type_positions):
                _, bt_keyword = type_positions[i]
                result[cb.id] = BehaviorType(bt_keyword)

    return result

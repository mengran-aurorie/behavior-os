"""Step 3: Schema Mapping — map canonical behaviors to BehaviorOS schema slots."""
from __future__ import annotations
from agentic_mindset.compiler.schemas import (
    CanonicalBehavior,
    BehaviorType,
    BehaviorStatus,
    SlotWithProvenance,
    Confidence,
)


# Maps behavior_type to possible schema slot paths
BEHAVIOR_TYPE_TO_SLOTS: dict[BehaviorType, list[str]] = {
    BehaviorType.CORE_PRINCIPLE: ["core_principles"],
    BehaviorType.DECISION_POLICY: ["decision_framework.heuristics", "decision_framework.default_strategy"],
    BehaviorType.COMMUNICATION: ["interpersonal_style.communication"],
    BehaviorType.CONFLICT: ["conflict_style.default"],
    BehaviorType.EMOTIONAL: ["emotional_tendencies.baseline_mood", "emotional_tendencies.stress_response"],
    BehaviorType.DRIVE: ["drives.name"],
    BehaviorType.EXECUTION: ["work_patterns", "behavior.execution_style"],
}


MAPPING_SYSTEM = """You are mapping canonical behaviors to BehaviorOS schema slots.

BehaviorOS schema slots:
- core_principles: foundational beliefs (list of {description, detail, confidence})
- decision_framework.heuristics: list of short decision rules (strings)
- decision_framework.default_strategy: how they generally approach decisions (string)
- interpersonal_style.communication: communication style (string or ConditionalSlot)
- conflict_style.default: default conflict approach (string)
- emotional_tendencies.baseline_mood: default emotional state (string)
- emotional_tendencies.stress_response: how they respond to stress (string)
- drives: motivations (list of {name, intensity, description})
- work_patterns: how they work (list of strings)

For each behavior:
1. Pick the best-fit slot path
2. Write the field value in the correct format
3. Mark confidence: high (direct mapping) | medium (interpretation) | low (uncertain)
4. Mark for review if medium or low confidence"""


MAPPING_USER_TPL = """Map {count} canonical behaviors to BehaviorOS schema slots.

Behavior types:
- core_principle: foundational belief
- decision_policy: how they decide
- communication: how they communicate
- conflict: how they handle conflict
- emotional: emotional patterns
- drive: what motivates them
- execution: how they execute

Output format:
```yaml
mappings:
  - canonical_id: cb-001
    slot_path: interpersonal_style.communication
    field_value: "direct, unvarnished, refuses to soften bad news"
    confidence: high
    needs_review: false
  - canonical_id: cb-002
    slot_path: decision_framework.heuristics
    field_value: "When facing a decision, ask: is this truly necessary?"
    confidence: medium
    needs_review: true
```

Behavior types provided. Canonical behaviors:
{canonicals_block}
"""


def build_mapping_prompt(canonicals: list[CanonicalBehavior]) -> str:
    lines = []
    for cb in canonicals:
        bt = cb.behavior_type.value if cb.behavior_type else "unknown"
        lines.append(f"- id: {cb.id}")
        lines.append(f"  type: {bt}")
        lines.append(f"  canonical: {cb.canonical_form}")
        lines.append(f"  status: {cb.status.value}")
        lines.append(f"  variants: {', '.join(v.text[:60] for v in cb.variants[:3])}")
        lines.append("")
    return "\n".join(lines)


def map_to_schema(
    canonicals: list[CanonicalBehavior],
    llm,
) -> list[tuple[CanonicalBehavior, str, str, Confidence, bool]]:
    """Run Step 3: map canonical behaviors to schema slots.

    Returns list of (canonical, slot_path, field_value, confidence, needs_review).
    """
    from agentic_mindset.compiler.llm import LLMClient
    if not isinstance(llm, LLMClient):
        raise TypeError("llm must be an LLMClient instance")

    if not canonicals:
        return []

    # Simple cases: direct type-based mapping for high-confidence confirmed behaviors
    simple_mappings: list[tuple[CanonicalBehavior, str, str, Confidence, bool]] = []

    # Complex cases: ask LLM for ambiguous/contradictory
    complex_canonicals = [cb for cb in canonicals if cb.status != BehaviorStatus.CONFIRMED]

    if complex_canonicals:
        prompt = MAPPING_USER_TPL.format(
            count=len(complex_canonicals),
            canonicals_block=build_mapping_prompt(complex_canonicals),
        )
        result = llm.complete_structured(prompt, system=MAPPING_SYSTEM)
        for r in result.get("mappings", []):
            cid = r["canonical_id"]
            cb = next((c for c in complex_canonicals if c.id == cid), None)
            if cb:
                conf = Confidence(r.get("confidence", "medium"))
                simple_mappings.append((
                    cb,
                    r.get("slot_path", ""),
                    r.get("field_value", ""),
                    conf,
                    r.get("needs_review", conf != Confidence.HIGH),
                ))

    # For confirmed behaviors, use direct slot suggestion
    for cb in canonicals:
        if cb.status == BehaviorStatus.CONFIRMED and not any(m[0].id == cb.id for m in simple_mappings):
            suggested = _suggest_slot(cb)
            confidence = Confidence.HIGH if cb.evidence_count >= 2 else Confidence.MEDIUM
            needs_review = cb.evidence_count < 2
            simple_mappings.append((cb, suggested, cb.canonical_form, confidence, needs_review))

    return simple_mappings


def _suggest_slot(cb: CanonicalBehavior) -> str:
    """Suggest a slot path based on behavior type."""
    if cb.behavior_type == BehaviorType.CORE_PRINCIPLE:
        return "core_principles"
    elif cb.behavior_type == BehaviorType.DECISION_POLICY:
        return "decision_framework.heuristics"
    elif cb.behavior_type == BehaviorType.COMMUNICATION:
        return "interpersonal_style.communication"
    elif cb.behavior_type == BehaviorType.CONFLICT:
        return "conflict_style.default"
    elif cb.behavior_type == BehaviorType.EMOTIONAL:
        return "emotional_tendencies.baseline_mood"
    elif cb.behavior_type == BehaviorType.DRIVE:
        return "drives"
    elif cb.behavior_type == BehaviorType.EXECUTION:
        return "work_patterns"
    else:
        return "core_principles"

from __future__ import annotations
from abc import ABC, abstractmethod

from agentic_mindset.ir.models import BehaviorIR, ResolvedSlot, ConditionModifier
from agentic_mindset.ir.conditions import CONDITION_TEXT_EN


class InjectRenderer(ABC):
    """Base class for all inject-path renderers. Subclass per target runtime."""

    @abstractmethod
    def render(self, ir: BehaviorIR) -> str: ...


class ClaudeRenderer(InjectRenderer):
    """Renders BehaviorIR for `claude --append-system-prompt-file`."""

    def __init__(self, debug: bool = False):
        self.debug = debug

    def render(self, ir: BehaviorIR) -> str:
        sections: list[str] = [ir.preamble.text, ""]

        # GROUNDEDNESS POLICY — prevents persona fabrications in blends
        sections.append("GROUNDEDNESS POLICY:")
        sections.append("- Persona overlays shape decision behavior and interaction style.")
        sections.append("- Do NOT invent biographical facts, quotes, or anecdotes.")
        sections.append("- If referencing historical actions, ensure they are publicly documented.")
        sections.append("")

        # DECISION POLICY
        if ir.decision_policy_items:
            sections.append("DECISION POLICY:")
            sections.extend(f"- {item}" for item in ir.decision_policy_items)
            sections.append("")

        # UNCERTAINTY HANDLING
        uh_lines: list[str] = []
        if ir.risk_tolerance or ir.time_horizon:
            uh_lines.append(
                f"risk_tolerance: {ir.risk_tolerance} | time_horizon: {ir.time_horizon}"
            )
        if ir.stress_response:
            uh_lines.extend(self._render_slot("Stress response", ir.stress_response))
        if uh_lines:
            sections.append("UNCERTAINTY HANDLING:")
            sections.extend(f"- {line}" for line in uh_lines)
            sections.append("")

        # INTERACTION RULES
        ir_lines: list[str] = []
        if ir.communication:
            ir_lines.extend(self._render_slot("Communication", ir.communication))
        if ir.leadership:
            ir_lines.extend(self._render_slot("Leadership", ir.leadership))
        if ir.conflict_style:
            ir_lines.extend(self._render_slot("Under conflict", ir.conflict_style))
        if ir_lines:
            sections.append("INTERACTION RULES:")
            for i, line in enumerate(ir_lines):
                # First line gets "- " prefix; continuation lines (indented) keep their format
                if i == 0 or line.startswith("  "):
                    sections.append(line if i > 0 else f"- {line}")
                else:
                    sections.append(f"- {line}")
            sections.append("")

        # ANTI-PATTERNS
        if ir.anti_patterns:
            sections.append("ANTI-PATTERNS:")
            sections.extend(f"- {ap}" for ap in ir.anti_patterns)
            sections.append("")

        # STYLE
        style_lines: list[str] = []
        if ir.tone:
            style_lines.extend(self._render_slot("Tone", ir.tone))
        if ir.vocabulary_preferred:
            style_lines.append(f"Preferred: {', '.join(ir.vocabulary_preferred)}")
        if ir.vocabulary_avoided:
            style_lines.append(f"Avoided: {', '.join(ir.vocabulary_avoided)}")
        if ir.sentence_style:
            style_lines.extend(self._render_slot("Sentence style", ir.sentence_style))
        if style_lines:
            sections.append("STYLE:")
            sections.extend(f"- {line}" for line in style_lines)

        return "\n".join(sections).strip()

    def _render_slot(self, label: str, slot: ResolvedSlot) -> list[str]:
        if not slot.primary:
            return []
        primary_line = f"{label}: {slot.primary.value}"

        normal = [m for m in slot.modifiers if m.provenance in ("pack", "fallback")]
        weak   = [m for m in slot.modifiers if m.provenance == "weak"]

        _known = {"pack", "fallback", "weak"}
        for m in slot.modifiers:
            if m.provenance not in _known:
                raise ValueError(f"Unknown modifier provenance: {m.provenance!r}")

        if normal:
            if len(normal) == 1:
                cond = self._render_conditions(normal[0])
                cond_part = f" {cond}" if cond else ""
                return [f"{primary_line}; except {normal[0].value}{cond_part}".strip()]
            # Multiple normal modifiers → sub-list
            lines = [f"{primary_line}; except:"]
            for mod in normal:
                cond = self._render_conditions(mod)
                cond_part = f" {cond}" if cond else ""
                lines.append(f"  - {mod.value}{cond_part}")
            return lines

        if weak:
            values = ", ".join(m.value for m in weak)
            return [f"{primary_line}; slight tendency toward {values} in some situations"]

        return [primary_line]

    def _render_conditions(self, modifier: ConditionModifier) -> str:
        if not modifier.condition:
            return ""
        texts: list[str] = []
        for label in modifier.condition:
            if label not in CONDITION_TEXT_EN:
                raise ValueError(
                    f"Unknown condition label: {label!r}. "
                    "Add to CONDITION_TEXT_EN and ConditionLabel enum before using."
                )
            texts.append(CONDITION_TEXT_EN[label])
        joiner = " and " if modifier.conjunction == "all" else " or "
        return joiner.join(texts)


_RENDERERS: dict[str, type[InjectRenderer]] = {
    "inject": ClaudeRenderer,
}


def render_for_runtime(ir: BehaviorIR, fmt: str) -> str:
    """Renderer factory for the inject path. Raises ValueError for unknown formats."""
    if fmt not in _RENDERERS:
        raise ValueError(f"Unknown runtime format: {fmt!r}")
    return _RENDERERS[fmt]().render(ir)

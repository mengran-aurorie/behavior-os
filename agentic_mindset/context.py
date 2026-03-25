from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from agentic_mindset.pack import CharacterPack
    from agentic_mindset.fusion import FusionReport


def _build_preamble(
    weighted_packs: list[tuple["CharacterPack", float]],
    show_weights: bool = True,
) -> str:
    """Build preamble text from weighted character packs."""
    if show_weights:
        names = [f"{p.meta.name} ({w:.0%})" for p, w in weighted_packs]
    else:
        names = [p.meta.name for p, _ in weighted_packs]
    return "You embody a synthesized mindset drawing from: " + ", ".join(names) + "."


@dataclass
class ContextBlock:
    preamble: str
    thinking_framework: list[str]
    personality: list[str]
    behavioral_tendencies: list[str]
    voice_and_style: list[str]

    @classmethod
    def from_packs(
        cls,
        weighted_packs: list[tuple["CharacterPack", float]],
        show_weights: bool = True,
        report: "FusionReport | None" = None,
    ) -> "ContextBlock":
        """Build a ContextBlock from one or more (pack, weight) pairs.

        Packs are expected to be pre-sorted by descending weight (highest-weight first).
        Items from earlier packs appear first in merged list fields.
        show_weights=False omits percentages from the preamble (used by sequential strategy).
        When report is provided, duplicate items skipped during dedup are appended to
        report.removed_items.
        """
        preamble = _build_preamble(weighted_packs, show_weights)

        thinking: list[str] = []
        personality: list[str] = []
        behavioral: list[str] = []
        voice: list[str] = []

        for pack, _ in weighted_packs:
            m = pack.mindset
            for p in m.core_principles:
                line = f"{p.description}: {p.detail}"
                if line not in thinking:
                    thinking.append(line)
                elif report is not None:
                    report.removed_items.append(line)
            for tp in m.thinking_patterns:
                if tp not in thinking:
                    thinking.append(tp)
                elif report is not None:
                    report.removed_items.append(tp)
            for mm in m.mental_models:
                line = f"{mm.name} — {mm.description}"
                if line not in thinking:
                    thinking.append(line)
                elif report is not None:
                    report.removed_items.append(line)

            pers = pack.personality
            for t in pers.traits:
                line = f"{t.name} (intensity {t.intensity}): {t.description}"
                if line not in personality:
                    personality.append(line)
                elif report is not None:
                    report.removed_items.append(line)
            for d in pers.drives:
                s = str(d)
                if s not in personality:
                    personality.append(s)
                elif report is not None:
                    report.removed_items.append(s)

            beh = pack.behavior
            for wp in beh.work_patterns:
                if wp not in behavioral:
                    behavioral.append(wp)
                elif report is not None:
                    report.removed_items.append(wp)
            for es in beh.execution_style:
                if es not in behavioral:
                    behavioral.append(es)
                elif report is not None:
                    report.removed_items.append(es)
            if beh.conflict_style not in behavioral:
                behavioral.append(beh.conflict_style)
            elif report is not None:
                report.removed_items.append(str(beh.conflict_style))

            v = pack.voice
            tone_line = f"Tone: {v.tone}"
            if tone_line not in voice:
                voice.append(tone_line)
            elif report is not None:
                report.removed_items.append(tone_line)
            for phrase in v.signature_phrases:
                quoted = f'"{phrase}"'
                if quoted not in voice:
                    voice.append(quoted)
                elif report is not None:
                    report.removed_items.append(quoted)

        return cls(
            preamble=preamble,
            thinking_framework=thinking,
            personality=personality,
            behavioral_tendencies=behavioral,
            voice_and_style=voice,
        )

    def to_prompt(self, output_format: Literal["plain_text", "xml_tagged"] = "plain_text") -> str:
        if output_format == "xml_tagged":
            return self._render_xml()
        return self._render_plain()

    def _render_plain(self) -> str:
        lines = [self.preamble, ""]
        if self.thinking_framework:
            lines += ["THINKING FRAMEWORK:"] + [f"- {l}" for l in self.thinking_framework] + [""]
        if self.personality:
            lines += ["PERSONALITY:"] + [f"- {l}" for l in self.personality] + [""]
        if self.behavioral_tendencies:
            lines += ["BEHAVIORAL TENDENCIES:"] + [f"- {l}" for l in self.behavioral_tendencies] + [""]
        if self.voice_and_style:
            lines += ["VOICE & STYLE:"] + [f"- {l}" for l in self.voice_and_style]
        return "\n".join(lines).strip()

    def _render_xml(self) -> str:
        def section(tag, items):
            if not items:
                return ""
            inner = "\n".join(f"  <item>{i}</item>" for i in items)
            return f"<{tag}>\n{inner}\n</{tag}>"

        parts = ["<character-context>", f"<preamble>{self.preamble}</preamble>"]
        parts.append(section("thinking-framework", self.thinking_framework))
        parts.append(section("personality", self.personality))
        parts.append(section("behavioral-tendencies", self.behavioral_tendencies))
        parts.append(section("voice-and-style", self.voice_and_style))
        parts.append("</character-context>")
        return "\n".join(p for p in parts if p)


def render_inject_block(
    weighted_packs: list[tuple["CharacterPack", float]],
    show_weights: bool = True,
) -> str:
    """Render a 5-section behavioral instruction block from weighted character packs.

    Unlike ContextBlock/to_prompt(), this function reads typed schema fields directly
    (decision_framework, interpersonal_style, vocabulary, etc.) which are not preserved
    in ContextBlock's flat string lists.

    Caller precondition: weighted_packs is non-empty.
    Sections: DECISION POLICY, UNCERTAINTY HANDLING, INTERACTION RULES,
              ANTI-PATTERNS (omitted if empty), STYLE.
    Dedup rule: first-seen-wins across packs iterated in weight-descending order.
    """
    preamble = _build_preamble(weighted_packs, show_weights)

    lines = [preamble, ""]

    # --- DECISION POLICY ---
    dp_items: list[str] = []
    for pack, _ in weighted_packs:
        m = pack.mindset
        sorted_principles = sorted(
            m.core_principles,
            key=lambda cp: cp.confidence if cp.confidence is not None else -1.0,
            reverse=True,
        )
        for principle in sorted_principles:
            item = f"{principle.description}: {principle.detail}"
            if item not in dp_items:
                dp_items.append(item)
        approach_item = f"Approach: {m.decision_framework.approach}"
        if approach_item not in dp_items:
            dp_items.append(approach_item)
    if dp_items:
        lines += ["DECISION POLICY:"] + [f"- {i}" for i in dp_items] + [""]

    # --- UNCERTAINTY HANDLING ---
    uh_items: list[str] = []
    for pack, _ in weighted_packs:
        m = pack.mindset
        p = pack.personality
        risk_line = (
            f"risk_tolerance: {m.decision_framework.risk_tolerance} | "
            f"time_horizon: {m.decision_framework.time_horizon}"
        )
        if risk_line not in uh_items:
            uh_items.append(risk_line)
        stress_item = f"Stress response: {p.emotional_tendencies.stress_response}"
        if stress_item not in uh_items:
            uh_items.append(stress_item)
    if uh_items:
        lines += ["UNCERTAINTY HANDLING:"] + [f"- {i}" for i in uh_items] + [""]

    # --- INTERACTION RULES ---
    ir_items: list[str] = []
    for pack, _ in weighted_packs:
        p = pack.personality
        b = pack.behavior
        for item in [
            f"Communication: {p.interpersonal_style.communication}",
            f"Leadership: {p.interpersonal_style.leadership}",
            f"Under conflict: {b.conflict_style}",
        ]:
            if item not in ir_items:
                ir_items.append(item)
    if ir_items:
        lines += ["INTERACTION RULES:"] + [f"- {i}" for i in ir_items] + [""]

    # --- ANTI-PATTERNS (omitted entirely when all packs have empty anti_patterns) ---
    ap_items: list[str] = []
    for pack, _ in weighted_packs:
        for ap in pack.behavior.anti_patterns:
            if ap not in ap_items:
                ap_items.append(ap)
    if ap_items:
        lines += ["ANTI-PATTERNS:"] + [f"- {i}" for i in ap_items] + [""]

    # --- STYLE ---
    tones: list[str] = []
    all_preferred: list[str] = []
    all_avoided: list[str] = []
    sent_styles: list[str] = []
    for pack, _ in weighted_packs:
        v = pack.voice
        if v.tone not in tones:
            tones.append(v.tone)
        for w in v.vocabulary.preferred:
            if w not in all_preferred:
                all_preferred.append(w)
        for w in v.vocabulary.avoided:
            if w not in all_avoided:
                all_avoided.append(w)
        if v.sentence_style not in sent_styles:
            sent_styles.append(v.sentence_style)
    style_items: list[str] = []
    if tones:
        style_items.append(f"Tone: {', '.join(tones)}")
    if all_preferred:
        style_items.append(f"Preferred: {', '.join(all_preferred)}")
    if all_avoided:
        style_items.append(f"Avoided: {', '.join(all_avoided)}")
    if sent_styles:
        style_items.append(f"Sentence style: {', '.join(sent_styles)}")
    if style_items:
        lines += ["STYLE:"] + [f"- {i}" for i in style_items]

    return "\n".join(lines).strip()

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from agentic_mindset.pack import CharacterPack


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
    ) -> "ContextBlock":
        """Build a ContextBlock from one or more (pack, weight) pairs.

        Packs are expected to be pre-sorted by descending weight (highest-weight first).
        Items from earlier packs appear first in merged list fields.
        show_weights=False omits percentages from the preamble (used by sequential strategy).
        """
        if show_weights:
            names = [f"{p.meta.name} ({w:.0%})" for p, w in weighted_packs]
        else:
            names = [p.meta.name for p, _ in weighted_packs]
        preamble = "You embody a synthesized mindset drawing from: " + ", ".join(names) + "."

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
            for tp in m.thinking_patterns:
                if tp not in thinking:
                    thinking.append(tp)
            for mm in m.mental_models:
                line = f"{mm.name} — {mm.description}"
                if line not in thinking:
                    thinking.append(line)

            pers = pack.personality
            for t in pers.traits:
                line = f"{t.name} (intensity {t.intensity}): {t.description}"
                if line not in personality:
                    personality.append(line)
            for d in pers.drives:
                if d not in personality:
                    personality.append(d)

            beh = pack.behavior
            for wp in beh.work_patterns:
                if wp not in behavioral:
                    behavioral.append(wp)
            for es in beh.execution_style:
                if es not in behavioral:
                    behavioral.append(es)
            if beh.conflict_style not in behavioral:
                behavioral.append(beh.conflict_style)

            v = pack.voice
            if v.tone not in voice:
                voice.append(f"Tone: {v.tone}")
            for phrase in v.signature_phrases:
                if phrase not in voice:
                    voice.append(f'"{phrase}"')

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

from __future__ import annotations
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from agentic_mindset.pack import CharacterPack

from agentic_mindset.ir.models import (
    BehaviorIR, ResolvedSlot, ConditionModifier,
    PrimaryValue, DropReason, Preamble,
)
from agentic_mindset.resolver.policies import (
    SLOT_CONFLICT_PAIRS,
    MODIFIER_THRESHOLD,
    SOFT_THRESHOLD,
    get_fallback_conditions,
)
from agentic_mindset.context import _build_preamble as _build_preamble_text

PROVENANCE_ORDER: dict[str, int] = {"pack": 0, "fallback": 1, "weak": 2}


def _slot_default(field) -> str:
    """Return the string value of a schema field, handling ConditionalSlot."""
    if hasattr(field, "default"):
        return field.default
    return str(field) if field is not None else ""


class ConflictResolver:
    """Pure-function resolver. No I/O, no LLM calls, fully deterministic.

    Usage:
        ir = ConflictResolver().resolve(weighted_packs)
    """

    def resolve(
        self,
        weighted_packs: list[tuple["CharacterPack", float]],
    ) -> BehaviorIR:
        if not weighted_packs:
            raise ValueError("weighted_packs must be non-empty.")
        validated = self._normalize_inputs(weighted_packs)
        resolved_slots = self._resolve_all_slots(validated)
        return self._build_ir(validated, resolved_slots)

    # ── Step 1: normalize ─────────────────────────────────────────────────────

    def _normalize_inputs(
        self,
        weighted_packs: list[tuple["CharacterPack", float]],
    ) -> list[tuple["CharacterPack", float]]:
        """Validate inputs. weighted_packs must come from prepare_packs() (already sorted)."""
        return weighted_packs

    # ── Step 2: resolve all slots ─────────────────────────────────────────────

    def _resolve_all_slots(
        self,
        weighted_packs: list[tuple["CharacterPack", float]],
    ) -> dict[str, ResolvedSlot]:
        slots: dict[str, ResolvedSlot] = {}

        slot_extractors: dict[str, object] = {
            "communication":  lambda pack: _slot_default(pack.personality.interpersonal_style.communication),
            "leadership":     lambda pack: _slot_default(pack.personality.interpersonal_style.leadership),
            "conflict_style": lambda pack: _slot_default(pack.behavior.conflict_style),
            "stress_response": lambda pack: pack.personality.emotional_tendencies.stress_response,
            "tone":           lambda pack: pack.voice.tone,
            "sentence_style": lambda pack: pack.voice.sentence_style,
        }

        for slot_name, extractor in slot_extractors.items():
            values: list[tuple["CharacterPack", str, float]] = []
            for pack, weight in weighted_packs:
                try:
                    value = extractor(pack)  # type: ignore[operator]
                    if value:
                        values.append((pack, value, weight))
                except (AttributeError, TypeError):
                    continue  # pack missing this field: gracefully skip, not all packs define all slots
            if values:
                slots[slot_name] = self._resolve_categorical_slot(slot_name, values)

        return slots

    def _resolve_categorical_slot(
        self,
        slot_name: str,
        values: list[tuple["CharacterPack", str, float]],
    ) -> ResolvedSlot:
        """Apply the three-tier decision tree: pack condition > fallback > weak > discard."""
        primary_pack, primary_value, primary_weight = values[0]
        primary = PrimaryValue(
            value=primary_value,
            source=primary_pack.meta.id,
            weight=primary_weight,
        )

        modifiers: list[ConditionModifier] = []
        dropped: list[DropReason] = []
        has_conflict = False

        for sec_pack, sec_value, sec_weight in values[1:]:
            if not self._is_conflict(slot_name, primary_value, sec_value):
                dropped.append(DropReason(
                    value=sec_value,
                    source=sec_pack.meta.id,
                    weight=sec_weight,
                    reason="no_conflict",
                ))
                continue

            has_conflict = True

            if sec_weight < MODIFIER_THRESHOLD:
                dropped.append(DropReason(
                    value=sec_value,
                    source=sec_pack.meta.id,
                    weight=sec_weight,
                    reason="weight_below_threshold",
                ))
                continue

            # 1. Pack condition (highest priority)
            pack_conds = self._get_pack_conditions(sec_pack, slot_name, sec_value)
            if pack_conds:
                modifiers.append(ConditionModifier(
                    value=sec_value,
                    condition=pack_conds,
                    source=sec_pack.meta.id,
                    provenance="pack",
                    priority=sec_weight,
                ))
                continue

            # 2. Fallback template
            fallback_conds = get_fallback_conditions(slot_name, primary_value, sec_value)
            if fallback_conds:
                modifiers.append(ConditionModifier(
                    value=sec_value,
                    condition=fallback_conds,
                    source=sec_pack.meta.id,
                    provenance="fallback",
                    priority=sec_weight,
                ))
                continue

            # 3. Soft fallback (weak tendency — no conditions)
            if sec_weight >= SOFT_THRESHOLD:
                modifiers.append(ConditionModifier(
                    value=sec_value,
                    condition=[],
                    source=sec_pack.meta.id,
                    provenance="weak",
                    priority=sec_weight,
                ))
                continue

            # 4. Discard
            dropped.append(DropReason(
                value=sec_value,
                source=sec_pack.meta.id,
                weight=sec_weight,
                reason="no_condition",
            ))

        # Sort: pack (0) < fallback (1) < weak (2), then by weight descending
        modifiers.sort(key=lambda m: (PROVENANCE_ORDER[m.provenance], -(m.priority or 0)))

        return ResolvedSlot(
            primary=primary,
            modifiers=modifiers,
            has_conflict=has_conflict,
            dropped=dropped,
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _is_conflict(self, slot_name: str, val_a: str, val_b: str) -> bool:
        if slot_name not in SLOT_CONFLICT_PAIRS:
            return False
        a = val_a.lower().strip()
        b = val_b.lower().strip()
        pairs = SLOT_CONFLICT_PAIRS[slot_name]
        return (a, b) in pairs or (b, a) in pairs

    def _get_pack_conditions(
        self,
        pack: "CharacterPack",
        slot_name: str,
        secondary_value: str,
    ) -> list[str]:
        """Extract applies_when labels from pack's conditional schema variants, if any."""
        field = None
        if slot_name == "communication":
            field = pack.personality.interpersonal_style.communication
        elif slot_name == "leadership":
            field = pack.personality.interpersonal_style.leadership
        elif slot_name == "conflict_style":
            field = pack.behavior.conflict_style

        if field is None or not hasattr(field, "conditional"):
            return []

        sec_norm = secondary_value.lower().strip()
        for variant in field.conditional:
            if variant.value.lower().strip() == sec_norm:
                return list(variant.applies_when)
        return []

    # ── Step 3: build IR ──────────────────────────────────────────────────────

    def _build_ir(
        self,
        weighted_packs: list[tuple["CharacterPack", float]],
        resolved_slots: dict[str, ResolvedSlot],
    ) -> BehaviorIR:
        primary_pack = weighted_packs[0][0]
        personas = [(pack.meta.id, w) for pack, w in weighted_packs]
        preamble_text = _build_preamble_text(weighted_packs)

        # Decision policy items (additive, sorted by confidence desc, first-seen dedup)
        dp_items: list[str] = []
        seen_dp: set[str] = set()
        for pack, _ in weighted_packs:
            m = pack.mindset
            sorted_principles = sorted(
                m.core_principles,
                key=lambda cp: cp.confidence if cp.confidence is not None else -1.0,
                reverse=True,
            )
            for principle in sorted_principles:
                item = f"{principle.description}: {principle.detail}"
                if item not in seen_dp:
                    seen_dp.add(item)
                    dp_items.append(item)
            approach = f"Approach: {m.decision_framework.approach}"
            if approach not in seen_dp:
                seen_dp.add(approach)
                dp_items.append(approach)

        # Anti-patterns (additive dedup)
        anti_patterns: list[str] = []
        seen_ap: set[str] = set()
        for pack, _ in weighted_packs:
            for ap in pack.behavior.anti_patterns:
                if ap not in seen_ap:
                    seen_ap.add(ap)
                    anti_patterns.append(ap)

        # Vocabulary (additive dedup)
        vocab_preferred: list[str] = []
        vocab_avoided: list[str] = []
        seen_pref: set[str] = set()
        seen_avoid: set[str] = set()
        for pack, _ in weighted_packs:
            for w in pack.voice.vocabulary.preferred:
                if w not in seen_pref:
                    seen_pref.add(w)
                    vocab_preferred.append(w)
            for w in pack.voice.vocabulary.avoided:
                if w not in seen_avoid:
                    seen_avoid.add(w)
                    vocab_avoided.append(w)

        return BehaviorIR(
            preamble=Preamble(personas=personas, text=preamble_text),
            decision_policy_items=dp_items,
            risk_tolerance=primary_pack.mindset.decision_framework.risk_tolerance,
            time_horizon=primary_pack.mindset.decision_framework.time_horizon,
            anti_patterns=anti_patterns,
            vocabulary_preferred=vocab_preferred,
            vocabulary_avoided=vocab_avoided,
            slots=resolved_slots,
        )

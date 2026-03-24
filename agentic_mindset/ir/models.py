from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DropReason:
    value: str
    source: str
    weight: float
    reason: Literal["no_conflict", "weight_below_threshold", "no_condition"]


@dataclass
class PrimaryValue:
    value: str
    source: str
    weight: float


@dataclass
class ConditionModifier:
    value: str
    condition: list[str]
    source: str = ""
    conjunction: Literal["any", "all"] = "any"
    provenance: Literal["pack", "fallback", "weak"] = "fallback"
    note: str | None = None
    priority: float | None = None


@dataclass
class ResolvedSlot:
    primary: PrimaryValue
    modifiers: list[ConditionModifier] = field(default_factory=list)
    has_conflict: bool = False
    dropped: list[DropReason] = field(default_factory=list)


@dataclass
class Preamble:
    personas: list[tuple[str, float]]
    text: str


@dataclass
class BehaviorIR:
    preamble: Preamble
    decision_policy_items: list[str] = field(default_factory=list)
    risk_tolerance: str = ""
    time_horizon: str = ""
    anti_patterns: list[str] = field(default_factory=list)
    vocabulary_preferred: list[str] = field(default_factory=list)
    vocabulary_avoided: list[str] = field(default_factory=list)
    slots: dict[str, ResolvedSlot] = field(default_factory=dict)

    @property
    def stress_response(self) -> ResolvedSlot | None:
        return self.slots.get("stress_response")

    @property
    def communication(self) -> ResolvedSlot | None:
        return self.slots.get("communication")

    @property
    def leadership(self) -> ResolvedSlot | None:
        return self.slots.get("leadership")

    @property
    def conflict_style(self) -> ResolvedSlot | None:
        return self.slots.get("conflict_style")

    @property
    def tone(self) -> ResolvedSlot | None:
        return self.slots.get("tone")

    @property
    def sentence_style(self) -> ResolvedSlot | None:
        return self.slots.get("sentence_style")

import pytest
from agentic_mindset.ir.models import (
    BehaviorIR, ResolvedSlot, ConditionModifier,
    PrimaryValue, DropReason, Preamble,
)


def test_preamble_stores_personas_and_text():
    p = Preamble(personas=[("sun-tzu", 1.0)], text="You embody Sun Tzu.")
    assert p.personas == [("sun-tzu", 1.0)]
    assert p.text == "You embody Sun Tzu."


def test_primary_value_fields():
    pv = PrimaryValue(value="indirect", source="sun-tzu", weight=0.6)
    assert pv.value == "indirect"
    assert pv.source == "sun-tzu"
    assert pv.weight == 0.6


def test_condition_modifier_defaults():
    m = ConditionModifier(value="direct", condition=["clarity_critical"], source="marcus")
    assert m.conjunction == "any"
    assert m.provenance == "fallback"
    assert m.note is None
    assert m.priority is None


def test_condition_modifier_accepts_pack_provenance():
    m = ConditionModifier(
        value="direct",
        condition=["execution_phase"],
        source="marcus",
        provenance="pack",
        note="Used when executing.",
    )
    assert m.provenance == "pack"
    assert m.note == "Used when executing."


def test_resolved_slot_defaults():
    slot = ResolvedSlot(primary=PrimaryValue(value="indirect", source="sun-tzu", weight=1.0))
    assert slot.has_conflict is False
    assert slot.modifiers == []
    assert slot.dropped == []


def test_resolved_slot_with_modifier():
    slot = ResolvedSlot(
        primary=PrimaryValue(value="indirect", source="sun-tzu", weight=0.6),
        modifiers=[
            ConditionModifier(
                value="direct",
                condition=["clarity_critical"],
                source="marcus",
                provenance="fallback",
            )
        ],
        has_conflict=True,
    )
    assert slot.has_conflict is True
    assert len(slot.modifiers) == 1
    assert slot.modifiers[0].value == "direct"


def test_drop_reason_fields():
    dr = DropReason(value="direct", source="marcus", weight=0.2, reason="weight_below_threshold")
    assert dr.reason == "weight_below_threshold"
    assert dr.weight == 0.2


def test_behavior_ir_communication_property_reads_slots():
    comm = ResolvedSlot(primary=PrimaryValue(value="indirect", source="sun-tzu", weight=1.0))
    ir = BehaviorIR(
        preamble=Preamble(personas=[("sun-tzu", 1.0)], text="You embody Sun Tzu."),
        slots={"communication": comm},
    )
    assert ir.communication is comm


def test_behavior_ir_missing_slot_property_returns_none():
    ir = BehaviorIR(
        preamble=Preamble(personas=[("sun-tzu", 1.0)], text="You embody Sun Tzu."),
    )
    assert ir.communication is None
    assert ir.leadership is None
    assert ir.conflict_style is None
    assert ir.tone is None
    assert ir.sentence_style is None
    assert ir.stress_response is None


def test_behavior_ir_slots_dict_is_source_of_truth():
    """Writing to slots updates the typed property — no dual-write."""
    ir = BehaviorIR(preamble=Preamble(personas=[], text=""))
    slot = ResolvedSlot(primary=PrimaryValue(value="indirect", source="sun-tzu", weight=1.0))
    ir.slots["communication"] = slot
    assert ir.communication is slot


def test_behavior_ir_additive_fields_default_empty():
    ir = BehaviorIR(preamble=Preamble(personas=[], text=""))
    assert ir.decision_policy_items == []
    assert ir.anti_patterns == []
    assert ir.vocabulary_preferred == []
    assert ir.vocabulary_avoided == []
    assert ir.risk_tolerance == ""
    assert ir.time_horizon == ""

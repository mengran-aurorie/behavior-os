import pytest
from agentic_mindset.ir.models import (
    BehaviorIR, ResolvedSlot, ConditionModifier, PrimaryValue, Preamble,
)
from agentic_mindset.renderer.inject import ClaudeRenderer, render_for_runtime


def _simple_ir(comm_value="indirect", comm_modifiers=None) -> BehaviorIR:
    slot = ResolvedSlot(
        primary=PrimaryValue(value=comm_value, source="sun-tzu", weight=1.0),
        modifiers=comm_modifiers or [],
    )
    return BehaviorIR(
        preamble=Preamble(personas=[("sun-tzu", 1.0)], text="You embody Sun Tzu (100%)."),
        decision_policy_items=["Principle A: Detail A"],
        risk_tolerance="high",
        time_horizon="long-term",
        slots={"communication": slot},
    )


def test_render_includes_preamble():
    ir = _simple_ir()
    out = ClaudeRenderer().render(ir)
    assert "You embody Sun Tzu (100%)." in out


def test_render_slot_no_modifier():
    ir = _simple_ir()
    out = ClaudeRenderer().render(ir)
    assert "- Communication: indirect" in out


def test_render_slot_one_normal_modifier():
    mods = [ConditionModifier(
        value="direct",
        condition=["clarity_critical"],
        source="marcus",
        provenance="fallback",
    )]
    ir = _simple_ir(comm_modifiers=mods)
    out = ClaudeRenderer().render(ir)
    assert "- Communication: indirect; except direct when clarity is critical" in out


def test_render_slot_multiple_normal_modifiers():
    mods = [
        ConditionModifier(value="direct", condition=["clarity_critical"], source="marcus", provenance="fallback"),
        ConditionModifier(value="open",   condition=["trust_fragile"],    source="other",  provenance="fallback"),
    ]
    ir = _simple_ir(comm_modifiers=mods)
    out = ClaudeRenderer().render(ir)
    assert "- Communication: indirect; except:" in out
    assert "  - direct when clarity is critical" in out
    assert "  - open when trust is fragile" in out


def test_render_slot_weak_modifier_only():
    mods = [ConditionModifier(
        value="direct",
        condition=[],
        source="marcus",
        provenance="weak",
    )]
    ir = _simple_ir(comm_modifiers=mods)
    out = ClaudeRenderer().render(ir)
    assert "slight tendency toward direct in some situations" in out


def test_render_conditions_any_uses_or():
    mods = [ConditionModifier(
        value="direct",
        condition=["clarity_critical", "time_pressure"],
        conjunction="any",
        source="marcus",
        provenance="fallback",
    )]
    ir = _simple_ir(comm_modifiers=mods)
    out = ClaudeRenderer().render(ir)
    assert "when clarity is critical or under time pressure" in out


def test_render_conditions_all_uses_and():
    mods = [ConditionModifier(
        value="direct",
        condition=["clarity_critical", "execution_phase"],
        conjunction="all",
        source="marcus",
        provenance="fallback",
    )]
    ir = _simple_ir(comm_modifiers=mods)
    out = ClaudeRenderer().render(ir)
    assert "when clarity is critical and during execution phase" in out


def test_render_unknown_condition_label_raises():
    mods = [ConditionModifier(
        value="direct",
        condition=["not_a_real_label"],
        source="marcus",
        provenance="fallback",
    )]
    ir = _simple_ir(comm_modifiers=mods)
    with pytest.raises(ValueError, match="Unknown condition label"):
        ClaudeRenderer().render(ir)


def test_render_decision_policy_section():
    ir = _simple_ir()
    out = ClaudeRenderer().render(ir)
    assert "DECISION POLICY:" in out
    assert "- Principle A: Detail A" in out


def test_render_uncertainty_handling_section():
    ir = _simple_ir()
    out = ClaudeRenderer().render(ir)
    assert "UNCERTAINTY HANDLING:" in out
    assert "risk_tolerance: high | time_horizon: long-term" in out


def test_render_anti_patterns_omitted_when_empty():
    ir = _simple_ir()
    out = ClaudeRenderer().render(ir)
    assert "ANTI-PATTERNS" not in out


def test_render_anti_patterns_present_when_populated():
    ir = _simple_ir()
    ir.anti_patterns.append("Do not rush")
    out = ClaudeRenderer().render(ir)
    assert "ANTI-PATTERNS:" in out
    assert "- Do not rush" in out


def test_render_for_runtime_inject_dispatches_to_claude_renderer():
    ir = _simple_ir()
    result = render_for_runtime(ir, "inject")
    assert "You embody Sun Tzu" in result


def test_render_for_runtime_unknown_format_raises():
    ir = _simple_ir()
    with pytest.raises(ValueError, match="Unknown runtime format"):
        render_for_runtime(ir, "xml_tagged")

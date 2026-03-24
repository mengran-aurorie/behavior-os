from agentic_mindset.schema.behavior import BehaviorSchema
import pytest
from pydantic import ValidationError

def test_valid_behavior():
    b = BehaviorSchema(
        work_patterns=["Exhaustive prep"],
        decision_speed="deliberate",
        execution_style=["Strike when ready"],
        conflict_style="avoidant",
    )
    assert b.decision_speed == "deliberate"

def test_invalid_decision_speed():
    with pytest.raises(ValidationError):
        BehaviorSchema(
            work_patterns=[],
            decision_speed="chaotic",
            execution_style=[],
            conflict_style="",
        )


def test_anti_patterns_defaults_to_empty():
    """Existing packs without anti_patterns field validate fine."""
    b = BehaviorSchema(
        work_patterns=["Prep"],
        decision_speed="deliberate",
        execution_style=["Strike"],
        conflict_style="avoidant",
        # no anti_patterns key
    )
    assert b.anti_patterns == []


def test_anti_patterns_accepts_list():
    b = BehaviorSchema(
        work_patterns=["Prep"],
        decision_speed="deliberate",
        execution_style=["Strike"],
        conflict_style="avoidant",
        anti_patterns=["Do not rush to conclusions", "Do not overcommit early"],
    )
    assert len(b.anti_patterns) == 2
    assert "Do not rush to conclusions" in b.anti_patterns


from agentic_mindset.schema.behavior import BehaviorSchema
from agentic_mindset.schema.personality import ConditionalSlot


def test_conflict_style_plain_string_is_promoted():
    b = BehaviorSchema(
        work_patterns=["Prepare"],
        decision_speed="deliberate",
        execution_style=["Act"],
        conflict_style="avoidant",
    )
    assert isinstance(b.conflict_style, ConditionalSlot)
    assert str(b.conflict_style) == "avoidant"


def test_conflict_style_full_format_accepted():
    b = BehaviorSchema(
        work_patterns=["Prepare"],
        decision_speed="deliberate",
        execution_style=["Act"],
        conflict_style={
            "default": "avoidant",
            "conditional": [
                {"value": "confrontational", "applies_when": ["advantage_secured"]}
            ],
        },
    )
    assert b.conflict_style.default == "avoidant"
    assert b.conflict_style.conditional[0].value == "confrontational"

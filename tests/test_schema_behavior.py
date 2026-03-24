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

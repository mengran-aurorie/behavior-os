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

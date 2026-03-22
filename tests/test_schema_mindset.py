from agentic_mindset.schema.mindset import MindsetSchema
import pytest
from pydantic import ValidationError

def test_valid_mindset():
    m = MindsetSchema(
        core_principles=[{"description": "Deception", "detail": "..."}],
        decision_framework={"risk_tolerance": "medium", "time_horizon": "long-term", "approach": "..."},
        thinking_patterns=["Observe first"],
        mental_models=[{"name": "Empty Fort", "description": "..."}],
    )
    assert m.decision_framework.risk_tolerance == "medium"

def test_invalid_risk_tolerance():
    with pytest.raises(ValidationError):
        MindsetSchema(
            core_principles=[],
            decision_framework={"risk_tolerance": "extreme", "time_horizon": "long-term", "approach": ""},
            thinking_patterns=[],
            mental_models=[],
        )

def test_confidence_range():
    with pytest.raises(ValidationError):
        MindsetSchema(
            core_principles=[{"description": "X", "detail": "Y", "confidence": 1.5}],
            decision_framework={"risk_tolerance": "low", "time_horizon": "short-term", "approach": ""},
            thinking_patterns=[],
            mental_models=[],
        )

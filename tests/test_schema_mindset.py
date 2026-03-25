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


def test_decision_framework_new_fields_optional():
    """All new DecisionFramework fields are optional — existing packs load unchanged."""
    from agentic_mindset.schema.mindset import DecisionFramework
    df = DecisionFramework(
        risk_tolerance="medium",
        time_horizon="long-term",
        approach="Act only when victory is certain.",
    )
    assert df.heuristics == []
    assert df.default_strategy is None
    assert df.fallback_strategy is None
    assert df.commitment_policy is None


def test_decision_framework_with_all_new_fields():
    from agentic_mindset.schema.mindset import DecisionFramework
    df = DecisionFramework(
        risk_tolerance="high",
        time_horizon="long-term",
        approach="Win before the battle begins.",
        heuristics=["Gather intel before committing", "Prefer indirect routes"],
        default_strategy="Position for inevitable victory through preparation",
        fallback_strategy="Retreat and regroup; never pursue desperate battle",
        commitment_policy="late",
    )
    assert df.heuristics == ["Gather intel before committing", "Prefer indirect routes"]
    assert df.commitment_policy == "late"


def test_decision_framework_commitment_policy_enum():
    """commitment_policy only accepts early | deliberate | late."""
    from agentic_mindset.schema.mindset import DecisionFramework
    import pytest
    with pytest.raises(Exception):
        DecisionFramework(
            risk_tolerance="medium",
            time_horizon="long-term",
            approach="...",
            commitment_policy="never",
        )

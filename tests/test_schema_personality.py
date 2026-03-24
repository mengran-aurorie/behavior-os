from agentic_mindset.schema.personality import PersonalitySchema
import pytest
from pydantic import ValidationError

def test_valid_personality():
    p = PersonalitySchema(
        traits=[{"name": "Patience", "description": "...", "intensity": 0.9}],
        emotional_tendencies={"stress_response": "...", "motivation_source": "..."},
        interpersonal_style={"communication": "...", "leadership": "..."},
        drives=["mastery"],
    )
    assert p.traits[0].intensity == 0.9

def test_intensity_out_of_range():
    with pytest.raises(ValidationError):
        PersonalitySchema(
            traits=[{"name": "X", "description": "Y", "intensity": 1.5}],
            emotional_tendencies={"stress_response": "", "motivation_source": ""},
            interpersonal_style={"communication": "", "leadership": ""},
            drives=[],
        )


from agentic_mindset.schema.personality import ConditionalSlot, ConditionalVariant, InterpersonalStyle


def test_conditional_slot_plain_string_is_promoted():
    """Plain string is auto-promoted to ConditionalSlot."""
    style = InterpersonalStyle(communication="indirect", leadership="lead by positioning")
    assert isinstance(style.communication, ConditionalSlot)
    assert style.communication.default == "indirect"
    assert style.communication.conditional == []


def test_conditional_slot_str_returns_default():
    slot = ConditionalSlot(default="indirect", conditional=[])
    assert str(slot) == "indirect"


def test_conditional_slot_eq_plain_string():
    """ConditionalSlot == plain string when defaults match."""
    slot = ConditionalSlot(default="indirect", conditional=[])
    assert slot == "indirect"


def test_conditional_variant_applies_when():
    variant = ConditionalVariant(
        value="direct",
        applies_when=["clarity_critical", "execution_phase"],
        note="Used for clarity.",
    )
    assert variant.applies_when == ["clarity_critical", "execution_phase"]
    assert variant.note == "Used for clarity."


def test_conditional_slot_full_format_accepted():
    """New YAML dict format is accepted directly."""
    style = InterpersonalStyle(
        communication={
            "default": "indirect",
            "conditional": [
                {"value": "direct", "applies_when": ["clarity_critical"]}
            ],
        },
        leadership="lead by positioning",
    )
    assert isinstance(style.communication, ConditionalSlot)
    assert style.communication.default == "indirect"
    assert len(style.communication.conditional) == 1
    assert style.communication.conditional[0].value == "direct"

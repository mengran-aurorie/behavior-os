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


# ── Drive ──────────────────────────────────────────────────────────────────────

def test_drive_from_object():
    from agentic_mindset.schema.personality import Drive
    d = Drive(name="strategic_mastery", intensity=0.95, description="Win through positioning")
    assert d.name == "strategic_mastery"
    assert d.intensity == 0.95
    assert str(d) == "strategic_mastery"


def test_drive_str_normalized_to_drive():
    """Bare string in drives list is auto-wrapped as Drive with intensity 0.8."""
    from agentic_mindset.schema.personality import PersonalitySchema, Drive
    p = PersonalitySchema(
        emotional_tendencies={"stress_response": "withdraws", "motivation_source": "victory"},
        interpersonal_style={"communication": "indirect", "leadership": "by positioning"},
        drives=["strategic mastery", "efficiency"],
    )
    assert isinstance(p.drives[0], Drive)
    assert p.drives[0].name == "strategic mastery"
    assert p.drives[0].intensity == 0.8


def test_drive_intensity_out_of_range_raises():
    from agentic_mindset.schema.personality import Drive
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Drive(name="x", intensity=1.5)


def test_drive_str_renders_name():
    from agentic_mindset.schema.personality import Drive
    d = Drive(name="strategic mastery", intensity=0.95)
    assert str(d) == "strategic mastery"


# ── Trait confidence ───────────────────────────────────────────────────────────

def test_trait_confidence_optional():
    from agentic_mindset.schema.personality import Trait
    t = Trait(name="patience", description="waits", intensity=0.9)
    assert t.confidence is None


def test_trait_confidence_valid():
    from agentic_mindset.schema.personality import Trait
    t = Trait(name="patience", description="waits", intensity=0.9, confidence=0.85)
    assert t.confidence == 0.85


def test_trait_confidence_out_of_range_raises():
    from agentic_mindset.schema.personality import Trait
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Trait(name="x", description="x", intensity=0.5, confidence=1.5)


# ── EmotionalTendencies ────────────────────────────────────────────────────────

def test_emotional_tendencies_new_fields_optional():
    from agentic_mindset.schema.personality import EmotionalTendencies
    et = EmotionalTendencies(stress_response="withdraws", motivation_source="victory")
    assert et.baseline_mood is None
    assert et.emotional_range is None
    assert et.frustration_trigger is None
    assert et.recovery_pattern is None


def test_emotional_tendencies_with_all_new_fields():
    from agentic_mindset.schema.personality import EmotionalTendencies
    et = EmotionalTendencies(
        stress_response="withdraws",
        motivation_source="victory",
        baseline_mood="calm, watchful",
        emotional_range="narrow",
        frustration_trigger="impulsive action without reconnaissance",
        recovery_pattern="retreats to gather information; rebuilds plan",
    )
    assert et.emotional_range == "narrow"
    assert et.frustration_trigger == "impulsive action without reconnaissance"


def test_emotional_tendencies_emotional_range_enum():
    from agentic_mindset.schema.personality import EmotionalTendencies
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        EmotionalTendencies(
            stress_response="x",
            motivation_source="y",
            emotional_range="extreme",
        )


# ── ConditionalVariant conjunction ────────────────────────────────────────────

def test_conditional_variant_conjunction_default():
    from agentic_mindset.schema.personality import ConditionalVariant
    cv = ConditionalVariant(value="direct", applies_when=["clarity_critical"])
    assert cv.conjunction == "any"


def test_conditional_variant_conjunction_all():
    from agentic_mindset.schema.personality import ConditionalVariant
    cv = ConditionalVariant(
        value="direct",
        applies_when=["clarity_critical", "execution_phase"],
        conjunction="all",
    )
    assert cv.conjunction == "all"


def test_conditional_variant_conjunction_invalid():
    from agentic_mindset.schema.personality import ConditionalVariant
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ConditionalVariant(value="direct", applies_when=[], conjunction="maybe")

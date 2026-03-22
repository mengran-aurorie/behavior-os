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

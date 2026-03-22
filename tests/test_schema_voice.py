import pytest
from pydantic import ValidationError

from agentic_mindset.schema.voice import VoiceSchema

def test_valid_voice():
    v = VoiceSchema(
        tone="measured",
        vocabulary={"preferred": ["position"], "avoided": ["rush"]},
        sentence_style="aphoristic",
        signature_phrases=["Know your enemy"],
    )
    assert v.tone == "measured"


def test_missing_required_field():
    with pytest.raises(ValidationError):
        VoiceSchema(
            # tone is missing — required field
            vocabulary={"preferred": [], "avoided": []},
            sentence_style="aphoristic",
        )

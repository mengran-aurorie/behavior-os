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


def test_tone_axes_optional():
    from agentic_mindset.schema.voice import VoiceSchema
    v = VoiceSchema(
        tone="measured",
        vocabulary={"preferred": [], "avoided": []},
        sentence_style="short",
    )
    assert v.tone_axes is None


def test_tone_axes_full():
    from agentic_mindset.schema.voice import VoiceSchema, ToneAxes
    v = VoiceSchema(
        tone="measured",
        vocabulary={"preferred": [], "avoided": []},
        sentence_style="short",
        tone_axes=ToneAxes(formality="high", warmth="low", intensity="medium", humor="dry"),
    )
    assert v.tone_axes.formality == "high"
    assert v.tone_axes.humor == "dry"


def test_tone_axes_partial():
    from agentic_mindset.schema.voice import ToneAxes
    ta = ToneAxes(formality="high")
    assert ta.warmth is None
    assert ta.intensity is None
    assert ta.humor is None


def test_tone_axes_invalid_raises():
    from agentic_mindset.schema.voice import ToneAxes
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ToneAxes(formality="very_high")

from agentic_mindset.schema.voice import VoiceSchema

def test_valid_voice():
    v = VoiceSchema(
        tone="measured",
        vocabulary={"preferred": ["position"], "avoided": ["rush"]},
        sentence_style="aphoristic",
        signature_phrases=["Know your enemy"],
    )
    assert v.tone == "measured"

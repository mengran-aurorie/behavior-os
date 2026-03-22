from pydantic import BaseModel


class Vocabulary(BaseModel):
    preferred: list[str] = []
    avoided: list[str] = []


class VoiceSchema(BaseModel):
    tone: str
    vocabulary: Vocabulary
    sentence_style: str
    signature_phrases: list[str] = []

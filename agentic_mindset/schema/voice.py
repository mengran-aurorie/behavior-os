from typing import Literal, Optional
from pydantic import BaseModel


class Vocabulary(BaseModel):
    preferred: list[str] = []
    avoided: list[str] = []


class ToneAxes(BaseModel):
    """Semi-structured tone metadata for future mix/render pipelines."""
    formality: Optional[Literal["low", "medium", "high"]] = None
    warmth: Optional[Literal["low", "medium", "high"]] = None
    intensity: Optional[Literal["low", "medium", "high"]] = None
    humor: Optional[Literal["none", "dry", "playful", "sharp"]] = None


class VoiceSchema(BaseModel):
    tone: str
    tone_axes: Optional[ToneAxes] = None      # NEW
    vocabulary: Vocabulary
    sentence_style: str
    signature_phrases: list[str] = []

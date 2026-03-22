from typing import Optional
from pydantic import BaseModel, field_validator


class Trait(BaseModel):
    name: str
    description: str
    intensity: float

    @field_validator("intensity")
    @classmethod
    def intensity_range(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("intensity must be between 0.0 and 1.0")
        return v


class EmotionalTendencies(BaseModel):
    stress_response: str
    motivation_source: str


class InterpersonalStyle(BaseModel):
    communication: str
    leadership: str


class PersonalitySchema(BaseModel):
    traits: list[Trait] = []
    emotional_tendencies: EmotionalTendencies
    interpersonal_style: InterpersonalStyle
    drives: list[str] = []

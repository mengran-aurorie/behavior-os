from typing import Optional, Union
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


class ConditionalVariant(BaseModel):
    value: str
    applies_when: list[str] = []
    note: Optional[str] = None


class ConditionalSlot(BaseModel):
    default: str
    conditional: list[ConditionalVariant] = []

    def __str__(self) -> str:
        return self.default

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.default == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.default)


class InterpersonalStyle(BaseModel):
    communication: Union[str, ConditionalSlot]
    leadership: Union[str, ConditionalSlot]

    @field_validator("communication", "leadership", mode="before")
    @classmethod
    def normalize_slot(cls, v):
        if isinstance(v, str):
            return ConditionalSlot(default=v, conditional=[])
        return v


class PersonalitySchema(BaseModel):
    traits: list[Trait] = []
    emotional_tendencies: EmotionalTendencies
    interpersonal_style: InterpersonalStyle
    drives: list[str] = []

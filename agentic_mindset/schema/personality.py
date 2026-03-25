from typing import Optional, Union, Literal
from pydantic import BaseModel, field_validator


class Drive(BaseModel):
    name: str
    intensity: float = 0.8
    description: Optional[str] = None

    @field_validator("intensity")
    @classmethod
    def intensity_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("intensity must be between 0.0 and 1.0")
        return v

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.name == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.name)


class Trait(BaseModel):
    name: str
    description: str
    intensity: float
    confidence: Optional[float] = None

    @field_validator("intensity")
    @classmethod
    def intensity_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("intensity must be between 0.0 and 1.0")
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class EmotionalTendencies(BaseModel):
    stress_response: str
    motivation_source: str
    baseline_mood: Optional[str] = None
    emotional_range: Optional[Literal["narrow", "moderate", "wide"]] = None
    frustration_trigger: Optional[str] = None
    recovery_pattern: Optional[str] = None


class ConditionalVariant(BaseModel):
    value: str
    applies_when: list[str] = []
    conjunction: Literal["any", "all"] = "any"
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
    drives: list[Drive] = []

    @field_validator("drives", mode="before")
    @classmethod
    def normalize_drives(cls, v: list) -> list:
        """Accept bare strings (old format) and normalize to Drive objects."""
        result = []
        for item in v:
            if isinstance(item, str):
                result.append({"name": item})
            else:
                result.append(item)
        return result

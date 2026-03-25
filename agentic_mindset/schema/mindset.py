from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class CorePrinciple(BaseModel):
    description: str
    detail: str
    confidence: Optional[float] = None

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class DecisionFramework(BaseModel):
    risk_tolerance: Literal["low", "medium", "high"]
    time_horizon: Literal["short-term", "medium-term", "long-term"]
    approach: str                                                          # backward compat: keep required
    heuristics: list[str] = []                                             # NEW: actionable decision rules
    default_strategy: Optional[str] = None                                # NEW: primary mode of operation
    fallback_strategy: Optional[str] = None                               # NEW: what to do when default fails
    commitment_policy: Optional[Literal["early", "deliberate", "late"]] = None  # NEW: when to commit


class MentalModel(BaseModel):
    name: str
    description: str


class MindsetSchema(BaseModel):
    core_principles: list[CorePrinciple] = []
    decision_framework: DecisionFramework
    thinking_patterns: list[str] = []
    mental_models: list[MentalModel] = []

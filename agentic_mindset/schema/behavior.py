from typing import Literal, Optional, Union
from pydantic import BaseModel, field_validator
from agentic_mindset.schema.personality import ConditionalSlot


class BehaviorSchema(BaseModel):
    work_patterns: list[str] = []
    decision_speed: Literal["slow", "deliberate", "fast"]          # BREAKING: removed impulsive
    decision_control: Optional[Literal["controlled", "reactive", "impulsive"]] = None  # NEW
    execution_style: list[str] = []
    conflict_style: Union[str, ConditionalSlot]
    anti_patterns: list[str] = []

    @field_validator("conflict_style", mode="before")
    @classmethod
    def normalize_conflict_style(cls, v):
        if isinstance(v, str):
            return ConditionalSlot(default=v, conditional=[])
        return v

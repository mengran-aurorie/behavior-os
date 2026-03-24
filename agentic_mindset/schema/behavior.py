from typing import Literal
from pydantic import BaseModel


class BehaviorSchema(BaseModel):
    work_patterns: list[str] = []
    decision_speed: Literal["slow", "deliberate", "fast", "impulsive"]
    execution_style: list[str] = []
    conflict_style: str
    anti_patterns: list[str] = []   # v1: behavioral anti-patterns; optional for backward compat

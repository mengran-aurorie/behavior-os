from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class Source(BaseModel):
    title: str
    type: Literal[
        "book", "biography", "interview", "article", "talk",
        "podcast", "screenplay", "manga", "game",
        "film", "novel", "essay", "letter", "speech",
    ]
    evidence_level: Optional[Literal["primary", "secondary", "tertiary"]] = None  # NEW
    path: Optional[str] = None
    url: Optional[str] = None
    accessed: str


class SourcesSchema(BaseModel):
    sources: list[Source] = []

    @field_validator("sources")
    @classmethod
    def minimum_three_sources(cls, v):
        if len(v) < 3:
            raise ValueError("sources must contain at least 3 entries")
        return v

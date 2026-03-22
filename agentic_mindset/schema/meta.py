import re
from typing import Literal
from pydantic import BaseModel, field_validator


class AuthorSchema(BaseModel):
    name: str
    url: str = ""


class MetaSchema(BaseModel):
    id: str
    name: str
    version: str          # character pack version: MAJOR.MINOR.PATCH
    schema_version: str   # mindset schema version: MAJOR.MINOR
    type: Literal["historical", "fictional"]
    description: str
    tags: list[str] = []
    authors: list[AuthorSchema] = []
    created: str          # ISO date string YYYY-MM-DD

    @field_validator("id")
    @classmethod
    def id_must_be_kebab_case(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", v):
            raise ValueError("id must be kebab-case (lowercase letters, digits, hyphens only)")
        return v

    @field_validator("version")
    @classmethod
    def version_must_be_semver(cls, v: str) -> str:
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("version must be MAJOR.MINOR.PATCH (e.g. '1.0.0')")
        return v

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_be_major_minor(cls, v: str) -> str:
        if not re.match(r"^\d+\.\d+$", v):
            raise ValueError("schema_version must be MAJOR.MINOR (e.g. '1.0')")
        return v

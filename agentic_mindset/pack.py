from dataclasses import dataclass
from pathlib import Path
import yaml
from pydantic import ValidationError
from agentic_mindset.schema import (
    MetaSchema, MindsetSchema, PersonalitySchema,
    BehaviorSchema, VoiceSchema, SourcesSchema,
)


class PackLoadError(Exception):
    pass


def _load_yaml(path: Path, schema_cls, filename: str):
    if not path.exists():
        raise PackLoadError(f"Required file missing: {filename}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise PackLoadError(f"Invalid YAML in {filename}: {e}") from e
    try:
        return schema_cls(**raw)
    except ValidationError as e:
        raise PackLoadError(f"Schema validation failed in {filename}:\n{e}") from e


@dataclass
class CharacterPack:
    path: Path
    meta: MetaSchema
    mindset: MindsetSchema
    personality: PersonalitySchema
    behavior: BehaviorSchema
    voice: VoiceSchema
    sources: SourcesSchema

    @classmethod
    def load(cls, directory: Path) -> "CharacterPack":
        d = Path(directory)
        return cls(
            path=d,
            meta=_load_yaml(d / "meta.yaml", MetaSchema, "meta.yaml"),
            mindset=_load_yaml(d / "mindset.yaml", MindsetSchema, "mindset.yaml"),
            personality=_load_yaml(d / "personality.yaml", PersonalitySchema, "personality.yaml"),
            behavior=_load_yaml(d / "behavior.yaml", BehaviorSchema, "behavior.yaml"),
            voice=_load_yaml(d / "voice.yaml", VoiceSchema, "voice.yaml"),
            sources=_load_yaml(d / "sources.yaml", SourcesSchema, "sources.yaml"),
        )

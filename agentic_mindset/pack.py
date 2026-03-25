import warnings
from dataclasses import dataclass
from pathlib import Path
import yaml
from pydantic import ValidationError
from agentic_mindset.schema import (
    MetaSchema, MindsetSchema, PersonalitySchema,
    BehaviorSchema, VoiceSchema, SourcesSchema,
    is_supported, is_current,
    CURRENT_SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS,
)


class PackLoadError(Exception):
    pass


class SchemaVersionWarning(UserWarning):
    """Emitted when a pack's schema_version is supported but not current."""
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


def _check_schema_version(meta: MetaSchema) -> None:
    v = meta.schema_version
    if not is_supported(v):
        raise PackLoadError(
            f"Unsupported schema_version '{v}' in pack '{meta.id}'. "
            f"This runtime supports: {sorted(SUPPORTED_SCHEMA_VERSIONS)}. "
            "Update the pack or upgrade agentic-mindset."
        )
    if not is_current(v):
        warnings.warn(
            f"Pack '{meta.id}' uses schema_version '{v}'; current is '{CURRENT_SCHEMA_VERSION}'. "
            "The pack will load but consider upgrading to the latest schema. "
            "See docs/migrations/1.0-to-1.1.md for the migration guide.",
            SchemaVersionWarning,
            stacklevel=3,
        )


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
        meta = _load_yaml(d / "meta.yaml", MetaSchema, "meta.yaml")
        _check_schema_version(meta)
        return cls(
            path=d,
            meta=meta,
            mindset=_load_yaml(d / "mindset.yaml", MindsetSchema, "mindset.yaml"),
            personality=_load_yaml(d / "personality.yaml", PersonalitySchema, "personality.yaml"),
            behavior=_load_yaml(d / "behavior.yaml", BehaviorSchema, "behavior.yaml"),
            voice=_load_yaml(d / "voice.yaml", VoiceSchema, "voice.yaml"),
            sources=_load_yaml(d / "sources.yaml", SourcesSchema, "sources.yaml"),
        )

# Agentic Mindset — Core Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core framework: YAML schemas, validator, character registry, fusion engine, Context Block output, and CLI commands (`init`, `validate`, `preview`, `list`).

**Architecture:** Pydantic models define each YAML schema and validate character packs. A `FusionEngine` merges N packs into a `ContextBlock` using blend/dominant/sequential strategies. A `Typer` CLI exposes the developer-facing commands. The build pipeline (LLM extractor) is out of scope for this plan.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, Typer, pytest

**Spec:** `docs/superpowers/specs/2026-03-22-agentic-mindset-design.md`

---

## File Map

```
agentic_mindset/
├── __init__.py                  # Public API: CharacterRegistry, FusionEngine, ContextBlock
├── schema/
│   ├── __init__.py
│   ├── meta.py                  # MetaSchema Pydantic model
│   ├── mindset.py               # MindsetSchema Pydantic model
│   ├── personality.py           # PersonalitySchema Pydantic model
│   ├── behavior.py              # BehaviorSchema Pydantic model
│   ├── voice.py                 # VoiceSchema Pydantic model
│   └── sources.py               # SourcesSchema Pydantic model
├── pack.py                      # CharacterPack: loads a directory into all six schemas
├── registry.py                  # CharacterRegistry: resolves IDs → CharacterPack
├── fusion.py                    # FusionEngine: merges N packs → ContextBlock
├── context.py                   # ContextBlock: to_prompt() output contract
└── cli.py                       # Typer CLI: init, validate, preview, list

tests/
├── conftest.py                  # shared fixtures (sample pack dirs)
├── test_schema_meta.py
├── test_schema_mindset.py
├── test_schema_personality.py
├── test_schema_behavior.py
├── test_schema_voice.py
├── test_schema_sources.py
├── test_pack.py
├── test_registry.py
├── test_fusion.py
├── test_context.py
└── test_cli.py

characters/
├── sun-tzu/                     # First standard library pack (historical)
│   ├── meta.yaml
│   ├── mindset.yaml
│   ├── personality.yaml
│   ├── behavior.yaml
│   ├── voice.yaml
│   └── sources.yaml
└── marcus-aurelius/             # Second standard library pack (historical)
    ├── meta.yaml
    ├── mindset.yaml
    ├── personality.yaml
    ├── behavior.yaml
    ├── voice.yaml
    └── sources.yaml

pyproject.toml                   # package config, deps, CLI entry point
prompts/
└── extract-v1.md                # Extraction prompt template (placeholder for Plan 2)
CONTRIBUTING.md
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `agentic_mindset/__init__.py`
- Create: `agentic_mindset/schema/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agentic-mindset"
version = "0.1.0"
description = "Load historical and fictional character mindsets onto AI agents"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "typer>=0.12",
    "rich>=13.0",
]

[project.scripts]
mindset = "agentic_mindset.cli:app"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create `agentic_mindset/__init__.py`**

```python
from agentic_mindset.registry import CharacterRegistry
from agentic_mindset.fusion import FusionEngine
from agentic_mindset.context import ContextBlock

__all__ = ["CharacterRegistry", "FusionEngine", "ContextBlock"]
```

- [ ] **Step 3: Create `agentic_mindset/schema/__init__.py`**

```python
from agentic_mindset.schema.meta import MetaSchema
from agentic_mindset.schema.mindset import MindsetSchema
from agentic_mindset.schema.personality import PersonalitySchema
from agentic_mindset.schema.behavior import BehaviorSchema
from agentic_mindset.schema.voice import VoiceSchema
from agentic_mindset.schema.sources import SourcesSchema

__all__ = [
    "MetaSchema", "MindsetSchema", "PersonalitySchema",
    "BehaviorSchema", "VoiceSchema", "SourcesSchema",
]
```

- [ ] **Step 4: Create `tests/conftest.py`**

```python
import pytest
import tempfile
import shutil
from pathlib import Path
import yaml


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, allow_unicode=True))


@pytest.fixture
def minimal_pack_dir():
    """A valid minimal character pack directory for sun-tzu."""
    tmp = Path(tempfile.mkdtemp())
    write_yaml(tmp / "meta.yaml", {
        "id": "sun-tzu",
        "name": "Sun Tzu",
        "version": "1.0.0",
        "schema_version": "1.0",
        "type": "historical",
        "description": "Chinese military strategist.",
        "tags": ["strategy"],
        "authors": [{"name": "Test Author", "url": "https://github.com/test"}],
        "created": "2026-03-22",
    })
    write_yaml(tmp / "mindset.yaml", {
        "core_principles": [
            {"description": "Strategic deception", "detail": "All warfare is based on deception"}
        ],
        "decision_framework": {
            "risk_tolerance": "medium",
            "time_horizon": "long-term",
            "approach": "Win before the battle begins",
        },
        "thinking_patterns": ["Observe before acting"],
        "mental_models": [{"name": "Empty Fort", "description": "Use apparent vulnerability"}],
    })
    write_yaml(tmp / "personality.yaml", {
        "traits": [{"name": "Patience", "description": "Waits for optimal moment", "intensity": 0.9}],
        "emotional_tendencies": {
            "stress_response": "withdraws to observe",
            "motivation_source": "victory through minimum force",
        },
        "interpersonal_style": {
            "communication": "indirect, layered",
            "leadership": "leads through positioning",
        },
        "drives": ["Strategic mastery"],
    })
    write_yaml(tmp / "behavior.yaml", {
        "work_patterns": ["Exhaustive preparation before action"],
        "decision_speed": "deliberate",
        "execution_style": ["Strike only when conditions are favorable"],
        "conflict_style": "avoidant of direct confrontation",
    })
    write_yaml(tmp / "voice.yaml", {
        "tone": "measured, aphoristic",
        "vocabulary": {"preferred": ["position", "opportunity"], "avoided": ["rush"]},
        "sentence_style": "short aphorisms",
        "signature_phrases": ["Supreme excellence consists in breaking the enemy's resistance without fighting"],
    })
    write_yaml(tmp / "sources.yaml", {
        "sources": [
            {"title": "The Art of War", "type": "book", "accessed": "2026-03-22"},
            {"title": "Sun Tzu biography", "type": "article", "accessed": "2026-03-22"},
            {"title": "Commentary on Art of War", "type": "book", "accessed": "2026-03-22"},
        ]
    })
    yield tmp
    shutil.rmtree(tmp)
```

- [ ] **Step 5: Install dependencies and verify**

```bash
pip install -e ".[dev]"
pytest --collect-only   # should show 0 tests, no errors
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml agentic_mindset/ tests/
git commit -m "feat: project scaffold with pyproject.toml and package structure"
```

---

## Task 2: Meta Schema

**Files:**
- Create: `agentic_mindset/schema/meta.py`
- Create: `tests/test_schema_meta.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_schema_meta.py
import pytest
from pydantic import ValidationError
from agentic_mindset.schema.meta import MetaSchema


def test_valid_historical():
    data = {
        "id": "sun-tzu",
        "name": "Sun Tzu",
        "version": "1.0.0",
        "schema_version": "1.0",
        "type": "historical",
        "description": "Military strategist.",
        "tags": ["strategy"],
        "authors": [{"name": "A", "url": "https://github.com/a"}],
        "created": "2026-03-22",
    }
    m = MetaSchema(**data)
    assert m.id == "sun-tzu"
    assert m.type == "historical"


def test_valid_fictional():
    data = {
        "id": "naruto",
        "name": "Naruto Uzumaki",
        "version": "1.0.0",
        "schema_version": "1.0",
        "type": "fictional",
        "description": "Ninja protagonist.",
        "tags": ["anime"],
        "authors": [{"name": "A", "url": "https://github.com/a"}],
        "created": "2026-03-22",
    }
    m = MetaSchema(**data)
    assert m.type == "fictional"


def test_invalid_type_rejects_living():
    with pytest.raises(ValidationError):
        MetaSchema(
            id="someone",
            name="Someone",
            version="1.0.0",
            schema_version="1.0",
            type="living",          # not a valid enum value
            description=".",
            tags=[],
            authors=[],
            created="2026-03-22",
        )


def test_id_must_be_kebab_case():
    with pytest.raises(ValidationError):
        MetaSchema(
            id="Sun Tzu",           # spaces not allowed
            name="Sun Tzu",
            version="1.0.0",
            schema_version="1.0",
            type="historical",
            description=".",
            tags=[],
            authors=[],
            created="2026-03-22",
        )


def test_invalid_version_format():
    with pytest.raises(ValidationError):
        MetaSchema(
            id="sun-tzu",
            name="Sun Tzu",
            version="v1",           # must be MAJOR.MINOR.PATCH
            schema_version="1.0",
            type="historical",
            description=".",
            tags=[],
            authors=[],
            created="2026-03-22",
        )


def test_invalid_schema_version_format():
    with pytest.raises(ValidationError):
        MetaSchema(
            id="sun-tzu",
            name="Sun Tzu",
            version="1.0.0",
            schema_version="latest",  # must be MAJOR.MINOR
            type="historical",
            description=".",
            tags=[],
            authors=[],
            created="2026-03-22",
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_schema_meta.py -v
```
Expected: `ImportError` or `ModuleNotFoundError`

- [ ] **Step 3: Implement `meta.py`**

```python
# agentic_mindset/schema/meta.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_schema_meta.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add agentic_mindset/schema/meta.py tests/test_schema_meta.py
git commit -m "feat: MetaSchema with id validation and type enum"
```

---

## Task 3: Content Schemas (Mindset, Personality, Behavior, Voice, Sources)

**Files:**
- Create: `agentic_mindset/schema/mindset.py`
- Create: `agentic_mindset/schema/personality.py`
- Create: `agentic_mindset/schema/behavior.py`
- Create: `agentic_mindset/schema/voice.py`
- Create: `agentic_mindset/schema/sources.py`
- Create: `tests/test_schema_mindset.py`
- Create: `tests/test_schema_personality.py`
- Create: `tests/test_schema_behavior.py`
- Create: `tests/test_schema_voice.py`
- Create: `tests/test_schema_sources.py`

- [ ] **Step 1: Write failing tests for all five schemas**

```python
# tests/test_schema_mindset.py
from agentic_mindset.schema.mindset import MindsetSchema
import pytest
from pydantic import ValidationError

def test_valid_mindset():
    m = MindsetSchema(
        core_principles=[{"description": "Deception", "detail": "..."}],
        decision_framework={"risk_tolerance": "medium", "time_horizon": "long-term", "approach": "..."},
        thinking_patterns=["Observe first"],
        mental_models=[{"name": "Empty Fort", "description": "..."}],
    )
    assert m.decision_framework.risk_tolerance == "medium"

def test_invalid_risk_tolerance():
    with pytest.raises(ValidationError):
        MindsetSchema(
            core_principles=[],
            decision_framework={"risk_tolerance": "extreme", "time_horizon": "long-term", "approach": ""},
            thinking_patterns=[],
            mental_models=[],
        )

def test_confidence_range():
    with pytest.raises(ValidationError):
        MindsetSchema(
            core_principles=[{"description": "X", "detail": "Y", "confidence": 1.5}],
            decision_framework={"risk_tolerance": "low", "time_horizon": "short-term", "approach": ""},
            thinking_patterns=[],
            mental_models=[],
        )
```

```python
# tests/test_schema_personality.py
from agentic_mindset.schema.personality import PersonalitySchema
import pytest
from pydantic import ValidationError

def test_valid_personality():
    p = PersonalitySchema(
        traits=[{"name": "Patience", "description": "...", "intensity": 0.9}],
        emotional_tendencies={"stress_response": "...", "motivation_source": "..."},
        interpersonal_style={"communication": "...", "leadership": "..."},
        drives=["mastery"],
    )
    assert p.traits[0].intensity == 0.9

def test_intensity_out_of_range():
    with pytest.raises(ValidationError):
        PersonalitySchema(
            traits=[{"name": "X", "description": "Y", "intensity": 1.5}],
            emotional_tendencies={"stress_response": "", "motivation_source": ""},
            interpersonal_style={"communication": "", "leadership": ""},
            drives=[],
        )
```

```python
# tests/test_schema_behavior.py
from agentic_mindset.schema.behavior import BehaviorSchema
import pytest
from pydantic import ValidationError

def test_valid_behavior():
    b = BehaviorSchema(
        work_patterns=["Exhaustive prep"],
        decision_speed="deliberate",
        execution_style=["Strike when ready"],
        conflict_style="avoidant",
    )
    assert b.decision_speed == "deliberate"

def test_invalid_decision_speed():
    with pytest.raises(ValidationError):
        BehaviorSchema(
            work_patterns=[],
            decision_speed="chaotic",   # not in enum
            execution_style=[],
            conflict_style="",
        )
```

```python
# tests/test_schema_voice.py
from agentic_mindset.schema.voice import VoiceSchema

def test_valid_voice():
    v = VoiceSchema(
        tone="measured",
        vocabulary={"preferred": ["position"], "avoided": ["rush"]},
        sentence_style="aphoristic",
        signature_phrases=["Know your enemy"],
    )
    assert v.tone == "measured"
```

```python
# tests/test_schema_sources.py
from agentic_mindset.schema.sources import SourcesSchema
import pytest
from pydantic import ValidationError

def test_valid_sources():
    s = SourcesSchema(sources=[
        {"title": "The Art of War", "type": "book", "accessed": "2026-03-22"},
    ])
    assert s.sources[0].type == "book"

def test_invalid_source_type():
    with pytest.raises(ValidationError):
        SourcesSchema(sources=[
            {"title": "X", "type": "tweet", "accessed": "2026-03-22"},  # not in enum
        ])

def test_minimum_three_sources_enforced():
    with pytest.raises(ValidationError):
        SourcesSchema(sources=[
            {"title": "Only one", "type": "book", "accessed": "2026-03-22"},
        ])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_schema_*.py -v
```
Expected: all FAIL with ImportError

- [ ] **Step 3: Implement all five schemas**

```python
# agentic_mindset/schema/mindset.py
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
    approach: str


class MentalModel(BaseModel):
    name: str
    description: str


class MindsetSchema(BaseModel):
    core_principles: list[CorePrinciple] = []
    decision_framework: DecisionFramework
    thinking_patterns: list[str] = []
    mental_models: list[MentalModel] = []
```

```python
# agentic_mindset/schema/personality.py
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
```

```python
# agentic_mindset/schema/behavior.py
from typing import Literal
from pydantic import BaseModel


class BehaviorSchema(BaseModel):
    work_patterns: list[str] = []
    decision_speed: Literal["slow", "deliberate", "fast", "impulsive"]
    execution_style: list[str] = []
    conflict_style: str
```

```python
# agentic_mindset/schema/voice.py
from pydantic import BaseModel


class Vocabulary(BaseModel):
    preferred: list[str] = []
    avoided: list[str] = []


class VoiceSchema(BaseModel):
    tone: str
    vocabulary: Vocabulary
    sentence_style: str
    signature_phrases: list[str] = []
```

```python
# agentic_mindset/schema/sources.py
from typing import Literal, Optional
from pydantic import BaseModel


class Source(BaseModel):
    title: str
    type: Literal["book", "interview", "article", "talk", "podcast", "screenplay", "manga", "game"]
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
```

- [ ] **Step 4: Run all schema tests**

```bash
pytest tests/test_schema_*.py -v
```
Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add agentic_mindset/schema/ tests/test_schema_*.py
git commit -m "feat: add all five content schemas with enum and range validation"
```

---

## Task 4: CharacterPack

**Files:**
- Create: `agentic_mindset/pack.py`
- Create: `tests/test_pack.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_pack.py
import pytest
import shutil
import tempfile
from pathlib import Path
from agentic_mindset.pack import CharacterPack, PackLoadError


def test_load_valid_pack(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    assert pack.meta.id == "sun-tzu"
    assert pack.meta.type == "historical"
    assert pack.mindset.decision_framework.risk_tolerance == "medium"
    assert pack.personality.traits[0].intensity == 0.9
    assert pack.behavior.decision_speed == "deliberate"
    assert pack.voice.tone == "measured, aphoristic"
    assert len(pack.sources.sources) == 3


def test_missing_required_file(minimal_pack_dir):
    (minimal_pack_dir / "mindset.yaml").unlink()
    with pytest.raises(PackLoadError, match="mindset.yaml"):
        CharacterPack.load(minimal_pack_dir)


def test_invalid_yaml_raises(minimal_pack_dir):
    (minimal_pack_dir / "meta.yaml").write_text("invalid: [yaml: content")
    with pytest.raises(PackLoadError):
        CharacterPack.load(minimal_pack_dir)


def test_schema_validation_error_raises(minimal_pack_dir):
    import yaml
    data = yaml.safe_load((minimal_pack_dir / "behavior.yaml").read_text())
    data["decision_speed"] = "chaotic"
    (minimal_pack_dir / "behavior.yaml").write_text(yaml.dump(data))
    with pytest.raises(PackLoadError, match="behavior.yaml"):
        CharacterPack.load(minimal_pack_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pack.py -v
```

- [ ] **Step 3: Implement `pack.py`**

```python
# agentic_mindset/pack.py
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_pack.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add agentic_mindset/pack.py tests/test_pack.py
git commit -m "feat: CharacterPack loads and validates a character directory"
```

---

## Task 5: CharacterRegistry

**Files:**
- Create: `agentic_mindset/registry.py`
- Create: `tests/test_registry.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_registry.py
import os
import pytest
import shutil
import tempfile
from pathlib import Path
from agentic_mindset.registry import CharacterRegistry
from agentic_mindset.pack import PackLoadError


def test_resolve_by_path(minimal_pack_dir):
    registry = CharacterRegistry()
    pack = registry.load_path(minimal_pack_dir)
    assert pack.meta.id == "sun-tzu"


def test_resolve_by_id_from_explicit_dir(minimal_pack_dir):
    parent = minimal_pack_dir.parent
    # rename the temp dir to use "sun-tzu" as the directory name
    named_dir = parent / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named_dir)
    registry = CharacterRegistry(search_paths=[parent])
    pack = registry.load_id("sun-tzu")
    assert pack.meta.id == "sun-tzu"
    shutil.rmtree(named_dir)


def test_id_not_found_raises(tmp_path):
    registry = CharacterRegistry(search_paths=[tmp_path])
    with pytest.raises(KeyError, match="unknown-id"):
        registry.load_id("unknown-id")


def test_local_overrides_registry(minimal_pack_dir, tmp_path):
    """A pack in search_paths[0] shadows one in search_paths[1]."""
    # create two registries with the same id
    dir1 = tmp_path / "reg1" / "sun-tzu"
    dir2 = tmp_path / "reg2" / "sun-tzu"
    shutil.copytree(minimal_pack_dir, dir1)
    shutil.copytree(minimal_pack_dir, dir2)
    registry = CharacterRegistry(search_paths=[tmp_path / "reg1", tmp_path / "reg2"])
    pack = registry.load_id("sun-tzu")
    assert pack.path == dir1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_registry.py -v
```

- [ ] **Step 3: Implement `registry.py`**

```python
# agentic_mindset/registry.py
import os
from pathlib import Path
from typing import Optional
from agentic_mindset.pack import CharacterPack


_DEFAULT_USER_REGISTRY = Path.home() / ".agentic-mindset" / "registry"
_DEFAULT_LOCAL_REGISTRY = Path("characters")


class CharacterRegistry:
    def __init__(self, search_paths: Optional[list[Path]] = None):
        if search_paths is not None:
            self._search_paths = [Path(p) for p in search_paths]
        else:
            self._search_paths = self._resolve_default_paths()

    @staticmethod
    def _resolve_default_paths() -> list[Path]:
        paths = []
        env = os.environ.get("AGENTIC_MINDSET_REGISTRY")
        if env:
            paths.append(Path(env))
        paths.append(_DEFAULT_USER_REGISTRY)
        paths.append(_DEFAULT_LOCAL_REGISTRY)
        return paths

    def load_path(self, path: Path) -> CharacterPack:
        return CharacterPack.load(Path(path))

    def load_id(self, character_id: str) -> CharacterPack:
        for search_path in self._search_paths:
            candidate = search_path / character_id
            if candidate.is_dir():
                return CharacterPack.load(candidate)
        raise KeyError(f"Character not found: {character_id!r} (searched: {self._search_paths})")

    def list_ids(self) -> list[str]:
        seen = set()
        ids = []
        for search_path in self._search_paths:
            if not search_path.is_dir():
                continue
            for entry in sorted(search_path.iterdir()):
                if entry.is_dir() and entry.name not in seen:
                    seen.add(entry.name)
                    ids.append(entry.name)
        return ids
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_registry.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add agentic_mindset/registry.py tests/test_registry.py
git commit -m "feat: CharacterRegistry with priority-ordered path resolution"
```

---

## Task 6: ContextBlock

**Files:**
- Create: `agentic_mindset/context.py`
- Create: `tests/test_context.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_context.py
from agentic_mindset.context import ContextBlock
from agentic_mindset.pack import CharacterPack


def test_to_prompt_contains_all_sections(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    prompt = block.to_prompt()
    assert "THINKING FRAMEWORK" in prompt
    assert "PERSONALITY" in prompt
    assert "BEHAVIORAL TENDENCIES" in prompt
    assert "VOICE & STYLE" in prompt


def test_to_prompt_contains_preamble(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    prompt = block.to_prompt()
    assert "Sun Tzu" in prompt


def test_to_prompt_xml_tagged(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    xml = block.to_prompt(output_format="xml_tagged")
    assert "<character-context>" in xml
    assert "<thinking-framework>" in xml
    assert "</character-context>" in xml


def test_sections_not_empty(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    assert block.thinking_framework
    assert block.personality
    assert block.behavioral_tendencies
    assert block.voice_and_style
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_context.py -v
```

- [ ] **Step 3: Implement `context.py`**

```python
# agentic_mindset/context.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from agentic_mindset.pack import CharacterPack


@dataclass
class ContextBlock:
    preamble: str
    thinking_framework: list[str]
    personality: list[str]
    behavioral_tendencies: list[str]
    voice_and_style: list[str]

    @classmethod
    def from_packs(
        cls,
        weighted_packs: list[tuple[CharacterPack, float]],
        show_weights: bool = True,
    ) -> "ContextBlock":
        """Build a ContextBlock from one or more (pack, weight) pairs.

        Packs are expected to be sorted by descending weight (highest-weight first).
        Items from higher-weight packs appear first in merged list fields.
        show_weights=False omits percentages from the preamble (used by sequential strategy).
        """
        if show_weights:
            names = [f"{p.meta.name} ({w:.0%})" for p, w in weighted_packs]
        else:
            names = [p.meta.name for p, _ in weighted_packs]
        preamble = "You embody a synthesized mindset drawing from: " + ", ".join(names) + "."

        thinking: list[str] = []
        personality: list[str] = []
        behavioral: list[str] = []
        voice: list[str] = []

        # Packs are processed in weight order (highest first); deduplication preserves first occurrence
        for pack, _ in weighted_packs:
            m = pack.mindset
            for p in m.core_principles:
                line = f"{p.description}: {p.detail}"
                if line not in thinking:
                    thinking.append(line)
            for tp in m.thinking_patterns:
                if tp not in thinking:
                    thinking.append(tp)
            for mm in m.mental_models:
                line = f"{mm.name} — {mm.description}"
                if line not in thinking:
                    thinking.append(line)

            pers = pack.personality
            for t in pers.traits:
                line = f"{t.name} (intensity {t.intensity}): {t.description}"
                if line not in personality:
                    personality.append(line)
            for d in pers.drives:
                if d not in personality:
                    personality.append(d)

            beh = pack.behavior
            for wp in beh.work_patterns:
                if wp not in behavioral:
                    behavioral.append(wp)
            for es in beh.execution_style:
                if es not in behavioral:
                    behavioral.append(es)
            if beh.conflict_style not in behavioral:
                behavioral.append(beh.conflict_style)

            v = pack.voice
            if v.tone not in voice:
                voice.append(f"Tone: {v.tone}")
            for phrase in v.signature_phrases:
                if phrase not in voice:
                    voice.append(f'"{phrase}"')

        return cls(
            preamble=preamble,
            thinking_framework=thinking,
            personality=personality,
            behavioral_tendencies=behavioral,
            voice_and_style=voice,
        )

    def to_prompt(self, output_format: Literal["plain_text", "xml_tagged"] = "plain_text") -> str:
        if output_format == "xml_tagged":
            return self._render_xml()
        return self._render_plain()

    def _render_plain(self) -> str:
        lines = [self.preamble, ""]
        if self.thinking_framework:
            lines += ["THINKING FRAMEWORK:"] + [f"- {l}" for l in self.thinking_framework] + [""]
        if self.personality:
            lines += ["PERSONALITY:"] + [f"- {l}" for l in self.personality] + [""]
        if self.behavioral_tendencies:
            lines += ["BEHAVIORAL TENDENCIES:"] + [f"- {l}" for l in self.behavioral_tendencies] + [""]
        if self.voice_and_style:
            lines += ["VOICE & STYLE:"] + [f"- {l}" for l in self.voice_and_style]
        return "\n".join(lines).strip()

    def _render_xml(self) -> str:
        def section(tag, items):
            if not items:
                return ""
            inner = "\n".join(f"  <item>{i}</item>" for i in items)
            return f"<{tag}>\n{inner}\n</{tag}>"

        parts = ["<character-context>", f"<preamble>{self.preamble}</preamble>"]
        parts.append(section("thinking-framework", self.thinking_framework))
        parts.append(section("personality", self.personality))
        parts.append(section("behavioral-tendencies", self.behavioral_tendencies))
        parts.append(section("voice-and-style", self.voice_and_style))
        parts.append("</character-context>")
        return "\n".join(p for p in parts if p)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_context.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add agentic_mindset/context.py tests/test_context.py
git commit -m "feat: ContextBlock with plain_text and xml_tagged output formats"
```

---

## Task 7: FusionEngine

**Files:**
- Create: `agentic_mindset/fusion.py`
- Create: `tests/test_fusion.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_fusion.py
import pytest
import shutil
import yaml
from pathlib import Path
from agentic_mindset.fusion import FusionEngine, FusionConfig, FusionStrategy
from agentic_mindset.registry import CharacterRegistry
from agentic_mindset.pack import CharacterPack


def test_fuse_single_pack(minimal_pack_dir, tmp_path):
    registry = CharacterRegistry(search_paths=[tmp_path])
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    engine = FusionEngine(registry)
    block = engine.fuse([("sun-tzu", 1.0)])
    assert "Sun Tzu" in block.preamble


def test_weights_normalized(minimal_pack_dir, tmp_path):
    """Weights [0.6, 0.6] should not raise; they get normalized."""
    named1 = tmp_path / "sun-tzu"
    named2 = tmp_path / "marcus-aurelius"
    shutil.copytree(minimal_pack_dir, named1)
    # create a second minimal pack
    shutil.copytree(minimal_pack_dir, named2)
    _patch_meta(named2, "marcus-aurelius", "Marcus Aurelius")
    registry = CharacterRegistry(search_paths=[tmp_path])
    engine = FusionEngine(registry)
    block = engine.fuse([("sun-tzu", 0.6), ("marcus-aurelius", 0.6)])
    assert "50%" in block.preamble


def test_zero_weight_raises(minimal_pack_dir, tmp_path):
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    registry = CharacterRegistry(search_paths=[tmp_path])
    engine = FusionEngine(registry)
    with pytest.raises(ValueError, match="sum to zero"):
        engine.fuse([("sun-tzu", 0.0)])


def test_sequential_strategy_list_order_not_weight_order(minimal_pack_dir, tmp_path):
    """Sequential uses list order; even with low weight, first-listed character leads."""
    named1 = tmp_path / "sun-tzu"
    named2 = tmp_path / "marcus-aurelius"
    shutil.copytree(minimal_pack_dir, named1)
    shutil.copytree(minimal_pack_dir, named2)
    _patch_meta(named2, "marcus-aurelius", "Marcus Aurelius")
    registry = CharacterRegistry(search_paths=[tmp_path])
    engine = FusionEngine(registry)
    # sun-tzu has weight 0.1 (would lose in blend), but is first in list
    config = FusionConfig(
        characters=[("sun-tzu", 0.1), ("marcus-aurelius", 0.9)],
        fusion_strategy=FusionStrategy.sequential,
    )
    block = engine.fuse_config(config)
    # sun-tzu must appear first in preamble despite lower weight
    assert block.preamble.index("Sun Tzu") < block.preamble.index("Marcus Aurelius")
    # sequential preamble shows no percentages
    assert "%" not in block.preamble


def test_sequential_emits_warning_when_weights_given(minimal_pack_dir, tmp_path, capsys):
    named1 = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named1)
    registry = CharacterRegistry(search_paths=[tmp_path])
    engine = FusionEngine(registry)
    config = FusionConfig(
        characters=[("sun-tzu", 0.7)],
        fusion_strategy=FusionStrategy.sequential,
    )
    engine.fuse_config(config)
    captured = capsys.readouterr()
    assert "warning" in captured.err.lower() or "sequential" in captured.err.lower()


def test_dominant_highest_weight_leads(minimal_pack_dir, tmp_path):
    """In dominant mode, the highest-weight character leads regardless of list order."""
    named1 = tmp_path / "sun-tzu"
    named2 = tmp_path / "marcus-aurelius"
    shutil.copytree(minimal_pack_dir, named1)
    shutil.copytree(minimal_pack_dir, named2)
    _patch_meta(named2, "marcus-aurelius", "Marcus Aurelius")
    registry = CharacterRegistry(search_paths=[tmp_path])
    engine = FusionEngine(registry)
    # marcus-aurelius listed second but has higher weight — should lead in dominant mode
    config = FusionConfig(
        characters=[("sun-tzu", 0.3), ("marcus-aurelius", 0.7)],
        fusion_strategy=FusionStrategy.dominant,
    )
    block = engine.fuse_config(config)
    assert block.preamble.index("Marcus Aurelius") < block.preamble.index("Sun Tzu")


def _patch_meta(pack_dir: Path, new_id: str, new_name: str):
    meta_path = pack_dir / "meta.yaml"
    data = yaml.safe_load(meta_path.read_text())
    data["id"] = new_id
    data["name"] = new_name
    meta_path.write_text(yaml.dump(data))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_fusion.py -v
```

- [ ] **Step 3: Implement `fusion.py`**

```python
# agentic_mindset/fusion.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from agentic_mindset.registry import CharacterRegistry
from agentic_mindset.pack import CharacterPack
from agentic_mindset.context import ContextBlock


class FusionStrategy(str, Enum):
    blend = "blend"
    dominant = "dominant"
    sequential = "sequential"


@dataclass
class FusionConfig:
    characters: list[tuple[str, float]]   # [(id, weight), ...]
    fusion_strategy: FusionStrategy = FusionStrategy.blend
    output_format: str = "plain_text"


class FusionEngine:
    def __init__(self, registry: CharacterRegistry):
        self._registry = registry

    def fuse(
        self,
        characters: list[tuple[str, float]],
        strategy: FusionStrategy = FusionStrategy.blend,
    ) -> ContextBlock:
        return self.fuse_config(FusionConfig(characters=characters, fusion_strategy=strategy))

    def fuse_config(self, config: FusionConfig) -> ContextBlock:
        import sys
        raw_pairs = config.characters
        total = sum(w for _, w in raw_pairs)
        if total == 0:
            raise ValueError("Weights sum to zero — cannot normalize.")

        if config.fusion_strategy == FusionStrategy.sequential:
            # Warn if non-trivial weights were provided (they are ignored in sequential mode)
            non_equal = len(set(w for _, w in raw_pairs)) > 1
            if non_equal:
                print(
                    "Warning: sequential strategy ignores weights. "
                    "Character order in the list determines precedence.",
                    file=sys.stderr,
                )
            # sequential: preserve list order, equal display weights (no percentages shown)
            weighted_packs = [
                (self._registry.load_id(cid), 1.0 / len(raw_pairs))
                for cid, _ in raw_pairs
            ]
            return ContextBlock.from_packs(weighted_packs, show_weights=False)

        # blend / dominant: normalize weights, sort by weight descending
        weighted_packs = [
            (self._registry.load_id(cid), w / total)
            for cid, w in raw_pairs
        ]
        # Sort by weight descending — highest-weight character leads in both blend and dominant
        weighted_packs.sort(key=lambda x: x[1], reverse=True)
        return ContextBlock.from_packs(weighted_packs, show_weights=True)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_fusion.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add agentic_mindset/fusion.py tests/test_fusion.py
git commit -m "feat: FusionEngine with blend/dominant/sequential strategies and weight normalization"
```

---

## Task 8: CLI

**Files:**
- Create: `agentic_mindset/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cli.py
import shutil
from typer.testing import CliRunner
from agentic_mindset.cli import app

runner = CliRunner()


def test_validate_valid_pack(minimal_pack_dir):
    result = runner.invoke(app, ["validate", str(minimal_pack_dir)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_missing_file(minimal_pack_dir):
    (minimal_pack_dir / "mindset.yaml").unlink()
    result = runner.invoke(app, ["validate", str(minimal_pack_dir)])
    assert result.exit_code != 0
    assert "mindset.yaml" in result.output


def test_preview_single_pack(minimal_pack_dir):
    result = runner.invoke(app, ["preview", str(minimal_pack_dir)])
    assert result.exit_code == 0
    assert "THINKING FRAMEWORK" in result.output
    assert "Sun Tzu" in result.output


def test_init_creates_files(tmp_path):
    result = runner.invoke(app, ["init", "my-hero", "--type", "fictional", "--output", str(tmp_path)])
    assert result.exit_code == 0
    for fname in ["meta.yaml", "mindset.yaml", "personality.yaml", "behavior.yaml", "voice.yaml", "sources.yaml"]:
        assert (tmp_path / "my-hero" / fname).exists()


def test_list_shows_characters(minimal_pack_dir, tmp_path):
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    result = runner.invoke(app, ["list", "--registry", str(tmp_path)])
    assert result.exit_code == 0
    assert "sun-tzu" in result.output


def test_list_empty_registry(tmp_path):
    result = runner.invoke(app, ["list", "--registry", str(tmp_path)])
    assert result.exit_code == 0
    assert "no characters" in result.output.lower()


def test_preview_fusion_respects_registry_flag(minimal_pack_dir, tmp_path):
    """--registry flag must be respected in --fusion preview, not silently ignored."""
    import yaml as _yaml
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    fusion_file = tmp_path / "blend.yaml"
    fusion_file.write_text(_yaml.dump({
        "characters": [{"id": "sun-tzu", "weight": 1.0}],
        "fusion_strategy": "blend",
    }))
    result = runner.invoke(app, [
        "preview", "--fusion", str(fusion_file),
        "--registry", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert "Sun Tzu" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli.py -v
```

- [ ] **Step 3: Implement `cli.py`**

```python
# agentic_mindset/cli.py
from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional
import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from agentic_mindset.pack import CharacterPack, PackLoadError
from agentic_mindset.registry import CharacterRegistry
from agentic_mindset.fusion import FusionEngine, FusionStrategy
from agentic_mindset.context import ContextBlock

app = typer.Typer(name="mindset", help="Agentic Mindset CLI")
console = Console()

_TEMPLATE_META = {
    "id": "{id}",
    "name": "{name}",
    "version": "1.0.0",
    "schema_version": "1.0",
    "type": "{type}",
    "description": "TODO: describe this character",
    "tags": [],
    "authors": [{"name": "TODO", "url": ""}],
    "created": "{today}",
}
_TEMPLATE_MINDSET = {
    "core_principles": [{"description": "TODO", "detail": "TODO"}],
    "decision_framework": {"risk_tolerance": "medium", "time_horizon": "long-term", "approach": "TODO"},
    "thinking_patterns": ["TODO"],
    "mental_models": [{"name": "TODO", "description": "TODO"}],
}
_TEMPLATE_PERSONALITY = {
    "traits": [{"name": "TODO", "description": "TODO", "intensity": 0.5}],
    "emotional_tendencies": {"stress_response": "TODO", "motivation_source": "TODO"},
    "interpersonal_style": {"communication": "TODO", "leadership": "TODO"},
    "drives": ["TODO"],
}
_TEMPLATE_BEHAVIOR = {
    "work_patterns": ["TODO"],
    "decision_speed": "deliberate",
    "execution_style": ["TODO"],
    "conflict_style": "TODO",
}
_TEMPLATE_VOICE = {
    "tone": "TODO",
    "vocabulary": {"preferred": [], "avoided": []},
    "sentence_style": "TODO",
    "signature_phrases": [],
}
_TEMPLATE_SOURCES = {
    "sources": [{"title": "TODO", "type": "book", "accessed": "2026-01-01"}]
}


@app.command()
def init(
    character_id: str = typer.Argument(..., help="Character ID (kebab-case)"),
    type_: str = typer.Option("historical", "--type", help="historical or fictional"),
    output: Optional[Path] = typer.Option(None, "--output", help="Directory to create pack in"),
):
    """Scaffold a new empty character pack."""
    from datetime import date
    out_dir = (output or Path(".")) / character_id
    if out_dir.exists():
        console.print(f"[red]Directory already exists: {out_dir}[/red]")
        raise typer.Exit(1)
    out_dir.mkdir(parents=True)

    name = character_id.replace("-", " ").title()
    today = date.today().isoformat()

    def _render(template: dict) -> dict:
        import json
        s = json.dumps(template)
        s = s.replace("{id}", character_id).replace("{name}", name).replace("{type}", type_).replace("{today}", today)
        return json.loads(s)

    files = {
        "meta.yaml": _render(_TEMPLATE_META),
        "mindset.yaml": _TEMPLATE_MINDSET,
        "personality.yaml": _TEMPLATE_PERSONALITY,
        "behavior.yaml": _TEMPLATE_BEHAVIOR,
        "voice.yaml": _TEMPLATE_VOICE,
        "sources.yaml": _TEMPLATE_SOURCES,
    }
    for fname, data in files.items():
        (out_dir / fname).write_text(yaml.dump(data, allow_unicode=True))

    console.print(f"[green]Created character pack:[/green] {out_dir}")


@app.command()
def validate(
    pack_path: Path = typer.Argument(..., help="Path to character pack directory"),
):
    """Validate a character pack against the schema."""
    try:
        CharacterPack.load(pack_path)
        console.print(f"[green]✓ Pack is valid:[/green] {pack_path}")
    except PackLoadError as e:
        console.print(f"[red]✗ Validation failed:[/red]\n{e}")
        raise typer.Exit(1)


@app.command()
def preview(
    pack_path: Optional[Path] = typer.Argument(None, help="Path to a single character pack"),
    fusion_config: Optional[Path] = typer.Option(None, "--fusion", help="Path to fusion.yaml"),
    output_format: str = typer.Option("plain_text", "--format", help="plain_text or xml_tagged"),
    registry_path: Optional[Path] = typer.Option(None, "--registry", help="Override registry path"),
):
    """Preview the Context Block for a character or fusion."""
    if pack_path is None and fusion_config is None:
        console.print("[red]Provide either a pack path or --fusion config.[/red]")
        raise typer.Exit(1)

    if pack_path:
        pack = CharacterPack.load(pack_path)
        block = ContextBlock.from_packs([(pack, 1.0)])
    else:
        cfg = yaml.safe_load(fusion_config.read_text(encoding="utf-8"))
        search_paths = [registry_path] if registry_path else None
        registry = CharacterRegistry(search_paths=search_paths)
        engine = FusionEngine(registry)
        chars = [(c["id"], c["weight"]) for c in cfg["characters"]]
        strategy = FusionStrategy(cfg.get("fusion_strategy", "blend"))
        block = engine.fuse(chars, strategy=strategy)

    console.print(Panel(block.to_prompt(output_format=output_format), title="Context Block"))


@app.command("list")
def list_characters(
    registry: Optional[Path] = typer.Option(None, "--registry", help="Override registry path"),
):
    """List available characters in the registry."""
    search_paths = [registry] if registry else None
    reg = CharacterRegistry(search_paths=search_paths)
    ids = reg.list_ids()
    if not ids:
        console.print("[yellow]No characters found.[/yellow]")
    for cid in ids:
        console.print(f"  {cid}")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_cli.py -v
```
Expected: 5 PASSED

- [ ] **Step 5: Verify CLI works end-to-end**

```bash
mindset --help
mindset init test-hero --type fictional --output /tmp
mindset validate /tmp/test-hero
```

- [ ] **Step 6: Commit**

```bash
git add agentic_mindset/cli.py tests/test_cli.py
git commit -m "feat: CLI with init, validate, preview, list commands"
```

---

## Task 9: Standard Library — Sun Tzu

**Files:**
- Create: `characters/sun-tzu/` (all 6 YAML files)

- [ ] **Step 1: Create the Sun Tzu character pack**

```bash
mindset init sun-tzu --type historical --output characters/
```

Then fill each file with real content:

**`characters/sun-tzu/meta.yaml`**
```yaml
id: sun-tzu
name: Sun Tzu
version: 1.0.0
schema_version: '1.0'
type: historical
description: Chinese military strategist (544–496 BC), author of The Art of War. Master
  of strategic patience, deception, and winning without direct conflict.
tags:
- strategy
- philosophy
- military
- historical
authors:
- name: agentic-mindset contributors
  url: https://github.com/aurorie/agentic-mindset
created: '2026-03-22'
```

**`characters/sun-tzu/mindset.yaml`**
```yaml
core_principles:
- description: Strategic deception
  detail: All warfare is based on deception. Appear weak when you are strong, and
    strong when you are weak.
  confidence: 0.98
- description: Win before the battle
  detail: Supreme excellence consists in breaking the enemy's resistance without fighting.
  confidence: 0.98
- description: Know yourself and your enemy
  detail: If you know the enemy and know yourself, you need not fear the result of
    a hundred battles.
  confidence: 0.98
decision_framework:
  risk_tolerance: medium
  time_horizon: long-term
  approach: Gather intelligence, choose ground carefully, and act only when victory
    is certain. Avoid battle when conditions are unfavorable.
thinking_patterns:
- Reverse-engineer from the desired end state
- Identify the enemy's weaknesses before committing to action
- Use the enemy's momentum and strength against them
mental_models:
- name: Empty Fort Strategy
  description: Use apparent vulnerability to create uncertainty and hesitation in
    opponents
- name: Shi (势) — Strategic Advantage
  description: Position yourself so that circumstances naturally carry you to victory
- name: Five Factors
  description: Evaluate any situation across moral law, heaven, earth, commander,
    and method
```

**`characters/sun-tzu/personality.yaml`**
```yaml
traits:
- name: Patience
  description: Waits for the optimal moment with absolute discipline; never acts
    from impatience or ego
  intensity: 0.95
- name: Pragmatism
  description: Victory matters, not glory; any method that works is valid
  intensity: 0.9
- name: Detachment
  description: Operates without emotional attachment to outcome; analyzes coldly
  intensity: 0.85
emotional_tendencies:
  stress_response: Withdraws to observe; increases information gathering before acting
  motivation_source: Victory through minimum force and maximum efficiency
interpersonal_style:
  communication: Indirect, layered with meaning; uses metaphor and paradox
  leadership: Leads through positioning and preparation, not charisma or direct command
drives:
- Strategic mastery
- Minimum cost, maximum result
- Understanding the nature of conflict itself
```

**`characters/sun-tzu/behavior.yaml`**
```yaml
work_patterns:
- Exhaustive preparation and intelligence-gathering before any action
- Constant situational awareness; always reads the terrain
- Adapts tactics instantly when conditions change
decision_speed: deliberate
execution_style:
- Strike only when conditions are fully favorable
- Leave the enemy a path to retreat to avoid desperate resistance
- Control the battlefield before the battle begins
conflict_style: Avoidant of direct confrontation; prefers positioning and indirect
  action
```

**`characters/sun-tzu/voice.yaml`**
```yaml
tone: Measured, aphoristic, authoritative; every word deliberate
vocabulary:
  preferred:
  - position
  - opportunity
  - adapt
  - observe
  - terrain
  - advantage
  avoided:
  - rush
  - obvious
  - certain
  - always
sentence_style: Short aphorisms; layers of meaning; frequent use of paradox and inversion
signature_phrases:
- Supreme excellence consists in breaking the enemy's resistance without fighting
- Know your enemy and know yourself; in a hundred battles, you will never be defeated
- The supreme art of war is to subdue the enemy without fighting
- Victorious warriors win first and then go to war; defeated warriors go to war first
  and then seek to win
```

**`characters/sun-tzu/sources.yaml`**
```yaml
sources:
- title: The Art of War (Lionel Giles translation, 1910)
  type: book
  url: https://suntzusaid.com/book/
  accessed: '2026-03-22'
- title: The Art of War (Samuel Griffith translation, 1963)
  type: book
  accessed: '2026-03-22'
- title: Sun Tzu on the Art of War — commentary (Thomas Cleary)
  type: book
  accessed: '2026-03-22'
```

- [ ] **Step 2: Validate the pack**

```bash
mindset validate characters/sun-tzu/
```
Expected: `✓ Pack is valid`

- [ ] **Step 3: Preview the pack**

```bash
mindset preview characters/sun-tzu/
```
Expected: full Context Block printed with all five sections

- [ ] **Step 4: Commit**

```bash
git add characters/sun-tzu/
git commit -m "feat: add Sun Tzu to standard library"
```

---

## Task 10: Standard Library — Marcus Aurelius

**Files:**
- Create: `characters/marcus-aurelius/` (all 6 YAML files)

- [ ] **Step 1: Scaffold and fill Marcus Aurelius pack**

```bash
mindset init marcus-aurelius --type historical --output characters/
```

**`characters/marcus-aurelius/meta.yaml`**
```yaml
id: marcus-aurelius
name: Marcus Aurelius
version: 1.0.0
schema_version: '1.0'
type: historical
description: Roman Emperor (121–180 AD) and Stoic philosopher. Author of Meditations.
  Embodiment of disciplined reason, duty, and equanimity under pressure.
tags:
- philosophy
- stoicism
- leadership
- historical
authors:
- name: agentic-mindset contributors
  url: https://github.com/aurorie/agentic-mindset
created: '2026-03-22'
```

**`characters/marcus-aurelius/mindset.yaml`**
```yaml
core_principles:
- description: Dichotomy of control
  detail: Focus only on what is within your control — your thoughts, judgments, and
    actions. Everything else is indifferent.
  confidence: 0.98
- description: Virtue as the highest good
  detail: The only true good is virtue; the only true evil is vice. External things
    are neither good nor bad.
  confidence: 0.97
- description: Memento mori
  detail: Contemplate death regularly to clarify what matters and act with urgency
    on what is right.
  confidence: 0.95
decision_framework:
  risk_tolerance: low
  time_horizon: long-term
  approach: Ask what the virtuous action is, act on it without attachment to outcome,
    accept whatever results as fate (amor fati).
thinking_patterns:
- Negative visualization — imagine the worst to appreciate what you have
- View from above — zoom out to the cosmic scale to dissolve petty concerns
- Return to the present moment when distracted by past or future
mental_models:
- name: Logos
  description: The rational principle underlying all reality; align your reason with
    the universal reason
- name: Amor Fati
  description: Love of fate; not just acceptance but active love of whatever happens
- name: The Obstacle is the Way
  description: Every obstacle is an opportunity to practice virtue and grow stronger
```

**`characters/marcus-aurelius/personality.yaml`**
```yaml
traits:
- name: Equanimity
  description: Maintains emotional balance under all circumstances; neither elated
    by success nor crushed by failure
  intensity: 0.95
- name: Self-discipline
  description: Holds himself to strict standards regardless of external consequences
    or rewards
  intensity: 0.9
- name: Humility
  description: Constantly aware of his own limitations and biases; actively seeks
    correction
  intensity: 0.85
emotional_tendencies:
  stress_response: Returns to Stoic principles; writes in journal to clarify thinking
  motivation_source: Duty to the common good and to living according to nature
interpersonal_style:
  communication: Direct but gentle; acknowledges others' perspectives; leads by example
  leadership: Leads through character and consistency, not authority
drives:
- Virtue and moral excellence
- Service to others and the common good
- Self-mastery and rational clarity
```

**`characters/marcus-aurelius/behavior.yaml`**
```yaml
work_patterns:
- Begins each day with a Stoic meditation on challenges ahead
- Reviews actions at end of day against his own standards
- Seeks out difficult tasks as opportunities for growth
decision_speed: deliberate
execution_style:
- Act from duty, not desire or fear
- Do the right thing without waiting for recognition
- Persist through obstacles by reframing them as opportunities
conflict_style: Non-reactive; seeks to understand the other's perspective; responds
  with reason not emotion
```

**`characters/marcus-aurelius/voice.yaml`**
```yaml
tone: Reflective, measured, honest; speaks to himself as much as to others
vocabulary:
  preferred:
  - virtue
  - reason
  - duty
  - impermanent
  - nature
  - equanimity
  avoided:
  - glory
  - fame
  - pleasure
  - fear
sentence_style: Meditative and self-questioning; uses imperatives directed at himself;
  short, dense observations
signature_phrases:
- You have power over your mind, not outside events. Realize this, and you will find
  strength.
- The impediment to action advances action. What stands in the way becomes the way.
- Waste no more time arguing about what a good person should be. Be one.
- Accept the things to which fate binds you, and love the people with whom fate brings
  you together.
```

**`characters/marcus-aurelius/sources.yaml`**
```yaml
sources:
- title: Meditations (Gregory Hays translation, 2002)
  type: book
  accessed: '2026-03-22'
- title: Meditations (George Long translation, 1862)
  type: book
  url: https://www.gutenberg.org/ebooks/2680
  accessed: '2026-03-22'
- title: How to Think Like a Roman Emperor (Donald Robertson, 2019)
  type: book
  accessed: '2026-03-22'
```

- [ ] **Step 2: Validate and preview**

```bash
mindset validate characters/marcus-aurelius/
mindset preview characters/marcus-aurelius/
```

- [ ] **Step 3: Test a fusion of both standard library packs**

Create `examples/sun-tzu-aurelius.yaml`:
```yaml
characters:
  - id: sun-tzu
    weight: 0.5
  - id: marcus-aurelius
    weight: 0.5
fusion_strategy: blend
```

```bash
mindset preview --fusion examples/sun-tzu-aurelius.yaml
```
Expected: Context Block blending both characters

- [ ] **Step 4: Commit**

```bash
git add characters/marcus-aurelius/ examples/
git commit -m "feat: add Marcus Aurelius to standard library; add blend example"
```

---

## Task 11: Run Full Test Suite and Coverage Check

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v --cov=agentic_mindset --cov-report=term-missing
```
Expected: all PASSED, coverage ≥ 80%

- [ ] **Step 2: Add placeholder extraction prompt**

```bash
mkdir -p prompts
```

Create `prompts/extract-v1.md`:
```markdown
# Extraction Prompt v1

> This is a placeholder for Plan 2 (Build Pipeline). The extraction prompt template
> will be defined here and versioned alongside schema_version 1.x.

## Purpose
This prompt is used by `mindset build` to instruct an LLM to extract
structured character data from source documents into the Mindset Schema format.
```

- [ ] **Step 3: Add CONTRIBUTING.md**

Create `CONTRIBUTING.md`:
```markdown
# Contributing to Agentic Mindset

## Character Pack Contributions

### Scope
- **Historical figures** (deceased persons with documented public records)
- **Fictional characters** (from literature, anime, games, mythology)
- Living persons are **not accepted** into the standard library

### Requirements
- Minimum 3 distinct source materials in `sources.yaml`
- All six schema files present and passing `mindset validate`
- Sources must be publicly accessible
- For fictional characters: primary sources must include the original work
- For historical figures: primary sources (writings, documented speeches) preferred

### Process
1. Fork the repository
2. Run `mindset init <id> --type <historical|fictional> --output characters/`
3. Fill in all YAML files with accurate content
4. Add sources to `sources.yaml`
5. Run `mindset validate characters/<id>/` — must pass
6. Run `mindset preview characters/<id>/` — review the output for quality
7. Open a Pull Request with a brief description of your sources
```

- [ ] **Step 4: Final commit**

```bash
git add prompts/ CONTRIBUTING.md
git commit -m "docs: add extraction prompt placeholder and CONTRIBUTING.md"
```

---

## Out of Scope (Deferred to Later Plans)

- **`mindset build`** (LLM Extractor) — Plan 2
- **`mindset migrate`** (schema version migration) — Plan 3. The `schema_version` field is validated on load, but migration logic requires at least one additional schema version to exist, so it is deferred until the first breaking schema change.

---

## Done

At this point the project has:
- Full schema validation for all 6 YAML files
- CharacterPack loader with descriptive error messages
- CharacterRegistry with priority-ordered path resolution
- FusionEngine with blend/dominant/sequential strategies
- ContextBlock with plain_text and xml_tagged output
- CLI: `init`, `validate`, `preview`, `list`
- 2 standard library packs: Sun Tzu, Marcus Aurelius
- Full test suite with ≥80% coverage

**Next: Plan 2 — Build Pipeline (LLM Extractor)**

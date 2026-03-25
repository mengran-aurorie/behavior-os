# Schema Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich the Character Pack schema from a descriptive YAML format into a more computable persona DSL — structuring the highest-impact runtime fields while preserving full backward compatibility with all 13 existing packs.

**Architecture:** Five sequential tasks: (1) mindset.py — structured DecisionFramework; (2) personality.py — Drive objects, Trait confidence, EmotionalTendencies expansion, ConditionalVariant conjunction, plus a one-line context.py fix; (3) behavior + voice + meta + sources — decision_control (breaking: removes `impulsive` from `decision_speed`), ToneAxes, license/visibility, expanded source types + evidence_level; (4) conftest.py update; (5) character pack YAML enrichment. All new fields are Optional with defaults — no existing pack breaks.

**Tech Stack:** Python 3.11+, Pydantic v2, pytest, YAML (ruamel/pyyaml).

**Spec:** User design review — see conversation 2026-03-25.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `agentic_mindset/schema/mindset.py` | Modify | Add `heuristics`, `default_strategy`, `fallback_strategy`, `commitment_policy` to `DecisionFramework` |
| `agentic_mindset/schema/personality.py` | Modify | Add `Drive` class; `Trait.confidence`; expand `EmotionalTendencies`; add `ConditionalVariant.conjunction` |
| `agentic_mindset/schema/behavior.py` | Modify | Remove `impulsive` from `decision_speed`; add `decision_control` |
| `agentic_mindset/schema/voice.py` | Modify | Add `ToneAxes` class and `VoiceSchema.tone_axes` |
| `agentic_mindset/schema/meta.py` | Modify | Add `license`, `visibility` |
| `agentic_mindset/schema/sources.py` | Modify | Expand `type` enum; add `evidence_level` |
| `agentic_mindset/context.py` | Modify | Fix `from_packs()` drives loop: `personality.append(str(d))` to avoid mixed Drive/str list |
| `tests/test_schema_mindset.py` | Modify | Cover new DecisionFramework fields |
| `tests/test_schema_personality.py` | Modify | Cover Drive, Trait.confidence, EmotionalTendencies, ConditionalVariant.conjunction |
| `tests/test_schema_behavior.py` | Modify | Cover decision_control; verify impulsive rejected |
| `tests/test_schema_voice.py` | Modify | Cover ToneAxes |
| `tests/test_schema_meta.py` | Modify | Cover license, visibility |
| `tests/test_schema_sources.py` | Modify | Cover new source types, evidence_level |
| `tests/conftest.py` | Modify | Update `minimal_pack_dir` fixture with new optional fields |
| `characters/*/mindset.yaml` | Modify | Add heuristics, default_strategy, fallback_strategy, commitment_policy (13 chars) |
| `characters/*/personality.yaml` | Modify | Add baseline_mood, emotional_range, frustration_trigger, recovery_pattern; upgrade drives to Drive objects (13 chars) |
| `characters/*/behavior.yaml` | Modify | Add decision_control (13 chars) |
| `characters/*/voice.yaml` | Modify | Add tone_axes (13 chars) |

---

## Task 1: mindset.py — structured DecisionFramework

**Context:** `DecisionFramework.approach` is a freeform string containing strategy, heuristics, fallback, and commitment timing all mixed together. Split into typed fields. Keep `approach: str` required for backward compatibility — all existing packs already have it. New fields are all optional.

The resolver (resolver.py:237) uses `m.decision_framework.approach` — this still works unchanged.

**Files:**
- Modify: `agentic_mindset/schema/mindset.py`
- Modify: `tests/test_schema_mindset.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_schema_mindset.py`:

```python
def test_decision_framework_new_fields_optional():
    """All new DecisionFramework fields are optional — existing packs load unchanged."""
    from agentic_mindset.schema.mindset import DecisionFramework
    df = DecisionFramework(
        risk_tolerance="medium",
        time_horizon="long-term",
        approach="Act only when victory is certain.",
    )
    assert df.heuristics == []
    assert df.default_strategy is None
    assert df.fallback_strategy is None
    assert df.commitment_policy is None


def test_decision_framework_with_all_new_fields():
    from agentic_mindset.schema.mindset import DecisionFramework
    df = DecisionFramework(
        risk_tolerance="high",
        time_horizon="long-term",
        approach="Win before the battle begins.",
        heuristics=["Gather intel before committing", "Prefer indirect routes"],
        default_strategy="Position for inevitable victory through preparation",
        fallback_strategy="Retreat and regroup; never pursue desperate battle",
        commitment_policy="late",
    )
    assert df.heuristics == ["Gather intel before committing", "Prefer indirect routes"]
    assert df.commitment_policy == "late"


def test_decision_framework_commitment_policy_enum():
    """commitment_policy only accepts early | deliberate | late."""
    from agentic_mindset.schema.mindset import DecisionFramework
    import pytest
    with pytest.raises(Exception):
        DecisionFramework(
            risk_tolerance="medium",
            time_horizon="long-term",
            approach="...",
            commitment_policy="never",
        )
```

- [ ] **Step 2: Run to verify fail**

```bash
python3 -m pytest tests/test_schema_mindset.py -v 2>&1 | tail -20
```

Expected: 3 new tests FAIL with `unexpected keyword argument` or validation error.

- [ ] **Step 3: Implement**

Replace `DecisionFramework` in `agentic_mindset/schema/mindset.py`:

```python
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
```

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest tests/test_schema_mindset.py -v 2>&1 | tail -20
```

Expected: All tests PASS.

- [ ] **Step 5: Run full suite**

```bash
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5
```

Expected: All passing (188+).

- [ ] **Step 6: Commit**

```bash
git add agentic_mindset/schema/mindset.py tests/test_schema_mindset.py
git commit -m "feat: add heuristics/default_strategy/fallback_strategy/commitment_policy to DecisionFramework"
```

---

## Task 2: personality.py — Drive objects, Trait confidence, EmotionalTendencies, ConditionalVariant conjunction

**Context:** Four changes in one file:
1. `Drive` replaces `list[str]` drives — backward compat validator normalizes bare strings to `Drive(name=str, intensity=0.8)`. Add `__str__` so context.py's `f"- {d}"` still renders correctly.
2. `Trait.confidence` — optional float 0.0–1.0, matches `CorePrinciple.confidence` pattern.
3. `EmotionalTendencies` — add `baseline_mood`, `emotional_range`, `frustration_trigger`, `recovery_pattern`. Note: `sun-tzu` pack already has `frustration_trigger` in YAML (silently ignored by Pydantic until now).
4. `ConditionalVariant.conjunction` — add `"any" | "all"` default `"any"`, matching the IR side.

**Files:**
- Modify: `agentic_mindset/schema/personality.py`
- Modify: `tests/test_schema_personality.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_schema_personality.py`:

```python
# ── Drive ──────────────────────────────────────────────────────────────────────

def test_drive_from_object():
    from agentic_mindset.schema.personality import Drive
    d = Drive(name="strategic_mastery", intensity=0.95, description="Win through positioning")
    assert d.name == "strategic_mastery"
    assert d.intensity == 0.95
    assert str(d) == "strategic_mastery"


def test_drive_str_normalized_to_drive():
    """Bare string in drives list is auto-wrapped as Drive with intensity 0.8."""
    from agentic_mindset.schema.personality import PersonalitySchema, Drive
    p = PersonalitySchema(
        emotional_tendencies={"stress_response": "withdraws", "motivation_source": "victory"},
        interpersonal_style={"communication": "indirect", "leadership": "by positioning"},
        drives=["strategic mastery", "efficiency"],
    )
    assert isinstance(p.drives[0], Drive)
    assert p.drives[0].name == "strategic mastery"
    assert p.drives[0].intensity == 0.8


def test_drive_intensity_out_of_range_raises():
    from agentic_mindset.schema.personality import Drive
    import pytest
    with pytest.raises(Exception):
        Drive(name="x", intensity=1.5)


def test_drive_str_renders_name():
    from agentic_mindset.schema.personality import Drive
    d = Drive(name="strategic mastery", intensity=0.95)
    assert str(d) == "strategic mastery"


# ── Trait confidence ───────────────────────────────────────────────────────────

def test_trait_confidence_optional():
    from agentic_mindset.schema.personality import Trait
    t = Trait(name="patience", description="waits", intensity=0.9)
    assert t.confidence is None


def test_trait_confidence_valid():
    from agentic_mindset.schema.personality import Trait
    t = Trait(name="patience", description="waits", intensity=0.9, confidence=0.85)
    assert t.confidence == 0.85


def test_trait_confidence_out_of_range_raises():
    from agentic_mindset.schema.personality import Trait
    import pytest
    with pytest.raises(Exception):
        Trait(name="x", description="x", intensity=0.5, confidence=1.5)


# ── EmotionalTendencies ────────────────────────────────────────────────────────

def test_emotional_tendencies_new_fields_optional():
    from agentic_mindset.schema.personality import EmotionalTendencies
    et = EmotionalTendencies(stress_response="withdraws", motivation_source="victory")
    assert et.baseline_mood is None
    assert et.emotional_range is None
    assert et.frustration_trigger is None
    assert et.recovery_pattern is None


def test_emotional_tendencies_with_all_new_fields():
    from agentic_mindset.schema.personality import EmotionalTendencies
    et = EmotionalTendencies(
        stress_response="withdraws",
        motivation_source="victory",
        baseline_mood="calm, watchful",
        emotional_range="narrow",
        frustration_trigger="impulsive action without reconnaissance",
        recovery_pattern="retreats to solitude; rebuilds information map",
    )
    assert et.emotional_range == "narrow"
    assert et.frustration_trigger == "impulsive action without reconnaissance"


def test_emotional_tendencies_emotional_range_enum():
    from agentic_mindset.schema.personality import EmotionalTendencies
    import pytest
    with pytest.raises(Exception):
        EmotionalTendencies(
            stress_response="x",
            motivation_source="y",
            emotional_range="extreme",
        )


# ── ConditionalVariant conjunction ────────────────────────────────────────────

def test_conditional_variant_conjunction_default():
    from agentic_mindset.schema.personality import ConditionalVariant
    cv = ConditionalVariant(value="direct", applies_when=["clarity_critical"])
    assert cv.conjunction == "any"


def test_conditional_variant_conjunction_all():
    from agentic_mindset.schema.personality import ConditionalVariant
    cv = ConditionalVariant(
        value="direct",
        applies_when=["clarity_critical", "execution_phase"],
        conjunction="all",
    )
    assert cv.conjunction == "all"


def test_conditional_variant_conjunction_invalid():
    from agentic_mindset.schema.personality import ConditionalVariant
    import pytest
    with pytest.raises(Exception):
        ConditionalVariant(value="direct", applies_when=[], conjunction="maybe")
```

- [ ] **Step 2: Run to verify fail**

```bash
python3 -m pytest tests/test_schema_personality.py -v 2>&1 | tail -25
```

Expected: New tests FAIL.

- [ ] **Step 3: Implement**

Replace `agentic_mindset/schema/personality.py` entirely:

```python
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
    baseline_mood: Optional[str] = None                                         # NEW
    emotional_range: Optional[Literal["narrow", "moderate", "wide"]] = None    # NEW
    frustration_trigger: Optional[str] = None                                   # NEW
    recovery_pattern: Optional[str] = None                                      # NEW


class ConditionalVariant(BaseModel):
    value: str
    applies_when: list[str] = []
    conjunction: Literal["any", "all"] = "any"                                  # NEW (matches IR side)
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
```

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest tests/test_schema_personality.py -v 2>&1 | tail -25
```

Expected: All PASS.

- [ ] **Step 5: Fix context.py drives loop**

`context.py:from_packs()` iterates `pers.drives` and appends each item into a `list[str]`. After this change, `d` is a `Drive` object — `str(d)` returns `d.name`, but `personality.append(d)` would insert a `Drive` into a str list, breaking dedup and rendering. One-line fix in `agentic_mindset/context.py`:

Find the drives loop (currently ~line 79):
```python
for d in pers.drives:
    if d not in personality:
        personality.append(d)
    elif report is not None:
        report.removed_items.append(d)
```

Change to:
```python
for d in pers.drives:
    s = str(d)
    if s not in personality:
        personality.append(s)
    elif report is not None:
        report.removed_items.append(s)
```

- [ ] **Step 6: Run full suite**

```bash
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5
```

Expected: All passing.

- [ ] **Step 7: Commit**

```bash
git add agentic_mindset/schema/personality.py agentic_mindset/context.py tests/test_schema_personality.py
git commit -m "feat: add Drive class, Trait.confidence, EmotionalTendencies expansion, ConditionalVariant.conjunction"
```

---

## Task 3: behavior + voice + meta + sources schema changes

**Context:** Four files, all additive/optional changes:
- `behavior.py`: remove `impulsive` from `decision_speed` (no existing pack uses it — all 13 use `slow/deliberate/fast`); add `decision_control: Optional[Literal["controlled","reactive","impulsive"]]`
- `voice.py`: add `ToneAxes` (formality/warmth/intensity/humor axes for future mix/render)
- `meta.py`: add `license: Optional[str]` and `visibility: Optional[Literal["public","private","internal"]]` defaulting to `"public"`
- `sources.py`: expand `type` enum to include `biography/film/novel/essay/letter/speech`; add `evidence_level: Optional[Literal["primary","secondary","tertiary"]]`

**Files:**
- Modify: `agentic_mindset/schema/behavior.py`
- Modify: `agentic_mindset/schema/voice.py`
- Modify: `agentic_mindset/schema/meta.py`
- Modify: `agentic_mindset/schema/sources.py`
- Modify: `tests/test_schema_behavior.py`
- Modify: `tests/test_schema_voice.py`
- Modify: `tests/test_schema_meta.py`
- Modify: `tests/test_schema_sources.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_schema_behavior.py`:

```python
def test_decision_speed_rejects_impulsive():
    """impulsive is no longer valid for decision_speed."""
    from agentic_mindset.schema.behavior import BehaviorSchema
    import pytest
    with pytest.raises(Exception):
        BehaviorSchema(
            decision_speed="impulsive",
            conflict_style="avoidant",
        )


def test_decision_control_optional():
    from agentic_mindset.schema.behavior import BehaviorSchema
    b = BehaviorSchema(decision_speed="fast", conflict_style="direct")
    assert b.decision_control is None


def test_decision_control_values():
    from agentic_mindset.schema.behavior import BehaviorSchema
    for val in ("controlled", "reactive", "impulsive"):
        b = BehaviorSchema(
            decision_speed="fast",
            conflict_style="direct",
            decision_control=val,
        )
        assert b.decision_control == val


def test_decision_control_invalid_raises():
    from agentic_mindset.schema.behavior import BehaviorSchema
    import pytest
    with pytest.raises(Exception):
        BehaviorSchema(
            decision_speed="fast",
            conflict_style="direct",
            decision_control="careful",
        )
```

Add to `tests/test_schema_voice.py`:

```python
def test_tone_axes_optional():
    from agentic_mindset.schema.voice import VoiceSchema
    v = VoiceSchema(
        tone="measured",
        vocabulary={"preferred": [], "avoided": []},
        sentence_style="short",
    )
    assert v.tone_axes is None


def test_tone_axes_full():
    from agentic_mindset.schema.voice import VoiceSchema, ToneAxes
    v = VoiceSchema(
        tone="measured",
        vocabulary={"preferred": [], "avoided": []},
        sentence_style="short",
        tone_axes=ToneAxes(formality="high", warmth="low", intensity="medium", humor="dry"),
    )
    assert v.tone_axes.formality == "high"
    assert v.tone_axes.humor == "dry"


def test_tone_axes_partial():
    from agentic_mindset.schema.voice import ToneAxes
    ta = ToneAxes(formality="high")
    assert ta.warmth is None
    assert ta.intensity is None
    assert ta.humor is None


def test_tone_axes_invalid_raises():
    from agentic_mindset.schema.voice import ToneAxes
    import pytest
    with pytest.raises(Exception):
        ToneAxes(formality="very_high")
```

Add to `tests/test_schema_meta.py`:

```python
def test_meta_license_optional():
    """license defaults to None."""
    from agentic_mindset.schema.meta import MetaSchema
    m = MetaSchema(
        id="sun-tzu", name="Sun Tzu", version="1.0.0",
        schema_version="1.0", type="historical",
        description="test", created="2026-03-25",
    )
    assert m.license is None


def test_meta_visibility_defaults_to_public():
    from agentic_mindset.schema.meta import MetaSchema
    m = MetaSchema(
        id="sun-tzu", name="Sun Tzu", version="1.0.0",
        schema_version="1.0", type="historical",
        description="test", created="2026-03-25",
    )
    assert m.visibility == "public"


def test_meta_visibility_private():
    from agentic_mindset.schema.meta import MetaSchema
    m = MetaSchema(
        id="sun-tzu", name="Sun Tzu", version="1.0.0",
        schema_version="1.0", type="historical",
        description="test", created="2026-03-25",
        visibility="private",
    )
    assert m.visibility == "private"


def test_meta_visibility_invalid_raises():
    from agentic_mindset.schema.meta import MetaSchema
    import pytest
    with pytest.raises(Exception):
        MetaSchema(
            id="sun-tzu", name="Sun Tzu", version="1.0.0",
            schema_version="1.0", type="historical",
            description="test", created="2026-03-25",
            visibility="confidential",
        )
```

Add to `tests/test_schema_sources.py`:

```python
def test_source_new_types_valid():
    """New source types: biography, film, novel, essay, letter, speech."""
    from agentic_mindset.schema.sources import Source
    for t in ("biography", "film", "novel", "essay", "letter", "speech"):
        s = Source(title="x", type=t, accessed="2026-03-25")
        assert s.type == t


def test_source_evidence_level_optional():
    from agentic_mindset.schema.sources import Source
    s = Source(title="The Art of War", type="book", accessed="2026-03-25")
    assert s.evidence_level is None


def test_source_evidence_level_primary():
    from agentic_mindset.schema.sources import Source
    s = Source(title="x", type="book", accessed="2026-03-25", evidence_level="primary")
    assert s.evidence_level == "primary"


def test_source_evidence_level_invalid_raises():
    from agentic_mindset.schema.sources import Source
    import pytest
    with pytest.raises(Exception):
        Source(title="x", type="book", accessed="2026-03-25", evidence_level="weak")
```

- [ ] **Step 2: Run to verify fail**

```bash
python3 -m pytest tests/test_schema_behavior.py tests/test_schema_voice.py tests/test_schema_meta.py tests/test_schema_sources.py -v 2>&1 | tail -30
```

Expected: New tests FAIL.

- [ ] **Step 3: Implement behavior.py**

Note: `impulsive` is removed from `decision_speed` — this is a **breaking schema change** for any external pack using that value (none of the 13 standard packs use it).

```python
from typing import Literal, Optional, Union
from pydantic import BaseModel, field_validator
from agentic_mindset.schema.personality import ConditionalSlot  # ConditionalVariant not needed here


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
```

- [ ] **Step 4: Implement voice.py**

```python
from typing import Literal, Optional
from pydantic import BaseModel


class Vocabulary(BaseModel):
    preferred: list[str] = []
    avoided: list[str] = []


class ToneAxes(BaseModel):
    """Semi-structured tone metadata for future mix/render pipelines."""
    formality: Optional[Literal["low", "medium", "high"]] = None
    warmth: Optional[Literal["low", "medium", "high"]] = None
    intensity: Optional[Literal["low", "medium", "high"]] = None
    humor: Optional[Literal["none", "dry", "playful", "sharp"]] = None


class VoiceSchema(BaseModel):
    tone: str
    tone_axes: Optional[ToneAxes] = None      # NEW
    vocabulary: Vocabulary
    sentence_style: str
    signature_phrases: list[str] = []
```

- [ ] **Step 5: Implement meta.py**

```python
import re
from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class AuthorSchema(BaseModel):
    name: str
    url: str = ""


class MetaSchema(BaseModel):
    id: str
    name: str
    version: str
    schema_version: str
    type: Literal["historical", "fictional"]
    description: str
    tags: list[str] = []
    authors: list[AuthorSchema] = []
    created: str
    license: Optional[str] = None                                               # NEW: None = unspecified
    visibility: Literal["public", "private", "internal"] = "public"            # NEW: always has a value

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

- [ ] **Step 6: Implement sources.py**

```python
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
```

- [ ] **Step 7: Run new tests**

```bash
python3 -m pytest tests/test_schema_behavior.py tests/test_schema_voice.py tests/test_schema_meta.py tests/test_schema_sources.py -v 2>&1 | tail -30
```

Expected: All new tests PASS.

- [ ] **Step 8: Run full suite**

```bash
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5
```

Expected: All passing.

- [ ] **Step 9: Commit**

```bash
git add agentic_mindset/schema/behavior.py agentic_mindset/schema/voice.py \
        agentic_mindset/schema/meta.py agentic_mindset/schema/sources.py \
        tests/test_schema_behavior.py tests/test_schema_voice.py \
        tests/test_schema_meta.py tests/test_schema_sources.py
git commit -m "feat!: add decision_control, ToneAxes, meta license/visibility, expanded source types + evidence_level

BREAKING: decision_speed no longer accepts 'impulsive' (moved to decision_control).
No standard pack uses decision_speed: impulsive."
```

---

## Task 4: Update conftest.py fixture

**Context:** `minimal_pack_dir` (and `anti_patterns_pack_dir`) in `tests/conftest.py` creates character packs inline. The fixture already uses `decision_speed: deliberate` (not `impulsive`), so no breaking change. Update the fixture to populate the new optional fields as an example — this validates end-to-end loading. The fixture must continue to work with all existing tests. No `schema_version` bump is required (that field is a format check only, not tied to a registry of known versions).

No new tests needed for conftest changes — existing tests cover it.

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Run existing tests to confirm baseline passes**

```bash
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5
```

Expected: All passing (should already pass after Task 3 since conftest uses `deliberate` not `impulsive`).

- [ ] **Step 2: Update conftest.py**

Update the `minimal_pack_dir` fixture — add a few optional new fields as an example (they're optional so existing tests don't break, but this validates end-to-end loading of new fields):

In `write_yaml(tmp / "mindset.yaml", {...})`, add to `decision_framework`:
```python
"heuristics": ["Observe before acting", "Gather intelligence first"],
"commitment_policy": "late",
```

In `write_yaml(tmp / "personality.yaml", {...})`, update `emotional_tendencies` and `drives`:
```python
"emotional_tendencies": {
    "stress_response": "withdraws to observe",
    "motivation_source": "victory through minimum force",
    "baseline_mood": "calm, watchful",
    "emotional_range": "narrow",
    "frustration_trigger": "impulsive action without preparation",
    "recovery_pattern": "retreats to gather information; rebuilds plan",
},
"drives": [
    {"name": "Strategic mastery", "intensity": 0.95},
    {"name": "Minimum force", "intensity": 0.85},
],
```

In `write_yaml(tmp / "behavior.yaml", {...})`, add `decision_control`:
```python
"decision_control": "controlled",
```

In `write_yaml(tmp / "voice.yaml", {...})`, add `tone_axes`:
```python
"tone_axes": {"formality": "high", "warmth": "low", "intensity": "medium", "humor": "none"},
```

In `write_yaml(tmp / "meta.yaml", {...})`, add `license` and `visibility`:
```python
"license": "CC-BY-4.0",
"visibility": "public",
```

In `write_yaml(tmp / "sources.yaml", {...})`, add `evidence_level` to each source:
```python
{"title": "The Art of War", "type": "book", "accessed": "2026-03-22", "evidence_level": "primary"},
{"title": "Sun Tzu biography", "type": "biography", "accessed": "2026-03-22", "evidence_level": "secondary"},
{"title": "Commentary on Art of War", "type": "book", "accessed": "2026-03-22", "evidence_level": "tertiary"},
```

Note: the second source type changes from `"article"` to `"biography"` — both are valid.

- [ ] **Step 3: Run full suite**

```bash
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -10
```

Expected: All passing.

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py
git commit -m "chore: update conftest fixture with new schema fields (Drive objects, ToneAxes, emotional_tendencies expansion)"
```

---

## Task 5: Character pack YAML enrichment

**Context:** All 13 characters need new fields added. All fields are optional so packs load fine without them. This task enriches their content so the new schema fields are actually populated.

Fields to add per character:
- `mindset.yaml`: `heuristics: list[str]`, `default_strategy: str`, `fallback_strategy: str`, `commitment_policy: early|deliberate|late`
- `personality.yaml`: `emotional_tendencies.baseline_mood`, `emotional_tendencies.emotional_range`, `emotional_tendencies.frustration_trigger`, `emotional_tendencies.recovery_pattern`; upgrade `drives` from `list[str]` to `list[{name, intensity, description?}]`
- `behavior.yaml`: `decision_control: controlled|reactive|impulsive`
- `voice.yaml`: `tone_axes: {formality, warmth, intensity, humor}`

**Important:** sun-tzu already has `frustration_trigger` in personality.yaml (was silently ignored before). Keep it.

**Process:** Work character by character. After each character, run the full test suite. Commit per character.

**All 13 characters:** `atticus-finch`, `confucius`, `gojo-satoru`, `leonardo-da-vinci`, `levi-ackermann`, `marcus-aurelius`, `napoleon-bonaparte`, `naruto-uzumaki`, `nikola-tesla`, `odysseus`, `seneca`, `sherlock-holmes`, `sun-tzu`.

**Files:**
- Modify: `characters/<id>/mindset.yaml` × 13
- Modify: `characters/<id>/personality.yaml` × 13
- Modify: `characters/<id>/behavior.yaml` × 13
- Modify: `characters/<id>/voice.yaml` × 13

### Sub-task 5a: sun-tzu (complete reference example)

- [ ] **Step 1: Update sun-tzu/mindset.yaml**

In `decision_framework`, add after `approach: ...`:
```yaml
heuristics:
  - Gather intelligence before any commitment; never act on incomplete maps
  - Choose ground carefully — position first, then invite battle
  - Prefer indirect action; spend effort on setup, not on brute execution
  - Always hold a secondary route; never commit everything to one line of attack
  - When the enemy adapts, change form; do not repeat a tactic that has been seen
default_strategy: Position for inevitable victory through preparation and deception; engage
  only when the outcome is already decided
fallback_strategy: Withdraw without battle, regroup, and re-evaluate terrain; never pursue
  a desperate fight when the position is unfavorable
commitment_policy: late
```

- [ ] **Step 2: Update sun-tzu/personality.yaml**

In `emotional_tendencies`, add (note: `frustration_trigger` already exists — keep it):
```yaml
baseline_mood: Calm, vigilant, and internally still; operates from a position of studied
  detachment
emotional_range: narrow
recovery_pattern: Retreats to solitude and information-gathering; rebuilds strategic map
  before returning to action; treats setback as data
```

Upgrade `drives` to object form:
```yaml
drives:
  - name: Strategic mastery
    intensity: 0.95
    description: The intellectual satisfaction of reducing conflict to a solved problem through superior preparation
  - name: Minimum cost, maximum result
    intensity: 0.92
    description: Economy of force as a moral and aesthetic principle, not just a tactic
  - name: Understanding conflict itself
    intensity: 0.88
    description: A drive to map the underlying structure of all adversarial systems
  - name: Information dominance
    intensity: 0.9
    description: Control the information environment before the physical one; shape the enemy's picture of reality
  - name: Structural inevitability
    intensity: 0.85
    description: The desire to expose why outcomes that look like luck are actually the product of earlier positioning
```

- [ ] **Step 3: Update sun-tzu/behavior.yaml**

Add after `decision_speed: deliberate`:
```yaml
decision_control: controlled
```

- [ ] **Step 4: Update sun-tzu/voice.yaml**

Add after `tone: ...`:
```yaml
tone_axes:
  formality: high
  warmth: low
  intensity: medium
  humor: none
```

- [ ] **Step 5: Validate**

```bash
python3 -c "
from agentic_mindset.pack import CharacterPack
from pathlib import Path
p = CharacterPack.load(Path('characters/sun-tzu'))
print('drives:', [str(d) for d in p.personality.drives])
print('commitment_policy:', p.mindset.decision_framework.commitment_policy)
print('baseline_mood:', p.personality.emotional_tendencies.baseline_mood)
print('tone_axes:', p.voice.tone_axes)
print('decision_control:', p.behavior.decision_control)
"
```

Expected output:
```
drives: ['Strategic mastery', 'Minimum cost, maximum result', ...]
commitment_policy: late
baseline_mood: Calm, vigilant, and internally still...
tone_axes: formality=high warmth=low...
decision_control: controlled
```

- [ ] **Step 6: Commit sun-tzu**

```bash
git add characters/sun-tzu/
git commit -m "chore(pack): enrich sun-tzu with new schema fields"
```

### Sub-task 5b: marcus-aurelius

- [ ] **Step 1: Update mindset.yaml** — add after `approach`:
```yaml
heuristics:
  - Ask what duty requires, not what desire prefers
  - Return to first principles when confused by circumstance
  - Distinguish what is in your control from what is not before reacting
  - Prefer the action that serves the common good over personal advantage
default_strategy: Act from duty and virtue regardless of outcome; focus on what you
  control and release the rest
fallback_strategy: Accept the outcome as part of nature; extract the lesson and return
  to equanimity
commitment_policy: deliberate
```

- [ ] **Step 2: Update personality.yaml** — add to `emotional_tendencies` and upgrade `drives`:
```yaml
# In emotional_tendencies, add:
baseline_mood: Steady, contemplative, and quietly purposeful
emotional_range: narrow
frustration_trigger: Moral failures in others, especially those with power who use it
  for personal gain; his own lapses from reason
recovery_pattern: Writes in his journal to clarify thought; returns to Stoic principles;
  treats his own failures with the same compassion he gives others

# drives upgrade:
drives:
  - name: Virtue and moral excellence
    intensity: 0.97
    description: Living according to reason and nature as the only genuine good
  - name: Service to others
    intensity: 0.93
    description: Duty to the common good as the emperor and as a human being
  - name: Self-mastery
    intensity: 0.9
    description: Rational clarity over emotion; the ongoing project of the examined life
```

- [ ] **Step 3: Update behavior.yaml** — add `decision_control: controlled`

- [ ] **Step 4: Update voice.yaml** — add:
```yaml
tone_axes:
  formality: medium
  warmth: medium
  intensity: low
  humor: none
```

- [ ] **Step 5: Validate and commit**

```bash
python3 -c "from agentic_mindset.pack import CharacterPack; from pathlib import Path; p = CharacterPack.load(Path('characters/marcus-aurelius')); print('ok:', p.meta.name)"
git add characters/marcus-aurelius/
git commit -m "chore(pack): enrich marcus-aurelius with new schema fields"
```

### Sub-task 5c–5m: remaining 11 characters

For each character below, follow the same four-file pattern as 5a/5b. Use the character's existing YAML as context to derive appropriate values. The table provides the critical fields — derive heuristics, fallback_strategy, drives details, and tone_axes from what is already written in the pack.

| Character | commitment_policy | decision_control | emotional_range | tone_axes.formality | tone_axes.humor |
|---|---|---|---|---|---|
| `atticus-finch` | `deliberate` | `controlled` | `narrow` | `medium` | `none` |
| `confucius` | `deliberate` | `controlled` | `moderate` | `high` | `none` |
| `gojo-satoru` | `early` | `reactive` | `wide` | `low` | `playful` |
| `leonardo-da-vinci` | `deliberate` | `reactive` | `wide` | `medium` | `dry` |
| `levi-ackermann` | `deliberate` | `controlled` | `narrow` | `low` | `none` |
| `napoleon-bonaparte` | `early` | `reactive` | `wide` | `high` | `none` |
| `naruto-uzumaki` | `early` | `reactive` | `wide` | `low` | `playful` |
| `nikola-tesla` | `deliberate` | `controlled` | `wide` | `medium` | `none` |
| `odysseus` | `late` | `controlled` | `moderate` | `medium` | `dry` |
| `seneca` | `deliberate` | `controlled` | `narrow` | `medium` | `dry` |
| `sherlock-holmes` | `late` | `controlled` | `narrow` | `medium` | `sharp` |

**For each character:**

- [ ] Add `heuristics` (3–5 items), `default_strategy`, `fallback_strategy`, `commitment_policy` to `mindset.yaml`
- [ ] Add `baseline_mood`, `emotional_range`, `frustration_trigger`, `recovery_pattern` to `personality.yaml` `emotional_tendencies`
- [ ] Upgrade `drives` from `list[str]` to `list[{name, intensity, description}]`
- [ ] Add `decision_control` to `behavior.yaml`
- [ ] Add `tone_axes` to `voice.yaml`
- [ ] Validate: `python3 -c "from agentic_mindset.pack import CharacterPack; from pathlib import Path; p = CharacterPack.load(Path('characters/<id>')); print('ok')"` → prints `ok`
- [ ] Commit: `git add characters/<id>/ && git commit -m "chore(pack): enrich <id> with new schema fields"`

- [ ] **Final: Run full suite after all 13 characters updated**

```bash
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5
```

Expected: All passing.

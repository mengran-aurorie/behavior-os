# Behavior IR — Design Spec

**Date:** 2026-03-24
**Status:** Draft

---

## 1. Problem Statement

The current `inject` format renders behavioral prompts by iterating weighted packs and deduplicating strings. This has two critical failure modes:

**Generic collapse.** When two personas have conflicting slot values (e.g., `communication: indirect` vs `communication: direct`), both appear in the output as separate bullets. An LLM receiving contradictory instructions defaults to generic assistant behavior — the conflict cancels both directives.

**No structured conflict resolution.** Conflicts are decided by the order strings appear, not by semantic policy. There is no concept of "this persona controls this slot" or "this value applies under these conditions." Deduplication is textual, not behavioral.

**Goal:** Introduce a structured intermediate representation (`BehaviorIR`) produced by a deterministic `ConflictResolver`. The renderer (`ClaudeRenderer`) reads only from the IR, never from raw packs. This separates three concerns that are currently tangled:

- *What the personas mean* (resolver — semantic decision layer)
- *What the blend intends* (BehaviorIR — stable intermediate representation)
- *How to express it to a runtime* (renderer — output adapter)

---

## 2. Architecture

### Pipeline

```
CharacterPack(s)
      │
      ▼
FusionEngine.prepare_packs()      ← normalized, sorted [(pack, weight), ...]
      │
      ├─► ConflictResolver.resolve()   ← NEW: semantic decision layer
      │         │
      │         ▼
      │   BehaviorIR                   ← NEW: single source of truth (inject path)
      │         │
      │         ▼
      │   InjectRenderer.render()      ← NEW: IR → runtime text
      │         │
      │         ▼
      │   (system prompt string)
      │
      └─► ContextBlock.from_packs()    ← EXISTING: text path unchanged
                │
                ▼
          to_prompt("plain_text")
```

### Path separation

| Path | Entry | Source of truth | Explain source |
|---|---|---|---|
| `inject` (default) | `prepare_packs()` → resolver | `BehaviorIR` | IR directly |
| `text` | `prepare_packs()` → `from_packs()` | `ContextBlock` | `FusionReport` |

Both paths start from `prepare_packs()`. This ensures identical normalization and sort order regardless of output format.

### Principle: BehaviorIR is the single source of truth for the inject path

- Renderer reads only from IR, never from packs
- `--explain` for inject dumps IR directly
- Future subagent slices, strategy engines, and benchmarks all read from IR
- `FusionReport` is retained for the text path only; the two abstractions must not be mixed

### Principle: ConflictResolver is a pure function

`resolve(weighted_packs) → BehaviorIR`. No external state, no LLM calls, no I/O. Same inputs always produce the same IR. This is a hard constraint — if the resolver becomes stateful or calls a model, the determinism guarantee is broken.

---

## 3. New Components

### 3.1 `DropReason` dataclass (`agentic_mindset/ir/models.py`)

Records why a secondary persona's slot value was not promoted to a modifier.

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class DropReason:
    value: str
    source: str   # character id
    weight: float
    reason: Literal[
        "no_conflict",             # non-conflicting secondary; winner-takes-all
        "weight_below_threshold",  # conflict detected but weight < MODIFIER_THRESHOLD
        "no_condition",            # conflict + weight ok, but no pack condition and no fallback template
    ]
```

### 3.2 `PrimaryValue` dataclass

```python
@dataclass
class PrimaryValue:
    value: str
    source: str    # character id
    weight: float  # normalized weight at resolution time
```

### 3.3 `ConditionModifier` dataclass

```python
@dataclass
class ConditionModifier:
    value: str
    condition: list[str]                          # controlled labels (see §5)
    conjunction: Literal["any", "all"] = "any"   # "any" = OR, "all" = AND
    source: str  = ""                            # character id
    provenance: Literal["pack", "fallback", "weak"] = "fallback"
    note: str | None = None                      # human annotation; not rendered
    priority: float | None = None                # reserved for future ordering
```

`provenance` semantics:
- `pack` — conditions came from the character pack's `conditional` schema field
- `fallback` — conditions came from `MODIFIER_FALLBACK_TEMPLATES` in the resolver
- `weak` — conflict detected, weight above soft threshold, but no conditions available; rendered as a soft tendency, not a rule

`note` is never rendered to the runtime; it appears only in `--explain` YAML output.

### 3.4 `ResolvedSlot` dataclass

```python
@dataclass
class ResolvedSlot:
    primary: PrimaryValue
    modifiers: list[ConditionModifier] = field(default_factory=list)
    has_conflict: bool = False
    dropped: list[DropReason] = field(default_factory=list)
```

`has_conflict` is `True` if any secondary value was identified as conflicting with the primary, regardless of whether a modifier was produced. A slot where `has_conflict=True` and `modifiers=[]` means a conflict was detected but all secondaries were either below the weight threshold, lacked conditions, and were below the soft threshold.

`dropped` records every secondary that did not become a modifier, with its reason.

### 3.5 `Preamble` dataclass

```python
@dataclass
class Preamble:
    personas: list[tuple[str, float]]   # [(character_id, normalized_weight), ...]
    text: str                           # rendered preamble string
```

### 3.6 `BehaviorIR` dataclass (`agentic_mindset/ir/models.py`)

```python
@dataclass
class BehaviorIR:
    # Metadata
    preamble: Preamble

    # DECISION POLICY — additive, sorted by confidence desc
    decision_policy_items: list[str] = field(default_factory=list)

    # UNCERTAINTY HANDLING (non-slot scalar fields)
    risk_tolerance: str = ""   # v1: primary pack's value; blend deferred
    time_horizon: str = ""     # v1: primary pack's value; blend deferred

    # ANTI-PATTERNS — additive dedup
    anti_patterns: list[str] = field(default_factory=list)

    # STYLE (non-slot scalar fields)
    vocabulary_preferred: list[str] = field(default_factory=list)
    vocabulary_avoided: list[str] = field(default_factory=list)

    # All ResolvedSlots — single source of truth
    slots: dict[str, ResolvedSlot] = field(default_factory=dict)

    # Typed accessors — convenience properties, not stored fields
    @property
    def stress_response(self) -> ResolvedSlot | None:
        return self.slots.get("stress_response")

    @property
    def communication(self) -> ResolvedSlot | None:
        return self.slots.get("communication")

    @property
    def leadership(self) -> ResolvedSlot | None:
        return self.slots.get("leadership")

    @property
    def conflict_style(self) -> ResolvedSlot | None:
        return self.slots.get("conflict_style")

    @property
    def tone(self) -> ResolvedSlot | None:
        return self.slots.get("tone")

    @property
    def sentence_style(self) -> ResolvedSlot | None:
        return self.slots.get("sentence_style")
```

`slots` is the only stored source of truth for all `ResolvedSlot` data. Typed properties are read-only aliases over `slots` — they are never written directly, eliminating dual-write risk. `build_ir()` only writes to `slots`; renderers and explain output access slots via either the dict or the typed properties interchangeably.

`risk_tolerance` and `time_horizon` are plain strings in v1. Numeric blend (weighted average over ordered enum) is deferred — the values are semantically context-dependent and the gain from blending them does not justify the risk of producing a value that is numerically coherent but semantically misleading (e.g., `high × 0.6 + medium × 0.4 → medium` where the character's risk profile is actually context-split).

---

## 4. ConflictResolver

### 4.1 File: `agentic_mindset/resolver/resolver.py`

```python
class ConflictResolver:
    def resolve(
        self,
        weighted_packs: list[tuple["CharacterPack", float]],
    ) -> BehaviorIR:
        validated = self._normalize_inputs(weighted_packs)
        resolved_slots = self._resolve_all_slots(validated)
        return self._build_ir(validated, resolved_slots)
```

### 4.2 `_normalize_inputs()`

Validates that `weighted_packs` is non-empty. Weights are expected already normalized (caller precondition: output of `prepare_packs()`). Returns the list unchanged or raises `ValueError`.

The resolver always populates `primary` from the highest-weight pack's slot value. `ResolvedSlot.primary` is never `None` after `resolve()` completes.

### 4.3 `_resolve_categorical_slot()` — decision tree

```
values = [(pack, value, weight), ...], sorted by weight desc

primary = values[0]

for each secondary in values[1:]:

    if not is_conflict(slot_name, primary.value, secondary.value):
        → dropped(reason="no_conflict")
        continue

    has_conflict = True

    if secondary.weight < MODIFIER_THRESHOLD:       # default: 0.3
        → dropped(reason="weight_below_threshold")
        continue

    # 1. Pack condition (highest priority)
    if pack has conditional variant matching secondary.value:
        → modifier(provenance="pack", condition=pack.applies_when)
        continue

    # 2. Resolver fallback template
    if MODIFIER_FALLBACK_TEMPLATES has (slot_name, secondary.value):
        → modifier(provenance="fallback", condition=template_conditions)
        continue

    # 3. Soft fallback (weak tendency)
    if secondary.weight >= SOFT_THRESHOLD:          # default: 0.35
        → modifier(provenance="weak", condition=[])
        continue

    # 4. Discard
    → dropped(reason="no_condition")
```

**Modifier sort order (deterministic output):**

After all secondaries are processed, the `modifiers` list is sorted before being stored in `ResolvedSlot`:

```python
PROVENANCE_ORDER = {"pack": 0, "fallback": 1, "weak": 2}

modifiers.sort(key=lambda m: (PROVENANCE_ORDER[m.provenance], -m.primary_weight))
```

Where `primary_weight` is the weight of the secondary pack that contributed the modifier (stored temporarily during resolution). This ensures: pack conditions appear before fallback, fallback before weak; within the same provenance tier, higher-weight secondaries appear first. The sort is stable and fully deterministic given the same inputs.

**`is_conflict()` implementation:**

```python
def _is_conflict(self, slot_name: str, val_a: str, val_b: str) -> bool:
    if slot_name not in SLOT_CONFLICT_PAIRS:
        return False
    a = val_a.lower().strip()
    b = val_b.lower().strip()
    pairs = SLOT_CONFLICT_PAIRS[slot_name]
    return (a, b) in pairs or (b, a) in pairs
```

**Pack conditional variant matching:** A pack's conditional section for slot X matches a secondary value when both refer to the same slot AND `secondary.value.lower().strip() == variant.value.lower().strip()`.

**Key invariant:** A modifier with no conditions never enters the IR via the `pack` or `fallback` path. The `weak` path explicitly signals "no conditions" via `condition=[]` and `provenance="weak"`, and is rendered differently (soft phrasing, not a rule).

### 4.4 Conflict taxonomy (`agentic_mindset/resolver/policies.py`)

```python
# slot_name → set of conflicting (value_a, value_b) pairs
# Matching is symmetric: (a, b) checks (a,b) and (b,a)
# Values are normalized: lower().strip() before comparison
SLOT_CONFLICT_PAIRS: dict[str, set[tuple[str, str]]] = {
    "communication": {
        ("indirect", "direct"),
        ("layered", "blunt"),
        ("reserved", "open"),
    },
    "conflict_style": {
        ("avoidant", "confrontational"),
        ("avoidant", "direct confrontation"),
    },
    "leadership": {
        ("positioning", "directive"),
    },
}
```

Values not in the taxonomy are not considered conflicting. Winner-takes-all applies. This is intentionally conservative — fuzzy/semantic matching is not attempted in v1.

### 4.5 Fallback templates (`agentic_mindset/resolver/policies.py`)

```python
# (slot_name, primary_value, secondary_value) → list[condition_labels]
# Use "*" as primary_value wildcard for primary-agnostic templates.
# Lookup order: exact (slot, primary, secondary) first, then (slot, "*", secondary).
MODIFIER_FALLBACK_TEMPLATES: dict[tuple[str, str, str], list[str]] = {
    ("communication", "*", "direct"):                ["clarity_critical", "time_pressure"],
    ("conflict_style", "*", "confrontational"):      ["advantage_secured"],
    ("conflict_style", "*", "direct confrontation"): ["advantage_secured"],
    ("leadership",    "*", "directive"):             ["execution_phase", "time_pressure"],
}
```

**Template lookup:**
```python
def _get_fallback_conditions(slot: str, primary: str, secondary: str) -> list[str]:
    specific = MODIFIER_FALLBACK_TEMPLATES.get((slot, primary.lower().strip(), secondary.lower().strip()))
    if specific is not None:
        return specific
    return MODIFIER_FALLBACK_TEMPLATES.get((slot, "*", secondary.lower().strip()), [])
```

The three-key structure enables primary-specific overrides. For example, `("communication", "reserved", "open")` could have a different template than `("communication", "indirect", "open")`. The wildcard `"*"` primary covers the common case and remains the default until a specific override is needed.

Not all `SLOT_CONFLICT_PAIRS` entries require a fallback template. Secondary values without a matching template become `weak` modifiers if `weight >= SOFT_THRESHOLD`, else are discarded (`reason="no_condition"`). For example, the pairs `("layered","blunt")`, `("reserved","open")` in `communication` have no fallback template in v1 — conflicts on those value pairs degrade to `weak` or are dropped. This is intentional: the fallback table grows as pack authors demonstrate need.

### 4.6 Thresholds

```python
MODIFIER_THRESHOLD = 0.3   # minimum secondary weight to be considered as modifier
SOFT_THRESHOLD = 0.35      # minimum secondary weight for weak modifier
```

Both are module-level constants, intended to become configurable in a future version.

---

## 5. Condition Label Vocabulary (`agentic_mindset/ir/conditions.py`)

All `applies_when` labels in pack schemas and all fallback template labels must come from this vocabulary.

```python
from enum import Enum

class ConditionLabel(str, Enum):
    # Context
    strategic_context = "strategic_context"
    execution_phase   = "execution_phase"
    time_pressure     = "time_pressure"
    high_uncertainty  = "high_uncertainty"
    # Goal / constraint
    clarity_critical          = "clarity_critical"
    advantage_secured         = "advantage_secured"
    relationship_preservation = "relationship_preservation"
    # Emotional / interaction
    high_tension         = "high_tension"
    public_confrontation = "public_confrontation"
    trust_fragile        = "trust_fragile"
```

**Strict enforcement (both layers):**

- **Schema validation:** Unknown labels in a pack's `applies_when` field raise `ValidationError` at pack load time. No silent acceptance.
- **Renderer:** Unknown labels in `ConditionModifier.condition` raise `ValueError`. This should be unreachable in production (schema validation runs first), but protects against internal bugs where IR is constructed without going through pack validation.

```python
# renderer/_render_conditions()
for label in modifier.condition:
    if label not in CONDITION_TEXT_EN:
        raise ValueError(f"Unknown condition label: {label!r}. Add to CONDITION_TEXT_EN or ConditionLabel enum.")
```

There is no silent fallback in either layer. If a label is valid enough to pass schema validation, it must have a renderer mapping. Adding a new label requires updating both `ConditionLabel` and `CONDITION_TEXT_EN` — the enum and renderer are kept in sync as a hard constraint.

Not all labels in `ConditionLabel` appear in `MODIFIER_FALLBACK_TEMPLATES`. Labels like `high_tension`, `public_confrontation`, and `trust_fragile` are reserved for pack-level `conditional` variants. The enum defines the full valid vocabulary; fallback templates use only the subset they need.

**Extending the vocabulary:** New labels are added to this enum via PR. Label names follow `snake_case`. Each new label requires a corresponding entry in `CONDITION_TEXT_EN` (the English renderer mapping).

---

## 6. InjectRenderer (`agentic_mindset/renderer/inject.py`)

### 6.1 Class hierarchy

```python
from abc import ABC, abstractmethod

class InjectRenderer(ABC):
    @abstractmethod
    def render(self, ir: BehaviorIR) -> str: ...

class ClaudeRenderer(InjectRenderer):
    """Renders BehaviorIR for claude --append-system-prompt-file."""
    def __init__(self, debug: bool = False): ...
    def render(self, ir: BehaviorIR) -> str: ...
```

`debug=True` appends condition label names as comments for human inspection. Not for production use.

### 6.2 `_render_slot()`

Three cases based on modifier provenance:

```
modifiers = slot.modifiers
normal = [m for m in modifiers if m.provenance in ("pack", "fallback")]
weak   = [m for m in modifiers if m.provenance == "weak"]

Case 1: no modifiers
    → "Communication: indirect"

Case 2: normal modifiers (exactly 1)
    → "Communication: indirect; except direct when clarity is critical or under time pressure"

Case 3: normal modifiers (>1)
    → "Communication: indirect; except:"
      "  - direct when clarity is critical or under time pressure"
      "  - open when trust is fragile"

Case 4: weak modifiers only (no normal)
    → "Communication: indirect; slight tendency toward direct in some situations"
```

Each modifier's conditions are joined using `_render_conditions(mod)`: `conjunction="any"` → `" or ".join(texts)`, prepended with `"when "`. The `conjunction` field controls this join — it is hardcoded logic in the renderer, not a mapping entry in `CONDITION_TEXT_EN`. If `mod.condition` is empty (`weak` provenance), `_render_conditions()` returns `""` and the caller strips trailing whitespace.

`except ... when` is the *golden pattern* — it expresses a rule with a conditional override. This phrasing is intentionally stable; wording must not vary between runs.

If `slot.has_conflict and not slot.modifiers`: no change to rendered output. The conflict-resolution result (winner-takes-all) is semantically correct and needs no annotation in the runtime prompt. The information is available in `--explain`.

### 6.3 Condition text mapping

```python
CONDITION_TEXT_EN: dict[str, str] = {
    "strategic_context":          "in a strategic context",
    "execution_phase":            "during execution phase",
    "time_pressure":              "under time pressure",
    "high_uncertainty":           "facing high uncertainty",
    "clarity_critical":           "when clarity is critical",
    "advantage_secured":          "when strategic advantage is secured",
    "relationship_preservation":  "when relationship preservation matters",
    "high_tension":               "under high tension",
    "public_confrontation":       "in a public confrontation",
    "trust_fragile":              "when trust is fragile",
}
```

Renderer uses `CONDITION_TEXT_EN[label]` — unknown labels raise `ValueError`. Both `ConditionLabel` enum and `CONDITION_TEXT_EN` must be updated together when adding a new label (strict co-evolution).

Multi-condition joining: `conjunction="any"` → `" or ".join(texts)`, prefixed with `"when "`.

`note` field: **not rendered**. Appears only in `--explain` YAML.

---

## 7. CLI Contract

### `mindset run` — updated flow

```python
# Shared: both paths start from prepare_packs
weighted_packs = engine.prepare_packs(chars, strat)

if format_ == "inject":
    ir = ConflictResolver().resolve(weighted_packs)
    injected = render_for_runtime(ir, fmt="inject")
    if explain:
        _emit_explain_from_ir(ir)

elif format_ == "text":
    show_weights = strat != FusionStrategy.sequential
    report = FusionReport() if explain else None
    block = ContextBlock.from_packs(weighted_packs, show_weights=show_weights, report=report)
    injected = block.to_prompt("plain_text")
    if explain:
        _emit_explain_from_report(report, weighted_packs)
```

`render_for_runtime()` signature changes from `(context_block: ContextBlock, fmt: str, weighted_packs: list | None = None) → str` to `(ir: BehaviorIR, fmt: str) → str`. The `text` format no longer routes through `render_for_runtime()`; it calls `block.to_prompt("plain_text")` directly. `render_for_runtime()` is inject-path only. It is a renderer factory:

```python
_RENDERERS: dict[str, type[InjectRenderer]] = {
    "inject": ClaudeRenderer,
}

def render_for_runtime(ir: BehaviorIR, fmt: str) -> str:
    if fmt not in _RENDERERS:
        raise ValueError(f"Unknown runtime format: {fmt!r}")
    return _RENDERERS[fmt]().render(ir)
```

### `mindset generate` — unchanged

`generate` continues to use the ContextBlock path: `engine.fuse()` → `ContextBlock` → `to_prompt("plain_text")`. `FusionReport` is still populated when `--explain` is passed. IR is not created in the `generate` path. `--format inject` for `generate` is deferred.

---

## 8. `--explain` Contract

### inject path (from IR)

```yaml
personas:
  - sun-tzu: 0.6
  - marcus-aurelius: 0.4

slots:
  communication:
    primary: {value: indirect, source: sun-tzu, weight: 0.6}
    has_conflict: true
    modifiers:
      - value: direct
        condition: [clarity_critical, time_pressure]
        conjunction: any
        source: marcus-aurelius
        provenance: fallback
    dropped: []

  conflict_style:
    primary: {value: avoidant, source: sun-tzu, weight: 0.6}
    has_conflict: true
    modifiers:
      - value: direct confrontation
        condition: [advantage_secured]
        conjunction: any
        source: marcus-aurelius
        provenance: fallback
    dropped: []

  leadership:
    primary: {value: lead by positioning, source: sun-tzu, weight: 0.6}
    has_conflict: false
    modifiers: []
    dropped: []
```

The `slots` dict in `--explain` YAML uses named slot keys (e.g., `communication`, `conflict_style`) matching the `BehaviorIR.slots` dict. Only slots that were resolved (i.e., the pack had a value for that slot) appear. The generic `slots` dict in the IR is the source; typed field access (`ir.communication`) is a convenience alias.

`dropped` entries make silent discard decisions auditable. A pack author who wonders "why did my persona not influence communication?" will see:

```yaml
dropped:
  - value: direct
    source: some-persona
    weight: 0.15
    reason: weight_below_threshold
```

### text path (from FusionReport)

Unchanged from current implementation.

---

## 9. Schema Changes

### `personality.yaml` — optional conditional variants

Backward compatible: `communication` and `leadership` can remain plain strings.

```yaml
# Old format — still valid
interpersonal_style:
  communication: indirect
  leadership: lead by positioning

# New format — optional
interpersonal_style:
  communication:
    default: indirect
    conditional:
      - value: direct
        applies_when:
          - clarity_critical
          - execution_phase
        note: "Used when clarity of intent outweighs strategic ambiguity."
```

### `behavior.yaml` — optional conditional variant for `conflict_style`

```yaml
# Old format — still valid
conflict_style: avoidant

# New format
conflict_style:
  default: avoidant
  conditional:
    - value: direct confrontation
      applies_when:
        - advantage_secured
```

Pydantic validators accept both `str` and the new dict structure via a `@field_validator` with `mode='before'`. When the field is a plain string, `conditional` is treated as empty — the resolver falls back to `MODIFIER_FALLBACK_TEMPLATES`.

```python
class ConditionalVariant(BaseModel):
    value: str
    applies_when: list[str] = []   # ConditionLabel values
    note: str | None = None

class ConditionalSlot(BaseModel):
    default: str
    conditional: list[ConditionalVariant] = []

class InterpersonalStyle(BaseModel):
    communication: Union[str, ConditionalSlot]
    leadership: Union[str, ConditionalSlot]

    @field_validator("communication", "leadership", mode="before")
    @classmethod
    def normalize_slot(cls, v):
        if isinstance(v, str):
            return ConditionalSlot(default=v, conditional=[])
        return v
```

Resolver accesses the conditional field via `isinstance(field, ConditionalSlot)` and iterates `field.conditional` to find a matching variant. When the field is a plain string (old packs), `field.conditional` is empty and the resolver proceeds to fallback templates.

---

## 10. Backward Compatibility

| Scenario | Behavior |
|---|---|
| `mindset run --format text` | Unchanged (ContextBlock path) |
| `mindset generate` (any format) | Unchanged |
| Existing packs without `conditional` fields | Valid; resolver uses fallback templates |
| `--explain` on inject | Richer YAML (slot-level provenance); not backward compat with old format |
| `--explain` on text / generate | Unchanged |
| All 126 existing tests | Must pass |

---

## 11. File Map

| File | Action |
|---|---|
| `agentic_mindset/ir/__init__.py` | New package |
| `agentic_mindset/ir/models.py` | `PrimaryValue`, `ConditionModifier`, `ResolvedSlot`, `Preamble`, `BehaviorIR`, `DropReason` |
| `agentic_mindset/ir/conditions.py` | `ConditionLabel` enum, `CONDITION_TEXT_EN` |
| `agentic_mindset/resolver/__init__.py` | New package |
| `agentic_mindset/resolver/resolver.py` | `ConflictResolver` |
| `agentic_mindset/resolver/policies.py` | `SLOT_CONFLICT_PAIRS`, `MODIFIER_FALLBACK_TEMPLATES`, thresholds |
| `agentic_mindset/renderer/__init__.py` | New package |
| `agentic_mindset/renderer/inject.py` | `InjectRenderer` (ABC), `ClaudeRenderer` |
| `agentic_mindset/schema/personality.py` | `communication` / `leadership` accept conditional variant |
| `agentic_mindset/schema/behavior.py` | `conflict_style` accepts conditional variant |
| `agentic_mindset/cli.py` | `render_for_runtime()` updated; `run()` dual-path |
| `tests/test_resolver.py` | New |
| `tests/test_ir.py` | New |
| `tests/test_renderer.py` | New |
| `tests/test_conditions.py` | New |
| `tests/test_cli.py` | New integration tests for inject path + explain |
| `tests/conftest.py` | New fixtures: `conflict_registry`, `three_persona_registry` |

### Import structure

```
cli.py
  ← from agentic_mindset.resolver.resolver import ConflictResolver
  ← from agentic_mindset.renderer.inject import ClaudeRenderer, render_for_runtime
  ← from agentic_mindset.ir.models import BehaviorIR

resolver/resolver.py
  ← from agentic_mindset.ir.models import (
        PrimaryValue, ConditionModifier, ResolvedSlot,
        BehaviorIR, DropReason, Preamble
     )
  ← from agentic_mindset.resolver.policies import (
        SLOT_CONFLICT_PAIRS, MODIFIER_FALLBACK_TEMPLATES,
        MODIFIER_THRESHOLD, SOFT_THRESHOLD
     )
  ← from agentic_mindset.ir.conditions import ConditionLabel

renderer/inject.py
  ← from agentic_mindset.ir.models import BehaviorIR, ResolvedSlot, ConditionModifier
  ← from agentic_mindset.ir.conditions import CONDITION_TEXT_EN
```

---

## 12. Non-Goals (v1)

- **No semantic/embedding-based conflict detection.** Only exact-match against `SLOT_CONFLICT_PAIRS` (after `lower().strip()` normalization).
- **No numeric blend for `risk_tolerance` / `time_horizon`.** Primary pack's value is used directly.
- **No `generate --format inject`.** `generate` stays text-only.
- **No multi-runtime adapters (OpenAI, Ollama, etc.).** Architecture supports them; only `ClaudeRenderer` is implemented.
- **No LLM-assisted condition synthesis.** All conditions are either from pack schema or hardcoded fallback templates.
- **No dynamic condition vocabulary extension.** New labels require code change to `ConditionLabel` enum.
- **No `decision_policy` conflict resolution.** Principles remain additive with string dedup in v1.

---

## 13. Future

The IR layer enables the following without changing the resolver or schema:

- **Multi-runtime adapters:** New `XxxRenderer(InjectRenderer)` subclass; no other changes.
- **IR diff / benchmark:** Compare `BehaviorIR` instances across personas or sessions; `has_conflict` and `dropped` fields provide structured signal.
- **Subagent slices:** `ir.slice(["communication", "leadership"])` returns a new `BehaviorIR` containing only the specified slots. Enables single-purpose agents (negotiation agent, leadership advisor, etc.) derived from the same fusion result.
- **Strategy engine:** `BehaviorIR` is the input to any strategy engine — not text, not prompt. Derive planning biases from `communication.primary`, `conflict_style.primary`, and modifier patterns.
- **`decision_policy` resolution:** Extend `ConflictResolver` to resolve `core_principles` conflicts by adding a `PolicyItem` dataclass with source/weight tracking (noted in §3.6).
- **Condition vocabulary expansion:** Defined process: PR to `ConditionLabel` enum + `CONDITION_TEXT_EN` entry + optional pack updates.
- **IR hash:** `BehaviorIR.hash() -> str` over `(slots, personas, risk_tolerance, time_horizon)`. Enables caching, exact-match deduplication across sessions, and reproducibility guarantees for benchmarks.
- **IR serialization:** `BehaviorIR.to_dict()` / `BehaviorIR.from_dict()` for cross-language interop, API exposure, and database storage. The `slots` dict structure maps directly to a JSON schema.
- **Renderer debug header:** An optional stable header in the rendered output (`# Mindset IR v1 | personas: sun-tzu(0.6), marcus(0.4)`) for downstream parsing and human-readable attribution. Disabled by default; enabled via `ClaudeRenderer(header=True)`.
- **Fallback table primary-specific overrides:** The `(slot, primary, secondary)` key structure already supports this. As pack diversity grows, primary-specific conditions can be registered without schema changes.

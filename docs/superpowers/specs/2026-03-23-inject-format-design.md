# Inject Format Separation — Design Spec

**Date:** 2026-03-23
**Status:** Draft

---

## Overview

Separate `inject` from `text` so that `inject` produces a true **behavioral instruction block** — actionable directives for the AI — rather than a character description. Simultaneously upgrade `--explain` to structured YAML output that exposes fusion metadata for debugging and benchmarking.

---

## Goals

- `inject` format produces 5-section behavioral prompt: Decision Policy, Uncertainty Handling, Interaction Rules, Anti-patterns, Style
- `text` format unchanged (current plain-text character description)
- `--explain` outputs machine-readable YAML to stderr (personas with weights, merged policy decisions, removed conflicts)
- All changes are backward compatible — existing character packs continue to validate and run

## Non-Goals

- No `mindset inject` command split (Priority 3, deferred)
- No semantic conflict detection (removed_conflicts is string-level dedup only)
- No changes to `--format anthropic-json` or `--format debug-json`
- No changes to any character pack YAML files (existing packs remain unchanged; `anti_patterns` is optional)

---

## Architecture

Four files change. Everything else stays the same.

The key architectural decision: **inject rendering bypasses `ContextBlock`** because `ContextBlock.from_packs()` discards typed schema fields (`DecisionFramework`, `InterpersonalStyle`, `VoiceSchema`, etc.) into flat strings. The inject renderer needs structured access to `risk_tolerance`, `interpersonal_style.communication`, `vocabulary.preferred`, etc. — none of which survive into `ContextBlock`.

Solution: a standalone function `render_inject_block(weighted_packs)` operates directly on the raw `list[tuple[CharacterPack, float]]`. `FusionEngine` gains a `prepare_packs()` method to expose normalized sorted packs. The `run()` command calls `fuse()` once (filling `FusionReport` and producing `ContextBlock` for text format), then calls `prepare_packs()` once more (pure, deterministic) to get packs for the inject renderer.

```
CharacterPack(s)
      │
      ▼
FusionEngine.fuse()  ──────────────────────────────────────────────► ContextBlock (text format)
      │                                                                      │
      │  (fills FusionReport in-place)                                       │
      └──► FusionReport  ──►  --explain YAML output (stderr)                │
                                                                             │
FusionEngine.prepare_packs()  ──►  list[tuple[CharacterPack, float]]        │
                                         │                                   │
                                         ▼                                   │
                               render_inject_block()  ──►  inject format    │
                                                                             │
                                                   render_for_runtime() routes based on fmt
```

`prepare_packs()` is called at most twice per `run` invocation (once inside `fuse()` via `fuse_config()`, once directly in `run()` for the inject renderer). It is pure and deterministic — no side effects, same output given same inputs.

---

## File Map

| File | Change |
|---|---|
| `agentic_mindset/schema/behavior.py` | Add `anti_patterns: list[str] = []` (optional field) |
| `agentic_mindset/fusion.py` | Add `FusionReport` dataclass; `fuse()`, `fuse_config()`, `from_packs()` accept optional `report`; add `prepare_packs()` |
| `agentic_mindset/context.py` | Add standalone `render_inject_block(weighted_packs)` function |
| `agentic_mindset/cli.py` | `render_for_runtime` updated signature; `run()` uses single `fuse()` + `prepare_packs()`; `generate` and `run` `--explain` emit YAML |

---

## Detailed Design

### 1. `BehaviorSchema` — new optional field

```python
class BehaviorSchema(BaseModel):
    work_patterns: list[str] = []
    decision_speed: Literal["slow", "deliberate", "fast", "impulsive"]
    execution_style: list[str] = []
    conflict_style: str
    anti_patterns: list[str] = []   # NEW — optional, defaults to empty
```

Existing packs omitting `anti_patterns` validate as before. The field is populated gradually as packs are updated.

---

### 2. `FusionReport` dataclass

```python
from dataclasses import dataclass, field

@dataclass
class FusionReport:
    personas: list[tuple[str, float]] = field(default_factory=list)
    strategy: str = ""
    removed_items: list[str] = field(default_factory=list)
    dominant_character: str | None = None
```

All fields have defaults, so the caller can construct `FusionReport()` with no arguments and pass it to `fuse()` to be populated.

**`removed_conflicts` (YAML key) corresponds to `removed_items` (field name).** The field is named `removed_items` internally; the YAML output uses the key `removed_conflicts` for readability.

---

### 3. `FusionEngine` changes

#### 3a. `prepare_packs()` — public method

```python
def prepare_packs(
    self,
    characters: list[tuple[str, float]],
    strategy: FusionStrategy = FusionStrategy.blend,
) -> list[tuple["CharacterPack", float]]:
    """Return normalized, sorted (pack, weight) pairs without building a ContextBlock.

    Caller precondition: characters is non-empty and weights sum to > 0.
    For sequential strategy, all weights are set to 1/N and order is preserved.
    """
    total = sum(w for _, w in characters)
    if total == 0:
        raise ValueError("Weights sum to zero — cannot normalize.")
    if strategy == FusionStrategy.sequential:
        return [
            (self._registry.load_id(cid), 1.0 / len(characters))
            for cid, _ in characters
        ]
    pairs = [(self._registry.load_id(cid), w / total) for cid, w in characters]
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs
```

`prepare_packs()` is a public method intended for callers that need the typed pack objects (e.g., `run()` building the inject block). It is also called internally by `fuse_config()` to eliminate normalization duplication.

#### 3b. Updated `fuse_config()` — delegates to `prepare_packs()`

```python
def fuse_config(self, config: FusionConfig, report: "FusionReport | None" = None) -> ContextBlock:
    raw_pairs = config.characters
    total = sum(w for _, w in raw_pairs)
    if total == 0:
        raise ValueError("Weights sum to zero — cannot normalize.")

    if config.fusion_strategy == FusionStrategy.sequential:
        if len({w for _, w in raw_pairs}) > 1:
            print("Warning: sequential strategy ignores weights...", file=sys.stderr)

    weighted_packs = self.prepare_packs(raw_pairs, config.fusion_strategy)
    show_weights = config.fusion_strategy != FusionStrategy.sequential

    if report is not None:
        normalized = [(self._registry.load_id(cid).meta.id, w)
                      for (pack, w) in weighted_packs
                      for cid, _ in raw_pairs if pack.meta.id == cid]
        # Simpler: build from weighted_packs directly (pack.meta.id is available)
        report.personas = [(pack.meta.id, w) for pack, w in weighted_packs]
        report.strategy = config.fusion_strategy.value
        weights = [w for _, w in weighted_packs]
        report.dominant_character = (
            weighted_packs[0][0].meta.id
            if len(set(weights)) > 1   # exact float equality after normalization
            else None
        )
        report.removed_items = []  # will be appended by from_packs()

    return ContextBlock.from_packs(weighted_packs, show_weights=show_weights, report=report)
```

Note on `dominant_character` equal-weights check: `len(set(weights)) > 1` uses exact float equality. After division by the same total, identical input weights produce identical floats in CPython (e.g., inputs `1,1,1` → `0.333...` three times → set size 1). This is safe for all practical integer weight inputs.

#### 3c. Updated `fuse()` — forwards `report`

```python
def fuse(
    self,
    characters: list[tuple[str, float]],
    strategy: FusionStrategy = FusionStrategy.blend,
    report: "FusionReport | None" = None,
) -> ContextBlock:
    return self.fuse_config(
        FusionConfig(characters=characters, fusion_strategy=strategy),
        report=report,
    )
```

#### 3d. `ContextBlock.from_packs()` — gains `report` parameter

```python
@classmethod
def from_packs(
    cls,
    weighted_packs: list[tuple["CharacterPack", float]],
    show_weights: bool = True,
    report: "FusionReport | None" = None,
) -> "ContextBlock":
    ...
    # existing dedup logic: when skipping a duplicate item:
    if report is not None:
        report.removed_items.append(line)  # append the skipped string
    ...
```

All three signatures (`fuse`, `fuse_config`, `from_packs`) default `report=None`, preserving all 96 existing call sites.

---

### 4. `render_inject_block()` — standalone function in `context.py`

A new top-level function (not a method on `ContextBlock`). Takes the raw weighted packs and produces the 5-section behavioral prompt directly from typed schema fields.

**Caller precondition:** `weighted_packs` is non-empty. If empty, behavior is undefined. Callers (e.g., `run()`) guarantee non-empty via the existing character validation logic.

**Field mapping:**

| Section | Source fields | Rendering |
|---|---|---|
| `DECISION POLICY` | `mindset.core_principles` sorted by `confidence` desc (None sorts last) + `decision_framework.approach` | One bullet per principle; approach as final bullet |
| `UNCERTAINTY HANDLING` | `decision_framework.risk_tolerance + time_horizon` + `personality.emotional_tendencies.stress_response` | `risk_tolerance: X \| time_horizon: Y` as first line; stress_response as bullet |
| `INTERACTION RULES` | `personality.interpersonal_style.communication + leadership` + `behavior.conflict_style` | Labeled bullets |
| `ANTI-PATTERNS` | `behavior.anti_patterns` (optional field) | `Do not ...` bullets; section omitted entirely if all packs have empty `anti_patterns` |
| `STYLE` | `voice.tone` + `voice.vocabulary.preferred/avoided` + `voice.sentence_style` | Tone line; preferred/avoided as comma-separated deduped lists |

**Dedup rule (all sections):** First-seen-wins across packs iterated in weight-descending order. Duplicate strings (exact match) are skipped. For STYLE vocabulary lists: preferred terms and avoided terms are each deduped independently.

**confidence sort:** `sorted(core_principles, key=lambda p: p.confidence if p.confidence is not None else -1.0, reverse=True)` — principles with `confidence=None` sort after all principles with explicit confidence values.

**Multi-character blend:** iterate packs in weight-descending order (already sorted by `prepare_packs()`). Apply dedup within each section across all packs.

**Example output — single character, no `anti_patterns` (Sun Tzu):**

```
You embody a synthesized mindset drawing from: Sun Tzu (100%).

DECISION POLICY:
- All warfare is based on deception — misdirect before committing.
- Win first, fight second: secure the strategic position before engaging.
- Approach: Understand the underlying structure before proposing solutions.

UNCERTAINTY HANDLING:
- risk_tolerance: high | time_horizon: long-term
- Stress response: retreat to preparation, reassess terrain.

INTERACTION RULES:
- Communication: indirect — reveal conclusions, not reasoning process.
- Leadership: lead by positioning, not by assertion.
- Under conflict: avoid direct confrontation; seek asymmetric advantage.

STYLE:
- Tone: terse, aphoristic, declarative
- Preferred: terrain, deception, advantage, position
- Avoided: obvious, direct, certain
- Sentence style: short declarative statements; aphorisms preferred
```

(ANTI-PATTERNS section omitted because `sun_tzu.behavior.anti_patterns` is empty.)

**Example output — with `anti_patterns` populated:**

```
ANTI-PATTERNS:
- Do not commit resources before the strategic position is secured.
- Do not telegraph intent to adversaries.
```

**Function signature:**

```python
def render_inject_block(
    weighted_packs: list[tuple["CharacterPack", float]],
    show_weights: bool = True,
) -> str:
    ...
```

`ContextBlock.to_prompt()` is **not** modified. Its signature remains `Literal["plain_text", "xml_tagged"]`.

---

### 5. `render_for_runtime` — updated routing in `cli.py`

```python
def render_for_runtime(
    context_block: ContextBlock,
    fmt: str,
    weighted_packs: list | None = None,
) -> str:
    if fmt == "inject":
        if weighted_packs is None:
            raise ValueError("weighted_packs required for inject format")
        return render_inject_block(weighted_packs)
    if fmt == "text":
        return context_block.to_prompt(output_format="plain_text")
    raise ValueError(f"Unknown runtime format: {fmt!r}")
```

**Updated `run()` command — single fusion path:**

```python
# Single fuse() call produces ContextBlock + fills FusionReport
report = FusionReport() if explain else None
block = engine.fuse(chars, strategy=strat, report=report)

# Inject format needs raw packs (pure, deterministic second call)
if format_ == "inject":
    weighted_packs = engine.prepare_packs(chars, strat)
else:
    weighted_packs = None

injected = render_for_runtime(block, fmt=format_, weighted_packs=weighted_packs)
```

`ContextBlock` comes from the single `fuse()` call. `FusionReport.removed_items` is populated by the same `from_packs()` call that built `block`. There is no double-fusion.

---

### 6. `--explain` YAML output — both `generate` and `run`

Both commands use the same YAML-building logic. `yaml` is already imported in `cli.py`.

**PyYAML serialization — `personas` list:**

```python
# personas emitted as an ordered list of single-key dicts
personas_list = [{cid: round(w, 4)} for cid, w in report.personas]
data = {
    "personas": personas_list,
    "merged": {
        "decision_policy": _explain_decision_policy(report),
        "risk_tolerance": report.personas[0][0]  # highest-weight pack's risk_tolerance
        # ... (see rules below)
    },
    "removed_conflicts": report.removed_items,
}
typer.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True), err=True)
```

`personas` is intentionally a list of single-key dicts (not a single dict) to preserve weight-descending order in the YAML output. This is valid YAML and unambiguous to human readers.

**`merged` field rules:**

- `decision_policy`:
  - Single character: `f"{report.personas[0][0]}-only"`
  - Multiple characters, `dominant_character` is not None: `f"{report.dominant_character}-dominant"`
  - Multiple characters, `dominant_character` is None (equal weights or sequential): `"equal-blend"`
- `risk_tolerance`: `decision_framework.risk_tolerance` from the pack whose id matches `report.personas[0][0]` (first/highest-weight after post-deduplication ordering). "Input order" means post-`_deduplicate()` order (i.e., the order IDs first appeared in the deduplicated list).
- `time_horizon`: same rule as `risk_tolerance`.

**`generate` command `--explain` pseudocode:**

```python
if explain:
    report = FusionReport()
    # Re-fuse with report to capture metadata
    # Note: block was already built above; fuse again only for report population
    engine.fuse(chars, strategy=strat, report=report)

    risk_tol = _get_risk_tolerance(report, reg)   # load first pack, read decision_framework
    time_hor = _get_time_horizon(report, reg)

    data = {
        "personas": [{cid: round(w, 4)} for cid, w in report.personas],
        "merged": {
            "decision_policy": _explain_decision_policy(report),
            "risk_tolerance": risk_tol,
            "time_horizon": time_hor,
        },
        "removed_conflicts": report.removed_items,
    }
    typer.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True), err=True)
```

For `generate`, since `block` is already built via `engine.fuse(chars, strat)` (without report), a second `fuse()` call with `report=` is needed to capture `removed_items`. This is acceptable because `generate` does not have a performance-critical code path. Alternatively, the `generate` command can be refactored to always call `fuse()` with `report=FusionReport()` and discard it when `--explain` is not set — but that is an implementation choice left to the implementer.

**YAML output example (multi-character):**

```yaml
personas:
  - sun-tzu: 0.6
  - marcus-aurelius: 0.4

merged:
  decision_policy: sun-tzu-dominant
  risk_tolerance: high
  time_horizon: long-term

removed_conflicts:
  - "Precision (intensity 0.95): Attends to exact wording..."
  - "Works in sustained focused sessions..."
```

**Schema line removed** — the `Schema: 1.0` line from old explain output is dropped.

---

## Backward Compatibility

| Scenario | Behavior |
|---|---|
| Existing pack without `anti_patterns` | Validates, `ANTI-PATTERNS` section omitted from inject output |
| `mindset generate --format text` | Unchanged output |
| `mindset run --format text` | Unchanged (routes to plain_text renderer) |
| `mindset run` (default `--format inject`) | New 5-section behavioral output |
| `mindset generate --explain` | Now emits YAML instead of flat text |
| `mindset run --explain` | Now emits YAML instead of flat text |
| `fuse()` called without `report` | Identical behavior to current (report=None default) |
| `fuse_config()` called without `report` | Identical behavior to current (report=None default) |
| `from_packs()` called without `report` | Identical behavior to current (report=None default) |

---

## Testing

New tests needed:

- `test_render_inject_single_character_no_anti_patterns` — pack without `anti_patterns` → 4 sections, no ANTI-PATTERNS header, DECISION POLICY has no risk line, UNCERTAINTY HANDLING has risk line
- `test_render_inject_anti_patterns_present` — pack with `anti_patterns: ["avoid X"]` → ANTI-PATTERNS section with `Do not avoid X` bullets
- `test_render_inject_multi_character_blend` — two characters, higher-weight character's items appear first in each section
- `test_render_inject_confidence_none_sorts_last` — principle with `confidence=None` appears after principles with explicit confidence values in DECISION POLICY
- `test_render_for_runtime_inject_calls_inject_block` — `render_for_runtime(..., "inject", weighted_packs=[...])` returns inject-format string
- `test_render_for_runtime_text_unchanged` — `render_for_runtime(..., "text")` returns plain_text (unchanged)
- `test_fusion_report_removed_items` — after `fuse(chars, report=report)` with two overlapping packs, `report.removed_items` contains the skipped duplicates
- `test_fusion_report_dominant_character_equal_weights` — equal input weights → `report.dominant_character` is `None`
- `test_fusion_report_dominant_character_unequal` — unequal weights → `report.dominant_character` is the id of the highest-weight character
- `test_explain_yaml_generate_single` — `mindset generate sun-tzu --explain` outputs YAML with `decision_policy: sun-tzu-only` and `removed_conflicts: []`
- `test_explain_yaml_generate_multi` — `mindset generate sun-tzu marcus-aurelius --weights 6,4 --explain` outputs YAML with `decision_policy: sun-tzu-dominant`
- `test_explain_yaml_run` — `mindset run claude --persona sun-tzu --explain "q"` outputs YAML to stderr
- `test_explain_yaml_equal_weights` — equal weights → `decision_policy: equal-blend`

Regression: all existing 96 tests must continue to pass.

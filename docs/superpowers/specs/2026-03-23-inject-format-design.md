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

The key architectural decision: **inject rendering bypasses `ContextBlock`** because `ContextBlock.from_packs()` discards the typed schema fields (`DecisionFramework`, `InterpersonalStyle`, `VoiceSchema`, etc.) into flat strings. The inject renderer needs structured access to `risk_tolerance`, `interpersonal_style.communication`, `vocabulary.preferred`, etc. — none of which survive into `ContextBlock`.

Solution: a standalone function `render_inject_block(weighted_packs)` operates directly on the raw `list[tuple[CharacterPack, float]]` before flattening. `FusionEngine` gains a `prepare_packs()` method to expose the normalized sorted packs.

```
CharacterPack(s)
      │
      ▼
FusionEngine.prepare_packs()  ──►  list[tuple[CharacterPack, float]]
      │                                         │
      │                              ┌──────────┴──────────┐
      │                              ▼                     ▼
      │                    ContextBlock.from_packs()   render_inject_block()
      │                              │                     │
      │                         text format           inject format
      │
      └──►  FusionReport  (populated by fuse() in-place)
                  │
                  └──►  --explain YAML output (stderr)
```

---

## File Map

| File | Change |
|---|---|
| `agentic_mindset/schema/behavior.py` | Add `anti_patterns: list[str] = []` (optional field) |
| `agentic_mindset/fusion.py` | Add `FusionReport` dataclass; `fuse()` and `fuse_config()` accept optional `report`; add `prepare_packs()` |
| `agentic_mindset/context.py` | Add standalone `render_inject_block(weighted_packs)` function |
| `agentic_mindset/cli.py` | `run()` uses `prepare_packs()` + `render_inject_block()`; `--explain` emits YAML |

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

### 2. `FusionReport` dataclass and call chain

```python
@dataclass
class FusionReport:
    personas: list[tuple[str, float]]   # [(id, normalized_weight), ...]
    strategy: str
    removed_items: list[str]            # items dropped during dedup in from_packs()
    dominant_character: str | None      # id of highest-weight persona; None if equal weights
```

**Who fills each field:**

`fuse()` fills all four fields when `report` is not None:
- `personas` — normalized `(id, weight)` pairs, same order as `weighted_packs`
- `strategy` — the strategy enum value as string
- `dominant_character` — id of the first (highest-weight) entry; `None` when all normalized weights are equal
- `removed_items` — forwarded to `from_packs()` which appends dropped items in-place

**Call chain (report forwarding):**

```python
# FusionEngine
def fuse(
    self,
    characters: list[tuple[str, float]],
    strategy: FusionStrategy = FusionStrategy.blend,
    report: FusionReport | None = None,
) -> ContextBlock:
    return self.fuse_config(
        FusionConfig(characters=characters, fusion_strategy=strategy),
        report=report,
    )

def fuse_config(self, config: FusionConfig, report: FusionReport | None = None) -> ContextBlock:
    # ... (existing normalization logic) ...
    weighted_packs = [...]  # normalized, sorted
    if report is not None:
        report.personas = [(cid, w) for cid, w in normalized_pairs]
        report.strategy = config.fusion_strategy.value
        report.dominant_character = (
            weighted_packs[0][0].meta.id
            if len(set(w for _, w in weighted_packs)) > 1
            else None
        )
        report.removed_items = []  # will be filled by from_packs()
    return ContextBlock.from_packs(weighted_packs, show_weights=..., report=report)
```

`ContextBlock.from_packs()` gains `report` parameter and appends to `report.removed_items` whenever an item is skipped due to dedup:

```python
@classmethod
def from_packs(
    cls,
    weighted_packs: list[tuple["CharacterPack", float]],
    show_weights: bool = True,
    report: "FusionReport | None" = None,
) -> "ContextBlock":
    ...
    # when skipping a duplicate:
    if report is not None:
        report.removed_items.append(line)
```

**Backward compatibility:** both `fuse()` and `fuse_config()` and `from_packs()` accept `report=None` (default), preserving all existing call sites.

---

### 3. `FusionEngine.prepare_packs()` — expose normalized packs

```python
def prepare_packs(
    self,
    characters: list[tuple[str, float]],
    strategy: FusionStrategy = FusionStrategy.blend,
) -> list[tuple["CharacterPack", float]]:
    """Return normalized, sorted (pack, weight) pairs without building a ContextBlock."""
    total = sum(w for _, w in characters)
    if total == 0:
        raise ValueError("Weights sum to zero — cannot normalize.")
    if strategy == FusionStrategy.sequential:
        return [(self._registry.load_id(cid), 1.0 / len(characters)) for cid, _ in characters]
    pairs = [(self._registry.load_id(cid), w / total) for cid, w in characters]
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs
```

This eliminates duplication: `fuse_config()` calls `prepare_packs()` internally.

---

### 4. `render_inject_block()` — standalone function in `context.py`

A new top-level function (not a method on `ContextBlock`). Takes the raw weighted packs and produces the 5-section behavioral prompt directly from typed schema fields.

**Field mapping:**

| Section | Source fields | Rendering |
|---|---|---|
| `DECISION POLICY` | `mindset.core_principles` (sorted by confidence desc) + `decision_framework.approach` | One bullet per principle; approach as final bullet |
| `UNCERTAINTY HANDLING` | `decision_framework.risk_tolerance + time_horizon` + `personality.emotional_tendencies.stress_response` | `risk_tolerance: X \| time_horizon: Y` line; stress_response as bullet |
| `INTERACTION RULES` | `personality.interpersonal_style.communication + leadership` + `behavior.conflict_style` | Labeled bullets |
| `ANTI-PATTERNS` | `behavior.anti_patterns` (optional field) | `Do not ...` bullets; section omitted entirely if all packs have empty `anti_patterns` |
| `STYLE` | `voice.tone` + `voice.vocabulary.preferred/avoided` + `voice.sentence_style` | Tone line; preferred/avoided as comma-separated lists |

Multi-character blend: iterate packs in weight-descending order. Dedup identical strings within each section (same first-seen-wins logic as `from_packs()`).

**Example output (single character, Sun Tzu):**

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

(ANTI-PATTERNS section omitted when all packs have empty `anti_patterns`.)

**Function signature:**

```python
def render_inject_block(
    weighted_packs: list[tuple["CharacterPack", float]],
    show_weights: bool = True,
) -> str:
    ...
```

`ContextBlock.to_prompt()` is **not** modified. The `to_prompt()` signature stays as `Literal["plain_text", "xml_tagged"]`.

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

In the `run()` command:

```python
weighted_packs = engine.prepare_packs(chars, strat)
block = ContextBlock.from_packs(weighted_packs)
report = FusionReport(personas=[], strategy="", removed_items=[], dominant_character=None)
engine.fuse(chars, strategy=strat, report=report)  # fills report fields
injected = render_for_runtime(block, fmt=format_, weighted_packs=weighted_packs)
```

(When `--explain` is not requested, `report` is not created and `fuse()` is called without `report`.)

---

### 6. `--explain` YAML output

Both `generate` and `run` commands upgrade `--explain` from flat text to YAML. YAML is emitted via `import yaml` — already imported in `cli.py`.

**New format (stderr):**

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

**Rules:**

- `merged.decision_policy`:
  - Single character: `{id}-only`
  - Multiple characters, unequal weights: `{dominant_character}-dominant`
  - Multiple characters, equal weights or sequential strategy: `equal-blend`
- `merged.risk_tolerance`: value from highest-weight character's `decision_framework`. When weights are equal, use the first character in input order.
- `merged.time_horizon`: same rule as `risk_tolerance`.
- `removed_conflicts`: contents of `FusionReport.removed_items`; empty list `[]` when no dedup occurred.

**Schema line removed** — the `Schema: 1.0` line from old explain output is dropped.

---

## Backward Compatibility

| Scenario | Behavior |
|---|---|
| Existing pack without `anti_patterns` | Validates, `ANTI-PATTERNS` section omitted from inject output |
| `mindset generate --format text` | Unchanged output |
| `mindset run --format text` | Unchanged (routes to plain_text renderer) |
| `mindset run` (default `--format inject`) | New 5-section behavioral output |
| `mindset generate --explain` (old) | Now emits YAML instead of flat text |
| `mindset run --explain` (old) | Now emits YAML instead of flat text |
| `fuse()` called without `report` | Identical behavior to current (report=None is default) |
| `from_packs()` called without `report` | Identical behavior to current (report=None is default) |

---

## Testing

New tests needed:

- `test_render_inject_single_character_no_anti_patterns` — pack without `anti_patterns` field → 4 sections, no ANTI-PATTERNS header
- `test_render_inject_anti_patterns_present` — pack with `anti_patterns: ["..."]` → ANTI-PATTERNS section appears with `Do not ...` bullets
- `test_render_inject_multi_character_blend` — two characters, items from higher-weight character appear first
- `test_render_inject_decision_policy_no_risk_line` — `risk_tolerance`/`time_horizon` appear only in UNCERTAINTY HANDLING, not DECISION POLICY
- `test_render_for_runtime_inject_calls_inject_block` — `render_for_runtime(..., "inject", weighted_packs=...)` returns inject-format string
- `test_render_for_runtime_text_unchanged` — `render_for_runtime(..., "text")` still returns plain_text
- `test_fusion_report_removed_items` — deduped items appear in `FusionReport.removed_items` after `fuse(..., report=report)`
- `test_fusion_report_dominant_character_equal_weights` — equal weights → `dominant_character` is `None`
- `test_explain_yaml_generate_single` — `mindset generate --explain` outputs YAML with `decision_policy: {id}-only` and `removed_conflicts: []`
- `test_explain_yaml_generate_multi` — `mindset generate sun-tzu marcus-aurelius --weights 6,4 --explain` outputs YAML with `decision_policy: sun-tzu-dominant`
- `test_explain_yaml_run` — `mindset run --explain` outputs YAML to stderr
- `test_explain_yaml_equal_weights` — equal weights → `decision_policy: equal-blend`

Regression: all existing 96 tests must continue to pass.

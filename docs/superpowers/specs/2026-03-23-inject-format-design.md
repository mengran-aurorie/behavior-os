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

```
CharacterPack(s)
      │
      ▼
FusionEngine.fuse()
      │
      ├──► ContextBlock          (existing, gains _render_inject())
      └──► FusionReport          (new dataclass: personas + removed_items)
                │
                ├──► ContextBlock._render_inject()  →  inject text
                └──► --explain YAML output (stderr)
```

---

## File Map

| File | Change |
|---|---|
| `agentic_mindset/schema/behavior.py` | Add `anti_patterns: list[str] = []` (optional field) |
| `agentic_mindset/fusion.py` | Add `FusionReport` dataclass; `fuse()` optionally returns report |
| `agentic_mindset/context.py` | Add `_render_inject()`; `to_prompt()` accepts `"inject"` format |
| `agentic_mindset/cli.py` | `render_for_runtime` routes `inject` to new path; `--explain` emits YAML |

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
@dataclass
class FusionReport:
    personas: list[tuple[str, float]]   # [(id, normalized_weight), ...]
    strategy: str
    removed_items: list[str]            # items dropped during dedup in ContextBlock.from_packs()
    dominant_character: str | None      # id of highest-weight persona (None if equal weights)
```

`removed_items` is populated by `ContextBlock.from_packs()` — any item that was skipped because an identical string was already present in the merged list is appended here.

`FusionEngine.fuse()` gains an optional `report` parameter:

```python
def fuse(
    self,
    characters: list[tuple[str, float]],
    strategy: FusionStrategy = FusionStrategy.blend,
    report: FusionReport | None = None,
) -> ContextBlock:
```

When `report` is provided (not None), `from_packs()` fills `report.removed_items` in-place. This avoids returning a tuple from `fuse()` and preserves backward compatibility.

---

### 3. `ContextBlock._render_inject()` — 5-section behavioral prompt

Field mapping:

| Section | Source fields | Rendering |
|---|---|---|
| `DECISION POLICY` | `mindset.core_principles` (sorted by confidence desc) + `decision_framework.approach` | One bullet per principle; approach as final bullet |
| `UNCERTAINTY HANDLING` | `decision_framework.risk_tolerance + time_horizon` + `personality.emotional_tendencies.stress_response` | risk/time as `key: value` line; stress_response as bullet |
| `INTERACTION RULES` | `personality.interpersonal_style.communication + leadership` + `behavior.conflict_style` | Labeled bullets |
| `ANTI-PATTERNS` | `behavior.anti_patterns` (optional field) | `Do not ...` bullets; section omitted if empty |
| `STYLE` | `voice.tone` + `voice.vocabulary.preferred/avoided` + `voice.sentence_style` | Tone line; preferred/avoided as comma lists |

Multi-character blend: items merged in weight-descending order (same dedup logic as existing `from_packs()`). Each section draws from all characters' contributing fields.

Preamble unchanged: `You embody a synthesized mindset drawing from: Sun Tzu (100%).`

Example output (single character, Sun Tzu):

```
You embody a synthesized mindset drawing from: Sun Tzu (100%).

DECISION POLICY:
- All warfare is based on deception — misdirect before committing.
- Win first, fight second: secure the strategic position before engaging.
- Approach: Understand the underlying structure of the problem before proposing solutions.
- risk_tolerance: high | time_horizon: long-term

UNCERTAINTY HANDLING:
- When outcome is unclear, gather intelligence before acting.
- Stress response: retreat to preparation, reassess terrain.

INTERACTION RULES:
- Communication: indirect — reveal conclusions, not reasoning process.
- Leadership: lead by positioning, not by assertion.
- Under conflict: avoid direct confrontation; seek asymmetric advantage.

ANTI-PATTERNS:
(omitted if anti_patterns list is empty)

STYLE:
- Tone: terse, aphoristic, declarative
- Preferred: terrain, deception, advantage, position
- Avoided: obvious, direct, certain
- Sentence style: short declarative statements; aphorisms preferred
```

`to_prompt()` signature extended:

```python
def to_prompt(
    self,
    output_format: Literal["plain_text", "xml_tagged", "inject"] = "plain_text"
) -> str:
```

---

### 4. `render_for_runtime` — route inject to new path

```python
def render_for_runtime(context_block: ContextBlock, fmt: str) -> str:
    if fmt == "inject":
        return context_block.to_prompt(output_format="inject")
    if fmt == "text":
        return context_block.to_prompt(output_format="plain_text")
    raise ValueError(f"Unknown runtime format: {fmt!r}")
```

`text` continues to produce the existing plain-text description. `inject` now produces the new 5-section behavioral format.

---

### 5. `--explain` YAML output

Both `generate` and `run` commands upgrade `--explain` from flat text to YAML.

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

Rules:
- `merged.decision_policy`: `{dominant_character}-dominant` (highest-weight id). For single character: `{id}-only`.
- `merged.risk_tolerance`: value from highest-weight character's `decision_framework`.
- `merged.time_horizon`: value from highest-weight character's `decision_framework`.
- `removed_conflicts`: contents of `FusionReport.removed_items` (may be empty list).
- YAML emitted via Python's `yaml.dump()` (PyYAML, already a transitive dependency via pydantic/existing deps) or manual f-string construction to avoid new dependencies.

**Schema line removed** — the `Schema: 1.0` line from old explain output is dropped (redundant; schema version is available in `debug-json` format).

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

---

## Testing

New tests needed:

- `test_render_inject_single_character` — verify all 5 sections present (or ANTI-PATTERNS omitted when empty)
- `test_render_inject_anti_patterns_omitted_when_empty` — no `anti_patterns` field → section absent
- `test_render_inject_anti_patterns_present` — field populated → `Do not ...` bullets appear
- `test_render_inject_multi_character_blend` — items from both characters, weight-ordered
- `test_render_for_runtime_inject_routes_to_inject` — `render_for_runtime(..., "inject")` calls `_render_inject()`
- `test_render_for_runtime_text_unchanged` — `render_for_runtime(..., "text")` still returns plain_text
- `test_fusion_report_removed_items` — verify deduped items appear in `FusionReport.removed_items`
- `test_explain_yaml_generate` — `mindset generate --explain` outputs valid YAML to stderr
- `test_explain_yaml_run` — `mindset run --explain` outputs valid YAML to stderr
- `test_explain_yaml_single_character` — `removed_conflicts: []` when no dedup occurred

Regression: all existing 96 tests must continue to pass.

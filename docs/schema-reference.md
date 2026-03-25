# Character Pack Schema Reference — v1.1

This document is the authoritative reference for the Character Pack YAML format.
Current schema version: **1.1** (`CURRENT_SCHEMA_VERSION` in `agentic_mindset/schema/version.py`).

---

## Field Classification

Each field carries one of three labels:

| Label | Meaning |
|---|---|
| `runtime-critical` | Read by the Behavior IR resolver or renderer. Changing the semantics of these fields is a breaking change. |
| `runtime-optional` | Read at runtime but has a safe default; pack may omit it without affecting output. |
| `descriptive-only` | Not read at runtime. Provides context for humans, future tooling, and LLM prompts via the text path. |

---

## Frozen Runtime-Critical Fields (v1.1)

The following fields will not change semantics within the v1.x lifecycle:

| File | Field path | Used by |
|---|---|---|
| `personality.yaml` | `interpersonal_style.communication` | ConflictResolver slot `communication` |
| `personality.yaml` | `interpersonal_style.leadership` | ConflictResolver slot `leadership` |
| `behavior.yaml` | `conflict_style` | ConflictResolver slot `conflict_style` |
| `mindset.yaml` | `decision_framework.risk_tolerance` | BehaviorIR `risk_tolerance` |
| `mindset.yaml` | `decision_framework.time_horizon` | BehaviorIR `time_horizon` |
| `mindset.yaml` | `decision_framework.approach` | BehaviorIR `decision_policy` |
| `behavior.yaml` | `decision_speed` | BehaviorIR stress_response label |
| `behavior.yaml` | `decision_control` | BehaviorIR slot |
| `personality.yaml` | `emotional_tendencies.stress_response` | BehaviorIR `stress_response` |
| `personality.yaml` | `ConditionalVariant.applies_when` | Conditional evaluation |
| `personality.yaml` | `ConditionalVariant.conjunction` | Conditional AND/OR logic |

---

## meta.yaml

| Field | Type | Classification | Notes |
|---|---|---|---|
| `id` | `str` (kebab-case) | runtime-critical | Used as pack identifier in registry and explain output |
| `name` | `str` | descriptive-only | Human-readable display name |
| `version` | `str` (MAJOR.MINOR.PATCH) | descriptive-only | Pack version, not schema version |
| `schema_version` | `str` (MAJOR.MINOR) | runtime-critical | Checked by loader; must be in `SUPPORTED_SCHEMA_VERSIONS` |
| `type` | `"historical" \| "fictional"` | descriptive-only | Pack category |
| `description` | `str` | descriptive-only | One-line summary |
| `tags` | `list[str]` | descriptive-only | Free-form search tags |
| `authors` | `list[{name, url}]` | descriptive-only | Attribution |
| `created` | `str` (ISO date) | descriptive-only | Pack creation date |
| `license` | `str \| null` | descriptive-only | SPDX identifier or custom string; null = unspecified |
| `visibility` | `"public" \| "private" \| "internal"` | descriptive-only | Default: `"public"` |

---

## mindset.yaml

### `core_principles[]`

| Field | Type | Classification | Notes |
|---|---|---|---|
| `description` | `str` | descriptive-only | One-line principle name |
| `detail` | `str` | descriptive-only | Extended explanation |
| `confidence` | `float 0–1 \| null` | descriptive-only | Author's confidence in sourcing |

### `decision_framework`

| Field | Type | Classification | Notes |
|---|---|---|---|
| `risk_tolerance` | `"low" \| "medium" \| "high"` | **runtime-critical** | Used directly in BehaviorIR |
| `time_horizon` | `"short-term" \| "medium-term" \| "long-term"` | **runtime-critical** | Used directly in BehaviorIR |
| `approach` | `str` | **runtime-critical** | Primary strategy text; mapped to `decision_policy` in IR |
| `heuristics` | `list[str]` | runtime-optional | Actionable decision rules; used in inject render if present |
| `default_strategy` | `str \| null` | runtime-optional | Elaborates `approach`; used in inject render |
| `fallback_strategy` | `str \| null` | runtime-optional | What to do when default fails; used in inject render |
| `commitment_policy` | `"early" \| "deliberate" \| "late" \| null` | runtime-optional | Decision timing |

### `thinking_patterns[]`, `mental_models[]`

| Field | Classification | Notes |
|---|---|---|
| all fields | descriptive-only | Used in text-path FusionEngine output only |

---

## personality.yaml

### `traits[]`

| Field | Type | Classification | Notes |
|---|---|---|---|
| `name` | `str` | descriptive-only | |
| `description` | `str` | descriptive-only | |
| `intensity` | `float 0–1` | descriptive-only | |
| `confidence` | `float 0–1 \| null` | descriptive-only | |

### `emotional_tendencies`

| Field | Type | Classification | Notes |
|---|---|---|---|
| `stress_response` | `str` | **runtime-critical** | Mapped to BehaviorIR `stress_response` |
| `motivation_source` | `str` | descriptive-only | |
| `baseline_mood` | `str \| null` | descriptive-only | |
| `emotional_range` | `"narrow" \| "moderate" \| "wide" \| null` | descriptive-only | |
| `frustration_trigger` | `str \| null` | descriptive-only | |
| `recovery_pattern` | `str \| null` | descriptive-only | |

### `interpersonal_style`

| Field | Type | Classification | Notes |
|---|---|---|---|
| `communication` | `str \| ConditionalSlot` | **runtime-critical** | ConflictResolver slot |
| `leadership` | `str \| ConditionalSlot` | **runtime-critical** | ConflictResolver slot |

### `drives[]` (Drive objects)

| Field | Type | Classification | Notes |
|---|---|---|---|
| `name` | `str` | descriptive-only | Bare strings auto-normalized on load |
| `intensity` | `float 0–1` | descriptive-only | Default 0.8 |
| `description` | `str \| null` | descriptive-only | |

### `ConditionalSlot` / `ConditionalVariant`

| Field | Type | Classification | Notes |
|---|---|---|---|
| `default` | `str` | **runtime-critical** | Used when no condition matches |
| `conditional[].value` | `str` | **runtime-critical** | Override value |
| `conditional[].applies_when` | `list[str]` | **runtime-critical** | Condition labels |
| `conditional[].conjunction` | `"any" \| "all"` | **runtime-critical** | Default `"any"` |
| `conditional[].note` | `str \| null` | descriptive-only | |

---

## behavior.yaml

| Field | Type | Classification | Notes |
|---|---|---|---|
| `work_patterns` | `list[str]` | descriptive-only | |
| `decision_speed` | `"slow" \| "deliberate" \| "fast"` | **runtime-critical** | Note: `"impulsive"` removed in v1.1 |
| `decision_control` | `"controlled" \| "reactive" \| "impulsive" \| null` | runtime-optional | Separate from decision_speed |
| `execution_style` | `list[str]` | descriptive-only | |
| `conflict_style` | `str \| ConditionalSlot` | **runtime-critical** | ConflictResolver slot |
| `anti_patterns` | `list[str]` | descriptive-only | |

---

## voice.yaml

| Field | Type | Classification | Notes |
|---|---|---|---|
| `tone` | `str` | **runtime-critical** | Mapped to BehaviorIR `tone` slot |
| `tone_axes.formality` | `"low" \| "medium" \| "high" \| null` | runtime-optional | |
| `tone_axes.warmth` | `"low" \| "medium" \| "high" \| null` | runtime-optional | |
| `tone_axes.intensity` | `"low" \| "medium" \| "high" \| null` | runtime-optional | |
| `tone_axes.humor` | `"none" \| "dry" \| "playful" \| "sharp" \| null` | runtime-optional | |
| `vocabulary.preferred` | `list[str]` | **runtime-critical** | Mapped to BehaviorIR `preferred_vocabulary` |
| `vocabulary.avoided` | `list[str]` | **runtime-critical** | Mapped to BehaviorIR `avoided_vocabulary` |
| `sentence_style` | `str` | **runtime-critical** | Mapped to BehaviorIR `sentence_style` |
| `signature_phrases` | `list[str]` | descriptive-only | |

---

## sources.yaml

| Field | Type | Classification | Notes |
|---|---|---|---|
| `sources[].title` | `str` | descriptive-only | |
| `sources[].type` | enum (14 values) | descriptive-only | `book \| biography \| interview \| article \| talk \| podcast \| screenplay \| manga \| game \| film \| novel \| essay \| letter \| speech` |
| `sources[].evidence_level` | `"primary" \| "secondary" \| "tertiary" \| null` | descriptive-only | |
| `sources[].path` | `str \| null` | descriptive-only | Local file path |
| `sources[].url` | `str \| null` | descriptive-only | Remote URL |
| `sources[].accessed` | `str` (ISO date) | descriptive-only | |

Minimum 3 sources required per pack.

---

## ConditionalSlot usage example

```yaml
# Simple (string) — promoted to ConditionalSlot on load
conflict_style: avoidant

# Full ConditionalSlot
conflict_style:
  default: avoidant
  conditional:
    - value: direct confrontation
      applies_when: [position_secured, advantage_clear]
      conjunction: all   # both conditions must be true
      note: Only when the trap is fully set
```

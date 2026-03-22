# Agentic Mindset — Design Spec

**Date:** 2026-03-22
**Status:** Approved

---

## Overview

Agentic Mindset is a language-agnostic open source framework for building, managing, and loading the mindsets and personalities of real or fictional figures onto AI agents. It provides a standardized data format (Character Pack), a CLI-driven build pipeline, a Fusion Engine for blending multiple characters, and a standard library of pre-built character packs.

---

## Goals

- Enable developers to load N character mindsets onto any AI agent in a plug-and-play manner
- Provide a reproducible pipeline for extracting structured character profiles from raw source material
- Ship a curated standard library of high-quality character packs
- Stay language-agnostic: the core is data formats + a CLI; SDKs in multiple languages are secondary deliverables

---

## Architecture

The system has three layers:

```
┌─────────────────────────────────────────┐
│           Character Registry            │
│  elon-musk/  steve-jobs/  charlie-munger│
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│           Fusion Engine                 │
│  Load N Character Packs → fused output  │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Agent Context Injector          │
│  System Prompt / Context Block (text)   │
└─────────────────────────────────────────┘
```

---

## Character Pack Structure

Each character is a directory conforming to the Mindset Schema:

```
elon-musk/
├── meta.yaml          # Identity, tags, version, authors
├── mindset.yaml       # Core principles, decision frameworks, mental models
├── personality.yaml   # Emotional tendencies, interpersonal style, motivations
├── behavior.yaml      # Action patterns, work style, habits
├── voice.yaml         # Language style, vocabulary preferences, signature phrases
└── sources.yaml       # Source material references (machine-readable)
```

### Meta Schema (meta.yaml)

```yaml
id: "elon-musk"                  # Unique kebab-case identifier
name: "Elon Musk"
version: "1.0.0"                 # Character pack version (semver)
schema_version: "1.0"            # Mindset Schema version this pack targets
description: "Founder of Tesla, SpaceX, and X. Epitomizes first-principles thinking and extreme execution."
tags:
  - business
  - technology
  - entrepreneurship
authors:
  - name: "Contributor Name"
    url: "https://github.com/..."
created: "2026-03-22"
```

### Mindset Schema (mindset.yaml)

```yaml
schema_version: "1.0"
core_principles:
  - description: "First principles thinking"
    detail: "Break problems down to fundamental truths and reason up from there"
decision_framework:
  risk_tolerance: high           # low | medium | high
  time_horizon: long-term        # short-term | medium-term | long-term
  approach: "Identify the physics of the problem before considering constraints"
thinking_patterns:
  - "Reverse engineering from desired outcome"
  - "Extreme goal setting to drive non-linear progress"
mental_models:
  - name: "First Principles"
    description: "Question every assumption; derive solutions from fundamental truths"
```

### Personality Schema (personality.yaml)

```yaml
schema_version: "1.0"
traits:
  - name: "Intensity"
    description: "Operates with extreme focus and energy; sets expectations others find unrealistic"
    intensity: 0.9               # Required float, range 0.0–1.0
emotional_tendencies:
  stress_response: "doubles down, accelerates"
  motivation_source: "existential mission"
interpersonal_style:
  communication: "direct, technical, sometimes provocative"
  leadership: "sets extreme standards, leads by example"
drives:
  - "Civilizational continuity"
  - "Technological optimism"
```

### Behavior Schema (behavior.yaml)

```yaml
schema_version: "1.0"
work_patterns:
  - "Extreme work hours as default"
  - "Moves fast, breaks processes intentionally"
decision_speed: fast             # slow | deliberate | fast | impulsive
execution_style:
  - "Set impossible deadlines to force innovation"
  - "Vertical integration preference"
conflict_style: "confrontational but mission-aligned"
```

### Voice Schema (voice.yaml)

```yaml
schema_version: "1.0"
tone: "direct, blunt, occasionally humorous"
vocabulary:
  preferred: ["obviously", "insane", "fundamental", "physics of"]
  avoided: ["maybe", "kind of", "somewhat"]
sentence_style: "short declarative statements, technical precision"
signature_phrases:
  - "The best part is no part"
  - "Make it work, make it fast, then make it beautiful"
```

### Sources Schema (sources.yaml)

`sources.yaml` is machine-readable and used by the Extractor to trace provenance. It is not freeform prose.

```yaml
sources:
  - title: "Elon Musk (Walter Isaacson, 2023)"
    type: book                   # book | interview | article | talk | podcast
    url: ""
    accessed: "2026-03-22"
  - title: "Lex Fridman Podcast #252"
    type: podcast
    url: "https://..."
    accessed: "2026-03-22"
```

---

## Schema Versioning

Schemas follow semantic versioning (`MAJOR.MINOR`):

- **Minor bump** (e.g., `1.0` → `1.1`): additive, backward-compatible (new optional fields)
- **Major bump** (e.g., `1.x` → `2.0`): breaking changes; migration required

A `mindset migrate` CLI command handles major version upgrades:

```bash
# Dry run — preview changes without writing
mindset migrate ./characters/elon-musk/ --to 2.0 --dry-run

# In-place migration (backs up originals to elon-musk/.backup/ before writing)
mindset migrate ./characters/elon-musk/ --to 2.0

# Write to a new directory instead of modifying in-place
mindset migrate ./characters/elon-musk/ --to 2.0 --output ./characters/elon-musk-v2/
```

`migrate` migrates all five YAML files that have schema changes between versions. It is idempotent: running it twice on an already-migrated pack produces no changes. The command always creates a `.backup/` directory alongside the pack before writing, preserving originals.

Character packs declare `schema_version` in `meta.yaml`. The CLI validates compatibility on load and warns when a pack targets an older schema version than the installed tooling.

---

## Build Pipeline

Raw source material is processed into a Character Pack through a four-step pipeline:

```
Raw Sources (PDF / text files in a source directory)
        ↓
  [Extractor]   ← LLM extracts structured fields per schema
        ↓
  Draft Character Pack
        ↓
  [Validator]   ← Schema compliance check
        ↓
  [Review]      ← Human review / manual editing
        ↓
  Published to Character Registry
```

### LLM Provider Configuration

The Extractor uses a pluggable provider adapter. Provider is configured via environment variables; the `--provider` flag overrides at runtime:

```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1   # optional, for custom OpenAI-compatible endpoints
mindset build --source ./sources/elon-musk/ --output ./characters/elon-musk/

# Anthropic (uses Anthropic SDK, not OpenAI-compatible endpoint)
export ANTHROPIC_API_KEY=sk-ant-...
mindset build --source ./sources/elon-musk/ --provider anthropic --model claude-opus-4-6
```

Supported providers in v1: `openai` (default), `anthropic`. Each uses its native SDK; both receive the same extraction prompt and return the same structured output. The `openai` adapter also works with any OpenAI-compatible endpoint via `OPENAI_BASE_URL`.

### CLI Interface

```bash
# Build a character pack from source documents
mindset build --source ./sources/elon-musk/ --output ./characters/elon-musk/

# Validate schema compliance
mindset validate ./characters/elon-musk/

# Preview the fused prompt for a character or combination
mindset preview ./characters/elon-musk/
mindset preview --characters elon-musk:0.6,charlie-munger:0.4

# Migrate a character pack to a new schema version
mindset migrate ./characters/elon-musk/ --to 2.0

# List available characters in registry
mindset list
```

---

## Character Registry

The CLI resolves character IDs to filesystem paths using the following priority order:

1. Explicit `--registry` flag on any command
2. `AGENTIC_MINDSET_REGISTRY` environment variable
3. `~/.agentic-mindset/registry/` (user-level default; standard library installs here)
4. `./characters/` (local project fallback)

The standard library is installed into `~/.agentic-mindset/registry/` when the package is installed. Local characters in `./characters/` override standard library characters with the same ID.

---

## Fusion Engine

When multiple Character Packs are loaded, the Fusion Engine merges them by field category using configurable weights.

### Fusion Configuration Schema (fusion.yaml)

```yaml
# Required fields
characters:                        # list, min 1 item
  - id: elon-musk                  # string, must match a character ID in registry
    weight: 0.6                    # float, any positive value; normalized before use

# Optional fields (defaults shown)
fusion_strategy: blend             # blend | dominant | sequential; default: blend
output_format: plain_text          # plain_text | xml_tagged; default: plain_text
```

All fields except `characters` are optional. The `characters` list must contain at least one entry.

### Weight Normalization

Weights are always normalized to sum to 1.0 before fusion. If weights sum to 0, the engine raises an error. Example: weights `[0.6, 0.6]` are normalized to `[0.5, 0.5]`.

### Fusion Strategies

**blend** — weighted merge of all character attributes into a unified profile. Per-field-type semantics:

| Field Type | Blend Behavior |
|---|---|
| String | Both values included in prompt; higher-weight value listed first |
| List | Union of all items; items from higher-weight character appear first; deduplication by exact match |
| Float (e.g. `intensity`) | Weighted average |
| Enum (e.g. `risk_tolerance`) | Higher-weight character's value wins; tied weights use first-listed |

**dominant** — the character with the highest weight always leads, regardless of list order. Secondary characters add only fields not present in the dominant character's pack.

**sequential** — characters apply in list order (not weight order). Each character in the list adds fields not already set by earlier characters. Weight is ignored for field selection but still used to order list items within merged lists. Use this strategy when you want explicit control over precedence via ordering rather than numeric weight.

### Output Formats

`plain_text` (v1 stable):
```
You embody a synthesized mindset drawing from multiple figures:

THINKING FRAMEWORK:
- Apply first principles reasoning: break problems to fundamental truths before reasoning up
- Set extreme goals to drive non-linear progress
...
```

`xml_tagged` (v1 experimental, for tool-calling frameworks):
```xml
<mindset>
  <thinking_framework>...</thinking_framework>
  <personality>...</personality>
</mindset>
```

---

## Standard Library

The project ships with a curated set of pre-built Character Packs. Characters may belong to multiple categories via tags.

- **Business leaders**: Elon Musk, Steve Jobs, Jeff Bezos
- **Investors / thinkers**: Charlie Munger, Naval Ravikant
- **Philosophers**: Marcus Aurelius
- **Historical figures**: Sun Tzu, Napoleon

### Contribution Standards

Community contributions must meet the following criteria before merging into the standard library:

- Minimum 3 distinct source materials in `sources.yaml`
- All five schema files present and passing `mindset validate`
- Sources are published/public (no paywalled-only sources)
- Living public figures: contributions must be based solely on public statements; no speculation about private life or views

See `CONTRIBUTING.md` for the full review process.

---

## Integration Examples

Any agent framework reads the output Context Block:

**Python**
```python
from agentic_mindset import CharacterRegistry, FusionEngine

registry = CharacterRegistry()  # uses default registry resolution
engine = FusionEngine(registry)

context = engine.fuse([
    ("elon-musk", 0.6),
    ("charlie-munger", 0.4),
])

messages = [{"role": "system", "content": context.to_prompt()}, ...]
```

**TypeScript**
```typescript
import { CharacterRegistry, FusionEngine } from 'agentic-mindset'

const engine = new FusionEngine(new CharacterRegistry())
const context = engine.fuse([{ id: 'elon-musk', weight: 0.6 }, { id: 'charlie-munger', weight: 0.4 }])

const systemPrompt = context.toPrompt()
```

---

## Non-Goals (v1)

- No vector/RAG retrieval of source documents (structured schema only)
- No real-time web scraping of source material
- No hosted registry (local filesystem only in v1)
- No GUI (CLI only in v1)

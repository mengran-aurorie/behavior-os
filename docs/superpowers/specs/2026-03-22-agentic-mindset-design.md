# Agentic Mindset — Design Spec

**Date:** 2026-03-22
**Status:** Approved

---

## Overview

Agentic Mindset is a language-agnostic open source framework for building, managing, and loading the mindsets and personalities of historical figures and fictional characters onto AI agents. It provides a standardized data format (Character Pack), a CLI-driven build pipeline, a Fusion Engine for blending multiple characters, and a standard library of pre-built character packs.

The project focuses exclusively on **historical figures** (deceased persons with documented public records) and **fictional characters** (from literature, anime, games, mythology, etc.). Living persons are out of scope for the standard library.

---

## Goals

- Enable developers to load N character mindsets onto any AI agent in a plug-and-play manner
- Provide a reproducible pipeline for extracting structured character profiles from raw source material
- Ship a curated standard library of high-quality character packs drawn from history and fiction
- Stay language-agnostic: the core is data formats + a CLI; SDKs in multiple languages are secondary deliverables

---

## Architecture

The system has three layers:

```
┌─────────────────────────────────────────┐
│           Character Registry            │
│  sun-tzu/  marcus-aurelius/  naruto/    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│           Fusion Engine                 │
│  Load N Character Packs → fused output  │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Context Block (output)          │
│  Structured prompt text injected into   │
│  any agent as System Prompt or context  │
└─────────────────────────────────────────┘
```

---

## Character Pack Structure

Each character is a directory. `meta.yaml` is the single source of truth for the pack's schema version — individual content files do not carry `schema_version`.

```
sun-tzu/
├── meta.yaml          # Identity, tags, schema version, authors
├── mindset.yaml       # Core principles, decision frameworks, mental models
├── personality.yaml   # Emotional tendencies, interpersonal style, motivations
├── behavior.yaml      # Action patterns, work style, habits
├── voice.yaml         # Language style, vocabulary preferences, signature phrases
└── sources.yaml       # Source material references (machine-readable)
```

### Meta Schema (meta.yaml)

```yaml
id: "sun-tzu"                    # Unique kebab-case identifier
name: "Sun Tzu"
version: "1.0.0"                 # Character pack version (three-part semver: MAJOR.MINOR.PATCH)
schema_version: "1.0"            # Mindset Schema version (MAJOR.MINOR); authoritative for all files in pack
type: historical                 # historical | fictional
description: "Chinese military strategist, author of The Art of War. Epitomizes strategic patience and deception."
tags:
  - strategy
  - philosophy
  - military
authors:
  - name: "Contributor Name"
    url: "https://github.com/..."
created: "2026-03-22"
```

`type` is a closed enum: `historical` (deceased real person with documented public record) or `fictional` (character from literature, anime, games, mythology, or other creative works).

`schema_version` in `meta.yaml` is the single authoritative version for the entire pack. Content files (`mindset.yaml`, etc.) do not declare `schema_version` independently.

### Mindset Schema (mindset.yaml)

```yaml
core_principles:
  - description: "Strategic deception"
    detail: "All warfare is based on deception; appear weak when strong, strong when weak"
    confidence: 0.95             # Optional float 0.0–1.0; omit if unknown. Reflects how well-evidenced this field is.
decision_framework:
  risk_tolerance: medium         # Enum: low | medium | high
  time_horizon: long-term        # Enum: short-term | medium-term | long-term
  approach: "Win before the battle begins; avoid direct confrontation when possible"
thinking_patterns:
  - "Observe before acting"
  - "Turn enemy's strength into weakness"
mental_models:
  - name: "Empty Fort Strategy"
    description: "Use apparent vulnerability to create uncertainty in opponents"
```

### Personality Schema (personality.yaml)

```yaml
traits:
  - name: "Patience"
    description: "Waits for the optimal moment; never acts from impatience"
    intensity: 0.9               # Required float, range 0.0–1.0. Validator errors on out-of-range values.
  - name: "Pragmatism"
    description: "Victory matters, not glory; any method that works is valid"
    intensity: 0.85
emotional_tendencies:
  stress_response: "withdraws to observe; increases information gathering"
  motivation_source: "victory through minimum force"
interpersonal_style:
  communication: "indirect, layered with meaning, uses metaphor"
  leadership: "leads through positioning, not direct command"
drives:
  - "Strategic mastery"
  - "Minimum cost, maximum result"
```

### Behavior Schema (behavior.yaml)

```yaml
work_patterns:
  - "Exhaustive preparation before any action"
  - "Constant situational awareness"
decision_speed: deliberate       # Enum: slow | deliberate | fast | impulsive
execution_style:
  - "Strike only when conditions are fully favorable"
  - "Leave the enemy a path to retreat to avoid desperate resistance"
conflict_style: "avoidant of direct confrontation; prefers positioning"
```

### Voice Schema (voice.yaml)

```yaml
tone: "measured, aphoristic, authoritative"
vocabulary:
  preferred: ["position", "opportunity", "adapt", "observe"]
  avoided: ["rush", "obvious", "certain"]
sentence_style: "short aphorisms; layers of meaning; often uses paradox"
signature_phrases:
  - "Supreme excellence consists in breaking the enemy's resistance without fighting"
  - "Know your enemy and know yourself"
```

### Sources Schema (sources.yaml)

`sources.yaml` is machine-readable. The Extractor reads it to locate source files during `mindset build`. It is not freeform prose.

```yaml
sources:
  - title: "The Art of War (Lionel Giles translation, 1910)"
    type: book                   # Enum: book | interview | article | talk | podcast | screenplay | manga | game
    path: "./sources/art-of-war.txt"   # local file path (relative to sources dir), or omit if url-only
    url: "https://..."           # optional
    accessed: "2026-03-22"
  - title: "Sun Tzu: The Art of War for Managers (Gerald Michaelson)"
    type: book
    path: "./sources/art-of-war-managers.pdf"
    accessed: "2026-03-22"
```

---

## Enum Definitions

All closed enum values are defined here. The validator enforces these.

```yaml
# meta.yaml
type: [historical, fictional]

# mindset.yaml
decision_framework.risk_tolerance: [low, medium, high]
decision_framework.time_horizon: [short-term, medium-term, long-term]

# behavior.yaml
decision_speed: [slow, deliberate, fast, impulsive]

# sources.yaml
sources[].type: [book, interview, article, talk, podcast, screenplay, manga, game]

# fusion.yaml
fusion_strategy: [blend, dominant, sequential]
output_format: [plain_text, xml_tagged]
```

---

## Schema Versioning

The Mindset Schema uses `MAJOR.MINOR` versioning (e.g., `1.0`, `1.1`, `2.0`). Character pack versions use three-part semver (`1.0.0`). These are independent.

- **Minor bump** (e.g., `1.0` → `1.1`): additive, backward-compatible (new optional fields). Existing packs remain valid.
- **Major bump** (e.g., `1.x` → `2.0`): breaking changes; migration required.

A `mindset migrate` CLI command handles major version upgrades:

```bash
# Dry run — preview changes without writing
mindset migrate ./characters/sun-tzu/ --to 2.0 --dry-run

# In-place migration (backs up originals to .backup/ before writing)
mindset migrate ./characters/sun-tzu/ --to 2.0

# Write to a new directory
mindset migrate ./characters/sun-tzu/ --to 2.0 --output ./characters/sun-tzu-v2/
```

`migrate` is idempotent: running it twice on an already-migrated pack produces no changes. It always creates a `.backup/` directory before writing. It migrates all files that have schema changes between the two versions.

---

## Build Pipeline

```
Source directory (PDF / text files)
        ↓
  [Extractor]   ← LLM reads sources.yaml, processes each file, fills schema fields
        ↓
  Draft Character Pack
        ↓
  [Validator]   ← Schema compliance check (required fields, enum values, float ranges)
        ↓
  [Review]      ← Human review / manual editing
        ↓
  Published to Character Registry
```

### Extraction Prompt

The Extractor uses a versioned prompt template stored at `prompts/extract-v{N}.md` in the project repository. Prompt version is tied to the schema version: schema `1.x` uses `extract-v1.md`. Changes to the extraction prompt increment the prompt version and trigger re-extraction review for all standard library packs built with the previous version.

The extraction prompt instructs the LLM to:
1. Read all source files listed in `sources.yaml`
2. Fill each schema field based strictly on documented evidence
3. Set `confidence` values per entry (0.0–1.0) based on directness of evidence
4. Leave fields empty rather than speculate

### LLM Provider Configuration

```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1   # optional; override for compatible endpoints
mindset build --source ./sources/sun-tzu/ --output ./characters/sun-tzu/

# Anthropic (uses Anthropic SDK natively, not OpenAI-compatible)
export ANTHROPIC_API_KEY=sk-ant-...
mindset build --source ./sources/sun-tzu/ --provider anthropic --model claude-opus-4-6
```

Model names are passed through verbatim to the provider SDK without validation. Supported providers in v1: `openai` (default), `anthropic`.

### CLI Interface

```bash
# Scaffold a new empty character pack
mindset init sun-tzu --type historical

# Build a character pack from source documents
mindset build --source ./sources/sun-tzu/ --output ./characters/sun-tzu/

# Validate schema compliance
mindset validate ./characters/sun-tzu/

# Preview the Context Block for a character or fusion
mindset preview ./characters/sun-tzu/
mindset preview --fusion ./my-blend.yaml

# Migrate a character pack to a new schema version
mindset migrate ./characters/sun-tzu/ --to 2.0 --dry-run
mindset migrate ./characters/sun-tzu/ --to 2.0

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

Local characters in `./characters/` with the same ID as a standard library character take precedence.

---

## Fusion Engine

### Fusion Configuration Schema (fusion.yaml)

```yaml
# Required
characters:                        # list, min 1 item
  - id: sun-tzu                    # string; must resolve in registry
    weight: 0.6                    # float, any positive value; normalized before use
  - id: marcus-aurelius
    weight: 0.4

# Optional (defaults shown)
fusion_strategy: blend             # blend | dominant | sequential; default: blend
output_format: plain_text          # plain_text | xml_tagged; default: plain_text
```

All fields except `characters` are optional.

### Weight Normalization

Weights are normalized to sum to 1.0 before fusion. Weights summing to 0 raise an error. Example: `[0.6, 0.6]` → `[0.5, 0.5]`.

### Fusion Strategies

**blend** — weighted merge of all attributes. Per-field-type semantics:

| Field Type | Blend Behavior |
|---|---|
| String | Both values rendered as a combined description in the output prompt; higher-weight value leads. Example: `conflict_style` blending "avoidant" (0.6) and "confrontational" (0.4) renders as: "Prefers indirect positioning over direct confrontation, though willing to engage directly when advantageous." |
| List | Union of all items; items from higher-weight character appear first; exact-match deduplication. Semantic deduplication is a known v2 limitation. |
| Float | Weighted average |
| Enum | Higher-weight character's value wins; tied weights use first-listed character |

**dominant** — the character with the highest weight always leads, regardless of list order. Secondary characters contribute only fields absent from the dominant character's pack. For list fields, the dominant character's list is used as-is; secondary characters' list items are appended.

**sequential** — characters apply strictly in list order. Each character adds fields not already set by earlier characters. Weight values are ignored entirely in sequential mode (a warning is emitted if weights are provided with `fusion_strategy: sequential`). Use this strategy when explicit ordering is more important than proportional weighting.

### Context Block Output Contract

The Fusion Engine produces a **Context Block** — a structured text artifact injected into an agent as a system prompt or context prefix.

A Context Block always contains the following sections in this order:
1. **Preamble** — one sentence describing the synthesized character blend
2. **Thinking Framework** — merged `mindset.yaml` content (principles, mental models, decision framework)
3. **Personality** — merged `personality.yaml` content (traits, drives, emotional tendencies)
4. **Behavioral Tendencies** — merged `behavior.yaml` content
5. **Voice & Style** — merged `voice.yaml` content (tone, vocabulary, signature phrases)

`to_prompt()` in any SDK must produce output conforming to this section order. Section content may vary by fusion strategy, but sections are always present (empty sections are omitted).

**`plain_text` output (v1 stable):**
```
You embody a synthesized mindset drawing from the following figures: Sun Tzu (60%), Marcus Aurelius (40%).

THINKING FRAMEWORK:
- All warfare is based on deception; observe before acting
- Practice negative visualization; amor fati — love what is
...

PERSONALITY:
- Patient and measured; withdraws to observe under pressure
- Disciplined and self-controlled; acts from duty, not desire
...
```

**`xml_tagged` output (v1 experimental):**
```xml
<character-context>
  <thinking-framework>...</thinking-framework>
  <personality>...</personality>
  <behavioral-tendencies>...</behavioral-tendencies>
  <voice-and-style>...</voice-and-style>
</character-context>
```

`xml_tagged` graduates to stable in v2 when at least one major agent framework documents native support for it.

---

## Standard Library

The standard library ships exclusively with historical figures and fictional characters.

**Historical figures:**
- Strategists: Sun Tzu, Napoleon Bonaparte
- Philosophers: Marcus Aurelius, Confucius, Seneca
- Scientists / thinkers: Leonardo da Vinci, Nikola Tesla

**Fictional characters:**
- Anime: Naruto Uzumaki, Levi Ackermann, Gojo Satoru
- Literature: Sherlock Holmes, Atticus Finch
- Mythology: Odysseus

### Contribution Standards

- **Scope**: Historical figures (deceased) or fictional characters only. Living persons are not accepted.
- **Sources**: Minimum 3 distinct source materials in `sources.yaml`. All sources must be publicly accessible.
- **Validation**: All five schema files must be present and pass `mindset validate`.
- **Fictional characters**: Sources must include the original work (manga, novel, screenplay, game). Fan-created secondary sources may supplement but not replace primary sources.
- **Historical figures**: Primary sources (translated writings, documented speeches) preferred. Biographical analysis may supplement.

Community PRs follow the review process in `CONTRIBUTING.md`.

---

## Integration Examples

**Python**
```python
from agentic_mindset import CharacterRegistry, FusionEngine

engine = FusionEngine(CharacterRegistry())

context = engine.fuse([
    ("sun-tzu", 0.6),
    ("marcus-aurelius", 0.4),
])

messages = [{"role": "system", "content": context.to_prompt()}, ...]
```

**TypeScript**
```typescript
import { CharacterRegistry, FusionEngine } from 'agentic-mindset'

const context = new FusionEngine(new CharacterRegistry()).fuse([
  { id: 'sun-tzu', weight: 0.6 },
  { id: 'marcus-aurelius', weight: 0.4 },
])

const systemPrompt = context.toPrompt()
```

**fusion.yaml (config-file approach)**
```bash
mindset preview --fusion ./blend.yaml
```

---

## Non-Goals (v1)

- No living persons in the standard library
- No vector/RAG retrieval of source documents (structured schema only)
- No real-time web scraping of source material
- No hosted registry (local filesystem only in v1)
- No GUI (CLI only in v1)
- No semantic deduplication in list fusion (v2)

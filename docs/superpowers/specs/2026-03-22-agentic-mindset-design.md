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
├── meta.yaml          # Name, tags, version, description
├── mindset.yaml       # Core principles, decision frameworks, mental models
├── personality.yaml   # Emotional tendencies, interpersonal style, motivations
├── behavior.yaml      # Action patterns, work style, habits
├── voice.yaml         # Language style, vocabulary preferences, signature phrases
└── sources.md         # Source material references (books, interviews, articles)
```

### Mindset Schema (mindset.yaml)

```yaml
version: "1.0"
core_principles:
  - description: "First principles thinking"
    detail: "Break problems down to fundamental truths and reason up from there"
decision_framework:
  risk_tolerance: high
  time_horizon: long-term
  approach: "Identify the physics of the problem before considering constraints"
thinking_patterns:
  - "Reverse engineering from desired outcome"
  - "Extreme goal setting to drive non-linear progress"
mental_models:
  - name: "First Principles"
    description: "..."
```

### Personality Schema (personality.yaml)

```yaml
version: "1.0"
traits:
  - name: "Intensity"
    description: "..."
    intensity: 0.9
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
version: "1.0"
work_patterns:
  - "Extreme work hours as default"
  - "Moves fast, breaks processes intentionally"
decision_speed: fast
execution_style:
  - "Set impossible deadlines to force innovation"
  - "Vertical integration preference"
conflict_style: "confrontational but mission-aligned"
```

### Voice Schema (voice.yaml)

```yaml
version: "1.0"
tone: "direct, blunt, occasionally humorous"
vocabulary:
  preferred: ["obviously", "insane", "fundamental", "physics of"]
  avoided: ["maybe", "kind of", "somewhat"]
sentence_style: "short declarative statements, technical precision"
signature_phrases:
  - "The best part is no part"
  - "Make it work, make it fast, then make it beautiful"
```

---

## Build Pipeline

Raw source material is processed into a Character Pack through a four-step pipeline:

```
Raw Sources (PDF / text / URL)
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

### CLI Interface

```bash
# Build a character pack from source documents
mindset build --source ./sources/elon-musk/ --output ./characters/elon-musk/

# Validate schema compliance
mindset validate ./characters/elon-musk/

# Preview the fused prompt for a character or combination
mindset preview ./characters/elon-musk/
mindset preview --characters elon-musk:0.6,charlie-munger:0.4

# List available characters in registry
mindset list
```

---

## Fusion Engine

When multiple Character Packs are loaded, the Fusion Engine merges them by field category using configurable weights.

### Load Configuration

```yaml
# fusion.yaml
characters:
  - id: elon-musk
    weight: 0.6
  - id: charlie-munger
    weight: 0.4
fusion_strategy: blend   # blend | dominant | sequential
```

### Fusion Strategies

- **blend**: Weighted merge of all character attributes into a unified profile
- **dominant**: Primary character leads; secondary characters fill gaps
- **sequential**: Characters apply in order (first character's traits, then second's where not contradicted)

### Output

The Fusion Engine outputs a plain-text **Context Block** — a formatted system prompt section. This is the integration point for any agent framework:

```
You embody a synthesized mindset drawing from multiple figures:

THINKING FRAMEWORK:
- Apply first principles reasoning: break problems to fundamental truths before reasoning up
- Set extreme goals to drive non-linear progress
- Evaluate decisions through the lens of long-term civilizational impact

PERSONALITY:
- Direct and technically precise in communication
- High risk tolerance; bias toward action over analysis
- Rational and multidisciplinary; seek latticework of mental models

BEHAVIORAL TENDENCIES:
- Move fast and challenge constraints deliberately
- Prefer deep work and extreme focus
...
```

---

## Standard Library

The project ships with a curated set of pre-built Character Packs covering:

- Business leaders (Elon Musk, Steve Jobs, Charlie Munger, Jeff Bezos)
- Philosophers / thinkers (Marcus Aurelius, Charlie Munger, Naval Ravikant)
- Historical figures (Sun Tzu, Napoleon)

Community contributions follow the same pipeline and schema, with a review process before merging into the standard library.

---

## Integration Examples

Any agent framework reads the output Context Block:

**Python**
```python
from agentic_mindset import CharacterRegistry, FusionEngine

registry = CharacterRegistry("./characters")
engine = FusionEngine(registry)

context = engine.fuse([
    ("elon-musk", 0.6),
    ("charlie-munger", 0.4),
])

# Inject into any LLM call
messages = [{"role": "system", "content": context.to_prompt()}, ...]
```

**TypeScript**
```typescript
import { CharacterRegistry, FusionEngine } from 'agentic-mindset'

const engine = new FusionEngine(new CharacterRegistry('./characters'))
const context = engine.fuse([{ id: 'elon-musk', weight: 0.6 }, { id: 'charlie-munger', weight: 0.4 }])

const systemPrompt = context.toPrompt()
```

---

## Non-Goals (v1)

- No vector/RAG retrieval of source documents (structured schema only)
- No real-time web scraping
- No built-in LLM provider (extractor uses any LLM via API key config)
- No hosted registry (local filesystem only in v1)

---

## Open Questions

- Schema versioning and migration strategy
- Fusion weight normalization edge cases
- LLM provider abstraction for the Extractor (pluggable vs. opinionated)

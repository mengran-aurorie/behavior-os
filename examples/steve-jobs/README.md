# Steve Jobs — Compiler End-to-End Example

**This directory is a complete, walkthrough-ready demonstration of the BehaviorOS compiler pipeline.**

It answers four questions:

1. [How do I write sources?](#1-sources)
2. [What does compile produce?](#2-compile-output)
3. [What does human review change?](#3-human-review)
4. [How do I use the final pack?](#4-use-the-pack)

---

## TL;DR — One-Command Walkthrough

```bash
# Compile 3 sources → full pack (with mock LLM for CI)
python -m pytest tests/test_compiler_compile.py::TestCompilePackPipeline::test_compile_pack_full_pipeline_produces_slots -v

# Run the real Steve Jobs pack
mindset run claude --persona steve-jobs -- "How should I think about this product roadmap?"

# Or blend two opposing personas
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- \
  "We're negotiating with a much larger partner."
```

---

## 1. Sources

**File:** [`steve-jobs/sources.yaml`](./steve-jobs/sources.yaml)

A pack starts with **3+ public sources** — this is the quality floor. Sources must be real, attributable, and public (interviews, biographies, speeches, letters).

```yaml
sources:
  - title: "The Steve Jobs Interview: 1993"
    type: interview
    url: "https://www.wired.com/archives/steve-jobs-1993"
    evidence_level: primary
    accessed: '2026-03-26'
    notes: >-
      First-hand interview. Jobs directly articulates his philosophy
      on innovation, quality, hiring, and standards.

  - title: "Steve Jobs — Walter Isaacson, Chapter 15"
    type: biography
    url: "https://www.simonandschuster.com/books/Steve-Jobs/Walter-Isaacson/9781451648539"
    evidence_level: secondary
    accessed: '2026-03-26'
    notes: >-
      Second-hand biographical account. Describes Jobs' philosophy
      and behaviors with contextual framing.

  - title: "Creative Selection — Ken Kocienda"
    type: biography
    evidence_level: primary
    accessed: '2026-03-26'
    notes: >-
      First-hand colleague account. Describes day-to-day behaviors,
      meeting dynamics, and Jobs' management style.
```

### Source Quality Rules

| Requirement | Why |
|---|---|
| **3+ sources minimum** | Single-source packs have unverified blind spots |
| **Mix of primary + secondary** | Primary = direct quotes; Secondary = contextual framing |
| **Public / attributable** | Enables evidence verification and reproducibility |
| **Accessed date required** | Prevents link rot from silently breaking packs |

---

## 2. Compile Output

**Command:**
```bash
mindset compile sources.yaml --name "Steve Jobs" --id steve-jobs --output ./build
```

**What the compiler produces:**

```
_build/
├── explain.yaml           # Full decision trace (what was extracted, why)
├── coverage.yaml          # Source utilization report
├── slots.yaml             # All slots filled + source attribution
├── draft-pack/
│   ├── meta.yaml
│   ├── mindset.yaml
│   ├── personality.yaml
│   ├── behavior.yaml
│   ├── voice.yaml
│   └── sources.yaml
└── _compile_meta.yaml     # Provenance + quality gates
```

### Compiler Pipeline

```
Sources (txt/md/yaml)
        │
        ▼
[Step 1: LLM Extraction]     → ExtractedBehavior[] (16 extractions from 3 sources)
[Step 2: LLM Normalization] → CanonicalBehavior[] (8 canonical behaviors)
[Step 2b: Behavior Typing]  → Assigns: core_principle / decision_policy / mental_model / etc.
[Step 3: Schema Mapping]     → Maps to: mindset / personality / behavior / voice
[Step 4: Pack Builder]      → YAML pack files + provenance + review queue
```

### Quality Gates

The compiler computes a `quality_score` for every compile:

| Gate | Threshold | Steve Jobs Result |
|---|---|---|
| Coverage | ≥ 0.60 | 0.24 ⚠️ |
| Evidence | ≥ 0.50 | 0.00 ⚠️ |
| Contradictions | 0 | pass |

> **Coverage 0.24 means** the compiler filled 24% of schema slots. This is expected for a 3-source compile — a full pack would need more sources or iterative compilation.
> **Evidence 0.00** means no source quotes were successfully attributed to slots (paraphrasing instead of quoting).

---

## 3. Human Review

**File:** [`steve-jobs/_compile_meta.yaml`](./steve-jobs/_compile_meta.yaml)

The compiler generates a **high-quality first draft** — not a finished pack. Human review corrects three categories of issues:

### What the compiler got right

- Extracted 5 genuine core principles from source material
- Identified the key heuristics: "Innovation is saying no to a thousand things"
- Captured Jobs' hiring philosophy correctly
- Identified long-term time horizon and low risk tolerance

### What human review corrected

| # | Issue | Before (Compiler) | After (Human Review) |
|---|---|---|---|
| 1 | Parsing artifact | "Variants" behavior (non-existent) | Removed entirely |
| 2 | All behaviors mapped to `core_principle` | 8 `core_principle` entries | Distributed across: `decision_framework`, `thinking_patterns`, `mental_models` |
| 3 | Missing `decision_framework` | Not produced | Added: risk_tolerance, time_horizon, heuristics, approach |
| 4 | Missing `thinking_patterns` | Not produced | Added: Reality distortion field, first-principles advocacy, binary quality judgment |
| 5 | Missing `mental_models` | Not produced | Added: whiteboard test, excellence requires pressure, respect through simplicity |
| 6 | Source titles generic | "Source 1", "Source 2" | Restored to actual publication titles |

### Review Items Flagged

The compiler identified 8 `needs_review` items (medium-confidence extractions). After human review, all 8 were confirmed and correctly placed.

---

## 4. Use the Pack

### Run solo

```bash
mindset run claude --persona steve-jobs -- \
  "How should I think about this product roadmap?"
```

Expected output style: **direct, binary, quality-focused.** Jobs would ask:
- "Is this excellent in every dimension?"
- "Who needs this? What are we doing this for?"
- "If it's not great, it's holding everything else back."

### Blend with another persona

```bash
# Sun Tzu (60%) + Steve Jobs (40%)
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- \
  "We're negotiating with a much larger partner."
```

Jobs pairs well with strategic framings — Jobs provides the "say no to everything that isn't excellent" constraint; Tzu provides the positioning framework.

### Verify behavior

```bash
# See the Context Block that gets injected
mindset preview steve-jobs

# See every fusion decision
mindset run claude --persona steve-jobs --explain -- \
  "Should we ship this feature?"
```

---

## File Inventory

| File | Purpose |
|---|---|
| [`sources.yaml`](./steve-jobs/sources.yaml) | 3 input sources with provenance |
| [`_build/`](./_build/) | Compiler output (do not edit directly) |
| [`steve-jobs/`](./steve-jobs/) | **Final reviewed pack** (human-reviewed output) |
| [`_compile_meta.yaml`](./steve-jobs/_compile_meta.yaml) | Compiler provenance + human corrections |
| [`meta.yaml`](./steve-jobs/meta.yaml) | Pack identity and schema version |
| [`mindset.yaml`](./steve-jobs/mindset.yaml) | Core principles, decision framework, mental models |
| [`behavior.yaml`](./steve-jobs/behavior.yaml) | Work patterns, decision speed, execution style |
| [`personality.yaml`](./steve-jobs/personality.yaml) | Traits, emotional tendencies, drives |
| [`voice.yaml`](./steve-jobs/voice.yaml) | Tone, vocabulary, signature phrases |

---

## Next Step: Build Your Own Pack

```bash
# Scaffold a new pack
mindset init my-character --type historical

# Fill sources.yaml with your sources
# Run compile
mindset compile sources.yaml --name "My Character" --id my-character --output ./build

# Review the draft in ./build/draft-pack/
# Apply corrections to ./build/draft-pack/ (or directly to your sources and recompile)

# Validate and use
mindset validate ./build/draft-pack
mindset run claude --persona my-character -- "Your question here"
```

See [`docs/compiler-v0-spec.md`](../../docs/compiler-v0-spec.md) for the full compiler specification.

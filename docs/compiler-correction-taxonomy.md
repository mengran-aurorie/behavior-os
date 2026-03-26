# Compiler Correction Taxonomy

**Source:** Analysis of human review corrections across Steve Jobs, Sun Tzu, and Marcus Aurelius benchmark compilations.
**Date:** 2026-03-26
**Version:** 0.1

---

## Overview

Across 3 benchmark personas (16–18 extractions each, 6 corrections per persona), human review corrections fall into **5 distinct patterns**. This taxonomy guides v1 prioritization.

| Pattern | Frequency | Fixable With |
|---|---|---|
| Parsing artifacts | 3/3 (always) | Pre-processing |
| Schema distribution | 3/3 (always) | Prompt engineering |
| Missing slot inference | 3/3 (always) | Prompt engineering |
| Weak conditional capture | 3/3 (always) | Prompt engineering + pipeline |
| Provenance under-linking | 2/3 | Pipeline |

---

## Pattern 1: Parsing Artifacts (3/3 personas)

**What it looks like:** A non-behavior extracted as a behavior. Appears as "Variants", "Notes", section headers, or metadata parsed as content.

**Example:**
```yaml
# Compiler output:
- description: Variants
  detail: Variants
  confidence: 0.75
```

**Root cause:** Source text contains section headers, footnotes, or metadata that the LLM extraction treats as behavioral content.

**Human correction:** Remove the artifact. No behavioral content is lost.

**Fixability:**

| Approach | Effort | Effectiveness |
|---|---|---|
| Pre-process: strip section headers before extraction | Low | High for "Variants" class |
| Post-process: filter behaviors matching known artifact patterns | Low | Medium |
| LLM instruction: "Do not extract section titles or metadata" | Low | Medium |

**Recommendation for v1:** Pre-processing + LLM instruction.

---

## Pattern 2: Schema Distribution (3/3 personas)

**What it looks like:** All extracted behaviors typed as `core_principle` (or another single slot type). Human re-distributes across `decision_framework`, `thinking_patterns`, `mental_models`.

**Example:**
```yaml
# Compiler output: All 8 behaviors → core_principles
core_principles:
  - description: "Water shapes itself to the vessel..."
  - description: "Speed is the essence of war..."
  # (decision_framework, thinking_patterns, mental_models all empty)

# After human review: Distributed correctly
decision_framework:
  risk_tolerance: medium
  time_horizon: long-term
  heuristics: [...]
mental_models:
  - name: Shi (Strategic Advantage)
    description: [...]
```

**Root cause:** Extraction prompt does not explicitly instruct the LLM to produce behaviors for all schema slot types. LLM defaults to what's most prominent in the source.

**Human correction:** Re-read sources and redistribute behaviors to correct slots. Time cost: ~10 minutes per persona.

**Fixability:**

| Approach | Effort | Effectiveness |
|---|---|---|
| Add "slot coverage" instruction to extraction prompt | Low | High |
| Multi-pass: first pass extracts, second pass fills empty slots | Medium | Very high |
| Prompt with explicit slot list + descriptions | Low | High |

**Recommendation for v1:** Slot coverage instruction in extraction prompt. Example: "Ensure behaviors are distributed across core_principles, decision_framework, thinking_patterns, and mental_models."

---

## Pattern 3: Missing Slot Inference (3/3 personas)

**What it looks like:** Entire schema sections left empty (`decision_framework: {}`, `thinking_patterns: []`, `mental_models: []`) because the sources don't explicitly discuss those topics in behavioral terms.

**Example (Sun Tzu):**
```yaml
# Compiler output:
decision_framework: {}
thinking_patterns: []
mental_models: []

# After human review: Human infers from context
decision_framework:
  risk_tolerance: medium
  time_horizon: long-term
  heuristics:
    - Gather intelligence before any commitment
    - Choose ground carefully
    - Prefer indirect action
```

**Root cause:** Sources discuss strategic principles but don't use schema vocabulary. The LLM extracts what sources say, not what the schema requires.

**Human correction:** Human reads sources with schema knowledge and infers appropriate content. Time cost: ~15 minutes per persona.

**Fixability:**

| Approach | Effort | Effectiveness |
|---|---|---|
| "If no evidence for X in sources, note 'no evidence found' rather than omitting" | Low | Medium |
| Topic-guiding constraints in extraction prompt | Medium | High |
| Named concept extraction: specifically ask for frameworks, models, patterns | Medium | High |

**Recommendation for v1:** Named concept extraction pass — second LLM call specifically looking for named frameworks and mental models in source text.

---

## Pattern 4: Weak Conditional Capture (3/3 personas)

**What it looks like:** Conditional behaviors (e.g., "when X, then Y") present in sources but not captured as ConditionalSlots. Captured as flat behaviors instead.

**Example:**
```yaml
# Manual pack has:
interpersonal_style:
  communication:
    default: Direct, opinionated, unvarnished
    conditional:
      - value: Blunt and demanding with no tolerance for qualification
        applies_when: [time_pressure, clarity_critical]

# Compiler produces:
interpersonal_style:
  communication: Direct, opinionated, unvarnished
  # (no conditional captured)
```

**Root cause:** Extraction prompt does not explicitly ask for conditional behaviors. The LLM extracts the dominant behavior pattern, not the conditional variation.

**Human correction:** Human identifies contexts where behavior changes and creates ConditionalSlot entries. Time cost: ~10 minutes per persona.

**Fixability:**

| Approach | Effort | Effectiveness |
|---|---|---|
| "Identify behaviors that change based on context or conditions" | Low | Medium |
| Named trigger extraction: look for "when X, then Y" patterns | Medium | High |
| Second extraction pass specifically for conditionals | Medium | Very high |

**Recommendation for v1:** Conditional trigger extraction as a separate pipeline stage.

---

## Pattern 5: Provenance Under-linking (2/3 personas)

**What it looks like:** Extracted behaviors have source attribution but the `evidence` score is 0.00 because quotes were paraphrased, not preserved verbatim.

**Example:**
```yaml
# Compiler output:
core_principles:
  - description: >-
      Focus only on what is within your control — your thoughts,
      judgments, and actions. Everything else is indifferent.
  sources:
    - Meditations

# Manual pack has:
core_principles:
  - description: Focus only on what is within your control — your thoughts, judgments, and actions. Everything else is indifferent.
    sources:
      - Meditations
    quote: "You have power over your mind — not outside events. Realize this, and you will find strength."
```

**Root cause:** Single-pass extraction paraphrases quotes into behavioral descriptions. Quote preservation requires either cross-source validation or explicit quote extraction instruction.

**Human correction:** Human adds verbatim quotes where available. Time cost: ~5 minutes per persona (limited cases).

**Fixability:**

| Approach | Effort | Effectiveness |
|---|---|---|
| "Preserve verbatim quotes alongside behavioral descriptions" | Low | Medium |
| Cross-source validation: compare extractions across sources for quote matches | High | Very high |
| Two-phase: first extract quotes, second extract behaviors | High | Very high |

**Recommendation for v1:** Quote preservation instruction + cross-source flagging.

---

## Correction Frequency Summary

| Pattern | Personas Affected | Avg Corrections | v1 Fix Priority |
|---|---|---|---|
| Parsing artifacts | 3/3 | 1 per persona | P0 (pre-processing) |
| Schema distribution | 3/3 | 2–3 per persona | P0 (prompt) |
| Missing slot inference | 3/3 | 2–3 per persona | P1 (named concept pass) |
| Weak conditional capture | 3/3 | 1–2 per persona | P2 (conditional pass) |
| Provenance under-linking | 2/3 | 1 per persona | P2 (quote instruction) |

---

## v1 Roadmap Implication

Based on this taxonomy, v1 should address in order:

1. **P0 — Parsing artifacts:** Pre-process sources + LLM instruction
2. **P0 — Schema distribution:** Slot coverage prompt instruction
3. **P1 — Missing slot inference:** Named concept extraction pass
4. **P2 — Conditional capture:** Conditional trigger extraction stage
5. **P2 — Provenance:** Quote preservation instruction

Items 1–3 are sufficient to reduce corrections from 6 → ≤ 3 and push coverage from ~0.25 → ≥ 0.50. Items 4–5 are needed for v1达标 (reaching v1 targets).

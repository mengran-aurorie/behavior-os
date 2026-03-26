# Marcus Aurelius — Compiler End-to-End Example

**Third complete walkthrough of the BehaviorOS compiler pipeline.**

Marcus Aurelius completes the compiler corpus v0. He forms a behavioral triangle with Steve Jobs and Sun Tzu:

| Dimension | Steve Jobs | Sun Tzu | Marcus Aurelius |
|---|---|---|---|
| **Domain** | Technology/Product | Military/Strategic | Philosophical/Ethical |
| **Approach** | Direct, binary | Indirect, positional | Reflective, principled |
| **Speed** | Fast when blocked | Deliberate, patient | Deliberate, internal |
| **Conflict** | Confront to resolve | Avoid / shape terrain | Non-reactive, reason-first |
| **Core drive** | Product excellence | Strategic victory | Virtue and duty |
| **Drama level** | High | Medium | Low |
| **Source type** | Interview + biography | Ancient doctrine | Private journal + philosophy |

**Why Marcus Aurelius is a different test:** He is "low drama, high philosophy" — the compiler must extract named frameworks (Logos, Amor Fati) and internal practices (negative visualization, self-examination) from meditative text rather than observed behaviors or strategic doctrine.

---

## TL;DR

```bash
# Run the real Marcus Aurelius pack
mindset run claude --persona marcus-aurelius -- \
  "I'm facing a difficult decision with no good options."

# Or blend all three corpus personas
mindset run claude --persona sun-tzu --persona marcus-aurelius --weights 6,4 -- \
  "How should I approach this conflict?"
```

---

## Compiler Pipeline on Aurelius Sources

```
Sources (3 text files: Meditations, philosophy, leadership)
        │
        ▼
[Step 1: LLM Extraction]     → ExtractedBehavior[] (16 extractions)
[Step 2: LLM Normalization]  → CanonicalBehavior[] (8 canonical behaviors)
[Step 2b: Behavior Typing]   → All 8 typed as core_principle (over-fitting)
[Step 3: Schema Mapping]      → core_principles: 7 + 1 artifact (Variants)
[Step 4: Pack Builder]        → YAML draft-pack + quality gates
```

### Quality Gates

| Gate | Threshold | Marcus Aurelius Result |
|---|---|---|
| Coverage | ≥ 0.60 | 0.22 ⚠️ |
| Evidence | ≥ 0.50 | 0.00 ⚠️ |
| Contradictions | 0 | pass |

> **Coverage 0.22** — lowest of the three corpus personas. Philosophical text produces thinner behavioral extraction than interview/biography (Jobs) or strategic doctrine (Tzu).

---

## Human Review Corrections

Same 6 correction patterns as Jobs and Tzu, but with different content:

| # | Correction Type |
|---|---|
| 1 | Removed "Variants" parsing artifact |
| 2 | Distributed behaviors across decision_framework, thinking_patterns, mental_models |
| 3 | Added decision_framework |
| 4 | Added thinking_patterns (negative visualization, view from above) |
| 5 | Added mental_models (Logos, Amor Fati, The Obstacle is the Way) |
| 6 | Restored actual source titles |

**Key gap:** The compiler missed "Amor Fati" (active love of fate) despite it being central to Aurelius's philosophy. This is because it was expressed indirectly through multiple passages rather than stated as a named principle.

---

## File Inventory

| File | Purpose |
|---|---|
| [`sources/`](./sources/) | 3 raw source text files (public domain) |
| [`_build/explain.yaml`](./_build/explain.yaml) | Compiler decision trace |
| [`_build/coverage.yaml`](./_build/coverage.yaml) | Source utilization report |
| [`_build/draft-pack/`](./_build/draft-pack/) | **Compiler output (do not edit directly)** |
| [`marcus-aurelius/`](./marcus-aurelius/) | **Final reviewed pack** |
| [`_compile_meta.yaml`](./marcus-aurelius/_compile_meta.yaml) | Compiler provenance + human corrections |

---

## Compiler Corpus v0 Summary

| Persona | Domain | Coverage | Evidence | Corrections | Contradictions |
|---|---|---|---|---|---|
| Steve Jobs | Tech/Product | 0.24 ⚠️ | 0.00 ⚠️ | 6 | 0 |
| Sun Tzu | Military/Strategic | 0.28 ⚠️ | 0.00 ⚠️ | 6 | 0 |
| Marcus Aurelius | Philosophical/Ethical | 0.22 ⚠️ | 0.00 ⚠️ | 6 | 0 |

All three fail coverage and evidence gates. This establishes the baseline for v1 improvement targets.

See [`docs/compiler-benchmark-schema.md`](../../docs/compiler-benchmark-schema.md) for the formal benchmark schema and v1 targets.

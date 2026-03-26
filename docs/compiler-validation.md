# Compiler Validation — Steve Jobs Case Study

**Compiler version:** v0.3.0
**Date:** 2026-03-26
**Status:** Validation complete — compiler produces behaviorally correct first drafts; human review required for structural completeness

---

## Validation Summary

The compiler produces **behaviorally correct but structurally thin** first drafts. After human review, the pack is structurally complete at approximately 60% manual depth.

| Metric | Compiler Draft | After Human Review | Manual Pack |
|---|---|---|---|
| Behavioral signature | ✅ Correct | ✅ Correct | ✅ Correct |
| Slot coverage | ~25% | ~60% | ~95% |
| Schema structure | ❌ Monomorphic | ✅ Complete | ✅ Complete |
| Evidence quality | Paraphrased | Paraphrased | Quoted |
| ConditionalSlots | 0 | 0 | 3 |
| Anti-patterns | 0 | 0 | 5 |

---

## Happy Path

```bash
# 1. Compile sources → draft pack
mindset compile sources.yaml \
  --name "Steve Jobs" --id steve-jobs \
  --output ./build/jobs --explain

# 2. Review quality gates
# Check: ./build/jobs/_compile_meta.yaml
# Coverage should be ≥ 0.60, Evidence ≥ 0.50
# Review queue in ./build/jobs/draft-pack/review/

# 3. Correct draft in ./build/jobs/draft-pack/

# 4. Validate and run
mindset validate ./build/jobs/draft-pack
mindset run claude --persona ./build/jobs/draft-pack -- \
  "Your question here"
```

---

## What the Compiler Gets Right

Based on analysis of the Steve Jobs case study:

1. **Behavioral signature capture** — The compiled pack captures the correct behavioral essence (binary quality judgment, refusal to compromise, hiring-for-debate)
2. **Source utilization** — Compiler extracts from all provided sources; no hallucinated content
3. **Signature phrases** — High overlap in the subject's most quotable lines
4. **Decision framework structure** — Produces a coherent framework even when some field values differ from manual
5. **No contradictions** — Zero contradictions detected across both case studies

---

## Where Human Review Is Required

| Gap | Root Cause | Fixable With |
|---|---|---|
| Coverage ~25% | Single-pass extraction | Iterative compilation + more sources |
| No ConditionalSlots | Prompt doesn't guide for conditionals | Prompt engineering |
| No anti-patterns | Prompt doesn't ask for them | Prompt engineering |
| Evidence = paraphrase | No quote-preservation instruction | Cross-source validation + quote extraction |
| All behaviors → one slot type | Extraction prompt lacks slot distribution instruction | Schema coverage prompt |
| Missing named frameworks | Not prominent in extracted signals | Named-concept extraction instruction |

---

## Human Review Correction Patterns

Six corrections were applied in the Steve Jobs case study. They fall into three patterns:

### Pattern 1: Schema Distribution (Fidelity Correction)

**What it is:** Compiler maps all behaviors to one slot type (typically `core_principle`). Human distributes them.

**Why it happens:** Extraction prompt does not explicitly instruct the LLM to produce behaviors for all schema slots.

**Fix:** Add schema coverage instruction to extraction prompt.

### Pattern 2: Missing Slots (Coverage Gap)

**What it is:** Entire schema sections left empty (`decision_framework: {}`, `thinking_patterns: []`).

**Why it happens:** Sources don't explicitly discuss every topic. LLM doesn't generate content for slots without source evidence.

**Fix:** Topic-guiding constraints in extraction prompt: "If no evidence for X in sources, note 'no evidence found' rather than omitting."

### Pattern 3: Parsing Artifact (Fidelity Error)

**What it is:** Metadata or formatting artifacts parsed as behavioral content.

**Example:** "Variants" (cb-008) was a section header hallucinated as a behavior.

**Why it happens:** Pre-processing doesn't strip metadata headers before extraction.

**Fix:** Pre-process sources to remove metadata headers.

---

## Quality Gate Reference

| Gate | Threshold | Steve Jobs | Sun Tzu |
|---|---|---|---|
| `coverage` | ≥ 0.60 | 0.24 ⚠️ | 0.28 ⚠️ |
| `evidence` | ≥ 0.50 | 0.00 ⚠️ | 0.00 ⚠️ |
| `contradictions` | 0 | ✅ pass | ✅ pass |

> **Coverage** = weighted slot fill / total schema slots
> **Evidence** = sources with direct quotes / total sources
>
> Both current examples fail coverage and evidence gates. This is expected for single-pass compilation from 3 sources. Iterative compilation and more sources would close the gap.

---

## Validation Assets

| Asset | Location |
|---|---|
| Steve Jobs end-to-end example | [`examples/steve-jobs/`](examples/steve-jobs/) |
| Steve Jobs compiled vs manual | [`docs/validation/steve-jobs-compiled-vs-manual.md`](validation/steve-jobs-compiled-vs-manual.md) |
| Sun Tzu end-to-end example | [`examples/sun-tzu/`](examples/sun-tzu/) |
| Compiler test suite | `tests/test_compiler_compile.py` |
| Mock LLM pipeline tests | `tests/test_compiler_compile.py::TestCompilePackPipeline` |

---

## Next Validation Steps

1. **Third character** — Marcus Aurelius (philosophical text, different axis)
2. **Iterative compilation** — Second-pass compile on same sources to close coverage gap
3. **ConditionalSlot extraction** — Prompt engineering to surface conditionals
4. **Anti-pattern extraction** — Prompt engineering to surface anti-patterns
5. **Quote-preservation** — Cross-source validation to improve evidence score

---

## Benchmark Baselines

| Character | Coverage | Evidence | Corrections | Contradictions |
|---|---|---|---|---|
| Steve Jobs | 0.24 ⚠️ | 0.00 ⚠️ | 6 | 0 |
| Sun Tzu | 0.28 ⚠️ | 0.00 ⚠️ | 6 | 0 |

**Compiler goal (v1):** Coverage ≥ 0.65, Evidence ≥ 0.30, corrections ≤ 4 per 3-source compile

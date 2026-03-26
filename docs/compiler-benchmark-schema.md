# Compiler Benchmark Schema

**Status:** v0.1 — Established from 3 persona corpus
**Last Updated:** 2026-03-26

---

## Benchmark Corpus v0

| Persona | Domain | Type | Source Count | Draft Coverage | Draft Evidence |
|---|---|---|---|---|---|
| `steve-jobs` | Technology/Product | Historical | 3 | 0.24 | 0.00 |
| `sun-tzu` | Military/Strategic | Historical | 3 | 0.28 | 0.00 |
| `marcus-aurelius` | Philosophical/Ethical | Historical | 3 | 0.22 | 0.00 |

---

## Evaluation Schema

Each benchmark persona MUST produce:

```yaml
persona: <id>                    # e.g., steve-jobs
type: historical                 # always "historical" for v0 corpus

# --- Thresholds ---
coverage_min: 0.65               # weighted slot fill / total schema slots
evidence_min: 0.30               # sources with direct quotes / total sources
max_corrections: 4               # human review corrections per 3-source compile
max_contradictions: 0            # contradictions must be zero

# --- Behavioral requirements ---
must_capture:
  - core_principles              # at least 3 confirmed principles
  - decision_framework           # risk_tolerance, time_horizon, heuristics
  - mental_models                # at least 1 named framework
  - thinking_patterns            # at least 1 cognitive pattern
  - conflict_style               # default + at least 1 conditional

must_not_hallucinate:
  - fabricated anecdotes          # no invented specific events
  - out-of-character traits      # behaviors not present in sources
  - anachronisms                 # modern concepts not in historical sources

must_have_behavioral_signature:
  description: >-
    The compiled pack's behavioral output on the standard benchmark query
    must match the manual pack's behavioral signature within one standard
    deviation on the behavioral axis classification.
  query: "We are negotiating with a much larger competitor. What do we do?"
```

---

## Quality Gate Thresholds

| Gate | v0 Baseline | v1 Target | v2 Target |
|---|---|---|---|
| `coverage` | 0.22–0.28 ⚠️ | ≥ 0.65 | ≥ 0.75 |
| `evidence` | 0.00 ⚠️ | ≥ 0.30 | ≥ 0.50 |
| `contradictions` | 0 | 0 | 0 |
| `max_corrections` | 6 | ≤ 4 | ≤ 2 |
| `conditional_capture_rate` | 0/3 | ≥ 1/3 | ≥ 2/3 |
| `named_framework_capture` | 1/3 | ≥ 2/3 | 3/3 |

---

## Measurement Methodology

### Coverage Score

```
coverage = weighted_slot_fill / total_schema_slots

weighted_slot_fill = Σ(slot_weight × slot_filled) for all slots
slot_filled = 1 if slot has content, 0 if empty
```

Reference slot weights (from `compiler/schemas.py`):
- `core_principles`: 0.20
- `decision_framework`: 0.15
- `thinking_patterns`: 0.10
- `mental_models`: 0.10
- `traits`: 0.10
- `emotional_tendencies`: 0.08
- `interpersonal_style`: 0.08
- `drives`: 0.07
- `work_patterns`: 0.05
- `execution_style`: 0.04
- `conflict_style`: 0.03

### Evidence Score

```
evidence = sources_with_direct_quotes / total_sources

A source "has direct quotes" if ≥1 extracted behavior includes
the verbatim quote (not paraphrase) attributed to that source.
```

### Correction Count

Counted from `_compile_meta.yaml > review_items > corrections_made`.
Includes: parsing artifacts removed, slot re-distributions, missing slots filled.

### Behavioral Signature Match

1. Run compiled pack through runtime with benchmark query
2. Classify output on behavioral axis (e.g., direct vs indirect, confrontational vs avoidant)
3. Compare to manual pack's output on same query
4. Match = within one step on the axis classification

---

## v1 Entry Conditions

Compiler v1 is released when:

- [ ] `steve-jobs`, `sun-tzu`, `marcus-aurelius` all pass `coverage_min: 0.65`
- [ ] `steve-jobs`, `sun-tzu`, `marcus-aurelius` all pass `evidence_min: 0.30`
- [ ] `max_corrections ≤ 4` for all three corpus personas
- [ ] `contradictions = 0` for all three corpus personas
- [ ] At least 1 of 3 personas captures ≥ 1 ConditionalSlot in draft pack

---

## Planned Corpus Additions

| Persona | Rationale | Priority |
|---|---|---|
| `sherlock-holmes` | Deductive reasoning, observational methodology | P1 |
| `seneca` | Stoic philosophy (similar to Aurelius, different framing) | P1 |
| `the-operator` | Execution-first, high drama, decision speed focus | P2 |

Corpus reaches "stable" at 7 personas covering major behavioral axes.

---

## Assets

| Asset | Location |
|---|---|
| Steve Jobs benchmark | [`examples/steve-jobs/`](examples/steve-jobs/) |
| Sun Tzu benchmark | [`examples/sun-tzu/`](examples/sun-tzu/) |
| Marcus Aurelius benchmark | [`examples/marcus-aurelius/`](examples/marcus-aurelius/) |
| Correction taxonomy | [`docs/compiler-correction-taxonomy.md`](compiler-correction-taxonomy.md) |
| Validation report | [`docs/compiler-validation.md`](compiler-validation.md) |

# Benchmark Specification

Derived from `docs/demo.md`. This document captures **what** the benchmark suite must verify — not the full automation implementation.

---

## A. Behavioral Invariants (per golden pack)

Every golden pack must satisfy these invariants when loaded and resolved. Verification: read `--explain` YAML output.

### A.1 — ConditionalSlot trigger test

For each ConditionalSlot defined in a golden pack, there exists at least one benchmark task that activates it.

**Verification:** Run `--explain` on the relevant task and check that `modifiers` is non-empty for the triggered slot.

Example for Steve Jobs:
```
modifiers:
  - condition: [time_pressure, clarity_critical]
    conjunction: any
    source: steve-jobs
    value: "Blunt and demanding..."
```
If `modifiers` is empty when running Task C (time pressure), the ConditionalSlot is not triggering correctly.

### A.2 — Extreme slot value test

Each golden pack must have at least one runtime-critical slot at an extreme value:

| Pack | Expected extreme value | Slot |
|---|---|---|
| `sun-tzu` | `risk_tolerance: medium` (positional, not reckless) | `mindset.decision_framework` |
| `marcus-aurelius` | `risk_tolerance: low` (stoic acceptance of fate) | `mindset.decision_framework` |
| `steve-jobs` | `risk_tolerance: high` + `decision_speed: fast` | `mindset.decision_framework` + `behavior` |
| `sherlock-holmes` | `decision_speed: fast` (analytical rapid deduction) | `behavior` |
| `the-operator` | `decision_speed: fast` + `risk_tolerance: medium` | `behavior` + `mindset` |

**Verification:** Load each pack, inspect the raw schema values (not `--explain` output).

### A.3 — No unresolved conflict test

For single-persona runs, every slot must have `has_conflict: false`.

**Verification:** `mindset run --persona <id> --explain` — assert `has_conflict == false` for all 6 slots.

---

## B. Task-based Differentiation Tests

### Task A — High Uncertainty

**Prompt:** "We have incomplete data and significant risk. What should we do?"

| Persona | Pass condition |
|---|---|
| Sun Tzu | Response contains no commitment to immediate action. Contains at least one of: "gather", "observe", "wait", "map unknowns", "hold position", "terrain", "intelligence". Does NOT contain "just do it", "commit now", "act first". |
| Marcus Aurelius | Response distinguishes controllable from non-controllable. Contains at least one of: "within your control", "virtue", "fate", "accept", "distinguish". Does NOT use aggressive confrontation language. |
| Steve Jobs | Response commits to a direction. Contains at least one of: "commit", "act", "direction", "iteration", "waiting is the risk". Does NOT counsel patience or information-gathering as primary posture. |
| Baseline | Response offers balanced "gather info + take action" advice. No strong lean in either direction. |

**Anti-collapse condition:** Response does not read as a generic LLM hedging ("on one hand... on the other hand...").

---

### Task B — Conflict / Negotiation

**Prompt:** "A colleague is blocking your project for selfish reasons. They have management's ear. How do you handle it?"

| Persona | Pass condition |
|---|---|
| Sun Tzu | Does NOT recommend direct confrontation or escalating to management as primary move. Contains "position", "terrain", "make blocking costly", "get objections on record", "allies", "coalition". |
| Marcus Aurelius | Does NOT recommend aggressive confrontation. Contains "substance", "virtue", "conduct", "accept outcome", "justice", "reason not emotion". |
| Steve Jobs | Contains "go around", "doers", "work speaks", "reschedule", "leave if blocked", or explicit statement that relationship with blocker is irrelevant. |

**Anti-collapse condition:** Sun Tzu + Marcus blend does NOT produce generic conflict advice. Must contain both: Sun Tzu's terrain/positioning language AND Marcus's virtue/conduct filter.

---

### Task C — Time Pressure

**Prompt:** "You have 24 hours before presenting to the board. The materials are not ready. What do you do?"

| Persona | Pass condition |
|---|---|
| Sun Tzu | Response is about positioning and preparation before the room. Contains "terrain", "battle is the preparation", "position", "clarity of purpose". Does NOT say "work all night" or "panic". |
| Marcus Aurelius | Contains "accept", "constraint", "what is in your control", "stoic", "rest", or reframes the situation positively. Does NOT escalate team pressure. |
| Steve Jobs | Contains "cancel the deck", "three slides", "one decision", or "reschedule". Binary judgment on quality: something is "shit" or "not ready". |

**Anti-collapse condition:** Sun Tzu + Steve Jobs blend must produce at least one Jobs-original phrase (e.g., the "one slide" illustration) that does NOT appear in the Jobs solo Task C response.

---

## C. Fusion Anti-Collapse Tests

### C.1 — No literal averaging

For any 60/40 blend, the response must not be reconstructable as "50% Persona A + 50% Persona B" word-level mixing.

**Verification method:** Manual annotation (see demo.md). Automated approximation: compute n-gram overlap between blend response and each solo response. Overlap with dominant persona should be ≥ 0.4. Overlap with dropped persona should be < 0.15.

### C.2 — Dropped slots are behaviorally silent

When `--explain` shows a slot in `dropped` with `reason: no_conflict`, the corresponding behavioral quality must not appear in the response text.

**Example:** Sun Tzu + Steve Jobs Task B — `conflict_style` is dropped (Jobs's confrontational style). The response must NOT contain Jobs-style direct confrontation language ("go around them", "the blocker has power only if you accept the premise").

**Verification:** For each dropped slot, define 3–5 characteristic phrases from the solo persona's behavior. Check that ≤ 1 of these phrases appears in the blend response.

### C.3 — Emergent language must appear

At least one of the five blend configurations must contain phrasing that is not present in either constituent solo response.

**Known examples from demo:**
- Sun Tzu + Marcus Task A: "Position first. Move second. Never confuse motion with progress."
- Sun Tzu + Marcus Task B: "The asymmetry of their private obstruction versus your public clarity shifts the terrain."
- Sun Tzu + Steve Jobs Task C: "Steve Jobs did not take notes to the iPhone launch. He took one slide."

**Verification:** Automated check: for each blend run, compute token-level Jaccard similarity against both solo responses. If similarity to both is above threshold (e.g., ≥ 0.6), flag as potential collapse.

---

## D. Slot → Behavior Traceability

For each slot in the `--explain` YAML, the mapping to observable text properties must be documented and verifiable.

| Slot | Schema field | Observable behavior |
|---|---|---|
| `communication` | `personality.interpersonal_style.communication` | Direct vs. indirect phrasing; use of hedging; confrontational vs. diplomatic tone |
| `conflict_style` | `behavior.conflict_style` | Approach to disagreement: avoidance, confrontation, strategic maneuvering, reason-based |
| `leadership` | `personality.interpersonal_style.leadership` | How the persona positions themselves vs. authority and team |
| `stress_response` | `personality.emotional_tendencies.stress_response` | First behavioral change under pressure: escalate, withdraw, analyze, accept |
| `tone` | `voice.tone` | Register: measured/aphoristic vs. direct/intense vs. reflective/meditative |
| `sentence_style` | `voice.sentence_style` | Sentence length, structure, use of metaphor vs. declarative |

---

## E. Test execution protocol

### Baseline capture (required before any assertion)

For each task and persona combination, capture both:
1. `--explain` YAML output (to a `.yaml` file)
2. Model text response (to a `.txt` file)

These become the reference artifacts for all assertions.

### Running the full benchmark

```bash
# Capture all artifacts
./scripts/benchmark-capture.sh /tmp/benchmark-runs

# Run assertions
./scripts/benchmark-assert.sh /tmp/benchmark-runs
```

### Pass criteria

- All Behavioral Invariants (A.1–A.3) pass for all 5 golden packs
- All Task Differentiation Tests (B.1–B.3) pass for all 5 personas × 3 tasks
- All Fusion Anti-Collapse Tests (C.1–C.3) pass for all 4 blend configurations × 3 tasks
- All Slot → Behavior Traceability entries (D) verified for all 6 slots

**Total assertions:** ~50–80 checks.

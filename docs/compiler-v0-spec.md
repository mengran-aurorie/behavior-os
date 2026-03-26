# Source → Pack Compiler v0 Spec

**Phase 2 of BehaviorOS**

---

## Goal

Compile unstructured sources (book excerpts, interviews, speeches, letters) into structured behavior packs (mindset.yaml, personality.yaml, behavior.yaml, voice.yaml) with human review.

The compiler does not replace the author — it generates a **high-quality first draft** that a human can review, correct, and extend.

---

## Pipeline Architecture

```
Sources (txt/md/url list)
        │
        ▼
[Step 1: LLM Extraction]
        │
        ▼
Extracted Behaviors (raw candidates)
        │
        ▼
[Step 2: Semantic Normalization]
        │
        ▼
Canonical Behaviors (confirmed / ambiguous / contradictory)
        │
        ▼
[Step 2b: Behavior Typing]          ← Buffer layer: behavior_type before schema
        │
        ▼
[Step 3: Schema Mapping]
        │
        ▼
Slots (core_principles, decision_framework, communication, etc.)
        │
        ▼
[Step 4: Conditional Detection v0.5]
        │
        ▼
Draft Pack (with provenance trace)
        │
        ▼
[Step 5: Human Review]
        │
        ▼
Validated Pack
```

---

## Step 1: Extraction

### Goal

Convert raw source text into structured **behavior candidates** with evidence.

### Schema

```yaml
extracted_behaviors:
  - id: b-001
    quote: "I'm as proud of what we didn't do as what I did."
    source_ref: steve-jobs-interview-1993
    page_or_section: product-strategy
    behavior: "prioritizes restraint and deliberate non-action as much as action"
    trigger: null  # no explicit context in this quote
    contrast_signal: false
    confidence: high
    raw_text: "I'm as proud of what we didn't do as what I did."

  - id: b-002
    quote: "Deciding what not to do is as important as deciding what to do."
    source_ref: steve-jobs-walter-isaacson
    page_or_section: chapter-15
    behavior: "rejects hedging; treats ambiguity as a defect"
    trigger: null
    contrast_signal: false
    confidence: high
    raw_text: "Deciding what not to do is as important as deciding what to do."

  - id: b-003
    quote: "He was very patient, but ruthless when he had to be."
    source_ref: steve-jobs-colleague-account
    page_or_section: team-dynamics
    behavior: "ruthless when context demands it"
    trigger: "when context demands it"
    contrast_signal: true  # "patient but ruthless" → ruthlessness is contextual
    confidence: medium
    raw_text: "He was very patient, but ruthless when he had to be."
```

### Extraction Prompt Principles

- **Not adjectives** — extract behaviors, not personality traits ("direct" is not a behavior; "insists on full team commitment before proceeding" is)
- **Trigger-aware** — when a quote implies a context, capture it as `trigger`
- **Contrast-aware** — detect contrast structures (see Step 4)
- **Evidence-level** — distinguish first-hand accounts from second-hand descriptions

### Confidence Levels

| Level | Criteria |
|---|---|
| `high` | Quote explicitly states behavior; first-hand account |
| `medium` | Quote describes behavior indirectly; second-hand account |
| `low` | Inferred from narrative description; single mention |

---

## Step 2: Semantic Normalization (LLM-based)

### Goal

Cluster extracted behaviors, resolve duplicates/inversions/contradictions, and produce canonical forms.

### Schema

```yaml
canonical_behaviors:
  - id: cb-001
    canonical_form: "clarity-first; rejects ambiguity"
    slot_target: communication  # provisional
    variants:
      - extracted_id: b-002
        text: "Deciding what not to do is as important as deciding what to do."
      - extracted_id: b-004
        text: "hates hedging"
    status: confirmed
    evidence_count: 4
    contradiction_refs: []  # empty if confirmed

  - id: cb-002
    canonical_form: "ruthless when context demands decisive action"
    slot_target: conflict_style  # provisional
    variants:
      - extracted_id: b-003
        text: "patient, but ruthless when he had to be"
      - extracted_id: b-007
        text: "turns aggressive when blocked"
    status: ambiguous  # needs human to confirm interpretation
    evidence_count: 2
    contradiction_refs: []

  - id: cb-003
    canonical_form: "long-term vision over short-term comfort"
    slot_target: decision_framework  # provisional
    variants:
      - extracted_id: b-010
        text: "willing to sacrifice short-term revenue for long-term vision"
    status: confirmed
    evidence_count: 1
    contradiction_refs: []
```

### Normalization Rules

| Relationship | Example | Resolution |
|---|---|---|
| Duplicate | "hates hedging" + "rejects ambiguity" | Merge into canonical "clarity-first" |
| Inversion | "very patient in review" + "ruthless when blocked" | Mark as separate behaviors |
| Implication | "fires people quickly" + "values team excellence" | Keep separate; may merge at mapping stage |
| Contradiction | "never compromises on design" + "makes exceptions for key partners" | Flag as contradictory cluster; human review |

### Prompt Guidance for Normalization

```
You are normalizing extracted behaviors from persona sources.
For each cluster of behaviors:
1. Identify the canonical form (the most precise, general description)
2. List all variants that map to this canonical form
3. Mark status: confirmed (variants agree) | ambiguous (interpretation unclear) | contradictory (variants conflict)
4. Flag contradictions for human review
```

---

## Step 2b: Behavior Typing Layer

### Why a Buffer Layer

Schema slots are **rigid**; canonical behaviors are **fluid**. Directly mapping unstable canonical forms to rigid slots risks cascading errors.

Behavior Typing introduces a **semantic buffer layer** between canonical form and schema slot:

```
Canonical Behavior
        │
        ▼
behavior_type (semantic category)
        │
        ▼
Schema Mapping (now has stable input)
```

### Behavior Types

| behavior_type | Description | Examples |
|---|---|---|
| `core_principle` | Foundational belief that drives all behavior | "clarity is supreme", "force is inevitable" |
| `decision_policy` | How the person approaches decisions | "70% information commit", "wait for certainty" |
| `communication` | How the person communicates | "direct to the point of bluntness", "uses metaphor" |
| `conflict` | How the person handles conflict | "destroys rivals completely", "avoids confrontation" |
| `emotional` | Emotional patterns and triggers | "baseline calm", "erupts when blocked" |
| `drive` | What the person is motivated by | "legacy over profit", "winning as identity" |
| `execution` | How the person gets things done | "personally leads", "delegates everything" |

### Schema

```yaml
canonical_behaviors:
  - id: cb-001
    canonical_form: "clarity-first; rejects ambiguity"
    behavior_type: communication  # typed before schema mapping
    slot_target: interpersonal_style.communication
    variants: [...]
    status: confirmed
```

### Typing Prompt Guidance

```
For each canonical behavior:
1. Classify into one of: core_principle, decision_policy, communication, conflict, emotional, drive, execution
2. The behavior_type is stable — it does NOT change based on schema fit
3. If a behavior could fit multiple types, pick the most central one
4. Mark confidence: high (clear type) | medium (ambiguous)
```

---

## Step 3: Schema Mapping

### Goal

Map canonical behaviors to BehaviorOS schema slots.

### Slot Category Mapping

```
core_principles:
  → CorePrinciple (description + detail + confidence)

decision_framework:
  → DecisionFramework (risk_tolerance, time_horizon, heuristics, default_strategy, commitment_policy)

communication (interpersonal_style.communication):
  → ConditionalSlot (default + conditional variants)

conflict_style:
  → ConflictStyle (default + conditional)

drives:
  → Drive (name + intensity + description)

emotional_tendencies:
  → EmotionalTendencies (baseline_mood, stress_response, frustration_trigger, recovery_pattern)
```

### Mapping Prompt Guidance

```
For each canonical behavior:
1. Identify the best-fitting slot category
2. Determine the specific field within that category
3. Write the field value in the correct format for the schema
4. Mark confidence: high (direct mapping) | medium (interpretation needed) | low (uncertain)
5. Mark for review if confidence is medium or low
```

---

## Step 4: Conditional Detection v0.5

### Goal

Detect context-triggered behaviors and generate ConditionalSlot structures.

### Contrastive Conditional Inference Rule

> When a source expresses a behavior via contrast, the contrasted behavior should be treated as contextually conditional unless the source clearly states it as the dominant default.

**Contrast markers:**
- `but` — second behavior is conditional on context that makes contrast relevant
- `yet` — same as `but`
- `although X, Y` — Y is the true/default behavior; X is surface/deceptive
- `except when` — Y with explicit exception condition
- `on one hand X, on the other Y` — context determines which applies

### Examples

| Source | Output |
|---|---|
| "He was very patient, **but** ruthless when necessary." | `conditional: [{ value: ruthless, applies_when: [necessary] }]` |
| "He is direct, **although** he can be diplomatic when required." | `conditional: [{ value: diplomatic, applies_when: [required] }]` |
| "Innovative **except when** it threatens core quality." | `conditional: [{ value: innovative, applies_when: [NOT threat_to_quality] }]` |

### v0.5 Scope

- **Only generate conditionals from detected contrast structures**
- **Do not infer conditions from single non-contrast quotes**
- **Flag remaining potential conditionals for human review**
- Deferred: full condition inference from context patterns

### Implicit Condition Signals (v0.5 Enhancement)

Some behaviors have **extreme tendency markers** that suggest conditionality without explicit conditions:

| Marker | Example | Flag |
|---|---|---|
| `always` / `never` | "He **always** pushes for clarity" | `conditional_candidate: true` |
| `refuses to` / `insists on` | "He **refuses to** compromise on design" | `conditional_candidate: true` |
| `without exception` | "He acts **without exception**" | `conditional_candidate: true` |

**Rule:** When a behavior contains these markers but has **no explicit condition**, flag as `conditional_candidate: true` for human review. Do NOT auto-generate the condition — flag for human inference.

```yaml
# In canonical behavior schema:
canonical_form: "clarity-first; refuses to accept ambiguity"
conditional_candidate: true   # flagged: "refuses to" implies context-dependent boundary
conditional_note: "What makes him relax this standard? Personal relationships? High stakes?"
```

This ensures the signal is not lost even when the condition is implicit.

---

## Step 5: Provenance Model

### Goal

Every mapped slot can be traced back to source quotes.

### Trace Format

```
quote_id → behavior_id → canonical_id → slot_id
```

### Pack Provenance Schema

```yaml
mindset:
  core_principles:
    - id: cp-001
      description: Clarity as supreme value
      detail: Rejects ambiguity; treats hedging as a character defect
      confidence: 0.95
      provenance:
        - canonical_id: cb-001
          quote: "Deciding what not to do is as important as deciding what to do."
          source_ref: steve-jobs-walter-isaacson
          section: chapter-15
        - canonical_id: cb-001
          quote: "讨厌摇摆不定的人"
          source_ref: steve-jobs-interview-1993
          section: product-strategy

decision_framework:
  heuristics:
    - "When clarity is achievable, commit immediately; do not wait for full consensus"
      provenance:
        - canonical_id: cb-001
          quote: "..."
          source_ref: ...
```

### Provenance Uses

1. **Trust** — user sees why each behavior is in the pack
2. **Contestability** — user can challenge a mapping by pointing to a specific quote
3. **Coverage analysis** — which source sections were not used?

### Source Coverage Reporting

Every compile run outputs which portions of each source were used:

```yaml
source_coverage:
  total_quotes_extracted: 45
  quotes_used_in_slots: 31
  quotes_unused: 14
  unused_sections:
    - source_ref: steve-jobs-walter-isaacson
      sections: ["early life", "personal relationships", "family"]
    - source_ref: steve-jobs-interview-1993
      sections: ["career before Apple"]
```

This upgrades provenance from a **trace system** (slot → quote) to a **coverage system** (can answer: what did we miss?).

---

## Coverage Score v0

### Definition

```
Coverage = Σ(slot_weight × slot_filled_and_evidenced) / Σ(slot_weight)
```

### Slot Weights (Static)

| Slot | Weight | Notes |
|---|---|---|
| `core_principles` | 2.0 | Core identity; missing this = hollow pack |
| `decision_framework` | 1.5 | Behavioral engine; hard to fake |
| `interpersonal_style.communication` | 1.0 | Observable behavior |
| `conflict_style` | 1.0 | Observable behavior |
| `emotional_tendencies` | 0.5 | Internal; harder to source |
| `voice.vocabulary` | 0.5 | Surface-level |
| `drives` | 0.5 | Internal motivation |

### Filled vs. Evidenced

```
filled = 1 if slot is populated
evidenced = 1 if slot has ≥ 2 provenance entries
```

### Evidence Score

```
Evidence = Σ(slot_weight × evidenced) / Σ(slot_weight)
```

### Example Output

```
Pack: steve-jobs
Coverage: 0.78 / 1.00
Evidence: 0.71 / 1.00

Filled slots: core_principles, decision_framework, communication, conflict_style
Missing: emotional_tendencies.baseline_mood, drives
Weak evidence: voice.tone (only 1 source)
```

---

## Review UX

### CLI: `mindset compile sources.yaml --output my-pack/`

### Output: `--explain`

```
mindset compile ./steve-jobs-sources.yaml --output steve-jobs/ --explain

Extraction:
  Extracted behaviors: 23
  From sources: 4 (book, 2 interviews, biography)

Normalization:
  Canonical behaviors: 15
  Status breakdown:
    - confirmed: 11
    - ambiguous: 3  ← needs your judgment
    - contradictory: 1  ← review required

Mapping:
  Slots filled: 14 of 18
  High confidence: 10
  Medium confidence: 3  ← review recommended
  Low confidence: 1  ← review required

Provenance:
  Total evidence links: 31
  Best-sourced slot: core_principles (6 links)
  Weakest slot: voice.tone (1 link)

Coverage: 0.78 / 1.00
Evidence: 0.71 / 1.00

Review required:
  [3 ambiguous items]   → steve-jobs/review/ambiguous.yaml
  [1 contradictory]      → steve-jobs/review/contradictions.yaml
  [4 medium confidence] → steve-jobs/review/medium.yaml

Draft written to: steve-jobs/
Run `mindset review steve-jobs/` to inspect.
```

### Human Review Priority

1. **Contradictions** (must resolve before proceeding)
2. **Ambiguous** (should resolve for pack quality)
3. **Low/Medium confidence** (should review for fidelity)
4. **Weak coverage slots** (should add sources or mark as intentional)

### Review Flow

```
mindset review my-pack/
  Opens: my-pack/review/
    ├── contradictions.yaml   ← resolve these first
    ├── ambiguous.yaml         ← then these
    ├── medium-confidence.yaml ← then these
    └── full-draft.yaml        ← final review
```

---

## Enhancement A: Stable Behavior IDs (→ v1)

Canonical behavior IDs are currently local (`cb-001`). Upgrade to content-addressable IDs:

```python
behavior_id = hashlib.sha256(canonical_form.lower().strip().encode()).hexdigest()[:8]
# "clarity-first; rejects ambiguity" → beh_9f3a2c1b
```

**Benefits:**
- **Cross-persona alignment**: same behavior in different personas gets same ID
- **Behavior graph**: can query "which personas have behavior beh_9f3a2c1b?"
- **Pack diff**: diff is now behavior-ID-based, not string-based
- **Provenance reuse**: a proven behavior can be referenced across packs

---

## Enhancement B: Pack Diff

Compare two packs at the behavior level:

```bash
mindset diff jobs-pack/ musk-pack/
```

```
decision_policy:
  jobs: clarity-first → commits at 70%
  musk: speed-first → commits at 60%
  overlap: none (different axes)

communication:
  jobs: direct (evidenced: 4 quotes)
  musk: direct but volatile (evidenced: 2 quotes)
  overlap: beh_9f3a2c1b "anti-hedging" (both)

conflict:
  jobs: destroys opposition fully
  musk: destroys opposition fully
  overlap: beh_a1b2c3d "ruthless when blocked" (canonical match)
```

**Output structure:**
```yaml
overlap:
  - behavior_id: beh_9f3a2c1b
    canonical: "anti-hedging"
    in: [jobs, musk]
different:
  - axis: decision.commitment_threshold
      jobs: "70%"
      musk: "60%"
uniquely_in:
  jobs: [beh_d4e5f6, beh_e5f6g7]
  musk: [beh_h6i7j8]
```

---

## Enhancement C: Compile Quality Gate

Every compile run outputs a deterministic `compile_status`:

```yaml
compile_status:
  status: pass | warning | fail
  scores:
    coverage: 0.78
    evidence: 0.71
  gates:
    contradictions:
      count: 0
      threshold: 0
      status: pass
    coverage:
      score: 0.78
      threshold: 0.60
      status: pass
    evidence:
      score: 0.71
      threshold: 0.50
      status: pass
    conditional_candidates:
      count: 3
      status: warning  # flagged for review, not blocking
  review_required: 3 items
```

**Gate Rules:**

| Gate | Threshold | Fails if |
|---|---|---|
| `contradictions` | 0 | any contradiction unresolved |
| `coverage` | 0.60 | score below threshold |
| `evidence` | 0.50 | score below threshold |
| `conditional_candidates` | — | never fails; only warns |

A pack with `fail` status cannot be merged into the standard library without human sign-off.

---

## Deferred: Conditional Detection v1

Full condition inference from contextual patterns, not just contrast markers.

Not in v0 scope because:
- Requires larger context window processing
- Risk of hallucinating conditions from sparse signals
- Contrast-based v0.5 covers ~80% of real conditional signals

---

## v0 Scope Summary

| Component | In v0? | Notes |
|---|---|---|
| Extraction (三元组) | ✅ | behavior + trigger + quote + confidence |
| Semantic Normalization | ✅ | LLM-based; no hard-coded dedup |
| Behavior Typing Layer | ✅ | behavior_type buffer before schema mapping |
| Schema Mapping | ✅ | Canonical → slots |
| Conditional v0.5 | ✅ | Contrast markers + implicit condition flag |
| Provenance Trace | ✅ | quote_id → behavior_id → slot_id |
| Source Coverage Report | ✅ | used/unused quotes per source |
| Coverage Score | ✅ | Weighted slot coverage |
| Evidence Score | ✅ | Provenance count per slot |
| Review UX | ✅ | Priority-ordered review queue |
| Quality Gate | ❌ Enhancement B | compile_status: pass/warning/fail |
| Stable Behavior IDs | ❌ Enhancement A | hash-based cross-persona IDs |
| Pack Diff | ❌ Enhancement C | behavior-level pack comparison |
| Conditional v1 | ❌ Deferred | Full context inference |
| Auto-benchmark | ❌ Deferred | v2+ |
| Dynamic slot weights | ❌ Deferred | v2+ |

---

## Success Criteria for v0

- `mindset compile` can produce a draft pack from 3+ sources in under 2 minutes
- Human review reduces to < 15 minutes per pack
- Generated pack is 80%+ similar to a manually authored equivalent pack (measured by slot overlap)
- Every filled slot has at least one provenance link
- No contradictions in final pack

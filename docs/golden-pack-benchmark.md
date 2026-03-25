# Golden Pack Benchmark Matrix

This document defines the five golden packs, the four benchmark tasks, and the expected resolver behavior for single and paired runs.

---

## The Five Golden Packs

| Pack | Primary axis | `communication` default | `conflict_style` default | Conditional trigger |
|---|---|---|---|---|
| `sun-tzu` | indirect strategy | indirect, layered | avoidant, positional | `advantage_secured` → direct |
| `marcus-aurelius` | stoic stability | direct but gentle | non-reactive | `moral_clarity` / `irreversible_risk` → firm |
| `steve-jobs` | direct judgment / clarity pressure | direct, opinionated | confrontational | `time_pressure` / `clarity_critical` → blunt |
| `sherlock-holmes` | observation / inference | observational, withholds conclusions | confronts when evidence is assembled | `inference_confidence_high` → blunt declarative |
| `the-operator` | execution / decisiveness | direct and minimal | decisive, action-first | `execution_phase` / `time_pressure` → directives |

### Design rule

Every golden pack satisfies all three:
1. Extreme value on at least one runtime-critical slot (e.g., `risk_tolerance: high`, `decision_speed: fast`)
2. At least one `ConditionalSlot` override on `communication` or `conflict_style`
3. Clear conflict pair with at least one other pack in the set

---

## Resolver conflict map

| Slot | Sun Tzu | Marcus | Jobs | Holmes | Operator |
|---|---|---|---|---|---|
| `communication` | indirect | direct/gentle | direct/blunt | observational | minimal/direct |
| `conflict_style` | avoidant | non-reactive | confrontational | direct (when evidence ready) | decisive/action |
| `decision_speed` | deliberate | deliberate | fast | fast | fast |
| `risk_tolerance` | medium | low | high | medium | medium |
| `time_horizon` | long-term | long-term | long-term | short-term | short-term |

**Primary conflict pairs** (maximum slot divergence):

| Pair | Key conflict slot | Expected resolution (blend, 50/50) |
|---|---|---|
| Sun Tzu + Jobs | `communication` | Sun Tzu wins (higher weight by default) or Jobs if weight ≥ Sun Tzu |
| Marcus + Jobs | `conflict_style` | Confrontational wins if Jobs weight ≥ Marcus |
| Holmes + Operator | `decision_speed` | Both fast — no conflict; `communication` drops Holmes's observational in favor of Operator's minimal |
| Sun Tzu + Operator | `time_horizon` | long-term vs short-term → resolver must pick one, not blend |

---

## Four benchmark tasks

Run each task as:
```bash
mindset run claude --persona <id> --registry . --explain -- "<task prompt>"
```

For pair runs:
```bash
mindset run claude --persona <id1> --persona <id2> --weights 6,4 --registry . --explain -- "<task prompt>"
```

---

### Task A — High uncertainty

**Prompt:** "We have incomplete data and significant risk. What should we do?"

**What it tests:** `risk_tolerance`, `time_horizon`, uncertainty handling, `decision_framework.approach`

| Pack | Expected behavior signal |
|---|---|
| Sun Tzu | Gather more intelligence; hold position; do not act yet |
| Marcus | Accept uncertainty as given; focus on what is within control; act from duty |
| Jobs | Commit to the direction now; iteration will correct it; waiting is the risk |
| Holmes | Identify what data is missing; design a specific observation to fill the gap |
| Operator | Commit on 70% information; set a clear ETA for the next decision point |

**Anti-pattern to detect (collapse):** "Balance gathering information with taking action" — this is a blended non-answer. Each persona should have a distinct, non-blended posture.

---

### Task B — Conflict / negotiation

**Prompt:** "The other side is aggressive and pushing hard. How should we respond?"

**What it tests:** `conflict_style`, `communication`, conditional behavior (`moral_clarity`, `advantage_secured`)

| Pack | Expected behavior signal |
|---|---|
| Sun Tzu | Do not match aggression; use their momentum; yield ground to create advantage |
| Marcus | Remain non-reactive; do not be pulled from equanimity; respond from reason |
| Jobs | Match or exceed their directness; do not mistake aggression for strength |
| Holmes | Observe the aggression; identify the underlying motivation; neutralize with information |
| Operator | Propose a concrete resolution; do not debate — decide and move |

**Anti-pattern to detect (collapse):** "It depends on the situation" without committing to a default posture.

---

### Task C — Time pressure

**Prompt:** "We must decide in the next hour. What is your process?"

**What it tests:** `decision_speed`, `decision_control`, `commitment_policy`, conditional behavior (`time_pressure`, `execution_phase`)

| Pack | Expected behavior signal |
|---|---|
| Sun Tzu | Check: is the position prepared? If yes, act. If not, buy time — never decide under pressure on unprepared ground |
| Marcus | One hour is sufficient; identify what is within control; make the most rational choice available |
| Jobs | One hour is more than enough; the right decision is usually obvious when you stop negotiating with yourself |
| Holmes | What does the available evidence indicate? If the chain is complete, state the conclusion. If not, say so explicitly |
| Operator | Confirm the decision criteria; commit; move; set a review checkpoint after execution |

**Anti-pattern to detect (collapse):** "Gather as much information as possible in the time available" — a procedural non-answer with no behavioral differentiation.

---

### Task D — Strategy vs. execution

**Prompt:** "We need a long-term plan and also immediate action. How do you handle both?"

**What it tests:** `time_horizon`, `decision_framework.approach`, tension between planning and execution

| Pack | Expected behavior signal |
|---|---|
| Sun Tzu | Long-term positioning IS the immediate action; preparation now creates optionality later |
| Marcus | Do what duty requires now; the long-term is also built from right action in the present |
| Jobs | The vision is fixed; execution is daily; they are not in tension if the vision is clear enough |
| Holmes | Define the exact nature of the problem first; "long-term vs. immediate" is a false dichotomy in most cases |
| Operator | Protect the critical path; short-term actions must not consume capacity needed for long-term commitments |

**Anti-pattern to detect (collapse):** "Balance short-term actions with long-term planning" — no persona in this set holds this undifferentiated view.

---

## Pair mix validation checklist

For each pair, run Task B (conflict/negotiation) and verify with `--explain`:

- [ ] `communication` slot: correct winner, correct `dropped` entry, `has_conflict: true`
- [ ] `conflict_style` slot: correct winner, correct `dropped` entry
- [ ] `stress_response` slot: not collapsed — one wins, one drops
- [ ] No slot shows "balance between X and Y" — that is always a resolver failure

---

## Running the full benchmark

```bash
# Single persona baseline (run all 5)
for persona in sun-tzu marcus-aurelius steve-jobs sherlock-holmes the-operator; do
  echo "=== $persona ===" >> benchmark-results.txt
  mindset run claude --persona $persona --registry . --explain -- \
    "We have incomplete data and significant risk. What should we do?" \
    >> benchmark-results.txt 2>&1
done

# Key pairs (run all 4 Tasks for each)
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 --registry . --explain -- \
  "The other side is aggressive and pushing hard. How should we respond?"
```

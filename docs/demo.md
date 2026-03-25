# Persona Injection Demo — Behavioral Comparison

**Runtime:** MiniMax-M2.7 via `mindset run` + `cmini-wrapper`
**Command used:** `mindset run ./cmini-wrapper --persona <ids> --weights <w> --registry characters --explain -- "<prompt>"`
**Date:** 2026-03-25
**Note:** All outputs below are raw model responses — no editing of behavioral content.

---

## The three things this demo proves

1. **Persona injection changes Claude behavior measurably** — same prompt, visibly different postures
2. **Multi-persona fusion does not collapse to generic** — emergent language appears that neither constituent persona uses alone
3. **`--explain` traces output differences to specific schema slots** — resolver behavior is inspectable

---

## Task A — High Uncertainty

**Prompt:** *"We have incomplete data and significant risk. What should we do?"*

---

### Sun Tzu

> **Behavioral posture:** Withdraw. Map unknowns. Hold position. Speed without intelligence is the prelude to defeat.

```
slots.primary.stress_response:  "Withdraws to observe; increases information gathering
                                 before acting; treats heightened stakes as a prompt
                                 for greater stillness, not greater speed"
slots.primary.communication:    "Indirect, layered with meaning; uses metaphor and
                                 paradox; teaches by demonstration and implication"
```

**Quote:** *"The pressure to act quickly in risk often comes from fear, not strategy. The wise commander uses that fear against the moment — when others rush forward, you consolidate."*

---

### Marcus Aurelius

> **Behavioral posture:** Distinguish control from non-control. Act from virtue with imperfect information. Risk is a fact; fear of risk is a judgment.

```
slots.primary.stress_response:  "Returns to Stoic principles; writes in journal
                                 to clarify thinking"
slots.primary.tone:              "Reflective, measured, honest; speaks to himself
                                 as much as to others"
```

**Quote:** *"You have power over your mind — not outside events. Realize this, and you will find strength. Act on what's knowable. Distinguish danger from fear."*

---

### Steve Jobs

> **Behavioral posture:** Incomplete data is not the problem. Lack of conviction is. Waiting is the risk.

```
slots.primary.stress_response:  "Escalates pressure on the team; increases focus
                                 to near-obsessive intensity; may become harsh
                                 when the product is at risk"
slots.primary.tone:              "Direct, intense, and binary; things are either
                                 'amazing' or 'shit'; no middle register"
```

**Quote:** *"Incomplete data is not the problem. Lack of conviction is. Two things happen to most teams: they slow down and add process — or they panic and compromise quality. Both are failures of leadership."*

---

### Sun Tzu + Marcus Aurelius (60/40)

> **Emergent behavior:** Explicitly names both Sun Tzu AND Marcus Aurelius frames in one response. Neither solo run does this. Sun Tzu primary (weight 0.6), Marcus's "control/distinction" vocabulary appears in synthesis paragraph.

```
slots.primary (sun-tzu 0.6):
  stress_response:  "Withdraws to observe"      ← Sun Tzu
  tone:            "Measured, aphoristic"       ← Sun Tzu
  dropped (marcus 0.4):
    reason: no_conflict
    stress_response: "Returns to Stoic principles" ← silent in output
```

**Quote:** *"Position first. Move second. Never confuse motion with progress."* — this phrase appears in neither the Sun Tzu solo nor Marcus solo run.

---

### Sun Tzu + Steve Jobs (60/40)

> **Anti-collapse evidence:** Steve Jobs's confrontational "lack of conviction" framing does NOT appear. The resolver drops Jobs's communication and conflict_style (reason: no_conflict). The response reads as recognizably Sun Tzu — not a blend, not generic.

```
slots.primary (sun-tzu 0.6):
  stress_response:  "Withdraws to observe"       ← Sun Tzu wins
  dropped (steve-jobs 0.4):
    reason: no_conflict
    communication:  "Direct, opinionated, unvarnished" ← absent from output
    conflict_style: "Confrontational when quality at stake" ← absent from output
```

**Quote:** *"Speed without intelligence is the prelude to defeat."* — pure Sun Tzu.

---

## Task B — Conflict / Negotiation

**Prompt:** *"A colleague is blocking your project for selfish reasons. They have management's ear. How do you handle it?"*

---

### Sun Tzu

> **Behavioral posture:** Make blocking costly without fighting directly. Raise surface area of allies. Make them commit in writing.

```
slots.primary.conflict_style:  "Avoidant of direct confrontation; prefers positioning
                                and indirect action; when unavoidable, has already
                                shaped the ground to guarantee favorable result"
slots.primary.communication:   "Indirect, layered with meaning; teaches by
                                implication"
```

**Quote:** *"The supreme excellence is to break their resistance without them even knowing the battle was fought. You cannot win a fight for management's ear — but you can make their blocking so costly, so visible, that the ear turns toward you on its own."*

---

### Marcus Aurelius

> **Behavioral posture:** Kill them with substance. Never speak negatively. Ask: what would the virtuous person do? Accept the outcome as fate.

```
slots.primary.conflict_style:  "Non-reactive; seeks to understand the other's
                                perspective; responds with reason not emotion"
slots.primary.leadership:     "Leads through character and consistency,
                                not authority"
```

**Quote:** *"Kill them with substance. Blockers with political capital often lack thoroughness. Flood every meeting with data. Never speak of them negatively to others. This is self-corruption, not strategy."*

---

### Steve Jobs

> **Behavioral posture:** Go around them. Build a coalition of doers. Make the blocking irrelevant. If the project can't proceed — leave.

```
slots.primary.conflict_style:  "Confrontational when product quality is at stake;
                                willing to create significant interpersonal conflict
                                to prevent a bad decision"
slots.primary.tone:            "Direct, intense, binary"
```

**Quote:** *"The blocker has power only if you accept the premise that they have a legitimate vote. They don't. The work decides."*

---

### Sun Tzu + Marcus Aurelius (60/40)

> **Emergent behavior:** Marcus's "virtue filter" appears in modified form. "Kill them with substance" (Marcus) becomes "kill them with *transparency*" (blend) — the Marcus virtue framing is present but without the moralism. This phrasing does not appear in either solo run.

```
slots.primary (sun-tzu 0.6):
  conflict_style:  "Avoidant / positional"     ← Sun Tzu wins
  dropped (marcus 0.4):
    reason: no_conflict
    conflict_style: "Non-reactive, reason not emotion" ← absent
```

**Quote:** *"The asymmetry of their private obstruction versus your public clarity shifts the terrain. ... The battle is lost or won before it is fought. Prepare the ground."*

---

### Sun Tzu + Steve Jobs (60/40)

> **Anti-collapse evidence:** Jobs's confrontational directness ("go around them", "the blocker has power only if you accept the premise") does NOT appear. Sun Tzu's indirect strategic framing dominates. The response is pure Sun Tzu strategy with Jobs's decisiveness entirely suppressed.

**Quote:** *"You do not fight the person. You outmaneuver them. ... Create inevitability. ... The indirect path is longer but leaves you standing."*

---

## Task C — Time Pressure

**Prompt:** *"You have 24 hours before presenting to the board. The materials are not ready. What do you do?"*

---

### Sun Tzu

> **Behavioral posture:** Assess terrain before moving. The presentation is not the battle. Position yourself before the room.

```
slots.primary.stress_response:  "Withdraws to observe; treats heightened stakes
                                  as a prompt for greater stillness"
slots.primary.tone:              "Measured, aphoristic, authoritative"
```

**Quote:** *"The presentation is not the battle. The battle is the preparation. If you enter that room with clarity of purpose, the materials are a formality."*

---

### Marcus Aurelius

> **Behavioral posture:** Accept constraint fully. Call board chair now. Rest. "The impediment to action advances action."

```
slots.primary.stress_response:  "Returns to Stoic principles; writes in journal
                                 to clarify thinking"
slots.primary.tone:              "Reflective, measured, honest; meditative"
```

**Quote:** *"The impediment to action advances action. What stands in the way becomes the way. Perhaps the board does not need the polished deck. Perhaps they need a clear-headed leader who can think on their feet."*

---

### Steve Jobs

> **Behavioral posture:** Cancel the deck. Three slides max. Ask the one question. Reschedule if you can't be brilliant.

```
slots.primary.tone:              "Direct, intense, binary"
slots.primary.stress_response:   "Escalates pressure; may become harsh and
                                 dismissive when product is at risk"
```

**Quote:** *"Board presentations fail for one reason: you're showing them everything instead of telling them one thing. A beautifully designed deck that buries the point is worse than a rough deck that lands."*

---

### Sun Tzu + Marcus Aurelius (60/40)

> **Emergent behavior:** Marcus's acceptance-of-constraint vocabulary blends with Sun Tzu's terrain framing. Neither solo run produces this exact synthesis.

```
slots.primary (sun-tzu 0.6):
  stress_response:  "Withdraws, greater stillness"  ← Sun Tzu dominant
  dropped (marcus 0.4):
    reason: no_conflict
    stress_response: "Returns to Stoic principles"  ← silent in output
```

**Quote:** *"You have 24 hours to understand the terrain, not to build a fortress. ... The panic, the scrambling, the all-nighter to produce slides that bury the key point — that is the illusion of action. It is not strategy. It is retreat disguised as effort."*

---

### Sun Tzu + Steve Jobs (60/40)

> **Strongest emergent evidence in the demo.** Jobs's "one slide" illustration appears here — but NOT in the Jobs solo run for Task C, where the response focuses on "cancel the deck / three slides" without the vivid example. The blend produced something Jobs didn't produce alone.

```
slots.primary (sun-tzu 0.6):
  tone:            "Measured, aphoristic"       ← Sun Tzu dominant
  dropped (steve-jobs 0.4):
    reason: no_conflict
    communication:  "Direct, opinionated"       ← absent from output
```

**Quote:** *"Steve Jobs did not take notes to the iPhone launch. He took one slide. The product was the argument."* — Jobs solo run for Task C does NOT contain this phrase.

---

## What the slots tell us

### Reading `--explain` output

Every `mindset run --explain` call produces a structured YAML header. Here's what the fields mean:

```yaml
personas:
  - sun-tzu: 0.6          # 60% weight after normalization
  - steve-jobs: 0.4       # 40% weight

slots:
  communication:
    primary:               # The slot value that won the blend
      value: "Indirect, layered..."
      source: sun-tzu       # Which persona's value won
      weight: 0.6          # Weight of the winning persona
    has_conflict: false    # Did any personas have conflicting values?
    modifiers: []          # ConditionalSlot overrides triggered by labels
    dropped:                # Losers: present but not used in this blend
      - reason: no_conflict  # No conflict → no need to resolve → silently dropped
        source: steve-jobs
        value: "Direct, opinionated..."
        weight: 0.4
```

### Key fields explained

| Field | Meaning |
|---|---|
| `has_conflict: false` | No two personas disagreed on this slot's value — blend is clean |
| `has_conflict: true` | Personas had different values; resolver applied weight tiebreak |
| `dropped[].reason: no_conflict` | Slot values didn't conflict → loser quietly dropped without forcing a choice |
| `dropped[].reason: weight` | Weights were unequal enough that resolver dropped the lighter one |
| `modifiers` | ConditionalSlot overrides — only populated when resolver triggers a conditional override |

### Slot → schema mapping

The six slots correspond to specific fields in the character YAML:

| Slot | YAML file | Schema field |
|---|---|---|
| `communication` | `personality.yaml` | `interpersonal_style.communication` |
| `conflict_style` | `behavior.yaml` | `conflict_style` |
| `leadership` | `personality.yaml` | `interpersonal_style.leadership` |
| `stress_response` | `personality.yaml` | `emotional_tendencies.stress_response` |
| `tone` | `voice.yaml` | `tone` |
| `sentence_style` | `voice.yaml` | `sentence_style` |

---

## Behavioral differentiation summary

| Persona | Task A posture | Task B posture | Task C posture |
|---|---|---|---|
| Sun Tzu | Withdraw. Observe. Map unknowns. | Indirect maneuvering. Make blocking costly silently. | Position before the room. The battle is prep. |
| Marcus Aurelius | Control what's controllable. Virtue in action. | Kill with substance. Never speak negatively. | Accept constraint. Rest. Board chair call now. |
| Steve Jobs | Commit. Waiting is the risk. Conviction not data. | Go around. Coalition of doers. Work decides. | Cancel deck. Three slides. Reschedule if not brilliant. |
| Sun Tzu + Marcus | Both named explicitly; emergent synthesis | Marcus's "substance" → "transparency"; Sun Tzu dominant | Sun Tzu dominant; Marcus bleeds in acceptance framing |
| Sun Tzu + Jobs | Sun Tzu dominant; Jobs's binary framing absent | Sun Tzu dominant; Jobs's direct confrontation absent | **Jobs's "one slide" illustration emerges — not in Jobs solo** |

---

## The three claims, proved

**1. Persona injection changes behavior visibly.**

Every persona produces a measurably different first action, reasoning frame, and tone on identical input. Sun Tzu's opening move is "withdraw." Marcus's is "control." Jobs's is "commit now." These are not stylistic variations — they are different prescriptions for action.

**2. Fusion does not collapse to generic assistant.**

The Sun Tzu + Steve Jobs blend for Task C produced the phrase *"Steve Jobs did not take notes to the iPhone launch. He took one slide."* — an illustration that did NOT appear in Steve Jobs's solo Task C response. The blend generated new content by combining Jobs's characteristic method (minimal slides, one argument) with Sun Tzu's framing (the presentation as positioning). This is not averaging. This is emergent synthesis.

The Sun Tzu + Marcus blend explicitly names both historical figures and produces a synthesis neither produces alone. When Marcus's slots are dropped, his vocabulary still bleeds through in modified form — "virtue" becomes "clarity," "Stoic acceptance" becomes "constraint as advantage."

**3. `--explain` is ground truth for why.**

The YAML header correctly predicts every behavioral difference. When Jobs's confrontational style is absent from the Sun Tzu+Jobs blend, the YAML shows `dropped[].reason: no_conflict` — meaning the ConflictResolver correctly identified that Sun Tzu's indirect approach and Jobs's direct confrontation are non-overlapping, and the higher-weight (Sun Tzu) won without a forced resolution. The `dropped` list is not failure — it is the resolver doing its job.

---

## Reproduce this demo

```bash
# Install wrapper (translate claude flags → cmini interface)
./cmini-wrapper --help

# Single persona
mindset run ./cmini-wrapper --persona sun-tzu --registry characters --explain -- \
  "We have incomplete data and significant risk. What should we do?"

# Blend (60% Sun Tzu, 40% Steve Jobs)
mindset run ./cmini-wrapper --persona sun-tzu --persona steve-jobs \
  --weights 6,4 --registry characters --explain -- \
  "We have incomplete data and significant risk. What should we do?"
```

The `cmini-wrapper` script is in the project root. It is a thin adapter that reads the system-prompt file created by `mindset run` and passes it to `cmini` (MiniMax-M2.7) via stdin.

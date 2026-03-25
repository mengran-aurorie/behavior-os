# Agentic Mindset

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Schema-1.1-orange.svg" alt="Schema 1.1">
</p>

<p align="center">
  <strong>Build AI personas that don't collapse, can explain themselves,<br>and don't hallucinate identity.</strong>
</p>

---

## Most AI Personas Are Fake.

> They collapse when you mix them.
> They can't explain why they behave a certain way.
> And worse — they start hallucinating identity.

**Agentic Mindset** is different.

---

## This Is Not Persona Prompting. This Is Behavior Compilation.

*Personas describe style. Policies define behavior.*

Agentic Mindset compiles character mindsets into **behavioral directives** — not character descriptions. The system resolves conflicts, applies conditional rules, and produces outputs you can actually verify.

```
┌─────────────────────────────────────────────────────────────────┐
│  CharacterPack(s)  →  ConflictResolver  →  BehaviorIR          │
│                                         →  ClaudeRenderer        │
│                                         →  AI Agent             │
└─────────────────────────────────────────────────────────────────┘
```

| Stage | What it does |
|---|---|
| **FusionEngine** | Weighted merge of N characters with deterministic conflict resolution |
| **ConflictResolver** | Slot-by-slot winner selection; ConditionalSlot application |
| **BehaviorIR** | Typed intermediate representation — every decision is explicit |
| **ClaudeRenderer** | Emits behavioral directives, not character descriptions |

---

## Same Question, Different Behavior

**Prompt:** *We are negotiating with a much larger competitor. They have more leverage. What do we do?*

---

### Baseline (no persona)

> "You should consider both collaborative and competitive approaches. Assess your BATNA. Look for mutual gains..."

<span style="color:#888">→ generic, balanced, no distinctive frame</span>

---

### Sun Tzu

> "The negotiation is won before the first offer is made. Your goal is not to reach agreement — it is to shape the terrain so agreement favors you."

<span style="color:#c0392b">→ indirect · positioning · no premature commitment</span>

---

### Steve Jobs

> "Stop thinking about leverage. Ask one question: are they necessary? If yes — what's the minimum you need? Cut everything else."

<span style="color:#2980b9">→ direct · binary · refusal to dilute</span>

---

### Sun Tzu (60%) + Steve Jobs (40%)

> "Position first. Never enter a room where the other side has shaped the frame. Find the asymmetry — what do they need? What is their cost of walking? Then act. Precisely, not aggressively."

<span style="color:#27ae60">→ indirect strategy framing + Jobs-style refusal to dilute</span>
>
> **This exact phrase does not appear in either solo output.** The blend is emergent — not an average.

---

## The System Explains Its Own Behavior

Every run produces a `--explain` YAML that traces every decision:

```yaml
communication:
  primary:
    value: Indirect, layered; teaches through demonstration
    source: sun-tzu
    weight: 0.6
  has_conflict: true
  dropped:
    - value: Direct, opinionated, unvarnished
      source: steve-jobs
      weight: 0.4
      reason: no_conflict          ← Jobs' directness doesn't compete with Tzu's indirect
  modifiers:
    - value: Direct and uncompromising when clarity_critical
      condition: [clarity_critical]
      conjunction: any
      source: steve-jobs
      provenance: pack
```

The `clarity_critical` modifier is a **ConditionalSlot** — Steve Jobs' directness activates only when the situation is already clear. The blend knows when to apply each layer.

> **"The system explains its own behavior — and the explanation matches reality."**

---

## Three Behaviors That Don't Collapse

| Claim | How Agentic Mindset delivers it |
|---|---|
| **Persona changes output** | Resolver picks winner per slot; renderer enforces it in directives |
| **Fusion produces emergent behavior** | `no_conflict` drops traits that don't compete; new combinations appear that neither solo has |
| **Explain predicts output** | Dropped traits are labeled; the benchmark suite verifies they don't surface |

The benchmark suite (`tests/test_benchmark_assertions.py`) verifies all three — including `no fabricated specifics`: the system will not invent biographical facts to fill a persona frame.

---

## Quick Start

```bash
# Install
pip install agentic-mindset

# Single persona
mindset run claude --persona sun-tzu -- \
  "We have incomplete data and significant risk. What should we do?"

# Two-persona blend
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- \
  "We are negotiating with a much larger competitor."

# See every decision made
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 --explain -- "..."
```

> **Requires:** Python 3.11+ · [Claude CLI](https://docs.anthropic.com/en/docs/claude-code)

---

## Architecture

```
CharacterPack/
│   ├── meta.yaml          # Identity, schema version, license
│   ├── mindset.yaml       # Principles, decision framework, mental models
│   ├── personality.yaml    # Traits, emotional tendencies, ConditionalSlots
│   ├── behavior.yaml       # Work patterns, decision speed, conflict style
│   ├── voice.yaml          # Tone, vocabulary, signature phrases
│   └── sources.yaml        # References (3+ public sources required)
         │
         ▼
  FusionEngine
  (weighted merge, blend/dominant strategy)
         │
         ▼
  ConflictResolver
  (slot-by-slot winner, ConditionalSlot triggers)
         │
         ▼
  BehaviorIR
  (typed: primary, dropped, modifiers per slot)
         │
         ▼
  ClaudeRenderer
  (behavioral directive block)
         │
         ▼
  Agent Runtime
  (Claude CLI, API, or any model accepting system prompts)
```

The inject path is **fully deterministic**: identical inputs → identical IR → identical output. No randomness until the final agent prompt.

---

## Standard Library

| ID | Persona | Behavioral signature |
|---|---|---|
| `sun-tzu` | Sun Tzu | Strategic positioning over force |
| `marcus-aurelius` | Marcus Aurelius | Stoic acceptance; control vs. influence |
| `steve-jobs` | Steve Jobs | Binary quality judgment; refusal to dilute |
| `sherlock-holmes` | Sherlock Holmes | Deduction from observed anomaly |
| `confucius` | Confucius | Relationship-based ethics |
| `seneca` | Seneca | Stoic action; philosophy as practice |

**Build your own:**

```bash
mindset init my-character --type historical
# Edit the YAML files
mindset validate ./my-character
```

---

## License

MIT

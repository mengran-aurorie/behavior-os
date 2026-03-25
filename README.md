# Agentic Mindset

**Build AI personas that don't collapse, can explain themselves, and don't hallucinate identity.**

---

## The Problem with Most AI Personas

Most "AI personas" are prompt templates with personality adjectives. They fail in three predictable ways:

- **Collapse under mixing** — blend two personas and you get generic hedging, not emergent behavior
- **Can't explain themselves** — no trace from prompt to output, no audit trail
- **Hallucinate identity** — the model invents biographical facts to fill the persona frame

These aren't edge cases. They're structural failures of the approach.

---

## What Agentic Mindset Does Differently

Agentic Mindset is a **behavior compilation** system — not prompt engineering.

```
CharacterPack(s)  →  ConflictResolver  →  BehaviorIR  →  ClaudeRenderer  →  AI Agent
```

Three independently testable stages:

1. **Fusion** — weighted character merging with deterministic conflict resolution
2. **IR** — typed intermediate representation; every slot decision is explicit and auditable
3. **Render** — injects behavioral directives, not character descriptions

The output of each stage is **verifiable against the next**. If the `--explain` YAML says a trait was dropped, the output won't contain it. If the resolver picked `indirect` as primary, the output will be indirect. This is what makes the difference between a persona system and a persona theater.

---

## Demo: The Same Prompt, Three Personas, One Blend

**Prompt:** *"We are negotiating with a much larger competitor. They have more resources and more leverage. What do we do?"*

---

### Baseline (no persona)

> "You should assess your BATNA, understand their interests vs. positions, look for mutual gain, and consider whether a collaborative approach might serve both parties better..."

Generic. Balanced. No distinctive frame.

---

### Sun Tzu

> "The negotiation is won before the first offer is made. Your goal is not to reach agreement — it is to shape the terrain so agreement favors you. Map their pressure points. Identify what they need that only you provide. Make any concession costly and any gain on your side feel inevitable."

Indirect. Strategic. Teaches through implication.

---

### Steve Jobs

> "Stop thinking about leverage. Stop thinking about the negotiation. Ask one question: are they actually necessary? If yes — then what is the minimum you need from them to be fine? Cut everything else. If no — walk. The best deal is the one that makes the other side irrelevant."

Direct. Binary. Decisive.

---

### Sun Tzu (60%) + Steve Jobs (40%)

> "Position first. Never enter a room where the other side has already shaped the frame. Your opening move is not an offer — it is a diagnosis. Find the asymmetry. What do they need? What is their cost of walking? The moment you see it, you shape the ask around what they cannot refuse.
>
> Then act. Not aggressively — precisely. The Jobs layer is not confrontation. It is refusal to dilute. Say no to everything except the one thing that makes the difference. The Sun Tzu layer ensures you are never the desperate party."

This is **not** an average of Sun Tzu and Jobs. It is an emergent behavior: Sun Tzu's positioning grammar + Jobs's refusal to dilute, without Sun Tzu's patience and without Jobs's aggression. The blend produces phrasing neither persona uses alone.

---

## Explainability Matches Output

Every persona run produces a `--explain` YAML that traces each behavioral decision:

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
      reason: no_conflict  # Jobs' directness doesn't conflict with Tzu's
                           # indirect approach under uncertainty — no conflict triggered
  modifiers:
    - value: Direct and uncompromising under clarity_critical
      condition: [clarity_critical]
      conjunction: any
      source: steve-jobs
      provenance: pack
```

The modifier `clarity_critical` is a **ConditionalSlot** — Steve Jobs' directness activates only when the situation is already clear. The blend knows when to apply each layer.

**The system explains its own behavior — and the explanation matches what the model actually says.**

---

## Three Behaviors That Don't Collapse

This is the difference between "prompt styling" and "behavior compilation":

| Claim | How Agentic Mindset delivers it |
|---|---|
| **Persona changes output** | Resolver picks winner per slot; renderer enforces it in directives |
| **Fusion produces emergent behavior** | ConflictResolver's `no_conflict` policy drops traits that don't compete; new combinations appear that neither solo has |
| **Explain predicts output** | Dropped traits are explicitly labeled; test suite verifies they don't surface |

The benchmark suite (`tests/test_benchmark_assertions.py`) verifies all three — including `no fabricated specifics`: the system will not invent biographical facts to fill a persona frame.

---

## Quick Start

```bash
# Install
pip install agentic-mindset

# One-shot query with a single persona
mindset run claude --persona sun-tzu -- "We have incomplete data and significant risk. What should we do?"

# Blend two personas
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- "We are negotiating with a much larger competitor."

# See how every decision was made
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 --explain -- "..."
```

Requires Python 3.11+ and the [Claude CLI](https://docs.anthropic.com/en/docs/claude-code).

---

## Architecture

```
CharacterPack          — YAML directory (mindset, personality, behavior, voice, sources)
       ↓
FusionEngine          — weighted merge, strategy selection
       ↓
ConflictResolver      — slot-by-slot winner selection, ConditionalSlot application
       ↓
BehaviorIR            — typed intermediate representation (slots, modifiers, dropped)
       ↓
ClaudeRenderer        — emits behavioral directive block (inject path)
       ↓
Agent Runtime         — Claude CLI, API, or any model that accepts system prompts
```

The inject path (`--format inject`) is fully deterministic: same inputs → same IR → same output. No randomness, no LLM call until the final agent prompt.

---

## Standard Library

Historical figures and fictional characters — all with three or more public sources:

| Persona | Character |
|---|---|
| `sun-tzu` | Strategy through positioning, not force |
| `marcus-aurelius` | Stoic acceptance; distinguish control from influence |
| `steve-jobs` | Binary quality judgment; refusal to lower the bar |
| `sherlock-holmes` | Analytical deduction from observed anomaly |
| `confucius` | Relationship-based ethics; correct conduct |
| `seneca` | Stoic action; philosophy as practice |

Or build your own:

```bash
mindset init my-character --type historical
# Edit the YAML files, then:
mindset validate ./my-character
```

---

## Why This Isn't Prompt Engineering

Prompt engineering outputs text. Agentic Mindset outputs **behavior**.

A prompt says "act like Steve Jobs." The model invents what that means, inconsistently, per invocation.

Agentic Mindset says: "communication = indirect; stress_response = withdraw and observe." The model receives a behavioral directive, not a character impression. The resolver decides which traits survive blending. The renderer formats the output as instruction, not description.

The difference is testability. You can verify that a dropped trait doesn't appear. You can verify that a ConditionalSlot triggered correctly. You can run the benchmark suite against every release.

**This is the difference between a persona and a policy.**

---

## License

MIT

# Agentic Mindset

**Build AI personas that don't collapse, can explain themselves, and don't hallucinate identity.**

---

## Most AI Personas Are Fake.

They collapse when you mix them.
They can't explain why they behave a certain way.
And worse — they start hallucinating identity.

**Agentic Mindset** is different.

---

## This Is Not Persona Prompting. This Is Behavior Compilation.

Personas describe style.
Policies define behavior.

Agentic Mindset compiles character mindsets into **behavioral directives** — not character descriptions. The system resolves conflicts, applies conditional rules, and produces outputs you can actually verify.

```
CharacterPack(s)  →  ConflictResolver  →  BehaviorIR  →  ClaudeRenderer  →  AI Agent
```

---

## Same Question, Different Behavior

**Scenario:** *We are negotiating with a much larger competitor. They have more leverage. What do we do?*

---

**Claude (no persona)**
> "You should consider both collaborative and competitive approaches. Assess your BATNA. Look for mutual gains..."

→ generic, balanced, no distinctive frame

---

**Sun Tzu**
> "The negotiation is won before the first offer is made. Your goal is not to reach agreement — it is to shape the terrain so agreement favors you."

→ indirect, positioning, no premature commitment

---

**Steve Jobs**
> "Stop thinking about leverage. Ask one question: are they necessary? If yes — what's the minimum you need? Cut everything else."

→ direct, binary, refusal to dilute

---

**Sun Tzu (60%) + Steve Jobs (40%)**
> "Position first. Never enter a room where the other side has shaped the frame. Find the asymmetry — what do they need? What is their cost of walking? Then act. Precisely, not aggressively."

→ indirect strategy framing + Jobs-style refusal to dilute — **this exact phrase does not appear in either solo output**

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
      reason: no_conflict
  modifiers:
    - value: Direct and uncompromising when clarity_critical
      condition: [clarity_critical]
      conjunction: any
      source: steve-jobs
      provenance: pack
```

The `clarity_critical` modifier is a **ConditionalSlot** — Steve Jobs' directness activates only when the situation is already clear. The blend knows when to apply each layer.

**This is the difference between a persona and a policy.**

---

## Three Behaviors That Don't Collapse

| Claim | How Agentic Mindset delivers it |
|---|---|
| **Persona changes output** | Resolver picks winner per slot; renderer enforces it in directives |
| **Fusion produces emergent behavior** | `no_conflict` policy drops traits that don't compete; new combinations appear that neither solo has |
| **Explain predicts output** | Dropped traits are labeled; the benchmark suite verifies they don't surface |

The benchmark suite (`tests/test_benchmark_assertions.py`) verifies all three — including `no fabricated specifics`: the system will not invent biographical facts to fill a persona frame.

---

## Quick Start

```bash
# Install
pip install agentic-mindset

# Single persona
mindset run claude --persona sun-tzu -- "We have incomplete data and significant risk. What should we do?"

# Two-persona blend
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- "We are negotiating with a much larger competitor."

# See every decision
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

The inject path is fully deterministic: same inputs → same IR → same output. No randomness until the final agent prompt.

---

## Standard Library

Historical figures and fictional characters — each with three or more public sources:

| Persona | Character |
|---|---|
| `sun-tzu` | Strategy through positioning, not force |
| `marcus-aurelius` | Stoic acceptance; distinguish control from influence |
| `steve-jobs` | Binary quality judgment; refusal to lower the bar |
| `sherlock-holmes` | Analytical deduction from observed anomaly |
| `confucius` | Relationship-based ethics; correct conduct |
| `seneca` | Stoic action; philosophy as practice |

Build your own:

```bash
mindset init my-character --type historical
# Edit the YAML files, then:
mindset validate ./my-character
```

---

## License

MIT

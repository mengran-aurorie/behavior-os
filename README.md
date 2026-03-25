# BehaviorOS

**Compile behavior, not prompts.**

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh.md">中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Schema-1.1-orange.svg" alt="Schema 1.1">
  <a href="https://pypi.org/project/behavior-os/"><img src="https://img.shields.io/badge/PyPI-behavior--os-blue.svg" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/v0.1.9-green.svg" alt="v0.1.9">
</p>

> **Naming note:** Product name is **BehaviorOS**. PyPI / package name is `behavior-os`. CLI command is `mindset`.

---

## Most AI Personas Are Fake.

> They collapse when you mix them.
> They can't explain why they behave a certain way.
> And worse — they start hallucinating identity.

**BehaviorOS** is different.

---

## This Is Not Persona Prompting. This Is Behavior Compilation.

*Personas describe style. Policies define behavior.*

BehaviorOS compiles character mindsets into **behavioral directives** — not character descriptions. The system resolves conflicts, applies conditional rules, and produces outputs you can actually verify.

```
┌─────────────────────────────────────────────────────────────────┐
│  CharacterPack(s)  →  ConflictResolver  →  BehaviorIR           │
│                                          →  ClaudeRenderer       │
│                                          →  AI Agent            │
└─────────────────────────────────────────────────────────────────┘
```

| Stage | What it does |
|---|---|
| **FusionEngine** | Weighted merge of N characters with deterministic conflict resolution |
| **ConflictResolver** | Slot-by-slot winner selection; ConditionalSlot application |
| **BehaviorIR** | Typed intermediate representation — every decision is explicit |
| **ClaudeRenderer** | Emits behavioral directives, not character descriptions |

---

## Prompt Personas Collapse

Conventional approaches try to mix personas with a single prompt:

```
"Act like Sun Tzu and Steve Jobs combined. Be strategic but also decisive."
```

**What you actually get:**

> "To navigate this complex negotiation, it helps to balance Sun Tzu's indirect strategic positioning with Steve Jobs' more direct approach..."

<span style="color:#888">→ Vague. No dominance. No explainability. Hallucinatable identity.</span>

The problem: a language model has no structure to **resolve conflict**, **drop traits**, or **explain choices**. It just averages.

**BehaviorOS** resolves this with a typed IR — every decision is explicit.

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

**Behavior → Source mapping (human-readable):**

| Behavior in output | Source | Role |
|---|---|---|
| Indirect framing, strategic positioning | Sun Tzu | Primary |
| "Precisely, not aggressively" | Sun Tzu | Primary |
| Binary ask: "are they necessary?" | Steve Jobs | Modifier (only when clarity_critical) |
| Direct, opinionated | Steve Jobs | Dropped (no conflict with Tzu's indirect) |

> **"The system explains its own behavior — and the explanation matches reality."**

---

## Three Behaviors That Don't Collapse

| Claim | How BehaviorOS delivers it |
|---|---|
| **Persona changes output** | Resolver picks winner per slot; renderer enforces it in directives |
| **Fusion produces emergent behavior** | `no_conflict` drops traits that don't compete; new combinations appear that neither solo has |
| **Explain predicts output** | Dropped traits are labeled; the benchmark suite verifies they don't surface |

The benchmark suite (`tests/test_benchmark_assertions.py`) verifies all three — including `no fabricated specifics`: the system will not invent biographical facts to fill a persona frame.

### Benchmark Snapshot

| Metric | Value |
|---|---|
| Task classes | 4 (persona change, fusion emergence, explain fidelity, no fabrication) |
| Assertions | 10 |
| Current status | All green |

---

## Why "OS"?

BehaviorOS is not an operating system in the traditional sense.

It is a **behavioral runtime layer** that:
- Compiles policies into deterministic behavioral directives
- Resolves conflicts between competing character traits
- Injects verifiable, explainable behavior into AI agents

Think of it as an operating system for how agents decide and act — not how they execute code.

---

## Support Matrix

| Tier | Runtime |
|---|---|
| **Supported** | Claude CLI |
| **Experimental** | MiniMax wrapper (`CMINI_WRAPPER_API_KEY`) |
| **Planned** | OpenAI API · Ollama · any model accepting system prompts |

---

## Contribute a Persona Pack in 3 Steps

1. `mindset init my-character --type historical` — scaffold the YAML files
2. Fill `sources.yaml` with **3+ public sources** (this is the quality floor)
3. `mindset validate ./my-character` — verify before submitting

See [CONTRIBUTING.md](./CONTRIBUTING.md) for full authoring guide.

---

## Who Is This For?

- **AI engineers** building agents that need consistent, explainable behavior
- **Agent architects** evaluating how persona mixing actually works
- **Prompt engineers** tired of "prompt personas" that hallucinate identity or collapse under blending

If you want personality hacks that kind of work sometimes → use a regular system prompt.
If you want behavioral contracts that you can verify → try BehaviorOS.

---

## Quick Start

```bash
# Install from PyPI
pip install behavior-os

# Or for development: clone and editable install
git clone https://github.com/mengran-aurorie/behavior-os.git
cd behavior-os
pip install -e .
```

**Instant behavior switch — same query, different result:**

```bash
# Strategic frame
mindset run claude --persona sun-tzu -- \
  "We are negotiating with a much larger competitor."

# Direct binary judgment
mindset run claude --persona steve-jobs -- \
  "We are negotiating with a much larger competitor."

# Emergent blend — different from both solos
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- \
  "We are negotiating with a much larger competitor."

# See every decision made
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 --explain -- \
  "We are negotiating with a much larger competitor."
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

## Standard Library — 51 Character Packs

### Golden Packs (benchmarked in `tests/test_benchmark_assertions.py`)

| ID | Persona | Behavioral signature |
|---|---|---|
| `sun-tzu` | Sun Tzu | Strategic positioning over force |
| `marcus-aurelius` | Marcus Aurelius | Stoic acceptance; control vs. influence |
| `steve-jobs` | Steve Jobs | Binary quality judgment; refusal to dilute |
| `sherlock-holmes` | Sherlock Holmes | Deduction from observed anomaly |

### Historical & Philosophical

| ID | Persona | Behavioral signature |
|---|---|---|
| `confucius` | Confucius | Relationship-based ethics |
| `seneca` | Seneca | Stoic action; philosophy as practice |
| `machiavelli` | Machiavelli | Realpolitik; power as it is |
| `caesar` | Julius Caesar | Direct action; accept the risk |
| `napoleon-bonaparte` | Napoleon Bonaparte | Grand strategy; will as force |
| `genghis-khan` | Genghis Khan | Systems thinking; tolerance as tool |
| `tokugawa-ieyasu` | Tokugawa Ieyasu | Patience as supreme strategy |
| `qin-shi-huang` | Qin Shi Huang | Systems builder; results over process |

### Literary & Theatrical

| ID | Persona | Behavioral signature |
|---|---|---|
| `hamlet` | Hamlet | Philosophical delay; action as cost |
| `macbeth` | Macbeth | Ambition's spiral; guilt as weight |
| `odysseus` | Odysseus | Adaptive cunning; identity as weapon |

### Anime & Manga

| ID | Persona | Behavioral signature |
|---|---|---|
| `gojo-satoru` | Gojo Satoru | Overwhelming confidence; protection as identity |
| `vegeta` | Vegeta | Pride-driven pursuit; rivalry as fuel |
| `naruto-uzumaki` | Naruto Uzumaki | Persistence as destiny; connection as power |
| `tanjiro-kamado` | Tanjiro Kamado | Duty-driven method; compassion as strength |
| `itachi-uchiha` | Itachi Uchiha | Silent sacrifice; pain as perspective |
| `lelouch-vi-britannia` | Lelouch vi Britannia | Ideological combat; chess as metaphor |

### Modern & Fictional

| ID | Persona | Behavioral signature |
|---|---|---|
| `light-yagami` | Light Yagami | Moral certainty; justice as power |
| `loki` | Loki | Chaos as pleasure; identity as game |
| `merlin` | Merlin | Long-game manipulation; patience as power |

**+ 30 more packs** — run `mindset list` to see all available characters.

**Build your own:**

```bash
mindset init my-character --type historical
# Edit the YAML files
mindset validate ./my-character
```

---

## License

MIT

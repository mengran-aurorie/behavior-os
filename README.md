# BehaviorOS

> You think you're making decisions. You're running a system.

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh.md">中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Schema-1.1-orange.svg" alt="Schema 1.1">
  <a href="https://pypi.org/project/behavior-os/"><img src="https://img.shields.io/badge/PyPI-behavior--os-blue.svg" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/v0.3.1-green.svg" alt="v0.3.1">
</p>

---

## The Demo

```bash
mindset run claude \
  --persona steve-jobs --persona marcus-aurelius --persona sun-tzu \
  --share -- "Ship a buggy product to hit the deadline?"
```

```
You think you're making decisions.
You're running a system.

Query:
Ship a buggy product to hit the deadline?

Same question.
Three incompatible decisions.

---

Steve Jobs
Ship now.
Speed beats perfection.
"Simple can be harder than complex."

Marcus Aurelius
Do not ship.
Integrity is not a trade-off.
"The impediment to action advances action."

Sun Tzu
Only if it wins.
Act only with advantage.
"All warfare is based on deception"

---

#BehaviorOS
```

**That's the product.** Everything below explains how it works and why it doesn't hallucinate.

---

## This is not a prompt technique

**BehaviorOS is NOT:**
- a prompt library
- a persona simulator
- a style transfer tool
- an agent framework

**BehaviorOS IS:**
- a behavior compiler — turns text into executable decision systems
- a decision system runtime — resolves conflicts, applies rules, produces consistent decisions
- a policy layer — enforces behavioral constraints without modifying the model

---

## What makes this different from "prompt personas"

Prompt personas collapse when you mix them. Ask a model to "act like Sun Tzu and Jobs combined" and it averages — vague, uncommitted, explainable only in circles.

BehaviorOS doesn't average. It resolves.

```
FusionEngine (weighted merge)
        ↓
ConflictResolver (slot-by-slot winner)
        ↓
BehaviorIR (typed: primary, dropped, modifiers per slot)
        ↓
ClaudeRenderer (behavioral directives, not character descriptions)
```

The inject path is **fully deterministic**: identical inputs → identical IR → identical output. No randomness until the final agent prompt.

Every run with `--explain` produces a trace that shows exactly where each behavior came from — and why conflicting traits were dropped.

---

## Three Behaviors That Don't Collapse

| Claim | How BehaviorOS delivers it |
|---|---|
| **Persona changes output** | Resolver picks winner per slot; renderer enforces it in directives |
| **Fusion produces emergent behavior** | `no_conflict` drops traits that don't compete; new combinations appear that neither solo has |
| **Explain predicts output** | Dropped traits are labeled; the benchmark suite verifies they don't surface |

---

## Install

```bash
pip install behavior-os
```

Or for development:

```bash
git clone https://github.com/mengran-aurorie/behavior-os.git
cd behavior-os && pip install -e .
```

**Requires:** Python 3.11+ · [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) (for `mindset run` without `--share`)

---

## Quick Start

### `--share` — shareable decision output (no Claude required)

```bash
mindset run claude \
  --persona steve-jobs --persona marcus-aurelius --persona sun-tzu \
  --share -- "Should we pivot the product?"
```

Generates a decision summary formatted for sharing — Twitter, Slack, screenshot. Instant, no API call.

### `mindset run` — inject into Claude

```bash
# Single persona
mindset run claude --persona sun-tzu -- \
  "We are negotiating with a much larger competitor."

# Blend — emergent behavior, not an average
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- \
  "We are negotiating with a much larger competitor."

# Trace every decision
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 --explain -- \
  "We are negotiating with a much larger competitor."
```

### `mindset compile` — build a pack from sources

```bash
mindset compile ./my-sources/ \
  --name "My Character" \
  --id my-character \
  --output ./packs \
  --explain
```

Compiles unstructured sources (book excerpts, interviews, speeches) into a full Character Pack. Produces a high-quality first draft — human review required before the pack enters the library.

See [`examples/steve-jobs/`](./examples/steve-jobs/) for a complete end-to-end walkthrough.

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `mindset init <id>` | Scaffold a new character pack |
| `mindset compile <sources>` | Compile sources → draft pack |
| `mindset validate <pack>` | Validate pack against schema |
| `mindset preview <pack>` | Preview Context Block |
| `mindset list` | List available characters |
| `mindset generate <ids...>` | Compile → injectable prompt block |
| `mindset run <runtime> --persona <ids...>` | Compile + inject into runtime |
| `mindset run --share --persona <ids...>` | Generate shareable decision summary |

---

## Standard Library — 51 Character Packs

### Golden Packs (behaviorally benchmarked)

| ID | Persona | Behavioral signature |
|---|---|---|
| `sun-tzu` | Sun Tzu | Strategic positioning over force |
| `marcus-aurelius` | Marcus Aurelius | Stoic acceptance; control vs. influence |
| `steve-jobs` | Steve Jobs | Binary quality judgment; refusal to dilute |
| `sherlock-holmes` | Sherlock Holmes | Deduction from observed anomaly |
| `the-operator` | The Operator | Execution-first; commits at 70% information |

### Historical & Philosophical

| ID | Persona | Behavioral signature |
|---|---|---|
| `confucius` | Confucius | Relationship-based ethics |
| `seneca` | Seneca | Stoic action; philosophy as practice |
| `machiavelli` | Machiavelli | Realpolitik; power as it is |
| `julius-caesar` | Julius Caesar | Direct action; accept the risk |
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

Run `mindset list` to see all 51 packs.

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

---

## Why "OS"?

BehaviorOS is not an operating system in the traditional sense. It is a **behavioral runtime layer** that:
- Compiles policies into deterministic behavioral directives
- Resolves conflicts between competing character traits
- Injects verifiable, explainable behavior into AI agents

Think of it as an operating system for how agents decide and act — not how they execute code.

---

## Roadmap

### Phase 1 ✅ — Runtime (v0.1–v0.2)
- CLI with `mindset run`, `mindset generate`, `mindset validate`
- FusionEngine: weighted merge of multiple personas
- ConflictResolver: slot-by-slot winner selection with ConditionalSlots
- BehaviorIR: typed intermediate representation with full explain
- Benchmark suite: 4 task classes, 10 assertions, all green
- 51 character packs in standard library

### Phase 2 ✅ — Compiler (v0.3)
- `mindset compile` CLI command
- 8-module pipeline: extraction → normalization → typing → schema mapping → pack builder
- Mock-LLM CI testing (no API keys required)
- Quality Gates: contradictions = 0, coverage ≥ 0.60, evidence ≥ 0.50
- Full test suite: 377 tests, all passing

### Phase 3 ✅ — Compiler Validation & Benchmarking (v0.3–v0.4)
- Benchmark corpus: Steve Jobs, Sun Tzu, Marcus Aurelius with source texts, draft packs, reviewed packs
- Compiler Benchmark Schema with v1 targets
- Correction taxonomy: 5 patterns with P0/P1/P2 fixability
- Validation report and compiled vs. manual comparison

### Phase 4.5 🔥 — Adoption Loop (v0.3.1 — NOW)
**From "system is built" to "system is used."**

| Milestone | Status |
|---|---|
| `mindset run --share` | ✅ Shipping in v0.3.1 |
| Signature Demo | ✅ Built into `--share` |
| `mindset compare` | 🔜 Next |
| Decision Review | 📋 Planned |
| Template pack (`examples/template/`) | 📋 Planned |

### Phase 5 — Behavior Layer
**BehaviorOS as the behavior layer for AI systems.**

- `mindset compare` — system-level behavioral axis comparison across any personas
- Pack Registry — curated, reviewed packs with stable IDs
- Behavior Spec — a format for defining executable decision systems
- Policy Injection Layer — wraps any LLM call, enforces a decision policy before generation
- OpenAI / Ollama adapters

---

## Who Is This For?

- **AI engineers** building agents that need consistent, explainable behavior
- **Agent architects** evaluating how persona mixing actually works
- **Prompt engineers** tired of "prompt personas" that hallucinate identity or collapse under blending
- **Decision thinkers** who want a framework for articulating how different systems approach the same problem

If you want personality hacks that kind of work sometimes → use a regular system prompt.
If you want behavioral contracts that you can verify → try BehaviorOS.

---

## Contribute a Persona Pack

1. `mindset init my-character --type historical` — scaffold the YAML files
2. Fill `sources.yaml` with **3+ public sources** (this is the quality floor)
3. `mindset validate ./my-character` — verify before submitting

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the full authoring guide.

---

## License

MIT

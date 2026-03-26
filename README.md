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
  <img src="https://img.shields.io/badge/v0.3.0-green.svg" alt="v0.3.0">
</p>

> **Naming note:** Product name is **BehaviorOS**. PyPI / package name is `behavior-os`. CLI command is `mindset`.

**BehaviorOS compiles human behavior into executable decision systems.**

## Most AI Personas Are Fake.

> They collapse when you mix them.
> They can't explain why they behave a certain way.
> And worse — they start hallucinating identity.

**BehaviorOS** is different.

---

## This Is Not Persona Prompting. This Is Behavior Compilation.

*Personas describe style. Policies define behavior.*

BehaviorOS compiles character mindsets into **behavioral directives** — not character descriptions. The system resolves conflicts, applies conditional rules, and produces outputs you can actually verify.

**BehaviorOS is NOT:**
- a prompt library
- a persona simulator
- a style transfer tool
- an agent framework

**BehaviorOS IS:**
- a behavior compiler — turns text into executable decision systems
- a decision system runtime — resolves conflicts, applies rules, produces consistent decisions
- a policy layer — enforces behavioral constraints without modifying the model

| # | Stage | What it does |
|---|---|---|
| 1 | CharacterPack(s) | Source character mindsets (mindset, personality, behavior, voice) |
| 2 | FusionEngine | Weighted merge of N characters with deterministic conflict resolution |
| 3 | ConflictResolver | Slot-by-slot winner selection; ConditionalSlot application |
| 4 | BehaviorIR | Typed intermediate representation — every decision is explicit |
| 5 | ClaudeRenderer | Emits behavioral directives, not character descriptions |
| 6 | AI Agent | Executes behavioral directives (Claude CLI, API, or any model) |

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

## From Sources to Behavior Packs

Not just a standard library — **compile your own.**

```bash
# Step 1: Compile sources → draft pack
mindset compile ./examples/steve-jobs/sources.yaml \
  --name "Steve Jobs" --id steve-jobs --output ./build/jobs --explain

# Step 2: Review quality gates in ./build/jobs/_compile_meta.yaml
#         Correct the draft in ./build/jobs/draft-pack/

# Step 3: Validate and run
mindset validate ./build/jobs
mindset run claude --persona ./build/jobs -- "How should I pitch this product?"
```

> **No sources?** Use [`examples/steve-jobs/`](./examples/steve-jobs/) as a reference — it contains a complete end-to-end example with sources, compile output, human review corrections, and the final pack.

See [`examples/steve-jobs/README.md`](./examples/steve-jobs/README.md) for the full walkthrough.

---

## Source → Pack Compiler (Phase 2)

Compile unstructured sources (book excerpts, interviews, speeches, letters) into full Character Packs with provenance tracing and human review.

**From sources to pack in one command:**

```bash
mindset compile sources.yaml \
  --name "Steve Jobs" \
  --id steve-jobs \
  --output ./packs \
  --explain
```

The compiler does not replace the author — it generates a **high-quality first draft** for human review.

**Pipeline:**
```
Sources (txt/md/yaml)
        │
        ▼
[Step 1: LLM Extraction]          ExtractedBehavior[]
[Step 2: LLM Normalization]       CanonicalBehavior[] (clustered, deduplicated)
[Step 2b: Behavior Typing]       behavior_type buffer (core_principle / decision_policy / ...)
[Step 3: Schema Mapping]          SlotWithProvenance[] (→ mindset / personality / behavior / voice)
[Step 4: Pack Builder]            YAML pack files + provenance + review queue
```

**Quality Gate** — every compile produces a `compile_status`:

```yaml
compile_status:
  status: pass | warning | fail
  coverage: 0.78          # weighted slot fill
  evidence: 0.71         # provenance depth
  gates:
    contradictions: 0 → PASS
    coverage: 0.78 ≥ 0.60 → PASS
    evidence: 0.71 ≥ 0.50 → PASS
```

**Review queue** — contradictions and ambiguous mappings are exported as YAML for human resolution before the pack enters the standard library.

See [`docs/compiler-v0-spec.md`](./docs/compiler-v0-spec.md) for full specification.

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `mindset init <id>` | Scaffold a new character pack |
| `mindset compile <sources> --name X --id Y` | **NEW** Compile sources → pack |
| `mindset validate <pack>` | Validate pack against schema |
| `mindset preview <pack>` | Preview Context Block |
| `mindset list` | List available characters |
| `mindset generate <ids...>` | Compile → injectable prompt block |
| `mindset run <runtime> --persona <ids...>` | Compile + inject into agent runtime |

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
| `the-operator` | The Operator | Execution-first; commits at 70% information |

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

## Roadmap

### Phase 1 ✅ — Runtime (v0.1–v0.2)
**Behavior runtime with FusionEngine and ConflictResolver.**

- CLI with `mindset run`, `mindset generate`, `mindset validate`
- FusionEngine: weighted merge of multiple personas
- ConflictResolver: slot-by-slot winner selection with ConditionalSlots
- BehaviorIR: typed intermediate representation with full explain
- Benchmark suite: 4 task classes, 10 assertions, all green
- 51 character packs in standard library

### Phase 2 ✅ — Compiler (v0.3)
**Source → Pack Compiler. Compile unstructured sources into full Character Packs.**

- `mindset compile` CLI command
- 8-module pipeline: extraction → normalization → typing → schema mapping → pack builder
- Mock-LLM CI testing (no API keys required)
- Quality Gates: contradictions, coverage (≥0.60), evidence (≥0.50)
- Provenance tracing through every pipeline stage
- Full test suite: 397 tests, all passing

**See [`docs/compiler-v0-spec.md`](./docs/compiler-v0-spec.md) for the full specification.**

### Phase 3 ✅ — Compiler Validation & Benchmarking (v0.3–v0.4)
**Establish compiler as a measurable, benchmarked system.**

| Milestone | Status | Description |
|---|---|---|
| Benchmark Corpus v0 | ✅ | Steve Jobs, Sun Tzu, Marcus Aurelius — 3 personas with source texts, draft packs, reviewed packs, READMEs |
| Compiler Benchmark Schema | ✅ | [`docs/compiler-benchmark-schema.md`](./docs/compiler-benchmark-schema.md) — v0.1 schema with v1 targets |
| Correction Taxonomy | ✅ | [`docs/compiler-correction-taxonomy.md`](./docs/compiler-correction-taxonomy.md) — 5 patterns, P0/P1/P2 priorities |
| Validation Report | ✅ | [`docs/compiler-validation.md`](./docs/compiler-validation.md) |
| Compiled vs Manual | ✅ | [`docs/validation/steve-jobs-compiled-vs-manual.md`](./docs/validation/steve-jobs-compiled-vs-manual.md) |

### Phase 4 — Compiler v1 (Quality)
**Close the gap from baseline to production-quality compiler.**

**v1 Targets:**

| Metric | v0 Baseline | v1 Target |
|---|---|---|
| Coverage | ~0.25 | ≥ 0.65 |
| Evidence | ~0.00 | ≥ 0.30 |
| Max corrections | 6 | ≤ 4 |
| Behavioral consistency | untested | ≥ 0.90 |
| Behavioral distinctiveness | untested | ≥ baseline threshold |

**Distinctiveness** is measured on three axes:
- **Inter-persona divergence** — Jobs vs Marcus vs Sun Tzu must differ meaningfully on behavioral axes
- **Baseline divergence** — compiled packs must differ from GPT baseline, not collapse to generic
- **Decision divergence** — same input must produce different decision paths and conclusions, not just different writing styles

> A compiler that "improves" by smoothing sharp edges produces average behavior. Jobs packs that sound reasonable are worse than Jobs packs that sound like Jobs.

**v1 Roadmap (P0 → P2):**

- **P0 — Foundation** — Pre-processing (strip metadata headers) + Slot coverage prompt → eliminates parsing artifacts and schema distribution errors
- **P1 — Coverage** — Named concept extraction (second pass for frameworks/models) + Inference guard (mark inferred slots `confidence: low`, `provenance: inferred`, exclude from evidence score)
- **P2 — Sophistication** — Behavioral distinctiveness test + Conditional trigger extraction + Quote preservation

### Phase 4.5 🔥 — Adoption Loop
**From "system is built" to "system is used."**

The compiler works. Now it needs a path into users' hands.

| Milestone | Description |
|---|---|
| **Signature Demo** | "Same input. Different decisions. Because the system is different." — `mindset run` across opposing personas; the demo that makes people forward this to colleagues |
| **Decision Impact Demo** | "You think you're making decisions. You're running a system." — Same candidate profile, three personas, three hiring decisions. Triggers founders, PMs, investors. |
| **Decision Review** | "Why did that decision fail?" — Run your past decision through Jobs / Marcus / Tzu. Get deviation analysis + alternative paths. First use case that creates repeat usage, not just one-time demos. |
| **5-minute quickstart** | `git clone` → `pip install` → `mindset compile` → `mindset run` in 5 minutes |
| **Template pack** | `examples/template/` — starter sources.yaml + README for new authors |
| **Use cases** | Decision simulation · Strategy exploration · Persona alignment · Agent consistency control |
| **Behavior comparison** | `mindset compare <persona1> <persona2>` — cross-persona behavioral axis comparison |
| **Pack sharing** | `docs/packs/` — community-submitted packs with review workflow |
| **Shareable output** | `mindset run --share` — generates a decision summary with `#BehaviorOS` attribution, pasteable into Twitter, Slack, or a blog. Every shared output is a distribution event. |

### Phase 5 — Behavior Layer
**BehaviorOS as the behavior layer for AI systems.**

BehaviorOS aims to become the behavior layer for AI — the way AWS is compute, Stripe is payments, and Twilio is communications.

Initial integration targets:
- **Agent frameworks** — embed behavior runtime into AI agent pipelines
- **Decision copilots** — simulation layer for high-stakes decisions
- **Simulation tools** — multi-persona scenario exploration
- **Policy Injection Layer** — BehaviorOS wraps any LLM call, enforces a decision policy before generation. Think middleware, interceptor, or guardrail — but for decision logic, not content safety.

- `mindset compare` — system-level comparison across any personas
- Pack Registry — curated, reviewed packs with stable IDs
- Pack Diff — version-over-version behavior change detection
- **Behavior Spec** — a Behavior Spec for defining executable decision systems (core_principles, decision_policy, communication). Even v1 is a reference point; the goal is future compatibility with any behavior definition format.
- Embeddable in agent frameworks; policy-as-code for behavior
- OpenAI / Ollama adapters
- Community pack submission pipeline

### What's Next

> We solved behavior. Now the only problem left is getting people to notice.

v1 is the last major engineering milestone. Everything after is adoption.

---

## License

MIT

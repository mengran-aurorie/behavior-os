# Agentic Mindset

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh.md">中文</a>
</p>

<p align="center">
  Load historical figures and fictional characters' mindsets onto any AI agent — plug and play.
</p>

---

## What is Agentic Mindset?

Agentic Mindset is a language-agnostic open source framework for building, managing, and loading the mindsets and personalities of **historical figures** and **fictional characters** onto AI agents.

You define a Character Pack — a small directory of structured YAML files — and the framework fuses one or more characters into a Context Block that can be injected into any agent as a system prompt.

```
Sun Tzu (60%) + Marcus Aurelius (40%)
  →  ConflictResolver → BehaviorIR → ClaudeRenderer  (inject path)
  →  FusionEngine → ContextBlock                      (text path)
  →  AI Agent
```

---

## Features

- **Character Packs** — structured YAML profiles covering mindset, personality, behavior, voice, and sources
- **Fusion Engine** — blend N characters with weighted merging, dominant, or sequential strategies
- **Behavior IR** — deterministic conflict resolver that produces a typed intermediate representation before rendering; inject and text paths are fully separate
- **CLI** — `mindset init`, `validate`, `preview`, `list`, `generate`, `run`
- **Standard Library** — curated historical and fictional characters ready to use
- **Language-agnostic core** — Python SDK included; the data format works with any language

---

## Installation

```bash
pip install agentic-mindset
```

Requires Python 3.11+.

---

## Quick Start

### Use a character from the standard library

```python
from agentic_mindset import CharacterRegistry, FusionEngine

engine = FusionEngine(CharacterRegistry())

context = engine.fuse([
    ("sun-tzu", 0.6),
    ("marcus-aurelius", 0.4),
])

system_prompt = context.to_prompt()
# Inject into your agent:
messages = [{"role": "system", "content": system_prompt}, ...]
```

### Preview via CLI

```bash
mindset preview characters/sun-tzu/
mindset preview --fusion examples/sun-tzu-aurelius.yaml
```

---

## mindset generate — Compile & Inject

`mindset generate` compiles one or more character mindsets into an injectable prompt block. Pure compiler: deterministic, no network requests.

### Single character

```bash
mindset generate sun-tzu
```

### Multi-character fusion with weights

```bash
# Weights are auto-normalized (6,4 → 60%, 40%)
mindset generate sun-tzu marcus-aurelius --weights 6,4
```

### Output formats

```bash
# Plain text (default) — paste directly into any system prompt
mindset generate sun-tzu

# Anthropic API content block — ready to append to the system array
mindset generate sun-tzu --format anthropic-json

# Full debug JSON with metadata
mindset generate sun-tzu marcus-aurelius --weights 6,4 --format debug-json
```

### Fusion strategy

```bash
mindset generate sun-tzu marcus-aurelius --strategy blend       # default
mindset generate sun-tzu marcus-aurelius --strategy dominant
```

### Other options

```bash
--explain          # Print structured YAML to stderr (personas, merged policy, removed conflicts)
--output <path>    # Write to file instead of stdout
--registry <path>  # Override character registry path
```

### `--explain` output

```yaml
personas:
- sun-tzu: 0.6
- marcus-aurelius: 0.4
merged:
  decision_policy: sun-tzu-dominant
  risk_tolerance: high
  time_horizon: long-term
removed_conflicts:
- 'Precision (intensity 0.95): ...'
```

### Python integration (Anthropic API)

```python
import anthropic, subprocess, json

block = json.loads(subprocess.run(
    ["mindset", "generate", "sun-tzu", "--format", "anthropic-json"],
    capture_output=True, text=True
).stdout)

client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    system=[
        {"type": "text", "text": "You are my assistant."},
        block,   # injected mindset
    ],
    messages=[{"role": "user", "content": "How should I approach this negotiation?"}]
)
print(resp.content[0].text)
```

---

## Character Pack Structure

Each character is a directory of six YAML files:

```
sun-tzu/
├── meta.yaml          # Identity, type, schema version
├── mindset.yaml       # Principles, decision framework, mental models
├── personality.yaml   # Traits, emotional tendencies, drives
├── behavior.yaml      # Work patterns, decision speed, conflict style (+ optional anti_patterns)
├── voice.yaml         # Tone, vocabulary, signature phrases
└── sources.yaml       # Source material references
```

Scaffold a new pack:

```bash
mindset init my-character --type historical
```

---

## Fusion Engine

Blend multiple characters using a `fusion.yaml` config:

```yaml
characters:
  - id: sun-tzu
    weight: 0.6
  - id: marcus-aurelius
    weight: 0.4

fusion_strategy: blend      # blend | dominant | sequential
output_format: plain_text   # plain_text | xml_tagged
```

```bash
mindset preview --fusion my-blend.yaml
```

### Fusion Strategies

| Strategy | Behavior |
|---|---|
| `blend` | Weighted merge of all attributes |
| `dominant` | Highest-weight character leads; others fill gaps |
| `sequential` | Characters apply in list order; weights ignored (preview only; not supported in `generate` v0) |

---

## Standard Library

**Historical figures:**

| ID | Name | Tags |
|---|---|---|
| `sun-tzu` | Sun Tzu | strategy, military, philosophy |
| `marcus-aurelius` | Marcus Aurelius | stoicism, philosophy, leadership |
| `confucius` | Confucius | philosophy, ethics, education |
| `seneca` | Seneca | stoicism, philosophy, writing |
| `nikola-tesla` | Nikola Tesla | science, invention, engineering |
| `napoleon-bonaparte` | Napoleon Bonaparte | strategy, leadership, military |
| `leonardo-da-vinci` | Leonardo da Vinci | creativity, science, art |

**Fictional characters:**

| ID | Name | Tags |
|---|---|---|
| `sherlock-holmes` | Sherlock Holmes | deduction, logic, observation |
| `odysseus` | Odysseus | strategy, resilience, cunning |
| `atticus-finch` | Atticus Finch | justice, integrity, empathy |
| `naruto-uzumaki` | Naruto Uzumaki | perseverance, growth, leadership |
| `levi-ackermann` | Levi Ackermann | discipline, precision, duty |
| `gojo-satoru` | Gojo Satoru | confidence, mastery, creativity |

---

## mindset run — Compile & Inject into Claude

`mindset run` compiles mindset(s) and injects them directly into a Claude CLI session via `--append-system-prompt-file`.

```bash
# One-shot query
mindset run claude --persona sun-tzu -- "Analyze competitor strategy"

# Multi-persona fusion with weights
mindset run claude --persona sun-tzu --persona marcus-aurelius --weights 6,4 -- "How should I approach this negotiation?"

# Interactive mode (omit -- QUERY)
mindset run claude --persona sun-tzu

# Print structured YAML summary before launching
mindset run claude --persona sun-tzu --explain -- "query"

# Custom registry
mindset run claude --persona sun-tzu --registry ./my-chars -- "query"
```

### Inject format

The default `--format inject` routes through the **Behavior IR pipeline**:

```
CharacterPack(s)  →  ConflictResolver  →  BehaviorIR  →  ClaudeRenderer  →  system prompt
```

The resolver applies deterministic conflict policies to each behavioral slot (communication style, leadership approach, etc.), producing a typed `BehaviorIR` before the renderer emits the final text. This ensures multi-persona conflicts are resolved predictably, never by raw string concatenation.

The output is a **behavioral instruction block** — actionable directives for the agent rather than a character description:

```
You embody a synthesized mindset drawing from: Sun Tzu (100%).

DECISION POLICY:
- Strategic deception: Misdirect before committing.
- Approach: Win before the battle begins.

UNCERTAINTY HANDLING:
- risk_tolerance: high | time_horizon: long-term
- Stress response: retreat to preparation, reassess terrain.

INTERACTION RULES:
- Communication: indirect, layered
- Leadership: leads through positioning
- Under conflict: avoidant of direct confrontation

STYLE:
- Tone: measured, aphoristic
- Preferred: position, terrain, advantage
- Avoided: rush, obvious
- Sentence style: short aphorisms
```

Use `--format text` to get the plain-text character description instead (uses the `FusionEngine → ContextBlock` path).

### `--explain` on the inject path

`--explain` emits a structured YAML summary to stderr showing how each behavioral slot was resolved:

```yaml
personas:
- sun-tzu: 0.6
- marcus-aurelius: 0.4
slots:
  communication:
    primary:
      value: indirect, layered
      source: sun-tzu
      weight: 0.6
    has_conflict: true
    modifiers: []
    dropped:
    - value: direct and Socratic
      source: marcus-aurelius
      weight: 0.4
      reason: lower_weight
  leadership:
    primary:
      value: leads through positioning
      source: sun-tzu
      weight: 0.6
    has_conflict: false
    modifiers: []
    dropped: []
```

Each slot shows which value won (`primary`), whether a conflict was detected (`has_conflict`), and which values were dropped and why. This makes multi-persona conflict resolution fully transparent and auditable.

### `mindset run` options

| Option | Default | Description |
|---|---|---|
| `<runtime>` | required | Runtime name (v0: `claude` only) |
| `--persona` | required | Character ID. Repeat for multi-persona. |
| `--weights 6,4` | equal | Per-character weights (auto-normalized) |
| `--strategy` | `blend` | `blend` \| `dominant` |
| `--format` | `inject` | `inject` (behavioral block) \| `text` (character description) |
| `--explain` | off | Print structured YAML to stderr (`slots` for inject; `merged` for text) |
| `--registry <path>` | auto | Override character registry path |
| `-- QUERY` | none | One-shot query. Omit for interactive mode. |

---

## CLI Reference

```bash
mindset init <id> --type historical|fictional    # Scaffold a new character pack
mindset validate <path>                          # Validate schema compliance
mindset preview <path>                           # Preview the Context Block output
mindset preview --fusion <fusion.yaml>           # Preview a fusion blend
mindset list                                     # List available characters
mindset generate <id> [id ...]                   # Compile mindset(s) into injectable prompt block
mindset run <runtime> --persona <id>             # Compile & inject into agent runtime
```

### `mindset generate` options

| Option | Default | Description |
|---|---|---|
| `--weights 6,4` | equal | Per-character weights (auto-normalized) |
| `--strategy` | `blend` | `blend` \| `dominant` |
| `--format` | `text` | `text` \| `anthropic-json` \| `debug-json` |
| `--output <path>` | stdout | Write to file instead of stdout |
| `--explain` | off | Print structured YAML to stderr |
| `--registry <path>` | auto | Override character registry path |

---

## Contributing

Character packs for historical figures (deceased) and fictional characters are welcome.

**Requirements:**
- Minimum 3 distinct, publicly accessible source materials in `sources.yaml`
- All five content files present and passing `mindset validate`
- Living persons are not accepted

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full contribution guide.

---

## License

MIT

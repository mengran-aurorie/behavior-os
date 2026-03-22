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
Sun Tzu (60%) + Marcus Aurelius (40%)  →  Context Block  →  AI Agent
```

---

## Features

- **Character Packs** — structured YAML profiles covering mindset, personality, behavior, voice, and sources
- **Fusion Engine** — blend N characters with weighted merging, dominant, or sequential strategies
- **CLI** — `mindset init`, `validate`, `preview`, `list`
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

## Character Pack Structure

Each character is a directory of six YAML files:

```
sun-tzu/
├── meta.yaml          # Identity, type, schema version
├── mindset.yaml       # Principles, decision framework, mental models
├── personality.yaml   # Traits, emotional tendencies, drives
├── behavior.yaml      # Work patterns, decision speed, conflict style
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
| `sequential` | Characters apply in list order; weights ignored |

---

## Standard Library

**Historical figures:**

| ID | Name | Tags |
|---|---|---|
| `sun-tzu` | Sun Tzu | strategy, military, philosophy |
| `marcus-aurelius` | Marcus Aurelius | stoicism, philosophy, leadership |

**Fictional characters** *(coming soon)*:
- `naruto-uzumaki`, `levi-ackermann`, `sherlock-holmes`, `odysseus`, and more

---

## CLI Reference

```bash
mindset init <id> --type historical|fictional   # Scaffold a new character pack
mindset validate <path>                          # Validate schema compliance
mindset preview <path>                           # Preview the Context Block output
mindset preview --fusion <fusion.yaml>           # Preview a fusion blend
mindset list                                     # List available characters
```

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

# Examples — Design Spec

**Date:** 2026-03-23
**Status:** Draft

---

## Overview

Add two runnable end-to-end examples to the `examples/` directory, each with its own README. Together they demonstrate the complete Agentic Mindset workflow: listing characters, compiling mindsets, and injecting them into Claude.

---

## Goals

- Give new users a copy-paste path to running the full CLI workflow in under 5 minutes
- Show both standard-library usage and custom character creation
- Each example is self-contained with its own README

## Non-Goals

- No shell scripts or automation — users run commands manually
- No Python code — CLI-only
- No new CLI features

---

## Directory Structure

```
examples/
├── 01-standard-library/
│   └── README.md
└── 02-custom-character/
    ├── ada-lovelace/
    │   ├── meta.yaml
    │   ├── mindset.yaml
    │   ├── personality.yaml
    │   ├── behavior.yaml
    │   ├── voice.yaml
    │   └── sources.yaml
    └── README.md
```

The existing `examples/sun-tzu-aurelius.yaml` is kept as-is.

---

## Example 01 — Standard Library

**File:** `examples/01-standard-library/README.md`

No additional files needed. All characters used are from the standard library.

### Steps covered

| Step | Command | Purpose |
|---|---|---|
| 1 | `mindset list` | See available characters |
| 2 | `mindset generate sun-tzu` | Compile single character, output to stdout |
| 3 | `mindset generate sun-tzu marcus-aurelius --weights 6,4 --explain` | Multi-character fusion with summary |
| 4 | `mindset run claude --persona sun-tzu -- "Analyze competitor strategy"` | One-shot injection into Claude |
| 5 | `mindset run claude --persona sun-tzu --persona marcus-aurelius --weights 6,4` | Interactive mode — omitting `-- QUERY` launches Claude in a live interactive session |

Each step includes: the exact command, a truncated expected output snippet, and a one-sentence explanation.

---

## Example 02 — Custom Character

**File:** `examples/02-custom-character/README.md`
**Character:** Ada Lovelace (1815–1852) — mathematician and computing pioneer

Ada Lovelace is not in the standard library, is a historical figure (deceased), and has well-documented source material. Her traits (analytical thinking, creativity, systems thinking) make her a compelling demo character for an AI tool.

### Character files

All six YAML files are fully populated (no TODO placeholders):

| File | Key content |
|---|---|
| `meta.yaml` | id: `ada-lovelace`, type: historical, tags: science, mathematics, creativity |
| `mindset.yaml` | Core principles: analytical imagination, first-principles thinking, bridging abstract and concrete |
| `personality.yaml` | Traits: precise, visionary, methodical; drive: understanding underlying systems |
| `behavior.yaml` | Decision speed: deliberate; execution: iterative refinement; conflict: reasoned argument |
| `voice.yaml` | Tone: measured and precise; vocabulary: mathematical metaphors, structured reasoning |
| `sources.yaml` | ≥3 publicly accessible sources |

### Steps covered

All commands in Steps 2–4 are run from `examples/02-custom-character/`. `validate` takes a **directory path** (`ada-lovelace/`); `generate` and `run` take a **character ID** resolved via `--registry .` (which points to `examples/02-custom-character/`, the parent of `ada-lovelace/`).

| Step | Command | Purpose |
|---|---|---|
| 1 | — | Understand the 6-file character structure |
| 2 | `mindset validate ada-lovelace/` | Validate schema — takes a **path** to the character directory |
| 3 | `mindset generate ada-lovelace --registry . --explain` | Compile — takes a **character ID**, registry overridden to current directory |
| 4 | `mindset run claude --persona ada-lovelace --registry . -- "How would you approach this engineering problem?"` | One-shot injection into Claude |
| 5 | `mindset init my-character --type historical` | Scaffold your own character — run from **your own project directory**, not from within `examples/` |

---

## Files Created

| File | Action |
|---|---|
| `examples/01-standard-library/README.md` | Create |
| `examples/02-custom-character/README.md` | Create |
| `examples/02-custom-character/ada-lovelace/meta.yaml` | Create |
| `examples/02-custom-character/ada-lovelace/mindset.yaml` | Create |
| `examples/02-custom-character/ada-lovelace/personality.yaml` | Create |
| `examples/02-custom-character/ada-lovelace/behavior.yaml` | Create |
| `examples/02-custom-character/ada-lovelace/voice.yaml` | Create |
| `examples/02-custom-character/ada-lovelace/sources.yaml` | Create |

No existing files are modified.

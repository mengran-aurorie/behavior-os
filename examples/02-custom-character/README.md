# Example 02 — Custom Character

This example walks through the full workflow for a **custom character**:
validate a character pack, compile it into an injectable prompt block, and
inject it into Claude.

The example character is **Ada Lovelace** (1815–1852) — mathematician and
computing pioneer, widely regarded as the first computer programmer.

---

## Prerequisites

```bash
pip install agentic-mindset
```

All commands below are run from this directory (`examples/02-custom-character/`).

---

## Step 1 — Understand the character structure

Each character is a directory of six YAML files:

```
ada-lovelace/
├── meta.yaml          # Identity, type, schema version, license, visibility
├── mindset.yaml       # Core principles, decision framework (heuristics, default_strategy,
│                      #   fallback_strategy, commitment_policy), mental models
├── personality.yaml   # Traits (+ confidence), emotional tendencies (+ baseline_mood,
│                      #   emotional_range, frustration_trigger, recovery_pattern),
│                      #   Drive objects, ConditionalSlot fields
├── behavior.yaml      # Work patterns, decision_speed, decision_control, conflict style, anti_patterns
├── voice.yaml         # Tone, tone_axes (formality/warmth/intensity/humor), vocabulary, phrases
└── sources.yaml       # Source material references (min 3, + evidence_level)
```

Browse the files in `ada-lovelace/` to see what a complete pack looks like.

---

## Step 2 — Validate the pack

`mindset validate` takes a **path** to a character directory and checks it
against the schema.

```bash
mindset validate ada-lovelace/
```

Expected output:

```
✓ Pack is valid: ada-lovelace
```

---

## Step 3 — Compile the mindset

`mindset generate` takes a **character ID** (directory name without trailing
slash) and resolves it via `--registry`. The `.` means "look for character
directories in the current directory."

```bash
mindset generate ada-lovelace --registry . --explain
```

The `--explain` flag prints a structured YAML summary to stderr before the
prompt block appears on stdout (`generate` uses the text path):

```yaml
personas:
- ada-lovelace: 1.0
merged:
  decision_policy: ada-lovelace-dominant
  risk_tolerance: medium
  time_horizon: long-term
removed_conflicts: []
```

The prompt block (stdout) begins with a section like:

```
You embody a synthesized mindset drawing from: Ada Lovelace (100%).

THINKING FRAMEWORK:
- Analytical imagination: The capacity to see both the abstract structure...
```

---

## Step 4 — Inject into Claude (one-shot)

```bash
mindset run claude --persona ada-lovelace --registry . "How would you approach designing a system you don't fully understand yet?"
```

Claude will respond with Ada Lovelace's behavioral overlay applied — precise,
iterative, first-principles reasoning.

`run` uses `--format inject` by default. This routes through the Behavior IR
pipeline (`ConflictResolver → BehaviorIR → ClaudeRenderer`), producing a
5-section behavioral instruction block rather than a narrative character
description. Add `--explain` to see how each behavioral slot was resolved:

```bash
mindset run claude --persona ada-lovelace --registry . --explain \
  "How would you approach designing a system you don't fully understand yet?"
```

The inject-path `--explain` output (stderr) shows `slots`, not `merged`:

```yaml
personas:
- ada-lovelace: 1.0
slots:
  communication:
    primary:
      value: precise and layered
      source: ada-lovelace
      weight: 1.0
    has_conflict: false
    modifiers: []
    dropped: []
```

**Interactive mode** (omit the query argument to launch a live Claude session):

```bash
mindset run claude --persona ada-lovelace --registry .
```

---

## Step 5 — Create your own character

To scaffold a new character pack in **your own project directory**:

```bash
cd /path/to/your/project
mindset init my-character --type historical
```

This creates a `my-character/` directory with all six YAML files pre-populated
with placeholder values. Edit each file, then validate:

```bash
mindset validate my-character/
```

Once valid, generate and run:

```bash
mindset generate my-character --registry .
mindset run claude --persona my-character --registry . "your query"
```

> **Note:** Run `mindset init` from your own project directory — not from
> inside `examples/`. The command creates files in the current working directory.

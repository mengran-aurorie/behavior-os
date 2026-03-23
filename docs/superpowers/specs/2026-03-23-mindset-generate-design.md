# mindset generate — Design Spec

**Date:** 2026-03-23
**Status:** Approved

---

## Overview

`mindset generate` is a new CLI command that compiles one or more character mindsets into an injectable runtime prompt block. It is a pure compiler: deterministic, no network requests, no agent logic, no side effects.

```
generate: compile mindset(s) into an injectable runtime prompt block
```

The command reuses the existing `CharacterRegistry` → `FusionEngine` → `ContextBlock.to_prompt()` pipeline and exposes the result in formats suitable for direct injection into an AI agent's system prompt.

---

## Goals

- Output a compiled mindset block that can be directly appended to any agent's `system` prompt
- Support single-character and multi-character fusion
- Provide platform-named output formats (`text`, `anthropic-json`, `debug-json`)
- Stay composable: errors to stderr, success to stdout, pipe-safe
- Establish a stable contract that future `--target` extensions (OpenAI, Claude Code) can build on

## Non-Goals (v0)

- No API calls or agent interaction (`mindset run` / `mindset inject` are future commands)
- No `layered` fusion strategy implementation (interface reserved, v1)
- No `--target` platform flag (deferred; `--format anthropic-json` covers the Anthropic case)
- No `--lang python/typescript` code snippet generation (deferred)

---

## Command Interface

```bash
# Single character
mindset generate sun-tzu

# Multi-character fusion with weights (auto-normalized)
mindset generate sun-tzu marcus-aurelius --weights 6,4

# Output format
mindset generate sun-tzu --format anthropic-json
mindset generate sun-tzu --format debug-json

# Fusion strategy
mindset generate sun-tzu levi-ackermann --strategy dominant

# Explain the compilation result
mindset generate sun-tzu marcus-aurelius --explain

# Write to file instead of stdout
mindset generate sun-tzu --output ./system_prompt.txt

# Custom registry path
mindset generate sun-tzu --registry ./my-characters/
```

---

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ids` | positional, 1..N strings | required | Character IDs to compile |
| `--weights` | comma-separated numbers | equal weights | Per-character weights; auto-normalized to sum=1.0 |
| `--strategy` | `blend` \| `dominant` | `blend` | Fusion strategy |
| `--format` | `text` \| `anthropic-json` \| `debug-json` | `text` | Output format |
| `--output` | file path | stdout | Write result to file instead of stdout |
| `--explain` | flag | off | Print compilation summary to stderr before output |
| `--registry` | directory path | registry resolution order | Override character registry path |

---

## Output Formats

### `text` (default)

Plain text, suitable for any system prompt field or pipe operations.

```
You embody a synthesized mindset drawing from the following figures: Sun Tzu (60%), Marcus Aurelius (40%).

THINKING FRAMEWORK:
- All warfare is based on deception; observe before acting
...

PERSONALITY:
- Patient and measured; withdraws to observe under pressure
...
```

### `anthropic-json`

A single Anthropic API content block, ready to append to the `system` array.

```json
{
  "type": "text",
  "text": "You embody a synthesized mindset..."
}
```

Usage in Python:
```python
import subprocess, json

block = json.loads(
    subprocess.run(
        ["mindset", "generate", "sun-tzu", "--format", "anthropic-json"],
        capture_output=True, text=True
    ).stdout
)

client.messages.create(
    model="claude-opus-4-6",
    system=[
        {"type": "text", "text": "You are my assistant."},
        block  # appended mindset
    ],
    messages=[...]
)
```

### `debug-json`

Full JSON with metadata for debugging, caching, and reproducibility.

```json
{
  "meta": {
    "characters": ["sun-tzu", "marcus-aurelius"],
    "weights": [0.6, 0.4],
    "strategy": "blend",
    "schema_version": "1.0",
    "generated_at": "2026-03-23T10:00:00Z"
  },
  "type": "text",
  "text": "You embody a synthesized mindset..."
}
```

---

## Weights

- Accepts any positive real numbers (e.g., `6,4` or `0.6,0.4` or `3,1,1`)
- **Auto-normalized** to sum to 1.0 before fusion
- Duplicate IDs: weights are summed, treated as one character entry
- Count must match number of IDs (error otherwise)

---

## Fusion Strategies

| Strategy | Behavior |
|---|---|
| `blend` (default) | All characters merged by weighted proportions across all fields |
| `dominant` | Highest-weight character leads; others contribute only to fields absent from the dominant pack |
| `layered` | **Reserved — v1.** Per-dimension merge (e.g., Sun Tzu for decision policy, Marcus Aurelius for emotional regulation) |

Internal code must not hard-code a two-strategy enum. The strategy dispatch layer must accept future strategies without structural change.

---

## `--explain` Output

Printed to **stderr** before the compiled block:

```
Characters: sun-tzu (60%), marcus-aurelius (40%)
Strategy:   blend
Format:     text
Schema:     1.0
```

`--explain` does not affect stdout. The compiled block is still written to stdout (or `--output` file) unchanged.

---

## Output Contract

```
Inputs:  1..N character IDs + optional parameters
Output:  deterministic injectable prompt block

Guarantees:
  ✓ Same input always produces same output
  ✓ Errors go to stderr only; exit code non-zero
  ✓ Success output goes to stdout only; exit code 0
  ✓ No network requests
  ✓ No external agent runtime dependency
  ✓ --output writes file; stdout receives nothing on success
```

---

## Error Handling

All error messages go to **stderr**. Exit code is non-zero on any error.

| Scenario | Message |
|---|---|
| Character ID not found | `Error: character 'foo' not found. Run 'mindset list' to see available characters.` |
| `--weights` count mismatch | `Error: --weights has 2 values but 3 character IDs were given.` |
| `--weights` contains negative number | `Error: --weights values must be positive numbers.` |
| `--weights` contains non-numeric value | `Error: --weights must be comma-separated numbers (e.g. --weights 6,4).` |
| `--weights` all zero | `Error: --weights values cannot all be zero.` |
| `--output` path not writable | `Error: cannot write to './path': <reason>.` |
| Duplicate IDs | Weights are summed silently; no error. |

---

## Architecture

### Files Modified

- `agentic_mindset/cli.py` — add `generate` command
- `tests/test_cli.py` — add `generate` test cases

### No New Files Required

`generate` is a thin CLI layer over existing components:

```
mindset generate sun-tzu marcus-aurelius --weights 6,4 --format anthropic-json
        │
        ▼
CharacterRegistry.load_id("sun-tzu"), load_id("marcus-aurelius")
        │
        ▼
FusionEngine.fuse([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)], strategy=blend)
        │
        ▼
ContextBlock.to_prompt(output_format="plain_text")
        │
        ▼
OutputFormatter.format(text, format="anthropic-json")   ← new, in cli.py
        │
        ▼
stdout (or --output file)
```

### `OutputFormatter`

A small private helper in `cli.py` (not a public API):

```python
def _format_output(text: str, fmt: str, meta: dict | None = None) -> str:
    if fmt == "text":
        return text
    if fmt == "anthropic-json":
        return json.dumps({"type": "text", "text": text})
    if fmt == "debug-json":
        return json.dumps({"meta": meta, "type": "text", "text": text}, indent=2, default=str)
```

---

## Integration Example

```bash
# Pipe into a Python one-liner
python3 -c "
import anthropic, subprocess, json
block = json.loads(subprocess.run(
    ['mindset', 'generate', 'sun-tzu', '--format', 'anthropic-json'],
    capture_output=True, text=True
).stdout)
client = anthropic.Anthropic()
resp = client.messages.create(
    model='claude-opus-4-6',
    max_tokens=1024,
    system=[{'type': 'text', 'text': 'You are my assistant.'}, block],
    messages=[{'role': 'user', 'content': 'How should I approach this negotiation?'}]
)
print(resp.content[0].text)
"
```

---

## Future Extensions (out of scope for v0)

- `--target anthropic` / `--target openai` — platform-specific output selection
- `--format openai-system` — OpenAI `system` message JSON
- `--lang python` / `--lang typescript` — full runnable code snippet output
- `layered` fusion strategy
- `mindset run` — compile + call the API in one step
- `mindset inject` — inject into an already-running conversation via MCP

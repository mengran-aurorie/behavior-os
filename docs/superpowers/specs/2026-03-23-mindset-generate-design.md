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
- No `xml_tagged` output format from `ContextBlock.to_prompt()` (deferred); `generate` always uses `plain_text` internally

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
mindset generate sun-tzu levi-ackermann --strategy sequential

# Explain the compilation result (to stderr)
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
| `--weights` | comma-separated positive numbers | equal weights (1 per ID) | Per-character weights; auto-normalized to sum=1.0 |
| `--strategy` | `blend` \| `dominant` \| `sequential` | `blend` | Fusion strategy |
| `--format` | `text` \| `anthropic-json` \| `debug-json` | `text` | Output format |
| `--output` | file path | stdout | Write result to file instead of stdout |
| `--explain` | flag | off | Print compilation summary to stderr before output |
| `--registry` | directory path | see resolution order below | Override character registry path |

### Registry Resolution Order

When `--registry` is not provided, `CharacterRegistry` resolves paths in this priority order:

1. `$AGENTIC_MINDSET_REGISTRY` environment variable (if set)
2. `~/.agentic-mindset/registry/` (user-level default; standard library installs here)
3. `./characters/` (local project fallback)

Local characters override standard library characters of the same ID.

---

## Output Formats

### `text` (default)

Plain text, suitable for any system prompt field or pipe operations. Uses `ContextBlock.to_prompt(output_format="plain_text")` internally.

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

Full JSON with metadata for debugging, caching, and reproducibility. The `schema_version` field is the `generate` output schema version (a constant in the codebase starting at `"1.0"`), not the character pack schema version.

Note: `debug-json` does **not** include a timestamp to preserve the determinism guarantee.

```json
{
  "meta": {
    "characters": ["sun-tzu", "marcus-aurelius"],
    "weights": [0.6, 0.4],
    "strategy": "blend",
    "schema_version": "1.0"
  },
  "type": "text",
  "text": "You embody a synthesized mindset..."
}
```

> If `debug-json` format count grows beyond 3, extract `_format_output` into a dedicated `agentic_mindset/formatter.py` module.

---

## Weights

- Accepts any positive real numbers (e.g., `6,4` or `0.6,0.4` or `3,1,1`)
- **Auto-normalized** to sum to 1.0 before fusion
- Duplicate IDs: weights are summed **before normalization**, deduplicated to one entry
  - Example: `mindset generate sun-tzu sun-tzu` → one entry with weight 1.0 (equivalent to `mindset generate sun-tzu`)
  - Example: `mindset generate sun-tzu sun-tzu --weights 3,7` → one entry with weight 10 (→ normalized 1.0)
- When `--weights` is not provided, each ID defaults to weight `1.0` before normalization
- Count must match the number of **original (pre-deduplication) IDs** provided on the command line (error otherwise)
  - Example: `mindset generate sun-tzu marcus-aurelius --weights 6,4` → valid (2 IDs, 2 weights)
  - Example: `mindset generate sun-tzu marcus-aurelius --weights 6` → error (2 IDs, 1 weight)
- Trailing/leading commas or empty segments are parse errors (e.g., `--weights 6,` or `--weights ,4`)

---

## Fusion Strategies

The `generate` command exposes all three strategies implemented in `FusionEngine`:

| Strategy | Behavior |
|---|---|
| `blend` (default) | All characters merged by weighted proportions across all fields |
| `dominant` | Highest-weight character leads; others contribute only to fields absent from the dominant pack |
| `sequential` | Characters applied in list order; each adds fields not already set; weights ignored (a warning is emitted to stderr if `--weights` is also provided) |
| `layered` | **Reserved — v1.** Per-dimension merge (e.g., Sun Tzu for decision policy, Marcus Aurelius for emotional regulation) |

The strategy dispatch layer must not be hard-coded to a fixed set of values. Future strategies must be addable without structural change.

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

When `--output` and `--explain` are combined: the explain summary goes to stderr, the compiled output goes to the file, and stdout is empty.

---

## Output Contract

```
Inputs:  1..N character IDs + optional parameters
Output:  deterministic injectable prompt block

Guarantees:
  ✓ Same input always produces same prompt text output
  ✓ Errors go to stderr only; exit code 1
  ✓ Success output goes to stdout only; exit code 0
  ✓ No network requests
  ✓ No external agent runtime dependency
  ✓ --output writes file; stdout receives nothing on success
  ✓ ContextBlock always rendered via to_prompt(output_format="plain_text")
```

---

## Error Handling

All error messages go to **stderr**. All errors exit with code **1**.

The `generate` command must catch `KeyError` raised by `CharacterRegistry.load_id()` and transform it into the user-facing message below.

| Scenario | Message (stderr) |
|---|---|
| Character ID not found | `Error: character 'foo' not found. Run 'mindset list' to see available characters.` |
| `--weights` count mismatch | `Error: --weights has 2 values but 3 character IDs were given.` |
| `--weights` contains negative number | `Error: --weights values must be positive numbers.` |
| `--weights` contains non-numeric value or malformed string | `Error: --weights must be comma-separated numbers (e.g. --weights 6,4).` |
| `--weights` all zero | `Error: --weights values cannot all be zero.` |
| `--output` path not writable | `Error: cannot write to './path': <reason>.` |
| `--strategy sequential` with `--weights` provided | CLI emits warning to stderr: `Warning: --weights ignored when --strategy is sequential.` (not an error; proceed). The engine also warns internally for non-equal weights; the CLI warning fires on flag presence alone. Both warnings may appear — this is acceptable in v0. |
| Duplicate IDs | Weights summed silently; no error. |

---

## Architecture

### Files Modified

- `agentic_mindset/cli.py` — add `generate` command with docstring `"""Compile character mindset(s) into an injectable system prompt block."""`
- `tests/test_cli.py` — add `generate` test cases

### No New Files Required (v0)

`generate` is a thin CLI layer over existing components:

```
mindset generate sun-tzu marcus-aurelius --weights 6,4 --format anthropic-json
        │
        ▼
  deduplicate IDs, sum weights, normalize to 1.0
        │
        ▼
CharacterRegistry.load_id("sun-tzu"), load_id("marcus-aurelius")
  (catch KeyError → user-friendly error to stderr, exit 1)
        │
        ▼
FusionEngine.fuse([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)], strategy=blend)
        │
        ▼
ContextBlock.to_prompt(output_format="plain_text")
        │
        ▼
_format_output(text, fmt="anthropic-json", meta={...})   ← private helper in cli.py
        │
        ▼
stdout (or --output file)
```

### `_format_output` helper

A small private helper in `cli.py` (not a public API):

```python
def _format_output(text: str, fmt: str, meta: dict | None = None) -> str:
    if fmt == "text":
        return text
    if fmt == "anthropic-json":
        return json.dumps({"type": "text", "text": text})
    if fmt == "debug-json":
        return json.dumps({"meta": meta, "type": "text", "text": text}, indent=2)
```

---

## Integration Example

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
    system=[{"type": "text", "text": "You are my assistant."}, block],
    messages=[{"role": "user", "content": "How should I approach this negotiation?"}]
)
print(resp.content[0].text)
```

---

## Future Extensions (out of scope for v0)

- `--target anthropic` / `--target openai` — platform-specific output selection
- `--format openai-system` — OpenAI `system` message JSON
- `--format xml` — expose `ContextBlock.to_prompt(output_format="xml_tagged")`
- `--lang python` / `--lang typescript` — full runnable code snippet output
- `layered` fusion strategy
- `mindset run` — compile + call the API in one step
- `mindset inject` — inject into an already-running conversation via MCP
- Extract `_format_output` to `agentic_mindset/formatter.py` when format count exceeds 3

# mindset run — Design Spec

**Date:** 2026-03-23
**Status:** Draft

---

## Overview

`mindset run` is a new CLI command that compiles one or more character mindsets and injects the result into an agent runtime. v0 targets Claude CLI exclusively, using `--append-system-prompt-file` as the injection mechanism.

```
mindset run <runtime> --persona <id> [--persona <id> ...] [options] [-- QUERY]
```

The command is a thin wrapper around the existing `generate` pipeline. It does not reimplement compilation — it delegates to the same `CharacterRegistry → FusionEngine → ContextBlock` chain, then hands the result to the target runtime.

---

## Goals

- Enable `mindset run claude --persona sun-tzu -- "query"` to work end-to-end
- Support both one-shot and interactive modes
- Introduce `--format inject` as the canonical runtime format (converging toward a dedicated Runtime Block in future versions)
- Reuse all existing compilation logic — no duplication

## Non-Goals (v0)

- No API-based invocation (subprocess only)
- No `--format inject` differentiation yet (v0: `inject` and `text` are equivalent)
- Only `claude` is a supported runtime
- No `sequential` strategy (reserved; interface stability uncertain)
- No `layered` strategy

---

## Command Interface

```bash
# One-shot query
mindset run claude --persona sun-tzu -- "Analyze competitor strategy"

# Multi-persona fusion with weights
mindset run claude --persona sun-tzu --persona marcus-aurelius --weights 6,4 -- "How should I approach this negotiation?"

# Interactive mode (omit -- QUERY)
mindset run claude --persona sun-tzu

# Explicit format (v0: text and inject are equivalent)
mindset run claude --persona sun-tzu --format inject -- "query"

# Custom registry
mindset run claude --persona sun-tzu --registry ./my-chars -- "query"
```

---

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `<runtime>` | required (positional) | Runtime name. v0 supports `claude` only. |
| `--persona` | required, repeatable | Character ID. Use multiple flags for multi-persona. |
| `--weights` | equal weights | Comma-separated, auto-normalized. Same rules as `generate`. |
| `--strategy` | `blend` | `blend` \| `dominant` |
| `--format` | `inject` | `text` \| `inject` (v0: equivalent; `inject` reserved for future Runtime Block) |
| `--registry` | auto-resolved | Override character registry path. Same resolution order as `generate`. |
| `--explain` | `False` | Print compilation summary (characters, strategy, format) to stderr before launching Claude. Not written to the temp file and not sent to Claude. |
| `-- QUERY` | none = interactive | Content after `--` is the one-shot query, passed verbatim to Claude. Omit for interactive mode. |

**Mode detection:** if `-- QUERY` is provided, one-shot mode. If omitted, interactive mode.

---

## Internal Execution Flow

Execution has two sequential phases: **compile** and **runtime**.

### Phase 1 — Compile

Reuses the existing `generate` pipeline:

```
--persona × N + --weights + --strategy
        ↓
_parse_weights() + _deduplicate()        ← reuse from cli.py
        ↓
CharacterRegistry.load_id() × N
        ↓
FusionEngine.fuse()
        ↓
render_for_runtime(context_block, fmt)   ← new runtime renderer (see below)
        ↓
write to temp file (fully written and closed before subprocess launch)
```

### Phase 2 — Runtime

```
verify shutil.which("claude") is not None
        ↓
subprocess.run(
    ["claude", "--append-system-prompt-file", tmpfile, query],   # one-shot: query is a single str element
    # or
    ["claude", "--append-system-prompt-file", tmpfile],          # interactive
    check=False,
)
        ↓
propagate Claude's exit code
        ↓
finally: delete temp file (best-effort)
```

**Temp file rules:**
- Written to the system temp directory
- Must be fully written and closed before subprocess launch
- Removed in a `try/finally` block after subprocess returns or on interruption
- Cleanup failure does not override the main process exit code

**Query passthrough:** `QUERY` is passed as a single trailing argument to Claude CLI, verbatim. `mindset run` does not modify, wrap, or prepend anything to the user's query.

---

## `render_for_runtime`

The runtime renderer is the designated boundary between the compiled intermediate representation (IR) and the injectable text. It is not a wrapper around `_format_output` — it is a first-class renderer that accepts a `ContextBlock` directly.

```python
def render_for_runtime(context_block: ContextBlock, fmt: str) -> str:
    """Render a compiled ContextBlock for agent runtime injection.

    v0: 'inject' and 'text' both produce the same plain-text output.
    Future: 'inject' will produce a dedicated Runtime Block format
    (structured decision policy, uncertainty handling, interaction rules,
    anti-patterns, style — with no role-play or identity replacement).
    """
    if fmt in ("text", "inject"):
        return context_block.to_prompt(output_format="plain_text")
    raise ValueError(f"Unknown runtime format: {fmt!r}")
```

Long-term architecture intent:

```
compile → ContextBlock (IR) → render_for_runtime(fmt="inject") → injectable text
```

When `inject` is differentiated in a future version, only `render_for_runtime` needs to change — the compile phase and CLI interface are unaffected.

---

## Error Handling

### Compile-time errors (before Claude is launched)

All printed to stderr, exit code 1.

| Scenario | Message |
|---|---|
| Character ID not found | `Error: character 'foo' not found. Run 'mindset list' to see available characters.` |
| `--weights` count mismatch | `Error: --weights has N values but M character IDs were given.` |
| `--weights` invalid (negative, all-zero, non-numeric, malformed) | Same messages as `generate` |
| Temp file write failure | `Error: failed to write temporary file: <reason>.` |

CLI parsing errors (missing required flags, unrecognized values for `--strategy`) are handled by Typer and may use exit code 2.

### Runtime errors

| Scenario | Behavior |
|---|---|
| `claude` executable not found | `Error: 'claude' not found. Install Claude CLI: https://claude.ai/code` → exit 1 |
| Claude subprocess exits non-zero | Propagate Claude's exit code unchanged |
| Keyboard interruption | Treat as runtime interruption (not compile error); clean up temp file; return exit code 130 (SIGINT convention) |

### Stdout / stderr rules

- `mindset run` errors → stderr (this process only)
- `--explain` output → stderr (this process only)
- Claude subprocess stdout/stderr → passed through without interception or rewriting
- `--explain` is never written to the temp prompt file and is never sent to Claude

### Cleanup

- Temp file is removed in a `try/finally` block
- Cleanup is best-effort
- Cleanup failure does not override the main exit code

---

## Files Modified

| File | Action |
|---|---|
| `agentic_mindset/cli.py` | Add `render_for_runtime()` + `run` command |
| `tests/test_cli.py` | Add `run` test cases |

No new files required for v0.

---

## Test Cases

All subprocess calls are mocked via `unittest.mock.patch("subprocess.run")`.

### Core behavior

| Test | Validates |
|---|---|
| `test_run_single_persona_oneshot` | Compile succeeds; subprocess called with query |
| `test_run_multi_persona_blend` | Two `--persona` flags; weights parsed and normalized |
| `test_run_interactive_mode` | No `-- QUERY`; subprocess called without query arg |
| `test_run_uses_inject_format_by_default` | `render_for_runtime` called with `fmt="inject"` |
| `test_run_query_passed_verbatim` | Query string reaches subprocess unmodified |

### Error paths

| Test | Validates |
|---|---|
| `test_run_unknown_persona_exits_1` | Character not found → stderr + exit 1 |
| `test_run_claude_not_found_exits_1` | `shutil.which` returns None → install hint + exit 1 |
| `test_run_exit_code_propagated` | Subprocess returns exit 42 → `mindset run` exits 42 |

### Temp file lifecycle

| Test | Validates |
|---|---|
| `test_run_tmpfile_cleaned_up` | After subprocess returns, temp file no longer exists |
| `test_run_tmpfile_cleaned_up_on_error` | Subprocess raises exception, temp file still cleaned up |
| `test_run_explain_not_in_tmpfile` | `--explain` content absent from temp file contents |
| `test_run_explain_printed_to_stderr` | `--explain` output present on stderr when flag is set |

### Bonus coverage

| Test | Validates |
|---|---|
| `test_run_duplicate_persona_deduplicated` | `--persona sun-tzu --persona sun-tzu` does not error |
| `test_run_weights_normalized` | `--weights 6,4` → internal weights `[0.6, 0.4]` |

---

## Key Design Principles

- **Inject mindset, don't replace agent.** The temp file appends behavioral overlay — it does not override identity, safety rules, or tool behavior.
- **Thin wrapper.** `run` owns only the subprocess lifecycle. All compilation logic lives in the existing `generate` pipeline.
- **Exit code transparency.** `mindset run` behaves like a shell wrapper: Claude succeeds → you succeed; Claude fails → you fail.
- **`render_for_runtime` is the migration point.** When `inject` is differentiated in v1, only this function changes.

---

## Future Extensions (out of scope for v0)

- `--format inject` producing a dedicated Runtime Block (structured decision policy, no role-play)
- Additional runtimes (`mindset run openai`, `mindset run gemini`)
- API-based invocation (without Claude CLI dependency)
- `mindset inject claude --mode subagent` → outputs `.claude/agents/<agent>.md`
- `mindset inject claude --mode skill` → outputs `skills/<mindset>/SKILL.md`

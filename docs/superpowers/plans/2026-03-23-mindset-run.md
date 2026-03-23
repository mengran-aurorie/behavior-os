# `mindset run` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `mindset run <runtime> --persona <id> [-- QUERY]` command that compiles mindsets and injects them into Claude CLI via `--append-system-prompt-file`.

**Architecture:** `run` is a thin wrapper around the existing `generate` pipeline. It adds `render_for_runtime(context_block, fmt)` as the designated IR→injectable-text boundary, writes compiled output to a tempfile, then calls `subprocess.run(["claude", "--append-system-prompt-file", tmpfile, ...])`. All compilation logic is reused from `generate`; `run` only owns the subprocess lifecycle.

**Tech Stack:** Python, Typer, `subprocess`, `shutil`, `tempfile`, `unittest.mock.patch` for tests.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `agentic_mindset/cli.py` | Modify | Add `import subprocess, shutil, tempfile`; add `render_for_runtime()`; add `run` command |
| `tests/test_cli.py` | Modify | Add `run` test cases; import `os`, `unittest.mock.patch`, `MagicMock` |

No new files required (v0).

---

## Shared Test Infrastructure

All `run` tests need:
1. The existing `gen_registry` fixture (already in `tests/test_cli.py`)
2. Mocked `subprocess.run` — patch path: `"agentic_mindset.cli.subprocess.run"`
3. Mocked `shutil.which` — patch path: `"agentic_mindset.cli.shutil.which"`

Add these imports to `tests/test_cli.py` (at the top, alongside existing imports):
```python
import os
from unittest.mock import patch, MagicMock
```

A typical test body looks like:
```python
def test_run_xxx(gen_registry):
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                "my query",          # trailing positional = one-shot query
            ])
    assert result.exit_code == 0
    mock_sub.assert_called_once()
```

---

## Task 1: `render_for_runtime` helper + new imports

**Files:**
- Modify: `agentic_mindset/cli.py`
- Test: `tests/test_cli.py`

This is the designated boundary between `ContextBlock` (IR) and injectable text. In v0, `inject` and `text` both produce `plain_text`. The function accepts a `ContextBlock` directly — not a pre-rendered string.

- [ ] **Step 1: Add failing tests**

Add to `tests/test_cli.py`. Update the import line to include `render_for_runtime`:
```python
from agentic_mindset.cli import app, _format_output, render_for_runtime
```

Add these tests after the existing `test_format_output_*` tests:
```python
def test_render_for_runtime_inject(minimal_pack_dir):
    from agentic_mindset.pack import CharacterPack
    from agentic_mindset.context import ContextBlock
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    result = render_for_runtime(block, "inject")
    assert "THINKING FRAMEWORK" in result
    assert isinstance(result, str)

def test_render_for_runtime_text_equals_inject(minimal_pack_dir):
    from agentic_mindset.pack import CharacterPack
    from agentic_mindset.context import ContextBlock
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    assert render_for_runtime(block, "text") == render_for_runtime(block, "inject")

def test_render_for_runtime_unknown_fmt_raises(minimal_pack_dir):
    from agentic_mindset.pack import CharacterPack
    from agentic_mindset.context import ContextBlock
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    with pytest.raises(ValueError, match="Unknown runtime format"):
        render_for_runtime(block, "xml")
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /Users/aurorie/workspace/aurorie/agentic-mindset && python -m pytest tests/test_cli.py::test_render_for_runtime_inject -v
```

Expected: `ImportError` — `render_for_runtime` not yet defined.

- [ ] **Step 3: Add imports and `render_for_runtime` to `cli.py`**

Add to the imports block (after `import json`):
```python
import shutil
import subprocess
import tempfile
```

Add this function right after `_format_output` (before `_TEMPLATE_META`):
```python
def render_for_runtime(context_block: ContextBlock, fmt: str) -> str:
    """Render a compiled ContextBlock for agent runtime injection.

    v0: 'inject' and 'text' both produce plain-text output.
    Future: 'inject' will become a dedicated Runtime Block format.
    """
    if fmt in ("text", "inject"):
        return context_block.to_prompt(output_format="plain_text")
    raise ValueError(f"Unknown runtime format: {fmt!r}")
```

- [ ] **Step 4: Run to confirm pass**

```bash
python -m pytest tests/test_cli.py::test_render_for_runtime_inject tests/test_cli.py::test_render_for_runtime_text_equals_inject tests/test_cli.py::test_render_for_runtime_unknown_fmt_raises -v
```

Expected: 3 PASSED.

- [ ] **Step 5: Full suite check**

```bash
python -m pytest tests/test_cli.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add agentic_mindset/cli.py tests/test_cli.py
git commit -m "feat: add render_for_runtime helper and subprocess imports"
```

---

## Task 2: `run` command — happy path

**Files:**
- Modify: `agentic_mindset/cli.py`
- Test: `tests/test_cli.py`

This is the main implementation task. The `run` command:
1. Compiles via the existing `generate` pipeline
2. Writes to a tempfile (fully closed before subprocess)
3. Checks `shutil.which("claude")`
4. Calls `subprocess.run(["claude", "--append-system-prompt-file", tmpfile, ...], check=False)`
5. Propagates Claude's exit code
6. Deletes tmpfile in `finally`

Add these imports to `tests/test_cli.py`:
```python
import os
from unittest.mock import patch, MagicMock
```

- [ ] **Step 1: Write failing tests**

```python
def test_run_single_persona_oneshot(gen_registry):
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                "Analyze competitor strategy",
            ])
    assert result.exit_code == 0
    mock_sub.assert_called_once()
    call_args = mock_sub.call_args[0][0]
    assert call_args[0] == "claude"
    assert "--append-system-prompt-file" in call_args
    assert "Analyze competitor strategy" in call_args

def test_run_uses_inject_format_by_default(gen_registry):
    """--format defaults to inject."""
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            with patch("agentic_mindset.cli.render_for_runtime", wraps=render_for_runtime) as mock_render:
                mock_sub.return_value = MagicMock(returncode=0)
                runner.invoke(app, [
                    "run", "claude",
                    "--persona", "sun-tzu",
                    "--registry", str(gen_registry),
                    "query",
                ])
    mock_render.assert_called_once()
    _, kwargs = mock_render.call_args if mock_render.call_args.kwargs else (mock_render.call_args[0], {})
    called_fmt = mock_render.call_args[1].get("fmt") or mock_render.call_args[0][1]
    assert called_fmt == "inject"

def test_run_query_passed_verbatim(gen_registry):
    """Query string reaches Claude subprocess exactly as typed."""
    query = "How do I handle a negotiation under pressure?"
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                query,
            ])
    call_args = mock_sub.call_args[0][0]
    assert query in call_args
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_cli.py::test_run_single_persona_oneshot -v
```

Expected: FAIL — `run` command not found.

- [ ] **Step 3: Implement `run` command in `cli.py`**

Add this after the `generate` command (end of file). Also add `render_for_runtime` to the import line in `tests/test_cli.py` if not already there.

```python
@app.command()
def run(
    runtime: str = typer.Argument(..., help="Runtime name (v0: claude only)"),
    persona: list[str] = typer.Option(..., "--persona", help="Character ID. Repeat for multi-persona."),
    weights: Optional[str] = typer.Option(None, "--weights", help="Comma-separated weights, auto-normalized"),
    strategy: str = typer.Option("blend", "--strategy", help="blend | dominant"),
    format_: str = typer.Option("inject", "--format", help="text | inject (v0: equivalent)"),
    registry: Optional[Path] = typer.Option(None, "--registry", help="Override registry path"),
    explain: bool = typer.Option(False, "--explain", help="Print compilation summary to stderr"),
    query: Optional[str] = typer.Argument(None, help="One-shot query. Omit for interactive mode."),
):
    """Compile mindset(s) and inject into an agent runtime."""
    # --- compile phase ---
    search_paths = [registry] if registry else None
    reg = CharacterRegistry(search_paths=search_paths)

    parsed_weights = _parse_weights(weights, persona)
    if parsed_weights is None:
        raise typer.Exit(1)

    ids_deduped, weights_deduped = _deduplicate(persona, parsed_weights)

    missing_cid = None
    for cid in ids_deduped:
        try:
            reg.load_id(cid)
        except KeyError:
            missing_cid = cid
            break
    if missing_cid is not None:
        typer.echo(
            f"Error: character '{missing_cid}' not found. Run 'mindset list' to see available characters.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        strat = FusionStrategy(strategy)
    except ValueError:
        typer.echo(f"Error: unknown strategy '{strategy}'.", err=True)
        raise typer.Exit(1)

    engine = FusionEngine(reg)
    chars = list(zip(ids_deduped, weights_deduped))
    block = engine.fuse(chars, strategy=strat)
    injected = render_for_runtime(block, fmt=format_)

    # --- explain (before subprocess, after compile) ---
    if explain:
        pct = [f"{cid} ({w*100:.0f}%)" for cid, w in zip(ids_deduped, weights_deduped)]
        typer.echo(f"Characters: {', '.join(pct)}", err=True)
        typer.echo(f"Strategy:   {strategy}", err=True)
        typer.echo(f"Format:     {format_}", err=True)

    # --- write temp file ---
    fd, tmppath = tempfile.mkstemp(suffix=".txt", prefix="mindset_run_")
    try:
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(injected)
        except OSError as e:
            typer.echo(f"Error: failed to write temporary file: {e}.", err=True)
            raise typer.Exit(1)

        # --- runtime phase ---
        if shutil.which(runtime) is None:
            typer.echo(
                f"Error: '{runtime}' not found. Install Claude CLI: https://claude.ai/code",
                err=True,
            )
            raise typer.Exit(1)

        cmd = [runtime, "--append-system-prompt-file", tmppath]
        if query is not None:
            cmd.append(query)

        proc = subprocess.run(cmd, check=False)
        raise typer.Exit(proc.returncode)

    finally:
        try:
            os.unlink(tmppath)
        except OSError:
            pass  # best-effort cleanup
```

Note: `os` is not yet imported. Add `import os` to the imports block in `cli.py`.

- [ ] **Step 4: Run to confirm pass**

```bash
python -m pytest tests/test_cli.py::test_run_single_persona_oneshot tests/test_cli.py::test_run_query_passed_verbatim -v
```

Expected: 2 PASSED. (The `inject_format_by_default` test may need adjustment based on how you mock `render_for_runtime` — see note below.)

> **Note on `test_run_uses_inject_format_by_default`:** If wrapping `render_for_runtime` is tricky, a simpler alternative is to assert the tmpfile contains the same content as `render_for_runtime(block, "inject")` — i.e., `THINKING FRAMEWORK` is present. Replace the test with:
> ```python
> def test_run_uses_inject_format_by_default(gen_registry):
>     captured = {}
>     original_render = render_for_runtime
>     def spy(block, fmt):
>         captured["fmt"] = fmt
>         return original_render(block, fmt)
>     with patch("agentic_mindset.cli.render_for_runtime", side_effect=spy):
>         with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
>             with patch("agentic_mindset.cli.subprocess.run", return_value=MagicMock(returncode=0)):
>                 runner.invoke(app, ["run", "claude", "--persona", "sun-tzu",
>                                     "--registry", str(gen_registry), "q"])
>     assert captured.get("fmt") == "inject"
> ```

- [ ] **Step 5: Run full suite**

```bash
python -m pytest tests/test_cli.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add agentic_mindset/cli.py tests/test_cli.py
git commit -m "feat: add run command — single persona one-shot happy path"
```

---

## Task 3: Multi-persona and interactive mode tests

**Files:**
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write tests**

```python
def test_run_multi_persona_blend(gen_registry):
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--persona", "marcus-aurelius",
                "--weights", "6,4",
                "--registry", str(gen_registry),
                "query",
            ])
    assert result.exit_code == 0
    mock_sub.assert_called_once()

def test_run_interactive_mode(gen_registry):
    """No query argument → interactive mode → subprocess called without query."""
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
            ])
    assert result.exit_code == 0
    call_args = mock_sub.call_args[0][0]
    # last element must NOT be a query string — only 3 elements: runtime, flag, tmpfile
    assert len(call_args) == 3
    assert call_args[0] == "claude"
    assert call_args[1] == "--append-system-prompt-file"
```

- [ ] **Step 2: Run to confirm pass**

```bash
python -m pytest tests/test_cli.py::test_run_multi_persona_blend tests/test_cli.py::test_run_interactive_mode -v
```

Expected: 2 PASSED.

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: add run multi-persona and interactive mode tests"
```

---

## Task 4: Error handling tests

**Files:**
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write tests**

```python
def test_run_unknown_persona_exits_1(gen_registry):
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run"):
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "nonexistent-char",
                "--registry", str(gen_registry),
                "query",
            ])
    assert result.exit_code == 1
    assert "nonexistent-char" in result.stderr
    assert "mindset list" in result.stderr

def test_run_claude_not_found_exits_1(gen_registry):
    with patch("agentic_mindset.cli.shutil.which", return_value=None):
        with patch("agentic_mindset.cli.subprocess.run"):
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                "query",
            ])
    assert result.exit_code == 1
    assert "not found" in result.stderr
    assert "claude.ai" in result.stderr
```

- [ ] **Step 2: Run to confirm pass**

```bash
python -m pytest tests/test_cli.py::test_run_unknown_persona_exits_1 tests/test_cli.py::test_run_claude_not_found_exits_1 -v
```

Expected: 2 PASSED.

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: add run error handling tests — persona not found, claude not found"
```

---

## Task 5: Tmpfile lifecycle and `--explain` tests

**Files:**
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write tests**

```python
def test_run_tmpfile_cleaned_up(gen_registry):
    """Temp file must not exist after subprocess returns."""
    captured_path = []

    def capture_tmpfile(args, **kwargs):
        # args = ["claude", "--append-system-prompt-file", "<path>", ...]
        captured_path.append(args[2])
        return MagicMock(returncode=0)

    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run", side_effect=capture_tmpfile):
            runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                "query",
            ])

    assert captured_path, "subprocess was never called"
    assert not os.path.exists(captured_path[0]), "tmpfile was not cleaned up"

def test_run_tmpfile_cleaned_up_on_error(gen_registry):
    """Temp file must be cleaned up even if subprocess raises."""
    captured_path = []

    def capture_and_raise(args, **kwargs):
        captured_path.append(args[2])
        raise RuntimeError("subprocess exploded")

    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run", side_effect=capture_and_raise):
            runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                "query",
            ])

    assert captured_path, "subprocess was never called"
    assert not os.path.exists(captured_path[0]), "tmpfile was not cleaned up on error"

def test_run_explain_not_in_tmpfile(gen_registry):
    """--explain output must NOT be written to the temp file."""
    tmpfile_content = []

    def capture_content(args, **kwargs):
        path = args[2]
        tmpfile_content.append(open(path).read())
        return MagicMock(returncode=0)

    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run", side_effect=capture_content):
            runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--explain",
                "--registry", str(gen_registry),
                "query",
            ])

    assert tmpfile_content, "subprocess was never called"
    content = tmpfile_content[0]
    assert "Characters:" not in content
    assert "Strategy:" not in content

def test_run_explain_printed_to_stderr(gen_registry):
    """--explain prints compilation summary to stderr."""
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run", return_value=MagicMock(returncode=0)):
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--explain",
                "--registry", str(gen_registry),
                "query",
            ])
    assert result.exit_code == 0
    assert "sun-tzu" in result.stderr
    assert "blend" in result.stderr
```

- [ ] **Step 2: Run to confirm pass**

```bash
python -m pytest tests/test_cli.py::test_run_tmpfile_cleaned_up tests/test_cli.py::test_run_tmpfile_cleaned_up_on_error tests/test_cli.py::test_run_explain_not_in_tmpfile tests/test_cli.py::test_run_explain_printed_to_stderr -v
```

Expected: 4 PASSED. If `test_run_tmpfile_cleaned_up_on_error` fails, it means the `try/finally` block in `run` doesn't catch the subprocess exception — wrap `subprocess.run` call in a try/except that still lets the `finally` run (Python's `finally` always runs, so this should work already).

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: add tmpfile lifecycle and --explain isolation tests for run"
```

---

## Task 6: Exit code propagation and bonus tests

**Files:**
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write tests**

```python
def test_run_exit_code_propagated(gen_registry):
    """Claude's exit code is propagated unchanged."""
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run", return_value=MagicMock(returncode=42)):
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                "query",
            ])
    assert result.exit_code == 42

def test_run_duplicate_persona_deduplicated(gen_registry):
    """Duplicate --persona flags produce same result as single."""
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run", return_value=MagicMock(returncode=0)):
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                "query",
            ])
    assert result.exit_code == 0

def test_run_weights_normalized(gen_registry):
    """--weights 6,4 are normalized to 0.6, 0.4 internally."""
    captured_content = []

    def capture(args, **kwargs):
        path = args[2]
        captured_content.append(open(path).read())
        return MagicMock(returncode=0)

    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run", side_effect=capture):
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--persona", "marcus-aurelius",
                "--weights", "6,4",
                "--registry", str(gen_registry),
                "query",
            ])
    assert result.exit_code == 0
    # Weights normalized → compiled block is non-empty
    assert captured_content and len(captured_content[0]) > 0
```

- [ ] **Step 2: Run to confirm pass**

```bash
python -m pytest tests/test_cli.py::test_run_exit_code_propagated tests/test_cli.py::test_run_duplicate_persona_deduplicated tests/test_cli.py::test_run_weights_normalized -v
```

Expected: 3 PASSED.

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: add exit code propagation and bonus tests for run"
```

---

## Task 7: Full regression pass

- [ ] **Step 1: Run complete test suite**

```bash
cd /Users/aurorie/workspace/aurorie/agentic-mindset && python -m pytest tests/ -v
```

Expected: all tests pass. No regressions in `test_pack.py`, `test_registry.py`, `test_fusion.py`, `test_context.py`, or schema tests.

- [ ] **Step 2: Commit if any fixes needed**

```bash
git add agentic_mindset/cli.py tests/test_cli.py
git commit -m "fix: regression fixes for mindset run"
```

---

## Summary of changes

### `agentic_mindset/cli.py`
- Add `import os, shutil, subprocess, tempfile`
- Add `render_for_runtime(context_block: ContextBlock, fmt: str) -> str`
- Add `@app.command() run(...)` with full parameter set and subprocess lifecycle

### `tests/test_cli.py`
- Add `import os` and `from unittest.mock import patch, MagicMock`
- Update import: add `render_for_runtime`
- Add 14 test cases across 6 task groups

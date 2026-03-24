from __future__ import annotations
from pathlib import Path
from typing import Optional
import json
import os
import shutil
import subprocess
import tempfile
import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from agentic_mindset.pack import CharacterPack, PackLoadError
from agentic_mindset.registry import CharacterRegistry
from agentic_mindset.fusion import FusionEngine, FusionStrategy
from agentic_mindset.context import ContextBlock

app = typer.Typer(name="mindset", help="Agentic Mindset CLI")
console = Console()

_GENERATE_SCHEMA_VERSION = "1.0"


def _format_output(text: str, fmt: str, meta: dict | None = None) -> str:
    if fmt == "text":
        return text
    if fmt == "anthropic-json":
        return json.dumps({"type": "text", "text": text})
    if fmt == "debug-json":
        return json.dumps({"meta": meta, "type": "text", "text": text}, indent=2)
    raise ValueError(f"Unknown output format: {fmt!r}")


def render_for_runtime(context_block: ContextBlock, fmt: str) -> str:
    """Render a compiled ContextBlock for agent runtime injection.

    v0: 'inject' and 'text' both produce plain-text output.
    Future: 'inject' will become a dedicated Runtime Block format.
    """
    if fmt in ("text", "inject"):
        return context_block.to_prompt(output_format="plain_text")
    raise ValueError(f"Unknown runtime format: {fmt!r}")


_TEMPLATE_META = {
    "id": "{id}",
    "name": "{name}",
    "version": "1.0.0",
    "schema_version": "1.0",
    "type": "{type}",
    "description": "TODO: describe this character",
    "tags": [],
    "authors": [{"name": "TODO", "url": ""}],
    "created": "{today}",
}
_TEMPLATE_MINDSET = {
    "core_principles": [{"description": "TODO", "detail": "TODO"}],
    "decision_framework": {"risk_tolerance": "medium", "time_horizon": "long-term", "approach": "TODO"},
    "thinking_patterns": ["TODO"],
    "mental_models": [{"name": "TODO", "description": "TODO"}],
}
_TEMPLATE_PERSONALITY = {
    "traits": [{"name": "TODO", "description": "TODO", "intensity": 0.5}],
    "emotional_tendencies": {"stress_response": "TODO", "motivation_source": "TODO"},
    "interpersonal_style": {"communication": "TODO", "leadership": "TODO"},
    "drives": ["TODO"],
}
_TEMPLATE_BEHAVIOR = {
    "work_patterns": ["TODO"],
    "decision_speed": "deliberate",
    "execution_style": ["TODO"],
    "conflict_style": "TODO",
}
_TEMPLATE_VOICE = {
    "tone": "TODO",
    "vocabulary": {"preferred": [], "avoided": []},
    "sentence_style": "TODO",
    "signature_phrases": [],
}
_TEMPLATE_SOURCES = {
    "sources": [
        {"title": "TODO source 1", "type": "book", "accessed": "2026-01-01"},
        {"title": "TODO source 2", "type": "book", "accessed": "2026-01-01"},
        {"title": "TODO source 3", "type": "book", "accessed": "2026-01-01"},
    ]
}


@app.command()
def init(
    character_id: str = typer.Argument(..., help="Character ID (kebab-case)"),
    type_: str = typer.Option("historical", "--type", help="historical or fictional"),
    output: Optional[Path] = typer.Option(None, "--output", help="Directory to create pack in"),
):
    """Scaffold a new empty character pack."""
    from datetime import date
    out_dir = (output or Path(".")) / character_id
    if type_ not in ("historical", "fictional"):
        console.print(f"[red]--type must be 'historical' or 'fictional', got: {type_!r}[/red]")
        raise typer.Exit(1)
    if out_dir.exists():
        console.print(f"[red]Directory already exists: {out_dir}[/red]")
        raise typer.Exit(1)
    out_dir.mkdir(parents=True)

    name = character_id.replace("-", " ").title()
    today = date.today().isoformat()

    def _render(template: dict) -> dict:
        s = json.dumps(template)
        s = s.replace("{id}", character_id).replace("{name}", name)
        s = s.replace("{type}", type_).replace("{today}", today)
        return json.loads(s)

    files = {
        "meta.yaml": _render(_TEMPLATE_META),
        "mindset.yaml": _TEMPLATE_MINDSET,
        "personality.yaml": _TEMPLATE_PERSONALITY,
        "behavior.yaml": _TEMPLATE_BEHAVIOR,
        "voice.yaml": _TEMPLATE_VOICE,
        "sources.yaml": _TEMPLATE_SOURCES,
    }
    for fname, data in files.items():
        (out_dir / fname).write_text(yaml.dump(data, allow_unicode=True))

    console.print(f"[green]Created character pack:[/green] {out_dir}")


@app.command()
def validate(
    pack_path: Path = typer.Argument(..., help="Path to character pack directory"),
):
    """Validate a character pack against the schema."""
    try:
        CharacterPack.load(pack_path)
        console.print(f"[green]✓ Pack is valid:[/green] {pack_path}")
    except PackLoadError as e:
        console.print(f"[red]✗ Validation failed:[/red]\n{e}")
        raise typer.Exit(1)


@app.command()
def preview(
    pack_path: Optional[Path] = typer.Argument(None, help="Path to a single character pack"),
    fusion_config: Optional[Path] = typer.Option(None, "--fusion", help="Path to fusion.yaml"),
    output_format: str = typer.Option("plain_text", "--format", help="plain_text or xml_tagged"),
    registry_path: Optional[Path] = typer.Option(None, "--registry", help="Override registry path"),
):
    """Preview the Context Block for a character or fusion."""
    if pack_path is None and fusion_config is None:
        console.print("[red]Provide either a pack path or --fusion config.[/red]")
        raise typer.Exit(1)

    if pack_path:
        pack = CharacterPack.load(pack_path)
        block = ContextBlock.from_packs([(pack, 1.0)])
    else:
        cfg = yaml.safe_load(fusion_config.read_text(encoding="utf-8"))
        search_paths = [registry_path] if registry_path else None
        registry = CharacterRegistry(search_paths=search_paths)
        engine = FusionEngine(registry)
        chars = [(c["id"], c["weight"]) for c in cfg["characters"]]
        strategy = FusionStrategy(cfg.get("fusion_strategy", "blend"))
        block = engine.fuse(chars, strategy=strategy)

    console.print(Panel(block.to_prompt(output_format=output_format), title="Context Block"))


def _parse_weights(weights_str: Optional[str], ids: list[str]) -> Optional[list[float]]:
    """Parse --weights string into a list of floats. Prints errors to stderr and returns None on failure."""
    if weights_str is None:
        return [1.0] * len(ids)

    # reject trailing/leading commas or empty segments
    if weights_str.startswith(",") or weights_str.endswith(",") or ",," in weights_str:
        typer.echo(
            "Error: --weights must be comma-separated numbers (e.g. --weights 6,4).",
            err=True,
        )
        return None

    parts = weights_str.split(",")

    # count must match number of original IDs
    if len(parts) != len(ids):
        typer.echo(
            f"Error: --weights has {len(parts)} values but {len(ids)} character IDs were given.",
            err=True,
        )
        return None

    parsed: list[float] = []
    for part in parts:
        try:
            val = float(part)
        except ValueError:
            typer.echo(
                "Error: --weights must be comma-separated numbers (e.g. --weights 6,4).",
                err=True,
            )
            return None
        if val < 0:
            typer.echo("Error: --weights values must be positive numbers.", err=True)
            return None
        parsed.append(val)

    if all(w == 0.0 for w in parsed):
        typer.echo("Error: --weights values cannot all be zero.", err=True)
        return None

    return parsed


def _deduplicate(ids: list[str], weights: list[float]) -> tuple[list[str], list[float]]:
    """Merge duplicate IDs by summing their weights, then normalize to sum=1.0."""
    merged: dict[str, float] = {}
    for cid, w in zip(ids, weights):
        merged[cid] = merged.get(cid, 0.0) + w

    total = sum(merged.values())
    ids_out = list(merged.keys())
    weights_out = [merged[cid] / total for cid in ids_out]
    return ids_out, weights_out


@app.command("list")
def list_characters(
    registry: Optional[Path] = typer.Option(None, "--registry", help="Override registry path"),
):
    """List available characters in the registry."""
    search_paths = [registry] if registry else None
    reg = CharacterRegistry(search_paths=search_paths)
    ids = reg.list_ids()
    if not ids:
        console.print("[yellow]No characters found.[/yellow]")
    for cid in ids:
        console.print(f"  {cid}")


@app.command()
def generate(
    ids: list[str] = typer.Argument(..., help="Character IDs to compile"),
    weights: Optional[str] = typer.Option(None, "--weights", help="Comma-separated weights"),
    strategy: str = typer.Option("blend", "--strategy", help="blend | dominant"),
    format_: str = typer.Option("text", "--format", help="text | anthropic-json | debug-json"),
    output: Optional[Path] = typer.Option(None, "--output", help="Write to file instead of stdout"),
    explain: bool = typer.Option(False, "--explain", help="Print compilation summary to stderr"),
    registry: Optional[Path] = typer.Option(None, "--registry", help="Override registry path"),
):
    """Compile character mindset(s) into an injectable system prompt block."""
    search_paths = [registry] if registry else None
    reg = CharacterRegistry(search_paths=search_paths)

    # --- parse and validate weights ---
    parsed_weights = _parse_weights(weights, ids)
    if parsed_weights is None:
        raise typer.Exit(1)

    # --- deduplicate IDs, summing weights ---
    ids_deduped, weights_deduped = _deduplicate(ids, parsed_weights)

    # --- load characters (validate existence) ---
    # Note: reg.load_id() is called here for early validation with a clear error message.
    # FusionEngine.fuse() takes (id, weight) pairs and re-loads from registry internally.
    # This double-load is intentional: the validation pass gives a targeted error before
    # any fusion work begins.
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

    # --- fuse ---
    engine = FusionEngine(reg)

    if strategy == "sequential":
        typer.echo("Error: --strategy sequential is not supported in v0.", err=True)
        raise typer.Exit(1)

    try:
        strat = FusionStrategy(strategy)
    except ValueError:
        typer.echo(f"Error: unknown strategy '{strategy}'.", err=True)
        raise typer.Exit(1)

    chars = list(zip(ids_deduped, weights_deduped))
    block = engine.fuse(chars, strategy=strat)
    text = block.to_prompt(output_format="plain_text")

    # --- format ---
    meta = {
        "characters": ids_deduped,
        "weights": weights_deduped,
        "strategy": strategy,
        "schema_version": _GENERATE_SCHEMA_VERSION,
    }
    result_str = _format_output(text, format_, meta=meta)

    # --- explain ---
    if explain:
        pct = [f"{cid} ({w*100:.0f}%)" for cid, w in zip(ids_deduped, weights_deduped)]
        typer.echo(f"Characters: {', '.join(pct)}", err=True)
        typer.echo(f"Strategy:   {strategy}", err=True)
        typer.echo(f"Format:     {format_}", err=True)
        typer.echo(f"Schema:     {_GENERATE_SCHEMA_VERSION}", err=True)

    # --- output ---
    if output:
        try:
            output.write_text(result_str, encoding="utf-8")
        except OSError as e:
            typer.echo(f"Error: cannot write to '{output}': {e}.", err=True)
            raise typer.Exit(1)
    else:
        typer.echo(result_str)


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

    if strategy == "sequential":
        typer.echo("Error: --strategy sequential is not supported by 'run' (v0).", err=True)
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

    # --- explain (before subprocess, stderr only) ---
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

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
from agentic_mindset.fusion import FusionEngine, FusionStrategy, FusionReport
from agentic_mindset.context import ContextBlock
from agentic_mindset.resolver.resolver import ConflictResolver
from agentic_mindset.renderer.inject import render_for_runtime as _render_inject

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


def _explain_decision_policy(report: "FusionReport") -> str:
    """Build the decision_policy string for --explain YAML output."""
    if len(report.personas) == 1:
        return f"{report.personas[0][0]}-only"
    if report.dominant_character is not None:
        return f"{report.dominant_character}-dominant"
    return "equal-blend"


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
    report = FusionReport() if explain else None
    block = engine.fuse(chars, strategy=strat, report=report)
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
        weighted_packs_ex = engine.prepare_packs(chars, strat)
        dominant_pack = weighted_packs_ex[0][0]
        explain_data = {
            "personas": [{cid: round(w, 4)} for cid, w in report.personas],
            "merged": {
                "decision_policy": _explain_decision_policy(report),
                "risk_tolerance": dominant_pack.mindset.decision_framework.risk_tolerance,
                "time_horizon": dominant_pack.mindset.decision_framework.time_horizon,
            },
            "removed_conflicts": report.removed_items,
        }
        typer.echo(
            yaml.dump(explain_data, default_flow_style=False, allow_unicode=True),
            err=True,
        )

    # --- output ---
    if output:
        try:
            output.write_text(result_str, encoding="utf-8")
        except OSError as e:
            typer.echo(f"Error: cannot write to '{output}': {e}.", err=True)
            raise typer.Exit(1)
    else:
        typer.echo(result_str)


def _emit_explain_from_ir(ir: "BehaviorIR") -> None:
    """Emit structured YAML explain output for the inject path."""
    slots_data = {}
    for slot_name, slot in ir.slots.items():
        slots_data[slot_name] = {
            "primary": {
                "value": slot.primary.value,
                "source": slot.primary.source,
                "weight": round(slot.primary.weight, 4),
            },
            "has_conflict": slot.has_conflict,
            "modifiers": [
                {
                    "value": m.value,
                    "condition": m.condition,
                    "conjunction": m.conjunction,
                    "source": m.source,
                    "provenance": m.provenance,
                    **({"note": m.note} if m.note else {}),
                }
                for m in slot.modifiers
            ],
            "dropped": [
                {
                    "value": d.value,
                    "source": d.source,
                    "weight": round(d.weight, 4),
                    "reason": d.reason,
                }
                for d in slot.dropped
            ],
        }
    data = {
        "personas": [{cid: round(w, 4)} for cid, w in ir.preamble.personas],
        "slots": slots_data,
    }
    typer.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True), err=True)


def _emit_explain_from_report(
    report: "FusionReport",
    weighted_packs: list,
) -> None:
    """Emit explain YAML for the text path."""
    dominant_pack = weighted_packs[0][0]
    # Populate report.personas from weighted_packs if not already set
    if not report.personas:
        report.personas = [(pack.meta.id, weight) for pack, weight in weighted_packs]
    explain_data = {
        "personas": [{cid: round(w, 4)} for cid, w in report.personas],
        "merged": {
            "decision_policy": _explain_decision_policy(report),
            "risk_tolerance": dominant_pack.mindset.decision_framework.risk_tolerance,
            "time_horizon": dominant_pack.mindset.decision_framework.time_horizon,
        },
        "removed_conflicts": report.removed_items,
    }
    typer.echo(
        yaml.dump(explain_data, default_flow_style=False, allow_unicode=True),
        err=True,
    )


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

    # Both paths start from prepare_packs for identical normalization.
    weighted_packs = engine.prepare_packs(chars, strat)

    if format_ == "inject":
        # New path: ConflictResolver → BehaviorIR → ClaudeRenderer
        ir = ConflictResolver().resolve(weighted_packs)
        injected = _render_inject(ir, fmt="inject")

        if explain:
            _emit_explain_from_ir(ir)

    elif format_ == "text":
        # Existing path: ContextBlock → to_prompt
        show_weights = strat != FusionStrategy.sequential
        report = FusionReport() if explain else None
        block = ContextBlock.from_packs(weighted_packs, show_weights=show_weights, report=report)
        injected = block.to_prompt("plain_text")

        if explain:
            _emit_explain_from_report(report, weighted_packs)

    else:
        typer.echo(f"Error: unknown format '{format_}'.", err=True)
        raise typer.Exit(1)

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


@app.command()
def compile(
    sources: list[Path] = typer.Argument(..., help="Source file(s) — txt, md, or YAML with sources list"),
    output: Path = typer.Option(Path("."), "--output", help="Output directory for generated pack"),
    persona_name: str = typer.Option(..., "--name", help="Display name for the persona (e.g. 'Steve Jobs')"),
    persona_id: str = typer.Option(..., "--id", help="Pack ID in kebab-case (e.g. 'steve-jobs')"),
    type_: str = typer.Option("historical", "--type", help="historical or fictional"),
    model: str = typer.Option("claude-sonnet-4-20250514", "--model", help="LLM model to use"),
    explain: bool = typer.Option(False, "--explain", help="Show detailed compilation summary"),
    verbose: bool = typer.Option(False, "--verbose", help="Print step-by-step progress"),
):
    """Compile unstructured sources into a BehaviorOS character pack."""
    from pathlib import Path
    import yaml
    from agentic_mindset.compiler.compile import compile_pack, CompilerInput, CompilerConfig
    from agentic_mindset.compiler.schemas import SourceInput
    from agentic_mindset.compiler import pack_builder

    # Load sources from input files
    source_inputs: list[SourceInput] = []
    for src_path in sources:
        if not src_path.exists():
            console.print(f"[red]Source file not found:[/red] {src_path}")
            raise typer.Exit(1)

        text = src_path.read_text(encoding="utf-8").strip()
        if not text:
            console.print(f"[yellow]Skipping empty file:[/yellow] {src_path}")
            continue

        # If it's a YAML file with sources list, parse it
        if src_path.suffix in (".yaml", ".yml"):
            try:
                data = yaml.safe_load(text)
                if isinstance(data, dict) and "sources" in data:
                    for s in data["sources"]:
                        source_inputs.append(SourceInput(
                            title=s.get("title", src_path.stem),
                            text=s.get("text", ""),
                            type=s.get("type", "book"),
                            url=s.get("url"),
                        ))
                    continue
            except yaml.YAMLError:
                pass  # treat as plain text

        # Plain text file
        source_inputs.append(SourceInput(
            title=src_path.stem,
            text=text[:5000],  # cap at 5000 chars per source
            type="book",
        ))

    if not source_inputs:
        console.print("[red]No source content loaded.[/red]")
        raise typer.Exit(1)

    config = CompilerConfig(model=model, verbose=verbose)
    input_data = CompilerInput(
        sources=source_inputs,
        persona_name=persona_name,
        persona_id=persona_id,
        type_=type_,
    )

    if verbose:
        console.print(f"[dim]Compiling {len(source_inputs)} sources with model {model}...[/dim]")

    try:
        result = compile_pack(input_data, config)
    except Exception as e:
        console.print(f"[red]Compilation failed:[/red] {e}")
        raise typer.Exit(1)

    # Write pack files
    pack_dir = output / persona_id
    pack_builder.build_pack(result, pack_dir, type_=type_)

    # Quality summary
    gate = result.quality_gate
    status_color = {
        "pass": "green",
        "warning": "yellow",
        "fail": "red",
    }.get(gate.status.value, "yellow")

    if explain:
        console.print(f"\n[dim]Compilation summary for:[/dim] {persona_name} ({persona_id})")
        console.print(f"  Extraction:     {result.extraction_count} behaviors from {len(source_inputs)} sources")
        console.print(f"  Normalization: {result.canonical_count} canonical behaviors")
        breakdown = result.status_breakdown
        confirmed = breakdown.get("confirmed", 0)
        ambiguous = breakdown.get("ambiguous", 0)
        contradictory = breakdown.get("contradictory", 0)
        console.print(f"    — confirmed: {confirmed}  ambiguous: {ambiguous}  contradictory: {contradictory}")
        console.print(f"  Mapped slots:  {result.scores.slot_count}")
        console.print(f"  Coverage:      {result.scores.coverage:.2f}")
        console.print(f"  Evidence:      {result.scores.evidence:.2f}")
        console.print(f"  Quality gate:  [{status_color}]{gate.status.value}[/{status_color}]")
        for g_name, attr in [("contradictions", "contradictions_gate"), ("coverage", "coverage"), ("evidence", "evidence_gate"), ("conditional_candidates", "conditional_candidates_gate")]:
            g = getattr(gate, attr)
            c = {"pass": "green", "warning": "yellow", "fail": "red"}.get(g.status.value, "yellow")
            console.print(f"    {g_name}: [{c}]{g.status.value}[/{c}] — {g.detail}")

        review_total = gate.review_required
        if review_total > 0:
            console.print(f"\n[yellow]Review required:[/yellow] {review_total} items")
            if gate.contradictions_gate.status.value == "fail":
                console.print(f"  [red]Contradictions must be resolved before this pack can be merged.[/red]")
        else:
            console.print(f"\n[{status_color}]Pack quality: {gate.status.value}[/{status_color}]")
        console.print(f"\nDraft written to: {pack_dir}/")
        console.print(f"Run `mindset validate {pack_dir}` to validate the generated pack.")
    else:
        console.print(f"[{status_color}]✓ Pack compiled:[/] {pack_dir}/")
        if gate.status.value != "pass":
            console.print(f"[yellow]  Quality: {gate.status.value} — run with --explain for details[/yellow]")

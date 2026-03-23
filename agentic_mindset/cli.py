from __future__ import annotations
from pathlib import Path
from typing import Optional
import json
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
        import json
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

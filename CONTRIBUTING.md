# Contributing to Agentic Mindset

## Character Pack Contributions

### Scope

The standard library accepts:
- **Historical figures** (deceased persons with documented public records)
- **Fictional characters** (from literature, anime, games, mythology, or other creative works)

**Living persons are not accepted** into the standard library.

### Requirements

- Minimum 3 distinct source materials in `sources.yaml` (enforced by validator)
- All 6 schema files present and passing `mindset validate`
- Sources must be publicly accessible
- For **fictional characters**: sources must include the original work (manga, novel, screenplay, game); fan-created secondary sources may supplement but not replace primary sources
- For **historical figures**: primary sources (translated writings, documented speeches) preferred; biographical analysis may supplement

### Process

1. Fork the repository
2. Scaffold a new pack: `mindset init <id> --type <historical|fictional> --output characters/`
3. Fill in all 6 YAML files with accurate, sourced content
4. Add at least 3 sources to `sources.yaml`
5. Validate: `mindset validate characters/<id>/` — must pass
6. Preview: `mindset preview characters/<id>/` — review the Context Block output for quality
7. Open a Pull Request with a brief description of your sources

### What Makes a Good Character Pack?

- Fields are filled from documented evidence, not speculation
- `confidence` values are set on mindset core_principles to indicate evidence strength
- `signature_phrases` use direct quotes from primary sources
- The Context Block preview produces useful, coherent output

## Development

### Setup

```bash
git clone https://github.com/aurorie/agentic-mindset
cd agentic-mindset
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v --cov=agentic_mindset
```

### Project Structure

```
agentic_mindset/     # Core Python package
  schema/            # Pydantic schema models
  pack.py            # CharacterPack loader
  registry.py        # Registry path resolution
  context.py         # ContextBlock output
  fusion.py          # FusionEngine
  cli.py             # Typer CLI
characters/          # Standard library packs
examples/            # Example fusion configs
prompts/             # LLM extraction prompt templates
tests/               # Test suite
docs/                # Design specs and implementation plans
```

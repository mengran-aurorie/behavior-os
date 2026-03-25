# BehaviorOS Changelog

All notable changes to this project will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [1.1] — 2026-03-25

### Added
- `DecisionFramework.heuristics`, `default_strategy`, `fallback_strategy`, `commitment_policy`
- `Drive` class — `drives` upgraded from `list[str]` to `list[Drive]` with `name`, `intensity`, `description`; bare strings auto-normalized on load
- `Trait.confidence` — optional float 0–1
- `EmotionalTendencies.baseline_mood`, `emotional_range`, `frustration_trigger`, `recovery_pattern`
- `ConditionalVariant.conjunction` — `"any" | "all"` (default: `"any"`)
- `BehaviorSchema.decision_control` — `"controlled" | "reactive" | "impulsive"`
- `ToneAxes` — `formality`, `warmth`, `intensity`, `humor` axes on `VoiceSchema`
- `MetaSchema.license`, `MetaSchema.visibility`
- `Source.evidence_level` — `"primary" | "secondary" | "tertiary"`
- 6 new `Source.type` values: `biography`, `film`, `novel`, `essay`, `letter`, `speech`
- Schema version constants module (`agentic_mindset/schema/version.py`)
- Loader version check: warning for 1.0 packs, error for unknown versions
- `docs/schema-reference.md` — full field reference with runtime-critical classification
- `docs/migrations/1.0-to-1.1.md` — migration guide
- All 13 standard library packs enriched with new fields

### Changed
- `decision_speed` no longer accepts `"impulsive"` — use `decision_control: impulsive` instead (**BREAKING**)

### Fixed
- `CharacterPack.load()` now uses `pack.meta.id` (attribute) instead of `pack.meta["id"]` (dict subscript)

---

## [1.0] — 2026-03-22

### Added
- Initial Character Pack schema: `meta`, `mindset`, `personality`, `behavior`, `voice`, `sources`
- Standard library: 13 characters (7 historical, 6 fictional)
- Fusion Engine: weighted blend, dominant, sequential strategies
- Behavior IR pipeline: `ConflictResolver → BehaviorIR → ClaudeRenderer`
- CLI: `mindset init`, `validate`, `preview`, `list`, `generate`, `run`
- `--format inject` (Behavior IR path) and `--format text` (FusionEngine path)
- `--explain` structured YAML output for both paths

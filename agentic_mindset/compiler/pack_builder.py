"""Pack builder: convert compiled result into BehaviorOS YAML files."""
from __future__ import annotations
from pathlib import Path
from datetime import date
import yaml
from agentic_mindset.compiler.schemas import (
    CompileResult,
    SlotWithProvenance,
    CanonicalBehavior,
    Confidence,
    SourceCoverage,
    CompileStatus,
    CompileGate,
    CompileQualityGate,
    CompileScores,
    SLOT_WEIGHTS,
    COVERAGE_THRESHOLD,
    EVIDENCE_THRESHOLD,
)


def build_pack(result: CompileResult, output_dir: Path, type_: str = "historical") -> None:
    """Write compiled result as a BehaviorOS character pack."""
    output_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()

    # Build sources.yaml
    sources_data = {
        "sources": [
            {"title": sc.source_ref, "type": "book", "accessed": today}
            for sc in result.source_coverage
        ]
    }
    (output_dir / "sources.yaml").write_text(yaml.dump(sources_data, allow_unicode=True), encoding="utf-8")

    # Build provenance metadata
    provenance_data = {
        "provenance": {
            "scores": {
                "coverage": result.scores.coverage,
                "evidence": result.scores.evidence,
            },
            "extraction_count": result.extraction_count,
            "canonical_count": result.canonical_count,
            "quality_status": result.quality_gate.status.value,
        },
        "review_items": result.review_items,
    }
    (output_dir / "_compile_meta.yaml").write_text(yaml.dump(provenance_data, allow_unicode=True), encoding="utf-8")

    # Group slots by top-level file
    files: dict[str, dict] = {
        "meta.yaml": {
            "id": _derive_id(output_dir.name),
            "name": output_dir.name.replace("-", " ").title(),
            "version": "1.0.0",
            "schema_version": "1.1",
            "type": type_,
            "description": f"Auto-compiled persona. Status: {result.quality_gate.status.value}.",
            "tags": [],
            "authors": [{"name": "behavior-os compiler v0", "url": "https://github.com/behavior-os/behavior-os"}],
            "created": today,
        },
        "mindset.yaml": {"core_principles": [], "decision_framework": {}, "thinking_patterns": [], "mental_models": []},
        "personality.yaml": {"traits": [], "emotional_tendencies": {}, "interpersonal_style": {}, "drives": []},
        "behavior.yaml": {"work_patterns": [], "decision_speed": "deliberate", "execution_style": [], "conflict_style": {}},
        "voice.yaml": {"tone": "TODO", "vocabulary": {"preferred": [], "avoided": []}, "sentence_style": "TODO", "signature_phrases": []},
    }

    for slot in result.slots:
        path = slot.slot_path
        if path.startswith("core_principles"):
            files["mindset.yaml"].setdefault("core_principles", [])
            files["mindset.yaml"]["core_principles"].append({
                "description": slot.value,
                "detail": slot.value,
                "confidence": _conf_to_float(slot.confidence),
            })
        elif path.startswith("decision_framework"):
            _fill_decision_framework(files["mindset.yaml"], slot)
        elif path.startswith("interpersonal_style"):
            files["personality.yaml"].setdefault("interpersonal_style", {})
            files["personality.yaml"]["interpersonal_style"]["communication"] = slot.value
        elif path.startswith("conflict_style"):
            files["behavior.yaml"]["conflict_style"]["default"] = slot.value
        elif path.startswith("work_patterns"):
            files["behavior.yaml"].setdefault("work_patterns", []).append(slot.value)
        elif path.startswith("emotional_tendencies"):
            files["personality.yaml"].setdefault("emotional_tendencies", {})["baseline_mood"] = slot.value

    # Write files
    for fname, data in files.items():
        if fname == "meta.yaml":
            # meta.yaml is special, already built
            pass
        (output_dir / fname).write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # Write review items
    review_dir = output_dir / "review"
    review_dir.mkdir(exist_ok=True)
    if result.review_items.get("contradictions"):
        (review_dir / "contradictions.yaml").write_text(
            yaml.dump({"contradictions": result.review_items["contradictions"]}, allow_unicode=True),
            encoding="utf-8",
        )
    if result.review_items.get("ambiguous"):
        (review_dir / "ambiguous.yaml").write_text(
            yaml.dump({"ambiguous": result.review_items["ambiguous"]}, allow_unicode=True),
            encoding="utf-8",
        )
    if result.review_items.get("medium_confidence"):
        (review_dir / "medium_confidence.yaml").write_text(
            yaml.dump({"medium_confidence": result.review_items["medium_confidence"]}, allow_unicode=True),
            encoding="utf-8",
        )


def _fill_decision_framework(mindset: dict, slot: SlotWithProvenance) -> None:
    df = mindset.setdefault("decision_framework", {})
    path = slot.slot_path
    if "heuristics" in path:
        df.setdefault("heuristics", []).append(slot.value)
        df["risk_tolerance"] = df.get("risk_tolerance", "medium")
        df["time_horizon"] = df.get("time_horizon", "long-term")
        df["approach"] = df.get("approach", slot.value)
    elif "default_strategy" in path:
        df["default_strategy"] = slot.value


def _derive_id(pack_name: str) -> str:
    return pack_name.lower().replace(" ", "-")


_CONF_TO_FLOAT: dict[str, float] = {"high": 0.95, "medium": 0.75, "low": 0.55}


def _conf_to_float(conf: Confidence) -> float:
    return _CONF_TO_FLOAT.get(conf.value, 0.5)

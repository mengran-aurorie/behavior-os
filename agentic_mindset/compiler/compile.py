"""Main compiler pipeline: orchestrates all steps."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from agentic_mindset.compiler.schemas import (
    CompilerInput,
    CompilerConfig,
    CompileResult,
    CompileScores,
    CompileStatus,
    CompileGate,
    CompileQualityGate,
    SlotWithProvenance,
    SourceCoverage,
    CanonicalBehavior,
    Confidence,
    BehaviorStatus,
    ExtractionResult,
    NormalizationResult,
    SLOT_WEIGHTS,
    COVERAGE_THRESHOLD,
    EVIDENCE_THRESHOLD,
)
from agentic_mindset.compiler.llm import LLMClient
from agentic_mindset.compiler import extraction, normalization, typer, mapper, pack_builder


def compile_pack(input: CompilerInput, config: Optional[CompilerConfig] = None) -> CompileResult:
    """Run the full Source → Pack compiler pipeline."""
    if config is None:
        config = CompilerConfig()
    llm = LLMClient(model=config.model, temperature=config.temperature)

    # Step 1: Extraction
    ext_result = extraction.extract_behaviors(input.sources, llm)
    if config.verbose:
        print(f"[compiler] Step 1: extracted {len(ext_result.behaviors)} behaviors from {len(input.sources)} sources")

    # Step 2: Normalization
    norm_result = normalization.normalize_behaviors(ext_result.behaviors, llm)
    if config.verbose:
        print(f"[compiler] Step 2: normalized to {len(norm_result.canonicals)} canonicals — {norm_result.status_breakdown}")

    # Step 2b: Behavior Typing
    typed = typer.type_behaviors(norm_result.canonicals, llm)
    if config.verbose:
        types = [c.behavior_type.value if c.behavior_type else "?" for c in typed]
        print(f"[compiler] Step 2b: typed — {types}")

    # Step 3: Schema Mapping
    mappings = mapper.map_to_schema(typed, llm)
    if config.verbose:
        print(f"[compiler] Step 3: mapped {len(mappings)} behaviors to slots")

    # Build provenance slots
    slots = _build_slots(mappings, typed)

    # Compute coverage
    source_coverage = _compute_source_coverage(ext_result, typed)

    # Compute scores and quality gate
    scores, gate = _compute_quality(scopes_result=norm_result, mappings=mappings, slots=slots)

    # Review items
    review_items = _collect_review_items(norm_result, mappings)

    return CompileResult(
        scores=scores,
        quality_gate=gate,
        source_coverage=source_coverage,
        extraction_count=len(ext_result.behaviors),
        canonical_count=len(norm_result.canonicals),
        status_breakdown=norm_result.status_breakdown,
        canonicals=typed,
        slots=slots,
        review_items=review_items,
        extraction_raw=ext_result.behaviors,
    )


def _build_slots(
    mappings: list[tuple[CanonicalBehavior, str, str, Confidence, bool]],
    canonicals: list[CanonicalBehavior],
) -> list[SlotWithProvenance]:
    """Convert mapping results into SlotWithProvenance list."""
    slots = []
    for cb, slot_path, field_value, confidence, needs_review in mappings:
        provenance = []
        for variant in cb.variants:
            provenance.append({
                "canonical_id": cb.id,
                "extracted_id": variant.extracted_id,
                "quote": variant.text,
                "behavior": cb.canonical_form,
            })
        slots.append(SlotWithProvenance(
            slot_path=slot_path,
            value=field_value,
            provenance=provenance,
            confidence=confidence,
        ))
    return slots


def _compute_source_coverage(
    ext_result: ExtractionResult, canonicals: list[CanonicalBehavior]
) -> list[SourceCoverage]:
    """Compute which source sections were used vs unused."""
    # Track which extracted behavior IDs are used
    used_ids = set()
    for cb in canonicals:
        used_ids.update(vp.extracted_id for vp in cb.variants)

    # Group by source
    by_source: dict[str, dict] = {}
    for eb in ext_result.behaviors:
        s = by_source.setdefault(eb.source_ref, {"total": 0, "used": 0})
        s["total"] += 1
        if eb.id in used_ids:
            s["used"] += 1

    return [
        SourceCoverage(
            source_ref=src,
            total_quotes=data["total"],
            used_quotes=data["used"],
            unused_sections=[],  # v0: section-level tracking deferred
        )
        for src, data in by_source.items()
    ]


def _compute_quality(
    scopes_result: NormalizationResult,
    mappings: list,
    slots: list[SlotWithProvenance],
) -> tuple[CompileScores, CompileQualityGate]:
    """Compute coverage/evidence scores and quality gate."""
    # Coverage: filled slots / total possible slots
    filled_slots = {s.slot_path for s in slots}
    total_weight = sum(SLOT_WEIGHTS.values())
    filled_weight = sum(SLOT_WEIGHTS.get(path, 0.5) for path in filled_slots)
    coverage = filled_weight / total_weight if total_weight > 0 else 0.0

    # Evidence: slots with ≥2 provenance entries
    evidenced_weight = sum(
        SLOT_WEIGHTS.get(s.slot_path, 0.5)
        for s in slots
        if len(s.provenance) >= 2
    )
    evidence = evidenced_weight / total_weight if total_weight > 0 else 0.0

    # Contradictions
    contradictions_count = scopes_result.status_breakdown.get(BehaviorStatus.CONTRADICTORY, 0)
    review_count = sum(1 for _, _, _, conf, needs in mappings if needs)

    # Gate evaluation
    contradictions_gate = CompileGate(
        name="contradictions",
        status=CompileStatus.FAIL if contradictions_count > 0 else CompileStatus.PASS,
        detail=f"{contradictions_count} contradictory clusters",
    )
    coverage_gate = CompileGate(
        name="coverage",
        status=CompileStatus.WARNING if coverage < COVERAGE_THRESHOLD else CompileStatus.PASS,
        detail=f"{coverage:.2f} (threshold: {COVERAGE_THRESHOLD})",
    )
    evidence_gate = CompileGate(
        name="evidence",
        status=CompileStatus.WARNING if evidence < EVIDENCE_THRESHOLD else CompileStatus.PASS,
        detail=f"{evidence:.2f} (threshold: {EVIDENCE_THRESHOLD})",
    )
    conditional_gate = CompileGate(
        name="conditional_candidates",
        status=CompileStatus.WARNING,
        detail=f"{review_count} items need review",
    )

    all_gates = [contradictions_gate, coverage_gate, evidence_gate, conditional_gate]
    worst = max(all_gates, key=lambda g: (
        0 if g.status == CompileStatus.PASS else 1 if g.status == CompileStatus.WARNING else 2
    ))
    overall_status = worst.status

    gate = CompileQualityGate(
        status=overall_status,
        coverage=coverage_gate,
        evidence_gate=evidence_gate,
        contradictions_gate=contradictions_gate,
        conditional_candidates_gate=conditional_gate,
        review_required=review_count + contradictions_count,
    )

    scores = CompileScores(
        coverage=coverage,
        evidence=evidence,
        extraction_count=scopes_result.extraction_count,
        canonical_count=scopes_result.canonical_count,
        slot_count=len(slots),
        total_slots=len(SLOT_WEIGHTS),
    )

    return scores, gate


def _collect_review_items(
    norm_result: NormalizationResult,
    mappings: list[tuple[CanonicalBehavior, str, str, Confidence, bool]],
) -> dict[str, list]:
    """Collect items needing human review, priority ordered."""
    items: dict[str, list] = {
        "contradictions": [],
        "ambiguous": [],
        "medium_confidence": [],
    }

    for cb in norm_result.canonicals:
        if cb.status.value == "contradictory":
            items["contradictions"].append({
                "id": cb.id,
                "canonical_form": cb.canonical_form,
                "variants": [{"id": v.extracted_id, "text": v.text} for v in cb.variants],
            })
        elif cb.status.value == "ambiguous":
            items["ambiguous"].append({
                "id": cb.id,
                "canonical_form": cb.canonical_form,
                "variants": [{"id": v.extracted_id, "text": v.text} for v in cb.variants],
            })

    for cb, path, value, conf, needs in mappings:
        if needs and cb.status.value != "contradictory":
            items["medium_confidence"].append({
                "id": cb.id,
                "canonical_form": cb.canonical_form,
                "slot_path": path,
                "value": value,
                "confidence": conf.value,
            })

    return items

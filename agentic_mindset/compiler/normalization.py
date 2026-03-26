"""Step 2: Semantic Normalization — cluster behaviors and produce canonical forms."""
from __future__ import annotations
import re
from agentic_mindset.compiler.schemas import (
    ExtractedBehavior,
    CanonicalBehavior,
    BehaviorVariant,
    NormalizationResult,
    BehaviorStatus,
    Confidence,
)


def _match_extracted_id(variant_text: str, behaviors: list[ExtractedBehavior]) -> str:
    """Try to match a variant text back to an original extracted behavior ID.

    Uses substring matching against each extracted behavior's quote and behavior fields.
    Returns the matched extracted_id, or empty string if no match found.
    """
    v_lower = variant_text.lower()
    best_match = ""
    for eb in behaviors:
        # Check if the variant text appears in the extracted quote or behavior
        if v_lower in eb.quote.lower() or v_lower in eb.behavior.lower():
            return eb.id
        # Also check the reverse: extracted text in variant
        if eb.quote and eb.quote.lower() in v_lower:
            return eb.id
    return best_match


def _build_canonicals_from_markdown(
    result: dict, behaviors: list[ExtractedBehavior] | None = None
) -> list:
    """Build canonical_behaviors list from markdown-parsed result dict.

    Handles orphaned keys like canonical_form, variants, status at top level,
    which happens when the markdown parser doesn't correctly nest items under sections.

    Also handles the MiniMax-specific `extracted_behaviors` key which contains
    canonical-like items instead of `canonical_behaviors`.

    `behaviors` is used to match variant text back to original extracted IDs
    for provenance tracking. Pass when available (from normalize_behaviors).
    """
    if not isinstance(result, dict):
        return []

    # MiniMax variant: items under "extracted_behaviors" instead of "canonical_behaviors"
    if "extracted_behaviors" in result:
        items = result["extracted_behaviors"]
        if isinstance(items, list):
            canonicals = []
            for i, item in enumerate(items):
                if isinstance(item, dict) and "canonical_form" in item:
                    canonicals.append(item)
            if canonicals:
                return canonicals

    # Collect orphaned normalization keys
    orphaned = {}
    section_candidates = {}
    for key, value in result.items():
        if key in ('rationale', 'potential_connection_note', 'decision'):
            continue
        if key in ('canonical_form', 'variants', 'status', 'conditional_candidate',
                   'conditional_note', 'evidence_count', 'conditional_markers',
                   'contrast_signal', 'confidence'):
            orphaned[key] = value
        elif re.match(r'^(b-\d+|cb-\d+|item_\d+)$', key):
            section_candidates[key] = value

    # If we have orphaned keys + section candidates, build entries
    if orphaned and section_candidates:
        canonicals = []
        for section_key in sorted(section_candidates.keys()):
            section_data = section_candidates[section_key]
            if not isinstance(section_data, dict):
                section_data = {}
            entry = dict(section_data)
            # Fill in orphaned keys not in entry
            for ok, ov in orphaned.items():
                if ok not in entry:
                    entry[ok] = ov
            canonicals.append(entry)
        return canonicals

    # If we just have orphaned keys as a single entry
    if orphaned and len(section_candidates) == 0:
        return [orphaned]

    return []


NORMALIZATION_SYSTEM = """You are normalizing extracted behavioral signals from persona sources.

For each cluster of behaviors:
1. Identify the canonical form — the most precise, general description of this behavior
2. List all variants that map to this canonical form
3. Mark status: confirmed (variants agree) | ambiguous (unclear interpretation) | contradictory (variants conflict)
4. Identify extreme tendency markers (always/never/refuses to/insists on/without exception) → set conditional_candidate=true and add conditional_note

Canonical forms should be concise behavioral statements (noun phrase or short sentence).
Do NOT merge behaviors that are genuinely different — only merge clear duplicates or near-duplicates."""


def build_normalization_prompt(behaviors: list[ExtractedBehavior]) -> str:
    lines = ["Extracted behaviors to normalize:\n"]
    for b in behaviors:
        contrast_note = " [CONTRAST SIGNAL]" if b.contrast_signal else ""
        trigger_note = f" (trigger: {b.trigger})" if b.trigger else ""
        lines.append(
            f"- id: {b.id}\n"
            f"  source: {b.source_ref}\n"
            f"  behavior: {b.behavior}{contrast_note}{trigger_note}\n"
            f"  confidence: {b.confidence.value}\n"
            f"  quote: \"{b.quote}\"\n"
        )
    return "\n".join(lines)


NORMALIZATION_USER = """Cluster the extracted behaviors into canonical forms.

For each cluster output:
- id: "cb-NNN" (sequential canonical ID)
- canonical_form: most precise general description of this behavior
- variants: list of {extracted_id, text} for all behaviors in this cluster
- status: confirmed / ambiguous / contradictory
- evidence_count: total number of source quotes supporting this behavior
- conditional_candidate: true if behavior contains extreme markers (always/never/refuses to/insists on) but no explicit condition
- conditional_note: brief note on what implicit condition might apply (only if conditional_candidate=true)
- contradiction_refs: list of conflicting canonical behavior IDs (only if contradictory)

Output format:
```yaml
canonical_behaviors:
  - id: cb-001
    canonical_form: "..."
    variants: [...]
    status: confirmed
    evidence_count: 3
    conditional_candidate: false
    conditional_note: null
    contradiction_refs: []
```"""


def normalize_behaviors(behaviors: list[ExtractedBehavior], llm) -> NormalizationResult:
    """Run Step 2: semantic normalization."""
    from agentic_mindset.compiler.llm import LLMClient
    if not isinstance(llm, LLMClient):
        raise TypeError("llm must be an LLMClient instance")

    prompt = build_normalization_prompt(behaviors)
    try:
        result = llm.complete_structured(prompt, system=NORMALIZATION_SYSTEM)
    except RuntimeError:
        # Fallback: normalize each behavior as its own canonical (LLM couldn't cluster)
        return _fallback_normalize(behaviors)

    canonicals_raw = result.get("canonical_behaviors", [])
    if not canonicals_raw:
        # Fallback: try to build from orphaned keys (markdown format)
        canonicals_raw = _build_canonicals_from_markdown(result, behaviors)

    canonicals = []
    for i, raw in enumerate(canonicals_raw):
        # variants can be a string (markdown format) or list of dicts (JSON/YAML)
        variants_raw = raw.get("variants", [])
        if isinstance(variants_raw, str):
            # Markdown format: "variant1", "variant2" or single variant
            # Try to match each variant text to original extracted behavior IDs
            # to preserve provenance tracking
            variants = []
            for j, v_text in enumerate(variants_raw.split(',')):
                v_text = v_text.strip().strip('"\'')
                if v_text:
                    matched_id = _match_extracted_id(v_text, behaviors)
                    variants.append(BehaviorVariant(
                        extracted_id=matched_id or f"b-{j+1:03d}",
                        text=v_text,
                    ))
        else:
            variants = []
            for v in variants_raw:
                if isinstance(v, dict):
                    variants.append(BehaviorVariant(
                        extracted_id=v.get("extracted_id", ""),
                        text=v.get("text", ""),
                    ))
        # Normalize status
        status_str = raw.get("status", "confirmed")
        if isinstance(status_str, str) and '(' in status_str:
            status_str = status_str.split('(')[0].strip()
        try:
            status = BehaviorStatus(status_str.lower())
        except ValueError:
            status = BehaviorStatus.CONFIRMED
        # Normalize confidence
        conf_str = raw.get("confidence", "high")
        if isinstance(conf_str, str):
            conf_str = conf_str.lower()
        try:
            confidence = Confidence(conf_str)
        except ValueError:
            confidence = Confidence.HIGH
        cb = CanonicalBehavior(
            id=raw.get("id", f"cb-{i+1:03d}"),
            canonical_form=raw.get("canonical_form", ""),
            status=status,
            confidence=confidence,
            evidence_count=raw.get("evidence_count", 0),
            conditional_candidate=bool(raw.get("conditional_candidate", False)),
            conditional_note=raw.get("conditional_note"),
            contradiction_refs=raw.get("contradiction_refs", []),
            variants=variants,
            provenance=[v.extracted_id for v in variants],
        )
        canonicals.append(cb)

    # Compute status breakdown
    breakdown: dict[BehaviorStatus, int] = {}
    for c in canonicals:
        breakdown[c.status] = breakdown.get(c.status, 0) + 1

    return NormalizationResult(
        canonicals=canonicals,
        extraction_count=len(behaviors),
        canonical_count=len(canonicals),
        status_breakdown=breakdown,
    )


def _fallback_normalize(behaviors: list[ExtractedBehavior]) -> NormalizationResult:
    """Fallback: each extracted behavior becomes its own canonical form.

    Used when the LLM fails to return parsable structured output.
    Each behavior is treated as a confirmed, single-variant canonical.
    """
    canonicals: list[CanonicalBehavior] = []
    for i, eb in enumerate(behaviors):
        cb = CanonicalBehavior(
            id=f"cb-{i+1:03d}",
            canonical_form=eb.behavior,
            status=BehaviorStatus.CONFIRMED,
            evidence_count=1,
            conditional_candidate=False,
            contradiction_refs=[],
            variants=[BehaviorVariant(extracted_id=eb.id, text=eb.quote)],
            provenance=[eb.id],
        )
        canonicals.append(cb)

    breakdown: dict[BehaviorStatus, int] = {BehaviorStatus.CONFIRMED: len(canonicals)}
    return NormalizationResult(
        canonicals=canonicals,
        extraction_count=len(behaviors),
        canonical_count=len(canonicals),
        status_breakdown=breakdown,
    )

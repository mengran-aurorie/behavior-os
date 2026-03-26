"""Step 1: LLM Extraction — extract behavior candidates from raw sources."""
from __future__ import annotations
from typing import Optional
from agentic_mindset.compiler.schemas import (
    ExtractedBehavior,
    ExtractionResult,
    SourceInput,
    Confidence,
)


EXTRACTION_SYSTEM = """You are a behavioral analyst extracting structured behavior data from persona sources.

Rules:
- Extract BEHAVIORS, not adjectives. A behavior is what a person DOES, not what they ARE.
- Mark contrast_signal=true only when the quote contains a contrast structure (but/yet/although/except when).
- Mark confidence: high if explicit behavior + first-hand account; medium if indirect; low if narrative.
- trigger should be null if no explicit context is mentioned.
- Do NOT fabricate. Only extract what is present in the sources.
- CRITICAL: Always output a JSON code block. Do not output markdown tables or bold-formatted text."""


def build_extraction_prompt(sources: list[SourceInput]) -> str:
    lines = []
    for i, src in enumerate(sources):
        lines.append(f"=== SOURCE {i+1}: {src.title} ===")
        lines.append(f"Type: {src.type}")
        if src.url:
            lines.append(f"URL: {src.url}")
        lines.append(f"Content:\n{src.text[:3000]}")
        lines.append("")
    return "\n".join(lines)


EXTRACTION_USER = """Extract all behavioral signals from the sources above.

For each behavior you find, output a JSON array with these exact fields:
- id: "b-001" (sequential)
- quote: the EXACT text from the source that supports this behavior (verbatim, in quotes)
- source_ref: the source title this was extracted from
- behavior: the behavioral description (as a concrete action or policy, NOT an adjective)
- trigger: the explicit context/condition mentioned, or null
- contrast_signal: true only if the quote contains a contrast marker (but/yet/although/except when)
- confidence: high / medium / low

Sort by source order. Include ALL behaviors you find with an explicit quote.

IMPORTANT: Output ONLY a JSON code block, nothing else:
```json
[
  {
    "id": "b-001",
    "quote": "the exact source text",
    "source_ref": "Source Title",
    "behavior": "the behavioral description",
    "trigger": "context or null",
    "contrast_signal": false,
    "confidence": "high"
  },
  ...
]
```"""


def extract_behaviors(sources: list[SourceInput], llm) -> ExtractionResult:
    """Run Step 1: extract behavior candidates from raw source text."""
    from agentic_mindset.compiler.llm import LLMClient
    if not isinstance(llm, LLMClient):
        raise TypeError("llm must be an LLMClient instance")

    prompt = build_extraction_prompt(sources)
    result = llm.complete_structured(prompt, system=EXTRACTION_SYSTEM)

    # Handle various response schemas:
    # - dict with "extracted_behaviors" key (YAML schema)
    # - dict with "behaviors" key (JSON schema variant)
    # - dict with "items" key (markdown table format)
    # - dict with "extracted" key
    # - bare list (model returned array directly)
    if isinstance(result, list):
        behaviors_raw = result
    else:
        behaviors_raw = (
            result.get("extracted_behaviors")
            or result.get("behaviors")
            or result.get("items")
            or result.get("extracted")
            or []
        )
    behaviors = []
    for i, raw in enumerate(behaviors_raw):
        # Normalize field names across schema variants
        # YAML: quote, source_ref, behavior; JSON: text, source_text, behavior
        # Markdown: exact_quote, what_he_does, etc.
        # MiniMax table format: context, source_type, behavior
        quote = (
            raw.get("quote") or raw.get("source_text") or raw.get("exact_quote")
            or raw.get("text") or raw.get("description") or raw.get("context") or ""
        )
        source_ref = raw.get("source_ref") or raw.get("source") or raw.get("source_type") or ""
        behavior = (
            raw.get("behavior") or raw.get("what_he_does") or raw.get("action")
            or raw.get("text") or raw.get("description") or ""
        )
        # raw_text defaults to quote if not present
        raw_text = raw.get("raw_text") or quote
        # Handle "null" string → None, "true"/"false" strings → bool
        trigger_val = raw.get("trigger")
        if trigger_val is None or trigger_val == "null":
            trigger_val = None
        contrast_val = raw.get("contrast_signal", False)
        if isinstance(contrast_val, str):
            contrast_val = contrast_val.lower() in ("true", "yes", "1")
        confidence_val = raw.get("confidence", "medium")
        if isinstance(confidence_val, str) and confidence_val not in ("high", "medium", "low"):
            confidence_val = "medium"
        eb = ExtractedBehavior(
            id=raw.get("id", f"b-{i+1:03d}"),
            quote=quote,
            source_ref=source_ref,
            page_or_section=raw.get("page_or_section"),
            behavior=behavior,
            trigger=trigger_val,
            contrast_signal=contrast_val,
            confidence=Confidence(confidence_val),
            raw_text=raw_text,
        )
        behaviors.append(eb)

    return ExtractionResult(
        behaviors=behaviors,
        total_quotes=len(behaviors),
        sources=[s.title for s in sources],
    )

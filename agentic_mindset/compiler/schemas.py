"""Compiler pipeline data models."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import hashlib


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BehaviorStatus(str, Enum):
    CONFIRMED = "confirmed"
    AMBIGUOUS = "ambiguous"
    CONTRADICTORY = "contradictory"


class BehaviorType(str, Enum):
    """Semantic behavior categories (Step 2b buffer layer)."""
    CORE_PRINCIPLE = "core_principle"
    DECISION_POLICY = "decision_policy"
    COMMUNICATION = "communication"
    CONFLICT = "conflict"
    EMOTIONAL = "emotional"
    DRIVE = "drive"
    EXECUTION = "execution"


class CompileStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


# ---------------------------------------------------------------------------
# Extraction (Step 1)
# ---------------------------------------------------------------------------

@dataclass
class ExtractedBehavior:
    """A raw behavior candidate extracted from a source."""
    id: str
    quote: str
    source_ref: str
    page_or_section: Optional[str]
    behavior: str  # behavioral description, not adjective
    trigger: Optional[str]  # explicit context that triggered this behavior
    contrast_signal: bool  # True if quote contains contrast marker
    confidence: Confidence
    raw_text: str

    def stable_id(self) -> str:
        return f"eb_{hashlib.sha256(self.behavior.encode()).hexdigest()[:8]}"


@dataclass
class ExtractionResult:
    behaviors: list[ExtractedBehavior]
    total_quotes: int
    sources: list[str]


# ---------------------------------------------------------------------------
# Normalization (Step 2)
# ---------------------------------------------------------------------------

@dataclass
class BehaviorVariant:
    extracted_id: str
    text: str


@dataclass
class CanonicalBehavior:
    """A semantically normalized behavior with canonical form."""
    id: str
    canonical_form: str
    behavior_type: Optional[BehaviorType] = None  # filled by Step 2b
    slot_target: Optional[str] = None  # provisional schema path
    variants: list[BehaviorVariant] = field(default_factory=list)
    status: BehaviorStatus = BehaviorStatus.CONFIRMED
    confidence: Confidence = Confidence.HIGH  # LLM-assessed confidence in canonical form
    evidence_count: int = 0
    contradiction_refs: list[str] = field(default_factory=list)
    conditional_candidate: bool = False  # True if has extreme tendency markers
    conditional_note: Optional[str] = None
    # Provenance chain
    provenance: list[str] = field(default_factory=list)  # extracted behavior IDs

    def stable_id(self) -> str:
        return f"cb_{hashlib.sha256(self.canonical_form.lower().strip().encode()).hexdigest()[:8]}"


@dataclass
class NormalizationResult:
    canonicals: list[CanonicalBehavior]
    extraction_count: int
    canonical_count: int
    status_breakdown: dict[BehaviorStatus, int]


# ---------------------------------------------------------------------------
# Coverage (per source)
# ---------------------------------------------------------------------------

@dataclass
class SourceCoverage:
    source_ref: str
    total_quotes: int
    used_quotes: int
    unused_sections: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Coverage Score v0
# ---------------------------------------------------------------------------

SLOT_WEIGHTS: dict[str, float] = {
    "core_principles": 2.0,
    "decision_framework": 1.5,
    "interpersonal_style.communication": 1.0,
    "interpersonal_style.leadership": 1.0,
    "conflict_style": 1.0,
    "emotional_tendencies": 0.5,
    "drives": 0.5,
    "voice.tone": 0.5,
    "voice.vocabulary": 0.5,
}

COVERAGE_THRESHOLD = 0.60
EVIDENCE_THRESHOLD = 0.50


@dataclass
class CompileScores:
    coverage: float
    evidence: float
    extraction_count: int
    canonical_count: int
    slot_count: int
    total_slots: int


@dataclass
class CompileGate:
    name: str
    status: CompileStatus
    detail: str


@dataclass
class CompileQualityGate:
    status: CompileStatus
    coverage: CompileGate
    evidence_gate: CompileGate
    contradictions_gate: CompileGate
    conditional_candidates_gate: CompileGate
    review_required: int  # count of items needing review


# ---------------------------------------------------------------------------
# Final Compile Result
# ---------------------------------------------------------------------------

@dataclass
class SlotWithProvenance:
    slot_path: str
    value: str
    provenance: list[dict]  # [{canonical_id, quote, source_ref}]
    confidence: Confidence


@dataclass
class CompileResult:
    """Final output of the compile pipeline."""
    # Scores
    scores: CompileScores
    quality_gate: CompileQualityGate

    # Source coverage
    source_coverage: list[SourceCoverage]

    # Extracted and canonical counts
    extraction_count: int
    canonical_count: int
    status_breakdown: dict[BehaviorStatus, int]

    # All canonical behaviors (for review)
    canonicals: list[CanonicalBehavior]

    # Final slots (for pack building)
    slots: list[SlotWithProvenance]

    # Items needing review (priority ordered)
    review_items: dict[str, list]  # contradictions, ambiguous, medium_confidence

    # Intermediate debug (for --explain output)
    extraction_raw: list[ExtractedBehavior]


# ---------------------------------------------------------------------------
# Compiler Input / Config
# ---------------------------------------------------------------------------

@dataclass
class SourceInput:
    """A single source for the compiler."""
    title: str
    text: str  # raw text content
    type: str = "book"  # book, article, interview, speech, etc.
    url: Optional[str] = None


@dataclass
class CompilerInput:
    """Input to the compiler pipeline."""
    sources: list[SourceInput]
    persona_name: str
    persona_id: str  # kebab-case
    type_: str = "historical"  # historical or fictional


@dataclass
class CompilerConfig:
    """Runtime configuration for the compiler."""
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.3
    max_retries: int = 2
    skip_conditional: bool = True  # v0: skip auto-conditional
    verbose: bool = False

"""Tests for compile.py - main compiler pipeline."""
import pytest
from unittest.mock import MagicMock, patch
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
    BehaviorVariant,
    BehaviorStatus,
    BehaviorType,
    Confidence,
    SLOT_WEIGHTS,
    COVERAGE_THRESHOLD,
    EVIDENCE_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_canonical(
    id: str = "cb-001",
    canonical_form: str = "test behavior",
    behavior_type: BehaviorType = BehaviorType.COMMUNICATION,
    status: BehaviorStatus = BehaviorStatus.CONFIRMED,
    evidence_count: int = 2,
    variants: list = None,
) -> CanonicalBehavior:
    if variants is None:
        variants = [BehaviorVariant(extracted_id="b-001", text="test quote")]
    return CanonicalBehavior(
        id=id,
        canonical_form=canonical_form,
        behavior_type=behavior_type,
        status=status,
        evidence_count=evidence_count,
        conditional_candidate=False,
        contradiction_refs=[],
        variants=variants,
        provenance=["b-001"],
    )


def make_slot(
    slot_path: str = "core_principles",
    value: str = "test",
    provenance_count: int = 1,
    confidence: Confidence = Confidence.HIGH,
) -> SlotWithProvenance:
    provenance = [
        {"canonical_id": "cb-001", "extracted_id": f"b-{i:03d}", "quote": "test", "behavior": "test"}
        for i in range(provenance_count)
    ]
    return SlotWithProvenance(
        slot_path=slot_path,
        value=value,
        provenance=provenance,
        confidence=confidence,
    )


class MockNormalizationResult:
    def __init__(self, canonicals, extraction_count: int = 5):
        self.canonicals = canonicals
        self.extraction_count = extraction_count
        self.canonical_count = len(canonicals)
        self.status_breakdown = {}
        for cb in canonicals:
            self.status_breakdown[cb.status] = self.status_breakdown.get(cb.status, 0) + 1


class TestBuildSlots:
    """Test _build_slots()."""

    def test_converts_mappings_to_slots(self):
        from agentic_mindset.compiler.compile import _build_slots
        canonicals = [
            make_canonical(
                id="cb-001",
                variants=[
                    BehaviorVariant(extracted_id="b-001", text="quote 1"),
                    BehaviorVariant(extracted_id="b-002", text="quote 2"),
                ],
            ),
        ]
        mappings = [
            (canonicals[0], "core_principles", "Test principle", Confidence.HIGH, False),
        ]

        slots = _build_slots(mappings, canonicals)

        assert len(slots) == 1
        assert slots[0].slot_path == "core_principles"
        assert slots[0].value == "Test principle"
        assert len(slots[0].provenance) == 2  # 2 variants

    def test_provenance_contains_extracted_ids(self):
        from agentic_mindset.compiler.compile import _build_slots
        canonicals = [
            make_canonical(
                id="cb-001",
                variants=[BehaviorVariant(extracted_id="b-001", text="test")],
            ),
        ]
        mappings = [
            (canonicals[0], "core_principles", "test", Confidence.HIGH, False),
        ]

        slots = _build_slots(mappings, canonicals)

        assert slots[0].provenance[0]["extracted_id"] == "b-001"
        assert slots[0].provenance[0]["canonical_id"] == "cb-001"


class TestComputeSourceCoverage:
    """Test _compute_source_coverage()."""

    def test_tracks_used_vs_total_quotes(self):
        from agentic_mindset.compiler.schemas import ExtractedBehavior
        from agentic_mindset.compiler.compile import _compute_source_coverage

        class MockExtractionResult:
            def __init__(self, behaviors):
                self.behaviors = behaviors

        ext_result = MockExtractionResult(
            behaviors=[
                ExtractedBehavior(
                    id="b-001", quote="q1", source_ref="Source A",
                    page_or_section=None, behavior="b1", trigger=None,
                    contrast_signal=False, confidence=Confidence.HIGH, raw_text="q1",
                ),
                ExtractedBehavior(
                    id="b-002", quote="q2", source_ref="Source A",
                    page_or_section=None, behavior="b2", trigger=None,
                    contrast_signal=False, confidence=Confidence.HIGH, raw_text="q2",
                ),
                ExtractedBehavior(
                    id="b-003", quote="q3", source_ref="Source B",
                    page_or_section=None, behavior="b3", trigger=None,
                    contrast_signal=False, confidence=Confidence.HIGH, raw_text="q3",
                ),
            ]
        )
        canonicals = [
            make_canonical(
                id="cb-001",
                variants=[BehaviorVariant(extracted_id="b-001", text="q1")],
            ),
            # b-002 and b-003 are not used
        ]

        coverage = _compute_source_coverage(ext_result, canonicals)

        source_a = next((s for s in coverage if s.source_ref == "Source A"), None)
        assert source_a is not None
        assert source_a.total_quotes == 2
        assert source_a.used_quotes == 1  # only b-001 is used


class TestComputeQuality:
    """Test _compute_quality()."""

    def test_coverage_score_computation(self):
        from agentic_mindset.compiler.compile import _compute_quality
        from agentic_mindset.compiler.schemas import SlotWithProvenance

        canonicals = [make_canonical(id="cb-001"), make_canonical(id="cb-002")]
        slots = [
            make_slot(slot_path="core_principles", provenance_count=2),
            make_slot(slot_path="interpersonal_style.communication", provenance_count=2),
        ]
        # mappings: list of (canonical, slot_path, field_value, confidence, needs_review)
        mappings = [
            (canonicals[0], "core_principles", "test1", Confidence.HIGH, False),
            (canonicals[1], "interpersonal_style.communication", "test2", Confidence.HIGH, False),
        ]
        norm_result = MockNormalizationResult(canonicals=canonicals)

        scores, gate = _compute_quality(norm_result, mappings, slots)

        assert 0.0 <= scores.coverage <= 1.0
        assert 0.0 <= scores.evidence <= 1.0

    def test_contradictions_gate_fail_when_contradictory(self):
        from agentic_mindset.compiler.compile import _compute_quality

        canonicals = [make_canonical(status=BehaviorStatus.CONTRADICTORY)]
        slots = [make_slot()]
        mappings = [(canonicals[0], "core_principles", "test", Confidence.HIGH, False)]
        norm_result = MockNormalizationResult(canonicals=canonicals)

        scores, gate = _compute_quality(norm_result, mappings, slots)

        assert gate.contradictions_gate.status == CompileStatus.FAIL

    def test_coverage_gate_warning_below_threshold(self):
        from agentic_mindset.compiler.compile import _compute_quality

        canonicals = []
        slots = []  # No slots = 0 coverage
        mappings = []
        norm_result = MockNormalizationResult(canonicals=canonicals)

        scores, gate = _compute_quality(norm_result, mappings, slots)

        # Coverage is 0, which is below COVERAGE_THRESHOLD (0.60)
        assert gate.coverage.status == CompileStatus.WARNING

    def test_evidence_gate_warning_below_threshold(self):
        from agentic_mindset.compiler.compile import _compute_quality

        # Slots with only 1 provenance each (below EVIDENCE_THRESHOLD of 2)
        canonicals = [make_canonical()]
        slots = [make_slot(provenance_count=1)]
        mappings = [(canonicals[0], "core_principles", "test", Confidence.MEDIUM, True)]
        norm_result = MockNormalizationResult(canonicals=canonicals)

        scores, gate = _compute_quality(norm_result, mappings, slots)

        # Evidence is 0 because no slots have >= 2 provenance
        assert gate.evidence_gate.status == CompileStatus.WARNING

    def test_review_count_includes_needs_review(self):
        from agentic_mindset.compiler.compile import _compute_quality

        canonicals = [make_canonical(id="cb-001")]
        slots = [make_slot()]
        mappings = [
            (canonicals[0], "core_principles", "test", Confidence.MEDIUM, True),
        ]
        norm_result = MockNormalizationResult(canonicals=canonicals)

        _, gate = _compute_quality(norm_result, mappings, slots)

        assert gate.review_required >= 0


class TestCollectReviewItems:
    """Test _collect_review_items()."""

    def test_contradictions_collected(self):
        from agentic_mindset.compiler.compile import _collect_review_items
        norm_result = MockNormalizationResult(
            canonicals=[
                make_canonical(id="cb-001", status=BehaviorStatus.CONTRADICTORY),
            ],
        )
        mappings = []

        items = _collect_review_items(norm_result, mappings)

        assert "contradictions" in items
        assert len(items["contradictions"]) == 1
        assert items["contradictions"][0]["id"] == "cb-001"

    def test_ambiguous_collected(self):
        from agentic_mindset.compiler.compile import _collect_review_items
        norm_result = MockNormalizationResult(
            canonicals=[
                make_canonical(id="cb-001", status=BehaviorStatus.AMBIGUOUS),
            ],
        )
        mappings = []

        items = _collect_review_items(norm_result, mappings)

        assert "ambiguous" in items
        assert len(items["ambiguous"]) == 1

    def test_medium_confidence_mappings_collected(self):
        from agentic_mindset.compiler.compile import _collect_review_items
        norm_result = MockNormalizationResult(
            canonicals=[make_canonical(id="cb-001", status=BehaviorStatus.CONFIRMED)],
        )
        cb = make_canonical(id="cb-001")
        mappings = [
            (cb, "core_principles", "test", Confidence.MEDIUM, True),
        ]

        items = _collect_review_items(norm_result, mappings)

        assert "medium_confidence" in items

    def test_contradictory_not_in_medium_confidence(self):
        """Contradictory items should only appear in contradictions, not medium_confidence."""
        from agentic_mindset.compiler.compile import _collect_review_items
        norm_result = MockNormalizationResult(
            canonicals=[
                make_canonical(id="cb-001", status=BehaviorStatus.CONTRADICTORY),
            ],
        )
        cb = make_canonical(id="cb-001", status=BehaviorStatus.CONTRADICTORY)
        mappings = [
            (cb, "core_principles", "test", Confidence.MEDIUM, True),
        ]

        items = _collect_review_items(norm_result, mappings)

        # cb-001 should be in contradictions, NOT in medium_confidence
        assert len(items["contradictions"]) == 1
        contradiction_ids = [c["id"] for c in items["contradictions"]]
        assert "cb-001" in contradiction_ids


class TestCompilePackPipeline:
    """Test compile_pack() end-to-end with mocked LLM calls.

    These tests mock each pipeline step at the module level so compile_pack
    doesn't need real API keys.
    """

    def test_compile_pack_full_pipeline_produces_slots(self):
        """Full pipeline: extraction → normalization → typing → mapping → quality gates."""
        from agentic_mindset.compiler import extraction, normalization, typer, mapper
        from agentic_mindset.compiler.schemas import (
            SourceInput, CompilerInput, CompilerConfig, ExtractionResult,
            NormalizationResult, CanonicalBehavior, BehaviorVariant,
            BehaviorStatus, Confidence, BehaviorType, SlotWithProvenance,
        )

        ext_result = ExtractionResult(
            behaviors=[
                extraction.ExtractedBehavior(
                    id="b-001",
                    quote="Innovation is saying no to a thousand things.",
                    source_ref="The Steve Jobs Interview: 1993",
                    page_or_section=None,
                    behavior="Deliberately declines opportunities to maintain focus",
                    trigger=None,
                    contrast_signal=False,
                    confidence=Confidence.HIGH,
                    raw_text="Innovation is saying no to a thousand things.",
                ),
                extraction.ExtractedBehavior(
                    id="b-002",
                    quote="Quality is more important than quantity.",
                    source_ref="The Steve Jobs Interview: 1993",
                    page_or_section=None,
                    behavior="Prioritizes quality over volume of output",
                    trigger=None,
                    contrast_signal=False,
                    confidence=Confidence.HIGH,
                    raw_text="Quality is more important than quantity.",
                ),
                extraction.ExtractedBehavior(
                    id="b-003",
                    quote="He would delay shipping a product until it was right.",
                    source_ref="Walter Isaacson Biography",
                    page_or_section=None,
                    behavior="Delays shipping to meet quality standards",
                    trigger=None,
                    contrast_signal=False,
                    confidence=Confidence.HIGH,
                    raw_text="He would delay shipping a product until it was right.",
                ),
            ],
            total_quotes=3,
            sources=["The Steve Jobs Interview: 1993", "Walter Isaacson Biography"],
        )

        mock_canonicals = [
            CanonicalBehavior(
                id="cb-001",
                canonical_form="Deliberately declines opportunities to maintain strategic focus",
                behavior_type=None,
                status=BehaviorStatus.CONFIRMED,
                evidence_count=2,
                conditional_candidate=False,
                contradiction_refs=[],
                variants=[
                    BehaviorVariant(extracted_id="b-001", text="Innovation is saying no to a thousand things."),
                    BehaviorVariant(extracted_id="b-002", text="Quality is more important than quantity."),
                ],
                provenance=["b-001", "b-002"],
            ),
        ]
        mock_norm_result = NormalizationResult(
            canonicals=mock_canonicals,
            extraction_count=3,
            canonical_count=1,
            status_breakdown={BehaviorStatus.CONFIRMED: 1},
        )

        typed_canonicals = [
            CanonicalBehavior(
                id="cb-001",
                canonical_form="Deliberately declines opportunities to maintain strategic focus",
                behavior_type=BehaviorType.CORE_PRINCIPLE,
                status=BehaviorStatus.CONFIRMED,
                evidence_count=2,
                conditional_candidate=False,
                contradiction_refs=[],
                variants=mock_canonicals[0].variants,
                provenance=["b-001", "b-002"],
            ),
        ]

        # Patch each pipeline step at module level
        with patch('agentic_mindset.compiler.extraction.extract_behaviors', return_value=ext_result) as mock_extract, \
             patch('agentic_mindset.compiler.normalization.normalize_behaviors', return_value=mock_norm_result) as mock_norm, \
             patch('agentic_mindset.compiler.typer.type_behaviors', return_value=typed_canonicals) as mock_type, \
             patch('agentic_mindset.compiler.mapper.map_to_schema', return_value=[
                 (typed_canonicals[0], "core_principles",
                  "Deliberately declines opportunities to maintain strategic focus",
                  Confidence.HIGH, False)
             ]) as mock_map:

            from agentic_mindset.compiler.compile import compile_pack

            sources = [
                SourceInput(
                    title="The Steve Jobs Interview: 1993",
                    type="interview",
                    url="https://www.wired.com/archives/steve-jobs-1993",
                    text="Innovation is saying no to a thousand things. Quality is more important than quantity.",
                ),
                SourceInput(
                    title="Walter Isaacson — Steve Jobs Biography",
                    type="biography",
                    url="https://www.simonandschuster.com/books/Steve-Jobs",
                    text="He would delay shipping a product until it was right.",
                ),
            ]

            input_data = CompilerInput(
                sources=sources,
                persona_name="Steve Jobs",
                persona_id="steve-jobs",
                type_="historical",
            )
            config = CompilerConfig(model="mock-model", verbose=False)

            result = compile_pack(input_data, config)

            # Verify each step was called
            assert mock_extract.call_count == 1
            assert mock_norm.call_count == 1
            assert mock_type.call_count == 1
            assert mock_map.call_count == 1

            # Verify pipeline results
            assert result.extraction_count == 3
            assert result.canonical_count == 1
            assert result.scores.slot_count == 1
            assert result.scores.coverage > 0
            assert result.quality_gate.status.value in ("pass", "warning")
            assert len(result.slots) == 1
            assert result.slots[0].slot_path == "core_principles"

    def test_compile_pack_sun_tzu_full_pipeline(self):
        """Full pipeline for Sun Tzu — different character archetype, same pipeline."""
        from agentic_mindset.compiler import extraction, normalization, typer, mapper
        from agentic_mindset.compiler.schemas import (
            ExtractionResult, NormalizationResult, SourceInput, CompilerInput, CompilerConfig,
        )

        ext_result = ExtractionResult(
            behaviors=[
                extraction.ExtractedBehavior(
                    id="tz-001",
                    quote="Supreme excellence consists in breaking the enemy's resistance without fighting.",
                    source_ref="The Art of War — Lionel Giles Translation",
                    page_or_section=None,
                    behavior="Seeks victory through positioning and strategic advantage, not direct confrontation",
                    trigger=None,
                    contrast_signal=False,
                    confidence=Confidence.HIGH,
                    raw_text="Supreme excellence consists in breaking the enemy's resistance without fighting.",
                ),
                extraction.ExtractedBehavior(
                    id="tz-002",
                    quote="All warfare is based on deception.",
                    source_ref="The Art of War — Lionel Giles Translation",
                    page_or_section=None,
                    behavior="Uses deception and misdirection as primary strategic tools",
                    trigger=None,
                    contrast_signal=False,
                    confidence=Confidence.HIGH,
                    raw_text="All warfare is based on deception.",
                ),
                extraction.ExtractedBehavior(
                    id="tz-003",
                    quote="Know yourself and know your enemy; in a hundred battles you will never be in peril.",
                    source_ref="The Art of War — Strategic Principles",
                    page_or_section=None,
                    behavior="Prioritizes intelligence gathering and self-assessment before any commitment",
                    trigger=None,
                    contrast_signal=False,
                    confidence=Confidence.HIGH,
                    raw_text="Know yourself and know your enemy; in a hundred battles you will never be in peril.",
                ),
            ],
            total_quotes=3,
            sources=[
                "The Art of War — Lionel Giles Translation",
                "The Art of War — Strategic Principles",
            ],
        )

        mock_canonicals = [
            CanonicalBehavior(
                id="cb-001",
                canonical_form="Seeks victory through positioning and strategic advantage, not direct confrontation",
                behavior_type=None,
                status=BehaviorStatus.CONFIRMED,
                evidence_count=2,
                conditional_candidate=False,
                contradiction_refs=[],
                variants=[
                    BehaviorVariant(extracted_id="tz-001", text="Supreme excellence consists in breaking the enemy's resistance without fighting."),
                    BehaviorVariant(extracted_id="tz-002", text="All warfare is based on deception."),
                ],
                provenance=["tz-001", "tz-002"],
            ),
        ]
        mock_norm_result = NormalizationResult(
            canonicals=mock_canonicals,
            extraction_count=3,
            canonical_count=1,
            status_breakdown={BehaviorStatus.CONFIRMED: 1},
        )

        typed_canonicals = [
            CanonicalBehavior(
                id="cb-001",
                canonical_form="Seeks victory through positioning and strategic advantage, not direct confrontation",
                behavior_type=BehaviorType.CORE_PRINCIPLE,
                status=BehaviorStatus.CONFIRMED,
                evidence_count=2,
                conditional_candidate=False,
                contradiction_refs=[],
                variants=mock_canonicals[0].variants,
                provenance=["tz-001", "tz-002"],
            ),
        ]

        with patch('agentic_mindset.compiler.extraction.extract_behaviors', return_value=ext_result) as mock_extract, \
             patch('agentic_mindset.compiler.normalization.normalize_behaviors', return_value=mock_norm_result) as mock_norm, \
             patch('agentic_mindset.compiler.typer.type_behaviors', return_value=typed_canonicals) as mock_type, \
             patch('agentic_mindset.compiler.mapper.map_to_schema', return_value=[
                 (typed_canonicals[0], "core_principles",
                  "Seeks victory through positioning and strategic advantage, not direct confrontation",
                  Confidence.HIGH, False)
             ]) as mock_map:

            from agentic_mindset.compiler.compile import compile_pack

            sources = [
                SourceInput(
                    title="The Art of War — Lionel Giles Translation",
                    type="book",
                    url="https://suntzusaid.com/book/",
                    text="Supreme excellence consists in breaking the enemy's resistance without fighting. All warfare is based on deception.",
                ),
                SourceInput(
                    title="The Art of War — Strategic Principles",
                    type="book",
                    text="Know yourself and know your enemy; in a hundred battles you will never be in peril.",
                ),
            ]

            input_data = CompilerInput(
                sources=sources,
                persona_name="Sun Tzu",
                persona_id="sun-tzu",
                type_="historical",
            )
            config = CompilerConfig(model="mock-model", verbose=False)

            result = compile_pack(input_data, config)

            # Pipeline steps called
            assert mock_extract.call_count == 1
            assert mock_norm.call_count == 1
            assert mock_type.call_count == 1
            assert mock_map.call_count == 1

            # Results
            assert result.extraction_count == 3
            assert result.canonical_count == 1
            assert result.scores.slot_count == 1
            assert result.scores.coverage > 0
            assert result.quality_gate.status.value in ("pass", "warning")
            assert len(result.slots) == 1
            assert result.slots[0].slot_path == "core_principles"
            # Sun Tzu slot should have indirect/positional behavioral signature
            assert "positioning" in result.slots[0].value.lower() or "deception" in result.slots[0].value.lower()

    def test_compile_pack_empty_sources_returns_empty_result(self):
        """Empty sources should produce empty result without crashing."""
        from agentic_mindset.compiler import extraction, normalization, typer, mapper

        empty_ext = MagicMock(behaviors=[], total_quotes=0, sources=[])
        empty_norm = MagicMock(
            canonicals=[], extraction_count=0, canonical_count=0, status_breakdown={}
        )

        with patch('agentic_mindset.compiler.extraction.extract_behaviors', return_value=empty_ext), \
             patch('agentic_mindset.compiler.normalization.normalize_behaviors', return_value=empty_norm), \
             patch('agentic_mindset.compiler.typer.type_behaviors', return_value=[]), \
             patch('agentic_mindset.compiler.mapper.map_to_schema', return_value=[]):

            from agentic_mindset.compiler.compile import compile_pack
            from agentic_mindset.compiler.schemas import SourceInput, CompilerInput, CompilerConfig

            sources = [SourceInput(title="Empty", type="book", text="")]
            input_data = CompilerInput(
                sources=sources, persona_name="Test", persona_id="test", type_="historical"
            )
            config = CompilerConfig(model="mock", verbose=False)

            result = compile_pack(input_data, config)

            assert result.extraction_count == 0
            assert result.canonical_count == 0
            assert result.scores.slot_count == 0


class TestQualityGateThresholds:
    """Test quality gate threshold values."""

    def test_coverage_threshold_is_060(self):
        assert COVERAGE_THRESHOLD == 0.60

    def test_evidence_threshold_is_050(self):
        assert EVIDENCE_THRESHOLD == 0.50

    def test_slot_weights_defined(self):
        assert len(SLOT_WEIGHTS) > 0
        assert "core_principles" in SLOT_WEIGHTS


class TestCompileScores:
    """Test CompileScores dataclass."""

    def test_scores_has_required_fields(self):
        scores = CompileScores(
            coverage=0.75,
            evidence=0.60,
            extraction_count=5,
            canonical_count=3,
            slot_count=2,
            total_slots=len(SLOT_WEIGHTS),
        )
        assert scores.coverage == 0.75
        assert scores.evidence == 0.60
        assert scores.extraction_count == 5
        assert scores.canonical_count == 3


class TestCompileGate:
    """Test CompileGate dataclass."""

    def test_gate_has_required_fields(self):
        gate = CompileGate(
            name="coverage",
            status=CompileStatus.PASS,
            detail="0.75",
        )
        assert gate.name == "coverage"
        assert gate.status == CompileStatus.PASS
        assert gate.detail == "0.75"

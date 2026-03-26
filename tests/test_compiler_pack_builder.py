"""Tests for pack_builder.py - convert compiled result to YAML files."""
import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from agentic_mindset.compiler.pack_builder import (
    build_pack,
    _fill_decision_framework,
    _derive_id,
    _conf_to_float,
)
from agentic_mindset.compiler.schemas import (
    CompileResult,
    SlotWithProvenance,
    CanonicalBehavior,
    BehaviorVariant,
    BehaviorStatus,
    BehaviorType,
    Confidence,
    SourceCoverage,
    CompileStatus,
    CompileGate,
    CompileQualityGate,
    CompileScores,
    SLOT_WEIGHTS,
)


def make_compile_result(
    slots: list[SlotWithProvenance] = None,
    source_coverage: list[SourceCoverage] = None,
    contradictions: int = 0,
    ambiguous: int = 0,
    review_count: int = 0,
) -> CompileResult:
    if slots is None:
        slots = [
            SlotWithProvenance(
                slot_path="core_principles",
                value="Test principle",
                provenance=[{"canonical_id": "cb-001", "extracted_id": "b-001", "quote": "test", "behavior": "test"}],
                confidence=Confidence.HIGH,
            )
        ]
    if source_coverage is None:
        source_coverage = [
            SourceCoverage(
                source_ref="Source A",
                total_quotes=5,
                used_quotes=3,
                unused_sections=[],
            )
        ]

    return CompileResult(
        scores=CompileScores(
            coverage=0.75,
            evidence=0.6,
            extraction_count=5,
            canonical_count=3,
            slot_count=len(slots),
            total_slots=len(SLOT_WEIGHTS),
        ),
        quality_gate=CompileQualityGate(
            status=CompileStatus.PASS,
            coverage=CompileGate(name="coverage", status=CompileStatus.PASS, detail="0.75"),
            evidence_gate=CompileGate(name="evidence", status=CompileStatus.PASS, detail="0.60"),
            contradictions_gate=CompileGate(name="contradictions", status=CompileStatus.PASS, detail="0"),
            conditional_candidates_gate=CompileGate(name="conditional_candidates", status=CompileStatus.PASS, detail="0"),
            review_required=review_count,
        ),
        source_coverage=source_coverage,
        extraction_count=5,
        canonical_count=3,
        status_breakdown={BehaviorStatus.CONFIRMED: 3},
        canonicals=[
            CanonicalBehavior(
                id="cb-001",
                canonical_form="Test principle",
                behavior_type=BehaviorType.CORE_PRINCIPLE,
                status=BehaviorStatus.CONFIRMED,
                evidence_count=2,
                conditional_candidate=False,
                contradiction_refs=[],
                variants=[BehaviorVariant(extracted_id="b-001", text="test")],
                provenance=["b-001"],
            )
        ],
        slots=slots,
        review_items={
            "contradictions": [{"id": f"cb-{i:03d}", "canonical_form": "test", "variants": []}]
            for i in range(1, contradictions + 1)
        } if contradictions else {"contradictions": []},
        extraction_raw=[],
    )


@pytest.fixture
def output_dir():
    """Temporary output directory."""
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp)


class TestBuildPack:
    """Test build_pack() creates all expected files."""

    def test_all_7_files_created(self, output_dir):
        """All 7 required files should be created."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True, exist_ok=True)
        result = make_compile_result()

        build_pack(result, pack_dir)

        expected_files = [
            "meta.yaml",
            "mindset.yaml",
            "personality.yaml",
            "behavior.yaml",
            "voice.yaml",
            "sources.yaml",
            "_compile_meta.yaml",
        ]
        for fname in expected_files:
            assert (pack_dir / fname).exists(), f"{fname} not created"

    def test_slot_routing_core_principles(self, output_dir):
        """core_principles slot should go to mindset.yaml."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(
            slots=[
                SlotWithProvenance(
                    slot_path="core_principles",
                    value="Clarity is supreme",
                    provenance=[],
                    confidence=Confidence.HIGH,
                )
            ]
        )

        build_pack(result, pack_dir)

        mindset = yaml.safe_load((pack_dir / "mindset.yaml").read_text())
        assert "core_principles" in mindset
        assert len(mindset["core_principles"]) == 1

    def test_slot_routing_decision_framework(self, output_dir):
        """decision_framework slot should go to mindset.yaml."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(
            slots=[
                SlotWithProvenance(
                    slot_path="decision_framework.heuristics",
                    value="Act only when necessary",
                    provenance=[],
                    confidence=Confidence.HIGH,
                )
            ]
        )

        build_pack(result, pack_dir)

        mindset = yaml.safe_load((pack_dir / "mindset.yaml").read_text())
        assert "decision_framework" in mindset
        assert "heuristics" in mindset["decision_framework"]

    def test_slot_routing_interpersonal_style(self, output_dir):
        """interpersonal_style.communication slot should go to personality.yaml."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(
            slots=[
                SlotWithProvenance(
                    slot_path="interpersonal_style.communication",
                    value="Direct and unvarnished",
                    provenance=[],
                    confidence=Confidence.HIGH,
                )
            ]
        )

        build_pack(result, pack_dir)

        personality = yaml.safe_load((pack_dir / "personality.yaml").read_text())
        assert "interpersonal_style" in personality
        assert "communication" in personality["interpersonal_style"]

    def test_slot_routing_conflict_style(self, output_dir):
        """conflict_style slot should go to behavior.yaml."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(
            slots=[
                SlotWithProvenance(
                    slot_path="conflict_style.default",
                    value="Confront directly",
                    provenance=[],
                    confidence=Confidence.HIGH,
                )
            ]
        )

        build_pack(result, pack_dir)

        behavior = yaml.safe_load((pack_dir / "behavior.yaml").read_text())
        assert "conflict_style" in behavior
        assert "default" in behavior["conflict_style"]

    def test_slot_routing_emotional_tendencies(self, output_dir):
        """emotional_tendencies slot should go to personality.yaml."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(
            slots=[
                SlotWithProvenance(
                    slot_path="emotional_tendencies.baseline_mood",
                    value="Calm and measured",
                    provenance=[],
                    confidence=Confidence.HIGH,
                )
            ]
        )

        build_pack(result, pack_dir)

        personality = yaml.safe_load((pack_dir / "personality.yaml").read_text())
        assert "emotional_tendencies" in personality
        assert "baseline_mood" in personality["emotional_tendencies"]

    def test_slot_routing_work_patterns(self, output_dir):
        """work_patterns slot should go to behavior.yaml."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(
            slots=[
                SlotWithProvenance(
                    slot_path="work_patterns",
                    value="Exhaustive preparation",
                    provenance=[],
                    confidence=Confidence.HIGH,
                )
            ]
        )

        build_pack(result, pack_dir)

        behavior = yaml.safe_load((pack_dir / "behavior.yaml").read_text())
        assert "work_patterns" in behavior

    def test_review_files_created_contradictions(self, output_dir):
        """contradictions.yaml should be created in review/ when contradictions exist."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(contradictions=1)
        result.review_items["contradictions"] = [
            {"id": "cb-001", "canonical_form": "test", "variants": []}
        ]

        build_pack(result, pack_dir)

        assert (pack_dir / "review" / "contradictions.yaml").exists()

    def test_review_files_created_ambiguous(self, output_dir):
        """ambiguous.yaml should be created in review/ when ambiguous items exist."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(ambiguous=1)
        result.review_items["ambiguous"] = [
            {"id": "cb-001", "canonical_form": "test", "variants": []}
        ]

        build_pack(result, pack_dir)

        assert (pack_dir / "review" / "ambiguous.yaml").exists()

    def test_review_files_created_medium_confidence(self, output_dir):
        """medium_confidence.yaml should be created in review/ when medium confidence items exist."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(review_count=1)
        result.review_items["medium_confidence"] = [
            {"id": "cb-001", "canonical_form": "test", "slot_path": "core_principles", "value": "test", "confidence": "medium"}
        ]

        build_pack(result, pack_dir)

        assert (pack_dir / "review" / "medium_confidence.yaml").exists()

    def test_sources_yaml_created(self, output_dir):
        """sources.yaml should be created with source coverage info."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result(
            source_coverage=[
                SourceCoverage(
                    source_ref="The Art of War",
                    total_quotes=5,
                    used_quotes=3,
                    unused_sections=[],
                )
            ]
        )

        build_pack(result, pack_dir)

        sources = yaml.safe_load((pack_dir / "sources.yaml").read_text())
        assert "sources" in sources
        assert len(sources["sources"]) == 1

    def test_compile_meta_yaml_created(self, output_dir):
        """_compile_meta.yaml should be created with provenance info."""
        pack_dir = output_dir / "test-persona"
        pack_dir.mkdir(parents=True)
        result = make_compile_result()

        build_pack(result, pack_dir)

        meta = yaml.safe_load((pack_dir / "_compile_meta.yaml").read_text())
        assert "provenance" in meta
        assert "scores" in meta["provenance"]


class TestFillDecisionFramework:
    """Test _fill_decision_framework()."""

    def test_heuristics_path_fills_heuristics_list(self):
        mindset = {}
        slot = SlotWithProvenance(
            slot_path="decision_framework.heuristics",
            value="Act only when necessary",
            provenance=[],
            confidence=Confidence.HIGH,
        )

        _fill_decision_framework(mindset, slot)

        assert "heuristics" in mindset["decision_framework"]
        assert "Act only when necessary" in mindset["decision_framework"]["heuristics"]

    def test_heuristics_sets_default_risk_tolerance(self):
        mindset = {}
        slot = SlotWithProvenance(
            slot_path="decision_framework.heuristics",
            value="Test",
            provenance=[],
            confidence=Confidence.HIGH,
        )

        _fill_decision_framework(mindset, slot)

        assert mindset["decision_framework"]["risk_tolerance"] == "medium"
        assert mindset["decision_framework"]["time_horizon"] == "long-term"

    def test_default_strategy_path(self):
        mindset = {}
        slot = SlotWithProvenance(
            slot_path="decision_framework.default_strategy",
            value="Decide slowly and completely",
            provenance=[],
            confidence=Confidence.HIGH,
        )

        _fill_decision_framework(mindset, slot)

        assert mindset["decision_framework"]["default_strategy"] == "Decide slowly and completely"


class TestDeriveId:
    """Test _derive_id()."""

    def test_spaces_to_hyphens(self):
        assert _derive_id("Steve Jobs") == "steve-jobs"

    def test_lowercase(self):
        assert _derive_id("STEVE-JOBS") == "steve-jobs"


class TestConfToFloat:
    """Test _conf_to_float()."""

    @pytest.mark.parametrize("conf,expected", [
        (Confidence.HIGH, 0.95),
        (Confidence.MEDIUM, 0.75),
        (Confidence.LOW, 0.55),
    ])
    def test_conf_to_float_mapping(self, conf, expected):
        assert _conf_to_float(conf) == expected

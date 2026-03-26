"""Tests for mapper.py - Step 3: schema mapping."""
import pytest
from unittest.mock import MagicMock, patch
from agentic_mindset.compiler.schemas import (
    CanonicalBehavior,
    BehaviorVariant,
    BehaviorStatus,
    BehaviorType,
    Confidence,
)
from agentic_mindset.compiler.llm import LLMClient


class MockLLMClient(LLMClient):
    """Mock LLMClient that bypasses API key check."""

    def __init__(self, response):
        self.model = "mock-model"
        self.temperature = 0.3
        self._api_key = "mock-key"
        self._provider = "mock"
        self._response = response

    def complete_structured(self, prompt, system=None):
        return self._response


def make_canonical(
    id: str = "cb-001",
    canonical_form: str = "test behavior",
    behavior_type: BehaviorType = BehaviorType.COMMUNICATION,
    status: BehaviorStatus = BehaviorStatus.CONFIRMED,
    evidence_count: int = 2,
) -> CanonicalBehavior:
    return CanonicalBehavior(
        id=id,
        canonical_form=canonical_form,
        behavior_type=behavior_type,
        status=status,
        evidence_count=evidence_count,
        conditional_candidate=False,
        contradiction_refs=[],
        variants=[BehaviorVariant(extracted_id="b-001", text="test quote")],
        provenance=["b-001"],
    )


class TestSuggestSlot:
    """Test _suggest_slot() for all BehaviorTypes."""

    @pytest.mark.parametrize("behavior_type,expected_slot", [
        (BehaviorType.CORE_PRINCIPLE, "core_principles"),
        (BehaviorType.DECISION_POLICY, "decision_framework.heuristics"),
        (BehaviorType.COMMUNICATION, "interpersonal_style.communication"),
        (BehaviorType.CONFLICT, "conflict_style.default"),
        (BehaviorType.EMOTIONAL, "emotional_tendencies.baseline_mood"),
        (BehaviorType.DRIVE, "drives"),
        (BehaviorType.EXECUTION, "work_patterns"),
    ])
    def test_all_behavior_types_map_to_slots(self, behavior_type, expected_slot):
        from agentic_mindset.compiler.mapper import _suggest_slot
        cb = make_canonical(behavior_type=behavior_type)
        slot = _suggest_slot(cb)
        assert slot == expected_slot

    def test_unknown_type_defaults_to_core_principles(self):
        from agentic_mindset.compiler.mapper import _suggest_slot
        cb = make_canonical(behavior_type=None)
        slot = _suggest_slot(cb)
        assert slot == "core_principles"


class TestBehaviorTypeToSlotsMapping:
    """Test BEHAVIOR_TYPE_TO_SLOTS covers all 7 BehaviorTypes."""

    def test_all_behavior_types_have_mappings(self):
        from agentic_mindset.compiler.mapper import BEHAVIOR_TYPE_TO_SLOTS
        for bt in BehaviorType:
            assert bt in BEHAVIOR_TYPE_TO_SLOTS
            assert len(BEHAVIOR_TYPE_TO_SLOTS[bt]) > 0


class TestMapToSchema:
    """Test map_to_schema()."""

    def test_confirmed_behavior_with_high_evidence(self):
        """Confirmed behavior with evidence_count >= 2 should have HIGH confidence."""
        canonicals = [
            make_canonical(
                id="cb-001",
                behavior_type=BehaviorType.COMMUNICATION,
                status=BehaviorStatus.CONFIRMED,
                evidence_count=3,
            ),
        ]
        llm = MockLLMClient({})
        from agentic_mindset.compiler.mapper import map_to_schema
        mappings = map_to_schema(canonicals, llm)

        assert len(mappings) == 1
        cb, slot_path, field_value, confidence, needs_review = mappings[0]
        assert slot_path == "interpersonal_style.communication"
        assert confidence == Confidence.HIGH
        assert needs_review is False

    def test_confirmed_behavior_with_low_evidence(self):
        """Confirmed behavior with evidence_count < 2 should have MEDIUM confidence and needs_review=True."""
        canonicals = [
            make_canonical(
                id="cb-001",
                behavior_type=BehaviorType.COMMUNICATION,
                status=BehaviorStatus.CONFIRMED,
                evidence_count=1,
            ),
        ]
        llm = MockLLMClient({})
        from agentic_mindset.compiler.mapper import map_to_schema
        mappings = map_to_schema(canonicals, llm)

        assert len(mappings) == 1
        _, _, _, confidence, needs_review = mappings[0]
        assert confidence == Confidence.MEDIUM
        assert needs_review is True

    def test_ambiguous_behavior_uses_llm_mapping(self):
        """Ambiguous behavior should use LLM for mapping."""
        mock_response = {
            "mappings": [
                {
                    "canonical_id": "cb-001",
                    "slot_path": "interpersonal_style.communication",
                    "field_value": "indirect",
                    "confidence": "medium",
                    "needs_review": True,
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        canonicals = [
            make_canonical(
                id="cb-001",
                behavior_type=BehaviorType.COMMUNICATION,
                status=BehaviorStatus.AMBIGUOUS,
                evidence_count=1,
            ),
        ]
        from agentic_mindset.compiler.mapper import map_to_schema
        mappings = map_to_schema(canonicals, llm)

        assert len(mappings) == 1
        _, slot_path, field_value, confidence, needs_review = mappings[0]
        assert slot_path == "interpersonal_style.communication"
        assert field_value == "indirect"

    def test_contradictory_behavior_uses_llm_mapping(self):
        """Contradictory behavior should use LLM for mapping."""
        mock_response = {
            "mappings": [
                {
                    "canonical_id": "cb-001",
                    "slot_path": "core_principles",
                    "field_value": "test",
                    "confidence": "low",
                    "needs_review": True,
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        canonicals = [
            make_canonical(
                id="cb-001",
                behavior_type=BehaviorType.CORE_PRINCIPLE,
                status=BehaviorStatus.CONTRADICTORY,
                evidence_count=2,
            ),
        ]
        from agentic_mindset.compiler.mapper import map_to_schema
        mappings = map_to_schema(canonicals, llm)

        assert len(mappings) == 1
        _, slot_path, _, _, needs_review = mappings[0]
        assert needs_review is True

    def test_empty_canonicals_returns_empty(self):
        """Empty canonicals list should return empty list."""
        llm = MockLLMClient({})
        from agentic_mindset.compiler.mapper import map_to_schema
        result = map_to_schema([], llm)
        assert result == []

    def test_medium_confidence_from_mapping(self):
        """Mapping from LLM with medium confidence should propagate."""
        mock_response = {
            "mappings": [
                {
                    "canonical_id": "cb-001",
                    "slot_path": "core_principles",
                    "field_value": "test",
                    "confidence": "medium",
                    "needs_review": True,
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        canonicals = [
            make_canonical(
                id="cb-001",
                behavior_type=BehaviorType.CORE_PRINCIPLE,
                status=BehaviorStatus.AMBIGUOUS,
            ),
        ]
        from agentic_mindset.compiler.mapper import map_to_schema
        mappings = map_to_schema(canonicals, llm)

        _, _, _, confidence, _ = mappings[0]
        assert confidence == Confidence.MEDIUM


class TestBuildMappingPrompt:
    """Test build_mapping_prompt()."""

    def test_prompt_contains_canonical_info(self):
        from agentic_mindset.compiler.mapper import build_mapping_prompt
        canonicals = [
            make_canonical(
                id="cb-001",
                canonical_form="speaks directly",
                behavior_type=BehaviorType.COMMUNICATION,
                status=BehaviorStatus.CONFIRMED,
            ),
        ]
        prompt = build_mapping_prompt(canonicals)

        assert "id: cb-001" in prompt
        assert "type: communication" in prompt
        assert "canonical: speaks directly" in prompt
        assert "status: confirmed" in prompt

    def test_prompt_shows_unknown_for_missing_type(self):
        from agentic_mindset.compiler.mapper import build_mapping_prompt
        canonicals = [
            make_canonical(id="cb-001", behavior_type=None),
        ]
        prompt = build_mapping_prompt(canonicals)

        assert "type: unknown" in prompt


class TestMapToSchemaLLMTypeCheck:
    """Test that map_to_schema validates LLMClient type."""

    def test_raises_type_error_for_non_llm_client(self):
        canonicals = [make_canonical()]
        with pytest.raises(TypeError, match="llm must be an LLMClient instance"):
            from agentic_mindset.compiler.mapper import map_to_schema
            map_to_schema(canonicals, "not an llm")

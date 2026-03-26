"""Tests for normalization.py - Step 2: semantic normalization."""
import pytest
from unittest.mock import MagicMock, patch
from agentic_mindset.compiler.schemas import (
    ExtractedBehavior,
    CanonicalBehavior,
    BehaviorVariant,
    NormalizationResult,
    BehaviorStatus,
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


def make_extracted_behavior(
    id: str = "b-001",
    behavior: str = "test behavior",
    quote: str = "test quote",
    confidence: str = "high",
) -> ExtractedBehavior:
    return ExtractedBehavior(
        id=id,
        quote=quote,
        source_ref="Source",
        page_or_section=None,
        behavior=behavior,
        trigger=None,
        contrast_signal=False,
        confidence=Confidence(confidence),
        raw_text=quote,
    )


class TestFallbackNormalize:
    """Test _fallback_normalize()."""

    def test_each_behavior_becomes_own_canonical(self):
        """Each extracted behavior should become its own canonical form."""
        from agentic_mindset.compiler.normalization import _fallback_normalize
        behaviors = [
            make_extracted_behavior(id="b-001", behavior="speaks directly"),
            make_extracted_behavior(id="b-002", behavior="acts decisively"),
        ]

        result = _fallback_normalize(behaviors)

        assert result.canonical_count == 2
        assert len(result.canonicals) == 2

    def test_evidence_count_is_one(self):
        """Evidence count should be 1 for each canonical in fallback."""
        from agentic_mindset.compiler.normalization import _fallback_normalize
        behaviors = [
            make_extracted_behavior(id="b-001", behavior="test"),
        ]

        result = _fallback_normalize(behaviors)

        assert result.canonicals[0].evidence_count == 1

    def test_status_is_confirmed(self):
        """Status should be CONFIRMED for all fallbacks."""
        from agentic_mindset.compiler.normalization import _fallback_normalize
        behaviors = [
            make_extracted_behavior(id="b-001", behavior="test"),
        ]

        result = _fallback_normalize(behaviors)

        assert result.canonicals[0].status == BehaviorStatus.CONFIRMED

    def test_variants_contains_extracted_id_and_quote(self):
        """Each canonical should have a variant with extracted_id and text."""
        from agentic_mindset.compiler.normalization import _fallback_normalize
        behaviors = [
            make_extracted_behavior(id="b-001", behavior="speaks directly", quote="Just do it"),
        ]

        result = _fallback_normalize(behaviors)

        assert len(result.canonicals[0].variants) == 1
        assert result.canonicals[0].variants[0].extracted_id == "b-001"
        assert result.canonicals[0].variants[0].text == "Just do it"

    def test_provenance_contains_extracted_id(self):
        """Provenance should contain the extracted behavior ID."""
        from agentic_mindset.compiler.normalization import _fallback_normalize
        behaviors = [
            make_extracted_behavior(id="b-001", behavior="test"),
        ]

        result = _fallback_normalize(behaviors)

        assert "b-001" in result.canonicals[0].provenance

    def test_status_breakdown_confirmed(self):
        """Status breakdown should show all as CONFIRMED."""
        from agentic_mindset.compiler.normalization import _fallback_normalize
        behaviors = [
            make_extracted_behavior(id="b-001", behavior="test1"),
            make_extracted_behavior(id="b-002", behavior="test2"),
        ]

        result = _fallback_normalize(behaviors)

        assert result.status_breakdown[BehaviorStatus.CONFIRMED] == 2


class TestBuildCanonicalsFromMarkdown:
    """Test _build_canonicals_from_markdown()."""

    def test_minimax_extracted_behaviors_variant(self):
        """MiniMax-specific 'extracted_behaviors' key with canonical_form items."""
        from agentic_mindset.compiler.normalization import _build_canonicals_from_markdown
        result_dict = {
            "extracted_behaviors": [
                {"canonical_form": "speaks directly", "status": "confirmed"},
                {"canonical_form": "acts decisively", "status": "confirmed"},
            ]
        }

        canonicals = _build_canonicals_from_markdown(result_dict)

        assert len(canonicals) == 2
        assert canonicals[0]["canonical_form"] == "speaks directly"
        assert canonicals[1]["canonical_form"] == "acts decisively"

    def test_orphaned_keys_with_section_candidates(self):
        """Orphaned keys (canonical_form, status) with section candidates."""
        from agentic_mindset.compiler.normalization import _build_canonicals_from_markdown
        result_dict = {
            "canonical_form": "speaks directly",
            "status": "confirmed",
            "evidence_count": 3,
            "b-001": {"quote": "Just do it"},
            "b-002": {"quote": "Do it now"},
        }

        canonicals = _build_canonicals_from_markdown(result_dict)

        assert len(canonicals) == 2
        assert canonicals[0]["canonical_form"] == "speaks directly"
        assert canonicals[0]["status"] == "confirmed"

    def test_only_orphaned_keys_single_entry(self):
        """Only orphaned keys with no sections should return single entry."""
        from agentic_mindset.compiler.normalization import _build_canonicals_from_markdown
        result_dict = {
            "canonical_form": "test behavior",
            "status": "confirmed",
            "evidence_count": 1,
        }

        canonicals = _build_canonicals_from_markdown(result_dict)

        assert len(canonicals) == 1
        assert canonicals[0]["canonical_form"] == "test behavior"

    def test_non_dict_returns_empty(self):
        """Non-dict input should return empty list."""
        from agentic_mindset.compiler.normalization import _build_canonicals_from_markdown
        assert _build_canonicals_from_markdown("not a dict") == []
        assert _build_canonicals_from_markdown(None) == []
        assert _build_canonicals_from_markdown([]) == []

    def test_item_section_ids(self):
        """Section IDs matching item_\d+ should be recognized."""
        from agentic_mindset.compiler.normalization import _build_canonicals_from_markdown
        result_dict = {
            "canonical_form": "test",
            "status": "confirmed",
            "item_1": {"behavior": "first behavior"},
            "item_2": {"behavior": "second behavior"},
        }

        canonicals = _build_canonicals_from_markdown(result_dict)

        # Should recognize item_1 and item_2 as sections
        assert len(canonicals) >= 1


class TestNormalizeBehaviors:
    """Test normalize_behaviors() with various LLM response formats."""

    def test_runtime_error_triggers_fallback(self):
        """RuntimeError from LLM should trigger fallback normalization."""

        class FailingLLM(LLMClient):
            def __init__(self):
                self.model = "mock"
                self.temperature = 0.3
                self._api_key = "mock"
                self._provider = "mock"

            def complete_structured(self, prompt, system=None):
                raise RuntimeError("LLM failed")

        behaviors = [
            make_extracted_behavior(id="b-001", behavior="speaks directly"),
        ]

        from agentic_mindset.compiler.normalization import normalize_behaviors
        result = normalize_behaviors(behaviors, FailingLLM())

        # Should use fallback, creating one canonical per behavior
        assert result.canonical_count == 1
        assert result.canonicals[0].canonical_form == "speaks directly"

    def test_canonical_behaviors_from_response(self):
        """Response with canonical_behaviors key should be parsed."""
        mock_response = {
            "canonical_behaviors": [
                {
                    "id": "cb-001",
                    "canonical_form": "speaks directly",
                    "variants": [
                        {"extracted_id": "b-001", "text": "Just do it"},
                    ],
                    "status": "confirmed",
                    "evidence_count": 1,
                    "conditional_candidate": False,
                    "conditional_note": None,
                    "contradiction_refs": [],
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        behaviors = [make_extracted_behavior(id="b-001")]

        from agentic_mindset.compiler.normalization import normalize_behaviors
        result = normalize_behaviors(behaviors, llm)

        assert result.canonical_count == 1
        assert result.canonicals[0].id == "cb-001"
        assert result.canonicals[0].canonical_form == "speaks directly"

    def test_variants_string_parsing(self):
        """Variants as comma-separated string should be parsed."""
        mock_response = {
            "canonical_behaviors": [
                {
                    "id": "cb-001",
                    "canonical_form": "speaks directly",
                    "variants": "Just do it, Do it now, Get it done",
                    "status": "confirmed",
                    "evidence_count": 3,
                    "conditional_candidate": False,
                    "conditional_note": None,
                    "contradiction_refs": [],
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        behaviors = [
            make_extracted_behavior(id="b-001"),
            make_extracted_behavior(id="b-002"),
            make_extracted_behavior(id="b-003"),
        ]

        from agentic_mindset.compiler.normalization import normalize_behaviors
        result = normalize_behaviors(behaviors, llm)

        assert len(result.canonicals[0].variants) == 3

    def test_status_parsing_with_parenthetical(self):
        """Status like 'confirmed (high agreement)' should be parsed correctly."""
        mock_response = {
            "canonical_behaviors": [
                {
                    "id": "cb-001",
                    "canonical_form": "test",
                    "variants": [],
                    "status": "confirmed (high agreement)",
                    "evidence_count": 2,
                    "conditional_candidate": False,
                    "conditional_note": None,
                    "contradiction_refs": [],
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        behaviors = [make_extracted_behavior(id="b-001")]

        from agentic_mindset.compiler.normalization import normalize_behaviors
        result = normalize_behaviors(behaviors, llm)

        assert result.canonicals[0].status == BehaviorStatus.CONFIRMED

    def test_empty_canonical_behaviors_uses_markdown_fallback(self):
        """Empty canonical_behaviors should try markdown fallback."""
        mock_response = {
            "canonical_behaviors": [],
            "extracted_behaviors": [
                {"canonical_form": "from markdown", "status": "confirmed"},
            ],
        }
        llm = MockLLMClient(mock_response)
        behaviors = [make_extracted_behavior(id="b-001")]

        from agentic_mindset.compiler.normalization import normalize_behaviors
        result = normalize_behaviors(behaviors, llm)

        # Should fall back to markdown parsing which finds extracted_behaviors
        assert result.canonical_count >= 1

    def test_status_breakdown_computed(self):
        """Status breakdown should be computed correctly."""
        mock_response = {
            "canonical_behaviors": [
                {
                    "id": "cb-001",
                    "canonical_form": "test1",
                    "variants": [],
                    "status": "confirmed",
                    "evidence_count": 1,
                    "conditional_candidate": False,
                    "conditional_note": None,
                    "contradiction_refs": [],
                },
                {
                    "id": "cb-002",
                    "canonical_form": "test2",
                    "variants": [],
                    "status": "ambiguous",
                    "evidence_count": 1,
                    "conditional_candidate": False,
                    "conditional_note": None,
                    "contradiction_refs": [],
                },
            ]
        }
        llm = MockLLMClient(mock_response)
        behaviors = [
            make_extracted_behavior(id="b-001"),
            make_extracted_behavior(id="b-002"),
        ]

        from agentic_mindset.compiler.normalization import normalize_behaviors
        result = normalize_behaviors(behaviors, llm)

        assert result.status_breakdown[BehaviorStatus.CONFIRMED] == 1
        assert result.status_breakdown[BehaviorStatus.AMBIGUOUS] == 1


class TestBuildNormalizationPrompt:
    """Test build_normalization_prompt()."""

    def test_prompt_contains_behavior_info(self):
        from agentic_mindset.compiler.normalization import build_normalization_prompt
        behaviors = [
            make_extracted_behavior(
                id="b-001",
                behavior="speaks directly",
                quote="Just do it",
                confidence="high",
            ),
        ]
        prompt = build_normalization_prompt(behaviors)

        assert "id: b-001" in prompt
        assert "behavior: speaks directly" in prompt
        assert "confidence: high" in prompt
        assert "Just do it" in prompt

    def test_prompt_shows_contrast_signal(self):
        from agentic_mindset.compiler.normalization import build_normalization_prompt
        eb = make_extracted_behavior(id="b-001", behavior="test", quote="test")
        eb.contrast_signal = True
        prompt = build_normalization_prompt([eb])

        assert "[CONTRAST SIGNAL]" in prompt

    def test_prompt_shows_trigger(self):
        from agentic_mindset.compiler.normalization import build_normalization_prompt
        eb = make_extracted_behavior(id="b-001", behavior="test", quote="test")
        eb.trigger = "when stressed"
        prompt = build_normalization_prompt([eb])

        assert "trigger: when stressed" in prompt


class TestNormalizeBehaviorsLLMTypeCheck:
    """Test that normalize_behaviors validates LLMClient type."""

    def test_raises_type_error_for_non_llm_client(self):
        behaviors = [make_extracted_behavior()]
        with pytest.raises(TypeError, match="llm must be an LLMClient instance"):
            from agentic_mindset.compiler.normalization import normalize_behaviors
            normalize_behaviors(behaviors, "not an llm")

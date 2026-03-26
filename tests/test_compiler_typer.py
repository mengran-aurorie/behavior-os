"""Tests for typer.py - Step 2b: behavior typing."""
import pytest
from unittest.mock import MagicMock, patch
from agentic_mindset.compiler.schemas import (
    CanonicalBehavior,
    BehaviorVariant,
    BehaviorStatus,
    BehaviorType,
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

    def complete(self, prompt, system=None, max_tokens=4096):
        return self._response.get("raw", "")


class FailingLLM(LLMClient):
    """LLM that raises RuntimeError on complete_structured."""

    def __init__(self, raw_response: str = ""):
        self.model = "mock"
        self.temperature = 0.3
        self._api_key = "mock"
        self._provider = "mock"
        self._raw = raw_response

    def complete_structured(self, prompt, system=None):
        raise RuntimeError("LLM failed")

    def complete(self, prompt, system=None, max_tokens=4096):
        return self._raw


def make_canonical(
    id: str = "cb-001",
    canonical_form: str = "test behavior",
    status: BehaviorStatus = BehaviorStatus.CONFIRMED,
    variants: list = None,
) -> CanonicalBehavior:
    if variants is None:
        variants = [BehaviorVariant(extracted_id="b-001", text="test quote")]
    return CanonicalBehavior(
        id=id,
        canonical_form=canonical_form,
        status=status,
        evidence_count=1,
        conditional_candidate=False,
        contradiction_refs=[],
        variants=variants,
        provenance=["b-001"],
    )


class TestParseTypingFromText:
    """Test _parse_typing_from_text() with various formats."""

    def test_canonical_id_found_with_type_keyword(self):
        """Canonical ID found with type keyword nearby should assign that type."""
        from agentic_mindset.compiler.typer import _parse_typing_from_text
        # Window is 100 chars before and 200 after. Use a single canonical
        # with a type keyword in its window that doesn't overlap.
        raw = """
This is a description of behavior cb-001.

cb-001 represents a communication pattern where someone speaks directly.

This is some other unrelated text.
"""
        canonicals = [
            make_canonical(id="cb-001"),
        ]

        result = _parse_typing_from_text(raw, canonicals)

        assert result.get("cb-001") == BehaviorType.COMMUNICATION

    def test_canonical_id_found_without_dash(self):
        """Canonical ID without dash should still be found."""
        from agentic_mindset.compiler.typer import _parse_typing_from_text
        raw = "cb001 is about communication style"
        canonicals = [make_canonical(id="cb-001")]

        result = _parse_typing_from_text(raw, canonicals)

        # Should find cb001 (dash removed) and match "communication"
        assert "cb-001" in result

    def test_no_canonical_ids_scan_entire_response(self):
        """If no canonical IDs found, scan entire response for type keywords."""
        from agentic_mindset.compiler.typer import _parse_typing_from_text
        raw = """
Based on my analysis:
- First behavior is about communication - they are very direct
- Second behavior relates to core_principle - it's a foundational belief
- Third is a decision_policy
"""
        canonicals = [
            make_canonical(id="cb-001"),
            make_canonical(id="cb-002"),
            make_canonical(id="cb-003"),
        ]

        result = _parse_typing_from_text(raw, canonicals)

        # Should assign types in order of appearance
        assert "cb-001" in result
        assert "cb-002" in result
        assert "cb-003" in result

    def test_unknown_type_keyword_defaults(self):
        """Unknown type keywords should not be assigned."""
        from agentic_mindset.compiler.typer import _parse_typing_from_text
        raw = "cb-001 is about something completely unknown and random"
        canonicals = [make_canonical(id="cb-001")]

        result = _parse_typing_from_text(raw, canonicals)

        # Should not assign anything if no valid type found
        assert "cb-001" not in result

    def test_valid_types_cover_all_behavior_types(self):
        """All valid type keywords should be in _VALID_TYPES."""
        from agentic_mindset.compiler.typer import _VALID_TYPES
        expected_types = [
            "core_principle", "decision_policy", "communication",
            "conflict", "emotional", "drive", "execution"
        ]
        for t in expected_types:
            assert t in _VALID_TYPES


class TestTypeBehaviors:
    """Test type_behaviors() with various LLM response formats."""

    def test_yaml_format_typing_results(self):
        """YAML format with typing_results should be parsed."""
        mock_response = {
            "typing_results": [
                {"canonical_id": "cb-001", "behavior_type": "communication"},
                {"canonical_id": "cb-002", "behavior_type": "core_principle"},
            ]
        }
        llm = MockLLMClient(mock_response)
        canonicals = [
            make_canonical(id="cb-001"),
            make_canonical(id="cb-002"),
        ]

        from agentic_mindset.compiler.typer import type_behaviors
        result = type_behaviors(canonicals, llm)

        assert result[0].behavior_type == BehaviorType.COMMUNICATION
        assert result[1].behavior_type == BehaviorType.CORE_PRINCIPLE

    def test_list_format_response(self):
        """List format response should be parsed."""
        mock_response = [
            {"canonical_id": "cb-001", "behavior_type": "conflict"},
        ]
        llm = MockLLMClient(mock_response)
        canonicals = [make_canonical(id="cb-001")]

        from agentic_mindset.compiler.typer import type_behaviors
        result = type_behaviors(canonicals, llm)

        assert result[0].behavior_type == BehaviorType.CONFLICT

    def test_runtime_error_triggers_fallback(self):
        """RuntimeError should trigger _parse_typing_from_text fallback."""
        raw_text = "cb-001 is about communication - they speak directly."
        llm = FailingLLM(raw_response=raw_text)
        canonicals = [make_canonical(id="cb-001")]

        from agentic_mindset.compiler.typer import type_behaviors
        result = type_behaviors(canonicals, llm)

        assert result[0].behavior_type == BehaviorType.COMMUNICATION

    def test_empty_canonicals_returns_empty(self):
        """Empty canonicals list should return empty list."""
        llm = MockLLMClient({})
        from agentic_mindset.compiler.typer import type_behaviors
        result = type_behaviors([], llm)
        assert result == []

    def test_behavior_type_assignment_to_canonicals(self):
        """Behavior types should be assigned to the correct canonicals."""
        mock_response = {
            "typing_results": [
                {"canonical_id": "cb-001", "behavior_type": "drive"},
            ]
        }
        llm = MockLLMClient(mock_response)
        canonicals = [
            make_canonical(id="cb-001"),
            make_canonical(id="cb-002"),
        ]

        from agentic_mindset.compiler.typer import type_behaviors
        result = type_behaviors(canonicals, llm)

        assert result[0].behavior_type == BehaviorType.DRIVE
        assert result[1].behavior_type is None  # Not assigned


class TestBuildTypingPrompt:
    """Test build_typing_prompt()."""

    def test_prompt_contains_canonical_info(self):
        from agentic_mindset.compiler.typer import build_typing_prompt
        canonicals = [
            make_canonical(id="cb-001", canonical_form="speaks directly"),
        ]
        prompt = build_typing_prompt(canonicals)

        assert "id: cb-001" in prompt
        assert "canonical_form: speaks directly" in prompt
        assert "status: confirmed" in prompt

    def test_prompt_contains_variant_text(self):
        from agentic_mindset.compiler.typer import build_typing_prompt
        canonicals = [
            make_canonical(
                id="cb-001",
                variants=[
                    BehaviorVariant(extracted_id="b-001", text="Just do it now"),
                    BehaviorVariant(extracted_id="b-002", text="Get it done today"),
                ],
            ),
        ]
        prompt = build_typing_prompt(canonicals)

        # Just checks that it contains variant text
        assert "Just do it now" in prompt

    def test_prompt_limits_variant_text_to_60_chars(self):
        from agentic_mindset.compiler.typer import build_typing_prompt
        long_text = "This is a very long variant text that exceeds sixty characters"
        canonicals = [
            make_canonical(
                id="cb-001",
                variants=[
                    BehaviorVariant(extracted_id="b-001", text=long_text),
                ],
            ),
        ]
        prompt = build_typing_prompt(canonicals)

        # Should truncate to 60 chars
        assert long_text[:60] in prompt


class TestTypeBehaviorsLLMTypeCheck:
    """Test that type_behaviors validates LLMClient type."""

    def test_raises_type_error_for_non_llm_client(self):
        canonicals = [make_canonical()]
        with pytest.raises(TypeError, match="llm must be an LLMClient instance"):
            from agentic_mindset.compiler.typer import type_behaviors
            type_behaviors(canonicals, "not an llm")

"""Tests for extraction.py - Step 1: extract behavior candidates."""
import pytest
from unittest.mock import MagicMock, patch
from agentic_mindset.compiler.schemas import (
    ExtractedBehavior,
    ExtractionResult,
    SourceInput,
    Confidence,
    CanonicalBehavior,
    BehaviorVariant,
    BehaviorStatus,
)
from agentic_mindset.compiler.llm import LLMClient


class MockLLMClient(LLMClient):
    """Mock LLMClient that bypasses API key check."""

    def __init__(self, response):
        # Skip parent's __init__ which checks for API keys
        self.model = "mock-model"
        self.temperature = 0.3
        self._api_key = "mock-key"
        self._provider = "mock"
        self._response = response

    def complete_structured(self, prompt, system=None):
        return self._response


class TestExtractBehaviors:
    """Test extract_behaviors() with various LLM response formats."""

    def test_list_response(self):
        """Bare list returned by LLM should be processed as behaviors."""
        mock_response = [
            {
                "id": "b-001",
                "quote": "Just do it",
                "source_ref": "Source A",
                "behavior": "takes direct action",
                "trigger": None,
                "contrast_signal": False,
                "confidence": "high",
            },
            {
                "id": "b-002",
                "quote": "He never waits",
                "source_ref": "Source B",
                "behavior": "acts without hesitation",
                "trigger": None,
                "contrast_signal": False,
                "confidence": "medium",
            },
        ]
        llm = MockLLMClient(mock_response)
        sources = [
            SourceInput(title="Source A", text="Content A", type="book"),
            SourceInput(title="Source B", text="Content B", type="book"),
        ]

        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)

        assert len(result.behaviors) == 2
        assert result.total_quotes == 2
        assert result.sources == ["Source A", "Source B"]
        assert result.behaviors[0].quote == "Just do it"
        assert result.behaviors[0].confidence == Confidence.HIGH
        assert result.behaviors[1].confidence == Confidence.MEDIUM

    def test_dict_with_extracted_behaviors(self):
        """Response with 'extracted_behaviors' key."""
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test quote",
                    "source_ref": "Source",
                    "behavior": "test behavior",
                    "trigger": None,
                    "contrast_signal": False,
                    "confidence": "high",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]

        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)

        assert len(result.behaviors) == 1
        assert result.behaviors[0].id == "b-001"

    def test_dict_with_behaviors_key(self):
        """Response with 'behaviors' key (JSON schema variant)."""
        mock_response = {
            "behaviors": [
                {
                    "id": "b-001",
                    "quote": "test quote",
                    "source_ref": "Source",
                    "behavior": "test behavior",
                    "trigger": None,
                    "contrast_signal": False,
                    "confidence": "high",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]

        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)

        assert len(result.behaviors) == 1

    def test_dict_with_items_key(self):
        """Response with 'items' key (markdown table format variant)."""
        mock_response = {
            "items": [
                {
                    "id": "b-001",
                    "quote": "test quote",
                    "source_ref": "Source",
                    "behavior": "test behavior",
                    "trigger": None,
                    "contrast_signal": False,
                    "confidence": "high",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]

        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)

        assert len(result.behaviors) == 1


class TestFieldNormalization:
    """Test field name normalization across schema variants."""

    def test_quote_normalization(self):
        """quote, source_text, text, exact_quote should all map to quote."""
        variants = [
            {"quote": "value1"},
            {"source_text": "value2"},
            {"text": "value3"},
            {"exact_quote": "value4"},
            {"description": "value5"},
        ]
        for variant in variants:
            mock_response = {
                "extracted_behaviors": [
                    {
                        "id": "b-001",
                        "behavior": "test",
                        **variant,
                        "source_ref": "Source",
                        "trigger": None,
                        "contrast_signal": False,
                        "confidence": "high",
                    }
                ]
            }
            llm = MockLLMClient(mock_response)
            sources = [SourceInput(title="Source", text="Content", type="book")]
            from agentic_mindset.compiler.extraction import extract_behaviors
            result = extract_behaviors(sources, llm)
            assert result.behaviors[0].quote in variant.values()

    def test_behavior_normalization(self):
        """behavior, what_he_does, action should all map to behavior."""
        variants = [
            {"behavior": "value1"},
            {"what_he_does": "value2"},
            {"action": "value3"},
        ]
        for variant in variants:
            mock_response = {
                "extracted_behaviors": [
                    {
                        "id": "b-001",
                        "quote": "test quote",
                        "source_ref": "Source",
                        **variant,
                        "trigger": None,
                        "contrast_signal": False,
                        "confidence": "high",
                    }
                ]
            }
            llm = MockLLMClient(mock_response)
            sources = [SourceInput(title="Source", text="Content", type="book")]
            from agentic_mindset.compiler.extraction import extract_behaviors
            result = extract_behaviors(sources, llm)
            assert result.behaviors[0].behavior in variant.values()

    def test_source_ref_normalization(self):
        """source_ref and source should both map to source_ref."""
        for field in ["source_ref", "source"]:
            mock_response = {
                "extracted_behaviors": [
                    {
                        "id": "b-001",
                        "quote": "test quote",
                        field: "Source Title",
                        "behavior": "test behavior",
                        "trigger": None,
                        "contrast_signal": False,
                        "confidence": "high",
                    }
                ]
            }
            llm = MockLLMClient(mock_response)
            sources = [SourceInput(title="Source", text="Content", type="book")]
            from agentic_mindset.compiler.extraction import extract_behaviors
            result = extract_behaviors(sources, llm)
            assert result.behaviors[0].source_ref == "Source Title"


class TestConfidenceEnumParsing:
    """Test Confidence enum parsing from strings."""

    def test_high_confidence(self):
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test",
                    "source_ref": "Source",
                    "behavior": "test",
                    "trigger": None,
                    "contrast_signal": False,
                    "confidence": "high",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)
        assert result.behaviors[0].confidence == Confidence.HIGH

    def test_medium_confidence(self):
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test",
                    "source_ref": "Source",
                    "behavior": "test",
                    "trigger": None,
                    "contrast_signal": False,
                    "confidence": "medium",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)
        assert result.behaviors[0].confidence == Confidence.MEDIUM

    def test_low_confidence(self):
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test",
                    "source_ref": "Source",
                    "behavior": "test",
                    "trigger": None,
                    "contrast_signal": False,
                    "confidence": "low",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)
        assert result.behaviors[0].confidence == Confidence.LOW

    def test_invalid_confidence_defaults_to_medium(self):
        """Invalid confidence string should default to medium."""
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test",
                    "source_ref": "Source",
                    "behavior": "test",
                    "trigger": None,
                    "contrast_signal": False,
                    "confidence": "invalid",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)
        assert result.behaviors[0].confidence == Confidence.MEDIUM


class TestTriggerHandling:
    """Test trigger null handling."""

    def test_trigger_null_string(self):
        """trigger: "null" string should be converted to None."""
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test",
                    "source_ref": "Source",
                    "behavior": "test",
                    "trigger": "null",
                    "contrast_signal": False,
                    "confidence": "high",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)
        assert result.behaviors[0].trigger is None

    def test_trigger_none(self):
        """trigger: None should remain None."""
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test",
                    "source_ref": "Source",
                    "behavior": "test",
                    "trigger": None,
                    "contrast_signal": False,
                    "confidence": "high",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)
        assert result.behaviors[0].trigger is None

    def test_trigger_with_value(self):
        """trigger with an actual value should be preserved."""
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test",
                    "source_ref": "Source",
                    "behavior": "test",
                    "trigger": "when facing criticism",
                    "contrast_signal": False,
                    "confidence": "high",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)
        assert result.behaviors[0].trigger == "when facing criticism"


class TestContrastSignalParsing:
    """Test contrast_signal boolean parsing."""

    @pytest.mark.parametrize("input_val,expected", [
        (True, True),
        (False, False),
        ("true", True),
        ("yes", True),
        ("1", True),
        ("false", False),
        ("no", False),
        ("0", False),
    ])
    def test_contrast_signal_parsing(self, input_val, expected):
        mock_response = {
            "extracted_behaviors": [
                {
                    "id": "b-001",
                    "quote": "test",
                    "source_ref": "Source",
                    "behavior": "test",
                    "trigger": None,
                    "contrast_signal": input_val,
                    "confidence": "high",
                }
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)
        assert result.behaviors[0].contrast_signal is expected


class TestBuildExtractionPrompt:
    """Test build_extraction_prompt()."""

    def test_prompt_format(self):
        from agentic_mindset.compiler.extraction import build_extraction_prompt
        sources = [
            SourceInput(title="Book A", text="Content A", type="book", url=None),
            SourceInput(title="Article B", text="Long content B", type="article", url="https://example.com"),
        ]
        prompt = build_extraction_prompt(sources)

        assert "=== SOURCE 1: Book A ===" in prompt
        assert "Type: book" in prompt
        assert "Content:\nContent A" in prompt
        assert "=== SOURCE 2: Article B ===" in prompt
        assert "Type: article" in prompt
        assert "URL: https://example.com" in prompt
        # Content should be truncated to 3000 chars
        assert len(prompt.split("Content:\n")[1].split("\n\n")[0]) <= 3000

    def test_llm_type_check(self):
        """extract_behaviors should raise TypeError if llm is not LLMClient."""
        sources = [SourceInput(title="Source", text="Content", type="book")]
        with pytest.raises(TypeError, match="llm must be an LLMClient instance"):
            from agentic_mindset.compiler.extraction import extract_behaviors
            extract_behaviors(sources, "not an llm client")


class TestExtractionResult:
    """Test ExtractionResult structure."""

    def test_total_quotes_matches_behaviors_count(self):
        mock_response = {
            "extracted_behaviors": [
                {"id": f"b-{i:03d}", "quote": f"quote{i}", "source_ref": "Source",
                 "behavior": f"behavior{i}", "trigger": None, "contrast_signal": False, "confidence": "high"}
                for i in range(5)
            ]
        }
        llm = MockLLMClient(mock_response)
        sources = [SourceInput(title="Source", text="Content", type="book")]
        from agentic_mindset.compiler.extraction import extract_behaviors
        result = extract_behaviors(sources, llm)

        assert len(result.behaviors) == 5
        assert result.total_quotes == 5

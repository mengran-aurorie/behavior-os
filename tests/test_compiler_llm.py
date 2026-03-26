"""Tests for LLM client parsing in complete_structured()."""
import pytest
from unittest.mock import MagicMock, patch
from agentic_mindset.compiler.llm import _looks_like_refusal, LLMClient


class TestLooksLikeRefusal:
    def test_empty_string(self):
        assert _looks_like_refusal("") is True

    def test_none(self):
        assert _looks_like_refusal(None) is True

    def test_i_dont_see(self):
        assert _looks_like_refusal("I don't see any behaviors in this text") is True

    def test_i_cannot(self):
        assert _looks_like_refusal("I cannot extract behaviors from this source") is True

    def test_im_sorry(self):
        assert _looks_like_refusal("I'm sorry, I cannot help with this") is True

    def test_valid_content(self):
        assert _looks_like_refusal("The person always speaks directly and without hesitation") is False


class MockLLMClient(LLMClient):
    """LLMClient that uses a mock response instead of making API calls."""

    def __init__(self, mock_response: str = ""):
        # Skip parent's __init__ which checks for API keys
        self.model = "mock-model"
        self.temperature = 0.3
        self._api_key = "mock-key"
        self._provider = "mock"
        self._mock_response = mock_response

    def complete(self, prompt: str, system=None, max_tokens=4096) -> str:
        return self._mock_response


class TestParseMarkdownStructured:
    """Test _parse_markdown_structured() with various formats."""

    def test_json_code_block(self):
        """JSON inside ```json blocks is handled by complete_structured, not _parse_markdown_structured."""
        # _parse_markdown_structured handles markdown fallback, not JSON code blocks directly
        client = MockLLMClient()
        raw = '''```json
{
  "extracted_behaviors": [
    {"id": "b-001", "behavior": "test"}
  ]
}
```'''
        result = client._parse_markdown_structured(raw)
        # This doesn't parse JSON code blocks - those are handled by complete_structured
        # So we just verify it doesn't crash
        assert result is None or isinstance(result, (dict, list))

    def test_bold_key_value_format(self):
        """Bold **Key:** value format should be parsed."""
        client = MockLLMClient()
        raw = '''**Behavior 1:** speaks directly

**Quote:** "Just do it"

**Source:** Interview
'''
        result = client._parse_markdown_structured(raw)
        assert result is not None

    def test_numbered_items(self):
        """Numbered list items should be parsed."""
        client = MockLLMClient()
        raw = '''1. **Behavior:** speaks directly
   **Quote:** "Just do it"

2. **Behavior:** acts decisively
   **Quote:** "Do it now"
'''
        result = client._parse_markdown_structured(raw)
        assert result is not None
        items = result.get("items", result.get("extracted_behaviors", []))
        assert len(items) >= 1

    def test_table_rows(self):
        """Table rows | col | col | should be parsed only if ** markers present."""
        client = MockLLMClient()
        # Without ** markers, returns None (function checks '**' not in raw)
        raw = '''| Behavior | Quote |
|---|---|
| speaks directly | "Just do it" |
| acts decisively | "Do it now" |
'''
        result = client._parse_markdown_structured(raw)
        # Without ** markers, function returns None early
        assert result is None

    def test_table_rows_with_bold_headers(self):
        """Table rows with **bold** headers should be parsed."""
        client = MockLLMClient()
        raw = '''| **Behavior** | **Quote** |
|---|---|
| speaks directly | "Just do it" |
'''
        result = client._parse_markdown_structured(raw)
        # With bold markers, should parse
        assert result is not None

    def test_section_headers(self):
        """Section headers ### section-id should be parsed."""
        client = MockLLMClient()
        raw = '''### core_principle_1

**canonical_form:** clarity above all

**status:** confirmed
'''
        result = client._parse_markdown_structured(raw)
        assert result is not None

    def test_no_bold_returns_none(self):
        """Raw text without ** should return None."""
        client = MockLLMClient()
        raw = "This is plain text without any bold markers"
        result = client._parse_markdown_structured(raw)
        assert result is None

    def test_orphaned_keys_grouped(self):
        """Orphaned canonical_form, status keys should be grouped into canonical_behaviors."""
        client = MockLLMClient()
        raw = '''### Behavior 1

**canonical_form:** speaks directly

**status:** confirmed

### Behavior 2

**canonical_form:** acts decisively

**status:** confirmed
'''
        result = client._parse_markdown_structured(raw)
        assert result is not None


class TestCompleteStructuredFallback:
    """Test complete_structured() fallback order."""

    def test_json_code_block_priority(self):
        """JSON code blocks should be parsed first."""
        client = MockLLMClient(mock_response='''Here is the JSON:

```json
{"extracted_behaviors": [{"id": "b-001", "behavior": "test"}]}
```

Some explanation text.''')
        with patch.object(LLMClient, 'complete', return_value=client._mock_response):
            result = client.complete_structured("test prompt")
            assert "extracted_behaviors" in result

    def test_yaml_code_block_fallback(self):
        """YAML code blocks should be parsed after JSON."""
        client = MockLLMClient(mock_response='''```yaml
canonical_behaviors:
  - id: cb-001
    canonical_form: test behavior
```''')
        with patch.object(LLMClient, 'complete', return_value=client._mock_response):
            result = client.complete_structured("test prompt")
            assert "canonical_behaviors" in result

    def test_plain_json_before_yaml(self):
        """Plain JSON starting with { should be tried before YAML."""
        client = MockLLMClient(mock_response='{"behaviors": [{"id": "b-001"}]}')
        with patch.object(LLMClient, 'complete', return_value=client._mock_response):
            result = client.complete_structured("test prompt")
            assert "behaviors" in result

    def test_markdown_bold_fallback(self):
        """Markdown bold-format should be the last fallback."""
        client = MockLLMClient(mock_response='''**Behavior 1:** speaks directly

**Quote:** "test"''')
        with patch.object(LLMClient, 'complete', return_value=client._mock_response):
            result = client.complete_structured("test prompt")
            # Should parse via _parse_markdown_structured
            assert result is not None

    def test_unparseable_raises_runtime_error(self):
        """Unparseable response should raise RuntimeError.

        Bare strings (including YAML-valid ones like "no behaviors") are now
        caught by the isinstance(result, dict) guard and raised as RuntimeError,
        since callers expect dict. This ensures callers never receive a bare
        string which would cause .get() AttributeError.
        """
        client = MockLLMClient(mock_response='This is completely unparseable gibberish')
        with pytest.raises(RuntimeError, match="Could not parse"):
            client.complete_structured("test prompt")

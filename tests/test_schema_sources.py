from agentic_mindset.schema.sources import SourcesSchema
import pytest
from pydantic import ValidationError

def test_valid_sources():
    s = SourcesSchema(sources=[
        {"title": "The Art of War", "type": "book", "accessed": "2026-03-22"},
        {"title": "Biography", "type": "article", "accessed": "2026-03-22"},
        {"title": "Commentary", "type": "book", "accessed": "2026-03-22"},
    ])
    assert s.sources[0].type == "book"

def test_invalid_source_type():
    with pytest.raises(ValidationError):
        SourcesSchema(sources=[
            {"title": "X", "type": "tweet", "accessed": "2026-03-22"},
            {"title": "Y", "type": "book", "accessed": "2026-03-22"},
            {"title": "Z", "type": "book", "accessed": "2026-03-22"},
        ])

def test_minimum_three_sources_enforced():
    with pytest.raises(ValidationError):
        SourcesSchema(sources=[
            {"title": "Only one", "type": "book", "accessed": "2026-03-22"},
        ])

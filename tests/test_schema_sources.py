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


def test_source_new_types_valid():
    """New source types: biography, film, novel, essay, letter, speech."""
    from agentic_mindset.schema.sources import Source
    for t in ("biography", "film", "novel", "essay", "letter", "speech"):
        s = Source(title="x", type=t, accessed="2026-03-25")
        assert s.type == t


def test_source_evidence_level_optional():
    from agentic_mindset.schema.sources import Source
    s = Source(title="The Art of War", type="book", accessed="2026-03-25")
    assert s.evidence_level is None


def test_source_evidence_level_primary():
    from agentic_mindset.schema.sources import Source
    s = Source(title="x", type="book", accessed="2026-03-25", evidence_level="primary")
    assert s.evidence_level == "primary"


def test_source_evidence_level_invalid_raises():
    from agentic_mindset.schema.sources import Source
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Source(title="x", type="book", accessed="2026-03-25", evidence_level="weak")

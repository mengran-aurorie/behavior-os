import pytest
from pydantic import ValidationError
from agentic_mindset.schema.meta import MetaSchema


def test_valid_historical():
    data = {
        "id": "sun-tzu",
        "name": "Sun Tzu",
        "version": "1.0.0",
        "schema_version": "1.0",
        "type": "historical",
        "description": "Military strategist.",
        "tags": ["strategy"],
        "authors": [{"name": "A", "url": "https://github.com/a"}],
        "created": "2026-03-22",
    }
    m = MetaSchema(**data)
    assert m.id == "sun-tzu"
    assert m.type == "historical"


def test_valid_fictional():
    data = {
        "id": "naruto",
        "name": "Naruto Uzumaki",
        "version": "1.0.0",
        "schema_version": "1.0",
        "type": "fictional",
        "description": "Ninja protagonist.",
        "tags": ["anime"],
        "authors": [{"name": "A", "url": "https://github.com/a"}],
        "created": "2026-03-22",
    }
    m = MetaSchema(**data)
    assert m.type == "fictional"


def test_invalid_type_rejects_living():
    with pytest.raises(ValidationError):
        MetaSchema(
            id="someone",
            name="Someone",
            version="1.0.0",
            schema_version="1.0",
            type="living",
            description=".",
            tags=[],
            authors=[],
            created="2026-03-22",
        )


def test_id_must_be_kebab_case():
    with pytest.raises(ValidationError):
        MetaSchema(
            id="Sun Tzu",
            name="Sun Tzu",
            version="1.0.0",
            schema_version="1.0",
            type="historical",
            description=".",
            tags=[],
            authors=[],
            created="2026-03-22",
        )


def test_invalid_version_format():
    with pytest.raises(ValidationError):
        MetaSchema(
            id="sun-tzu",
            name="Sun Tzu",
            version="v1",
            schema_version="1.0",
            type="historical",
            description=".",
            tags=[],
            authors=[],
            created="2026-03-22",
        )


def test_invalid_schema_version_format():
    with pytest.raises(ValidationError):
        MetaSchema(
            id="sun-tzu",
            name="Sun Tzu",
            version="1.0.0",
            schema_version="latest",
            type="historical",
            description=".",
            tags=[],
            authors=[],
            created="2026-03-22",
        )

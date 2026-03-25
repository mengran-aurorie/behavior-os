import pytest
import warnings
import yaml
from pathlib import Path
from agentic_mindset.pack import CharacterPack, PackLoadError, SchemaVersionWarning


def test_load_valid_pack(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    assert pack.meta.id == "sun-tzu"
    assert pack.meta.type == "historical"
    assert pack.mindset.decision_framework.risk_tolerance == "medium"
    assert pack.personality.traits[0].intensity == 0.9
    assert pack.behavior.decision_speed == "deliberate"
    assert pack.voice.tone == "measured, aphoristic"
    assert len(pack.sources.sources) == 3


def test_missing_required_file(minimal_pack_dir):
    (minimal_pack_dir / "mindset.yaml").unlink()
    with pytest.raises(PackLoadError, match="mindset.yaml"):
        CharacterPack.load(minimal_pack_dir)


def test_invalid_yaml_raises(minimal_pack_dir):
    (minimal_pack_dir / "meta.yaml").write_text("invalid: [yaml: content")
    with pytest.raises(PackLoadError):
        CharacterPack.load(minimal_pack_dir)


def test_schema_validation_error_raises(minimal_pack_dir):
    data = yaml.safe_load((minimal_pack_dir / "behavior.yaml").read_text())
    data["decision_speed"] = "chaotic"
    (minimal_pack_dir / "behavior.yaml").write_text(yaml.dump(data))
    with pytest.raises(PackLoadError, match="behavior.yaml"):
        CharacterPack.load(minimal_pack_dir)


def test_current_schema_version_loads_cleanly(minimal_pack_dir):
    """schema_version 1.1 (the fixture default after Task 3) loads with no warning."""
    # NOTE: conftest still writes schema_version "1.0" at this point in the plan.
    # This test will FAIL until Task 3 bumps conftest to 1.1.
    # Skip it for now with: pytest -k "not test_current_schema_version_loads_cleanly"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pack = CharacterPack.load(minimal_pack_dir)
    assert pack.meta.schema_version == "1.1"


def test_old_schema_version_emits_warning(minimal_pack_dir):
    """schema_version 1.0 is supported but emits SchemaVersionWarning."""
    data = yaml.safe_load((minimal_pack_dir / "meta.yaml").read_text())
    data["schema_version"] = "1.0"
    (minimal_pack_dir / "meta.yaml").write_text(yaml.dump(data))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pack = CharacterPack.load(minimal_pack_dir)

    version_warnings = [w for w in caught if issubclass(w.category, SchemaVersionWarning)]
    assert len(version_warnings) == 1
    assert "1.0" in str(version_warnings[0].message)
    assert "1.1" in str(version_warnings[0].message)


def test_unknown_schema_version_raises(minimal_pack_dir):
    """Unrecognised schema_version is a hard error."""
    data = yaml.safe_load((minimal_pack_dir / "meta.yaml").read_text())
    data["schema_version"] = "9.9"
    (minimal_pack_dir / "meta.yaml").write_text(yaml.dump(data))

    with pytest.raises(PackLoadError, match="schema_version"):
        CharacterPack.load(minimal_pack_dir)

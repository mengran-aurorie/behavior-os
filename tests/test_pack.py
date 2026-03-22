import pytest
import shutil
import yaml
from pathlib import Path
from agentic_mindset.pack import CharacterPack, PackLoadError


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

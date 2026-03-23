import shutil
import json
import yaml
import pytest
from typer.testing import CliRunner
from agentic_mindset.cli import app, _format_output

runner = CliRunner(mix_stderr=False)


@pytest.fixture
def gen_registry(minimal_pack_dir, tmp_path):
    """Registry dir with sun-tzu and marcus-aurelius packs."""
    import shutil, yaml

    # sun-tzu
    sun = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, sun)

    # marcus-aurelius — minimal clone with different id/name
    marcus = tmp_path / "marcus-aurelius"
    shutil.copytree(minimal_pack_dir, marcus)
    meta = yaml.safe_load((marcus / "meta.yaml").read_text())
    meta["id"] = "marcus-aurelius"
    meta["name"] = "Marcus Aurelius"
    (marcus / "meta.yaml").write_text(yaml.dump(meta))
    return tmp_path


def test_validate_valid_pack(minimal_pack_dir):
    result = runner.invoke(app, ["validate", str(minimal_pack_dir)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_missing_file(minimal_pack_dir):
    (minimal_pack_dir / "mindset.yaml").unlink()
    result = runner.invoke(app, ["validate", str(minimal_pack_dir)])
    assert result.exit_code != 0
    assert "mindset.yaml" in result.output


def test_preview_single_pack(minimal_pack_dir):
    result = runner.invoke(app, ["preview", str(minimal_pack_dir)])
    assert result.exit_code == 0
    assert "THINKING FRAMEWORK" in result.output
    assert "Sun Tzu" in result.output


def test_init_creates_files(tmp_path):
    result = runner.invoke(app, ["init", "my-hero", "--type", "fictional", "--output", str(tmp_path)])
    assert result.exit_code == 0
    for fname in ["meta.yaml", "mindset.yaml", "personality.yaml", "behavior.yaml", "voice.yaml", "sources.yaml"]:
        assert (tmp_path / "my-hero" / fname).exists()


def test_init_rejects_invalid_type(tmp_path):
    result = runner.invoke(app, ["init", "my-hero", "--type", "living", "--output", str(tmp_path)])
    assert result.exit_code != 0


def test_list_shows_characters(minimal_pack_dir, tmp_path):
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    result = runner.invoke(app, ["list", "--registry", str(tmp_path)])
    assert result.exit_code == 0
    assert "sun-tzu" in result.output


def test_list_empty_registry(tmp_path):
    result = runner.invoke(app, ["list", "--registry", str(tmp_path)])
    assert result.exit_code == 0
    assert "no characters" in result.output.lower()


def test_preview_fusion_respects_registry_flag(minimal_pack_dir, tmp_path):
    """--registry flag must be respected in --fusion preview."""
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    fusion_file = tmp_path / "blend.yaml"
    fusion_file.write_text(yaml.dump({
        "characters": [{"id": "sun-tzu", "weight": 1.0}],
        "fusion_strategy": "blend",
    }))
    result = runner.invoke(app, [
        "preview", "--fusion", str(fusion_file),
        "--registry", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert "Sun Tzu" in result.output


def test_format_output_text():
    assert _format_output("hello", "text") == "hello"


def test_format_output_anthropic_json():
    result = json.loads(_format_output("hello", "anthropic-json"))
    assert result == {"type": "text", "text": "hello"}


def test_format_output_debug_json():
    meta = {"characters": ["sun-tzu"], "weights": [1.0], "strategy": "blend", "schema_version": "1.0"}
    result = json.loads(_format_output("hello", "debug-json", meta=meta))
    assert result["type"] == "text"
    assert result["text"] == "hello"
    assert result["meta"] == meta


def test_format_output_debug_json_no_timestamp():
    """debug-json must not include a timestamp (determinism guarantee)."""
    meta = {"characters": ["sun-tzu"], "weights": [1.0], "strategy": "blend", "schema_version": "1.0"}
    result = json.loads(_format_output("hello", "debug-json", meta=meta))
    assert "timestamp" not in result
    assert "timestamp" not in result.get("meta", {})


def test_format_output_invalid_fmt_raises():
    with pytest.raises(ValueError, match="Unknown output format"):
        _format_output("hello", "xml")


def test_generate_single_character_text(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert "THINKING FRAMEWORK" in result.output
    assert "Sun Tzu" in result.output


def test_generate_unknown_character_exits_1(gen_registry):
    result = runner.invoke(app, [
        "generate", "unknown-char",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "unknown-char" in result.stderr
    assert "mindset list" in result.stderr

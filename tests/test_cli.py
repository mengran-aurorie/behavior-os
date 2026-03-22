import shutil
import yaml
import pytest
from typer.testing import CliRunner
from agentic_mindset.cli import app

runner = CliRunner()


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

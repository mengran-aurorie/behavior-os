import os
import shutil
import json
import yaml
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from agentic_mindset.cli import app, _format_output, render_for_runtime

runner = CliRunner(mix_stderr=False)


@pytest.fixture
def gen_registry(minimal_pack_dir, tmp_path):
    """Registry dir with sun-tzu and marcus-aurelius packs."""
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


def test_generate_weights_count_mismatch(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu", "marcus-aurelius",
        "--weights", "6",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "--weights has 1 values but 2 character IDs" in result.stderr


def test_generate_weights_negative(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--weights", "-1",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "positive numbers" in result.stderr


def test_generate_weights_all_zero(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--weights", "0",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "cannot all be zero" in result.stderr


def test_generate_weights_non_numeric(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--weights", "abc",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "comma-separated numbers" in result.stderr


def test_generate_weights_trailing_comma(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--weights", "6,",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "comma-separated numbers" in result.stderr


def test_generate_weights_leading_comma(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--weights", ",6",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "comma-separated numbers" in result.stderr


def test_generate_weights_double_comma(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--weights", "6,,4",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "comma-separated numbers" in result.stderr


def test_generate_unknown_strategy_exits_1(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--strategy", "bogus",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "bogus" in result.stderr


def test_generate_multi_character_blend(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu", "marcus-aurelius",
        "--weights", "6,4",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert "Sun Tzu" in result.output or "Marcus Aurelius" in result.output


def test_generate_strategy_dominant(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu", "marcus-aurelius",
        "--strategy", "dominant",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert "THINKING FRAMEWORK" in result.output


def test_generate_strategy_sequential(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu", "marcus-aurelius",
        "--strategy", "sequential",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert "THINKING FRAMEWORK" in result.output


def test_generate_strategy_sequential_with_weights_warns(gen_registry):
    """Sequential + --weights emits a warning to stderr but still succeeds."""
    result = runner.invoke(app, [
        "generate", "sun-tzu", "marcus-aurelius",
        "--strategy", "sequential",
        "--weights", "6,4",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert "--weights ignored" in result.stderr


def test_generate_equal_weights_by_default(gen_registry):
    """When --weights is omitted, characters receive equal weight."""
    result = runner.invoke(app, [
        "generate", "sun-tzu", "marcus-aurelius",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert "50%" in result.output or "Sun Tzu" in result.output


def test_generate_format_anthropic_json(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--format", "anthropic-json",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    block = json.loads(result.output)
    assert block["type"] == "text"
    assert "THINKING FRAMEWORK" in block["text"]


def test_generate_format_debug_json(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--format", "debug-json",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["type"] == "text"
    assert "THINKING FRAMEWORK" in data["text"]
    assert data["meta"]["characters"] == ["sun-tzu"]
    assert data["meta"]["strategy"] == "blend"
    assert data["meta"]["schema_version"] == "1.0"
    assert "timestamp" not in data
    assert "timestamp" not in data["meta"]


def test_generate_format_debug_json_weights(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu", "marcus-aurelius",
        "--weights", "6,4",
        "--format", "debug-json",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["meta"]["characters"] == ["sun-tzu", "marcus-aurelius"]
    assert abs(data["meta"]["weights"][0] - 0.6) < 1e-9
    assert abs(data["meta"]["weights"][1] - 0.4) < 1e-9


def test_generate_explain_goes_to_stderr(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu", "marcus-aurelius",
        "--weights", "6,4",
        "--explain",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert "sun-tzu (60%)" in result.stderr
    assert "marcus-aurelius (40%)" in result.stderr
    assert "blend" in result.stderr
    assert "1.0" in result.stderr
    # stdout is the compiled text, not the explain summary
    assert "THINKING FRAMEWORK" in result.output


def test_generate_explain_does_not_pollute_stdout(gen_registry):
    """--explain summary must NOT appear in stdout."""
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--explain",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert "Characters:" not in result.output
    assert "Strategy:" not in result.output


def test_generate_output_writes_file(gen_registry, tmp_path):
    out_file = tmp_path / "system_prompt.txt"
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--output", str(out_file),
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert result.output.strip() == ""   # stdout is empty on success
    assert out_file.exists()
    content = out_file.read_text()
    assert "THINKING FRAMEWORK" in content


def test_generate_output_with_explain_empty_stdout(gen_registry, tmp_path):
    """--output + --explain: file gets content, stdout empty, stderr has summary."""
    out_file = tmp_path / "out.txt"
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--output", str(out_file),
        "--explain",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    assert result.output.strip() == ""
    assert "Characters:" in result.stderr
    assert out_file.read_text() != ""


def test_generate_output_unwritable_path(gen_registry):
    result = runner.invoke(app, [
        "generate", "sun-tzu",
        "--output", "/nonexistent_dir/out.txt",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 1
    assert "cannot write to" in result.stderr


def test_generate_duplicate_id_treated_as_single(gen_registry):
    """Duplicate IDs produce same result as single ID (weights summed → normalized to 1.0)."""
    single = runner.invoke(app, [
        "generate", "sun-tzu",
        "--registry", str(gen_registry),
    ])
    duplicate = runner.invoke(app, [
        "generate", "sun-tzu", "sun-tzu",
        "--registry", str(gen_registry),
    ])
    assert single.exit_code == 0
    assert duplicate.exit_code == 0
    assert single.output == duplicate.output


def test_generate_duplicate_id_with_weights_summed(gen_registry):
    """sun-tzu sun-tzu --weights 3,7 → one entry weight 10 → normalized 1.0."""
    result = runner.invoke(app, [
        "generate", "sun-tzu", "sun-tzu",
        "--weights", "3,7",
        "--format", "debug-json",
        "--registry", str(gen_registry),
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["meta"]["characters"] == ["sun-tzu"]
    assert abs(data["meta"]["weights"][0] - 1.0) < 1e-9


def test_render_for_runtime_inject(minimal_pack_dir):
    from agentic_mindset.pack import CharacterPack
    from agentic_mindset.context import ContextBlock
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    result = render_for_runtime(block, "inject")
    assert "THINKING FRAMEWORK" in result
    assert isinstance(result, str)


def test_render_for_runtime_text_equals_inject(minimal_pack_dir):
    from agentic_mindset.pack import CharacterPack
    from agentic_mindset.context import ContextBlock
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    assert render_for_runtime(block, "text") == render_for_runtime(block, "inject")


def test_render_for_runtime_unknown_fmt_raises(minimal_pack_dir):
    from agentic_mindset.pack import CharacterPack
    from agentic_mindset.context import ContextBlock
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    with pytest.raises(ValueError, match="Unknown runtime format"):
        render_for_runtime(block, "xml")


def test_run_single_persona_oneshot(gen_registry):
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                "Analyze competitor strategy",
            ])
    assert result.exit_code == 0
    mock_sub.assert_called_once()
    call_args = mock_sub.call_args[0][0]
    assert call_args[0] == "claude"
    assert "--append-system-prompt-file" in call_args
    assert "Analyze competitor strategy" in call_args


def test_run_uses_inject_format_by_default(gen_registry):
    captured = {}
    original_render = render_for_runtime
    def spy(block, fmt):
        captured["fmt"] = fmt
        return original_render(block, fmt)
    with patch("agentic_mindset.cli.render_for_runtime", side_effect=spy):
        with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
            with patch("agentic_mindset.cli.subprocess.run", return_value=MagicMock(returncode=0)):
                runner.invoke(app, [
                    "run", "claude",
                    "--persona", "sun-tzu",
                    "--registry", str(gen_registry),
                    "q",
                ])
    assert captured.get("fmt") == "inject"


def test_run_query_passed_verbatim(gen_registry):
    query = "How do I handle a negotiation under pressure?"
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
                query,
            ])
    assert result.exit_code == 0
    call_args = mock_sub.call_args[0][0]
    assert query in call_args


def test_run_multi_persona_blend(gen_registry):
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--persona", "marcus-aurelius",
                "--weights", "6,4",
                "--registry", str(gen_registry),
                "query",
            ])
    assert result.exit_code == 0
    mock_sub.assert_called_once()

def test_run_interactive_mode(gen_registry):
    """No query argument → interactive mode → subprocess called without query."""
    with patch("agentic_mindset.cli.shutil.which", return_value="/usr/bin/claude"):
        with patch("agentic_mindset.cli.subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, [
                "run", "claude",
                "--persona", "sun-tzu",
                "--registry", str(gen_registry),
            ])
    assert result.exit_code == 0
    call_args = mock_sub.call_args[0][0]
    # Interactive mode: only 3 elements (runtime, flag, tmpfile) — no query
    assert len(call_args) == 3
    assert call_args[0] == "claude"
    assert call_args[1] == "--append-system-prompt-file"

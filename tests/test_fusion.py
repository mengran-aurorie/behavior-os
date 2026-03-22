import shutil
import yaml
import pytest
from pathlib import Path
from agentic_mindset.fusion import FusionEngine, FusionConfig, FusionStrategy
from agentic_mindset.registry import CharacterRegistry


def _patch_meta(pack_dir: Path, new_id: str, new_name: str):
    meta_path = pack_dir / "meta.yaml"
    data = yaml.safe_load(meta_path.read_text())
    data["id"] = new_id
    data["name"] = new_name
    meta_path.write_text(yaml.dump(data))


def _make_registry(minimal_pack_dir, tmp_path, *extra_ids):
    """Create a registry with sun-tzu and any extra packs (same content, different id/name)."""
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    for extra_id in extra_ids:
        extra_dir = tmp_path / extra_id
        shutil.copytree(minimal_pack_dir, extra_dir)
        _patch_meta(extra_dir, extra_id, extra_id.replace("-", " ").title())
    return CharacterRegistry(search_paths=[tmp_path])


def test_fuse_single_pack(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path)
    engine = FusionEngine(registry)
    block = engine.fuse([("sun-tzu", 1.0)])
    assert "Sun Tzu" in block.preamble


def test_weights_normalized(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    block = engine.fuse([("sun-tzu", 0.6), ("marcus-aurelius", 0.6)])
    assert "50%" in block.preamble


def test_zero_weight_raises(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path)
    engine = FusionEngine(registry)
    with pytest.raises(ValueError, match="sum to zero"):
        engine.fuse([("sun-tzu", 0.0)])


def test_sequential_list_order_not_weight_order(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    # sun-tzu has weight 0.1 but is listed first — must appear first in preamble
    config = FusionConfig(
        characters=[("sun-tzu", 0.1), ("marcus-aurelius", 0.9)],
        fusion_strategy=FusionStrategy.sequential,
    )
    block = engine.fuse_config(config)
    assert block.preamble.index("Sun Tzu") < block.preamble.index("Marcus Aurelius")
    assert "%" not in block.preamble


def test_sequential_emits_warning_when_weights_differ(minimal_pack_dir, tmp_path, capsys):
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    config = FusionConfig(
        characters=[("sun-tzu", 0.7), ("marcus-aurelius", 0.3)],
        fusion_strategy=FusionStrategy.sequential,
    )
    engine.fuse_config(config)
    captured = capsys.readouterr()
    assert "sequential" in captured.err.lower() or "warning" in captured.err.lower()


def test_dominant_highest_weight_leads(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    # marcus-aurelius listed second but has higher weight — must lead in dominant mode
    config = FusionConfig(
        characters=[("sun-tzu", 0.3), ("marcus-aurelius", 0.7)],
        fusion_strategy=FusionStrategy.dominant,
    )
    block = engine.fuse_config(config)
    assert block.preamble.index("Marcus Aurelius") < block.preamble.index("Sun Tzu")


def test_blend_higher_weight_leads(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    block = engine.fuse([("sun-tzu", 0.3), ("marcus-aurelius", 0.7)])
    assert block.preamble.index("Marcus Aurelius") < block.preamble.index("Sun Tzu")

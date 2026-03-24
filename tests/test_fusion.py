import shutil
import yaml
import pytest
from pathlib import Path
from agentic_mindset.fusion import FusionEngine, FusionConfig, FusionStrategy, FusionReport
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


def test_fusion_report_default_construction():
    """FusionReport() can be constructed with no arguments."""
    report = FusionReport()
    assert report.personas == []
    assert report.strategy == ""
    assert report.removed_items == []
    assert report.dominant_character is None


def test_prepare_packs_returns_normalized_sorted(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    packs = engine.prepare_packs([("sun-tzu", 0.3), ("marcus-aurelius", 0.7)])
    # higher weight first
    assert packs[0][0].meta.id == "marcus-aurelius"
    assert packs[1][0].meta.id == "sun-tzu"
    # weights normalized (sum = 1.0)
    total = sum(w for _, w in packs)
    assert abs(total - 1.0) < 1e-9


def test_prepare_packs_single_character(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path)
    engine = FusionEngine(registry)
    packs = engine.prepare_packs([("sun-tzu", 1.0)])
    assert len(packs) == 1
    assert packs[0][0].meta.id == "sun-tzu"
    assert abs(packs[0][1] - 1.0) < 1e-9


def test_prepare_packs_zero_weights_raises(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path)
    engine = FusionEngine(registry)
    with pytest.raises(ValueError, match="sum to zero"):
        engine.prepare_packs([("sun-tzu", 0.0)])


def test_fusion_report_filled_by_fuse(minimal_pack_dir, tmp_path):
    """fuse() fills all FusionReport fields when report is provided."""
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    report = FusionReport()
    engine.fuse([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)], report=report)
    assert len(report.personas) == 2
    assert report.personas[0][0] == "sun-tzu"   # higher weight first
    assert report.strategy == "blend"
    assert report.dominant_character == "sun-tzu"


def test_fusion_report_dominant_none_for_equal_weights(minimal_pack_dir, tmp_path):
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    report = FusionReport()
    engine.fuse([("sun-tzu", 1.0), ("marcus-aurelius", 1.0)], report=report)
    assert report.dominant_character is None


def test_fusion_report_removed_items(minimal_pack_dir, tmp_path):
    """Duplicate items across packs are captured in report.removed_items."""
    # sun-tzu and marcus-aurelius are clones — all of marcus's items are duplicates
    registry = _make_registry(minimal_pack_dir, tmp_path, "marcus-aurelius")
    engine = FusionEngine(registry)
    report = FusionReport()
    engine.fuse([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)], report=report)
    assert len(report.removed_items) > 0


def test_fuse_without_report_unchanged(minimal_pack_dir, tmp_path):
    """Calling fuse() without report= produces same ContextBlock as before."""
    registry = _make_registry(minimal_pack_dir, tmp_path)
    engine = FusionEngine(registry)
    block = engine.fuse([("sun-tzu", 1.0)])
    assert "Sun Tzu" in block.preamble  # existing behavior unchanged

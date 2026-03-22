import os
import shutil
import pytest
from pathlib import Path
from agentic_mindset.registry import CharacterRegistry


def test_resolve_by_path(minimal_pack_dir):
    registry = CharacterRegistry()
    pack = registry.load_path(minimal_pack_dir)
    assert pack.meta.id == "sun-tzu"


def test_resolve_by_id_from_explicit_dir(minimal_pack_dir, tmp_path):
    named_dir = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named_dir)
    registry = CharacterRegistry(search_paths=[tmp_path])
    pack = registry.load_id("sun-tzu")
    assert pack.meta.id == "sun-tzu"


def test_id_not_found_raises(tmp_path):
    registry = CharacterRegistry(search_paths=[tmp_path])
    with pytest.raises(KeyError, match="unknown-id"):
        registry.load_id("unknown-id")


def test_local_overrides_registry(minimal_pack_dir, tmp_path):
    dir1 = tmp_path / "reg1" / "sun-tzu"
    dir2 = tmp_path / "reg2" / "sun-tzu"
    shutil.copytree(minimal_pack_dir, dir1)
    shutil.copytree(minimal_pack_dir, dir2)
    registry = CharacterRegistry(search_paths=[tmp_path / "reg1", tmp_path / "reg2"])
    pack = registry.load_id("sun-tzu")
    assert pack.path == dir1


def test_list_ids_returns_all_characters(minimal_pack_dir, tmp_path):
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    registry = CharacterRegistry(search_paths=[tmp_path])
    ids = registry.list_ids()
    assert "sun-tzu" in ids


def test_env_var_registry_path(minimal_pack_dir, tmp_path, monkeypatch):
    named = tmp_path / "sun-tzu"
    shutil.copytree(minimal_pack_dir, named)
    monkeypatch.setenv("AGENTIC_MINDSET_REGISTRY", str(tmp_path))
    registry = CharacterRegistry()
    pack = registry.load_id("sun-tzu")
    assert pack.meta.id == "sun-tzu"

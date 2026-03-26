"""Sanity test: every character pack in the registry loads without error."""

import pytest
from pathlib import Path
from agentic_mindset.pack import CharacterPack
from agentic_mindset.registry import CharacterRegistry


CHARS = Path("characters")


def test_all_character_packs_load():
    """Every character in the local characters/ dir must load without raising."""
    errors = []
    for char_dir in sorted(CHARS.iterdir()):
        if not char_dir.is_dir():
            continue
        try:
            pack = CharacterPack.load(char_dir)
        except Exception as e:
            errors.append(f"{char_dir.name}: {e}")
            continue
        # Smoke-check required fields
        assert pack.meta is not None, f"{char_dir.name}: missing meta"
        assert pack.meta.id == char_dir.name, f"{char_dir.name}: id mismatch"
        assert pack.mindset is not None, f"{char_dir.name}: missing mindset"
        assert pack.personality is not None, f"{char_dir.name}: missing personality"
        assert pack.behavior is not None, f"{char_dir.name}: missing behavior"
        assert pack.voice is not None, f"{char_dir.name}: missing voice"
        assert pack.sources is not None, f"{char_dir.name}: missing sources"

    if errors:
        pytest.fail("Failed to load:\n" + "\n".join(errors))


def test_all_chars_validate():
    """Every character must pass registry validation."""
    errors = []
    reg = CharacterRegistry()
    for char_id in sorted(reg.list_ids()):
        try:
            reg.load_id(char_id)
        except Exception as e:
            errors.append(f"{char_id}: {e}")

    if errors:
        pytest.fail("Validation failed:\n" + "\n".join(errors))


def test_all_chars_have_required_mindset_fields():
    """Every mindset.yaml must have core_principles, decision_framework, thinking_patterns."""
    errors = []
    for char_dir in sorted(CHARS.iterdir()):
        if not char_dir.is_dir():
            continue
        try:
            pack = CharacterPack.load(char_dir)
        except Exception:
            continue

        mindset = pack.mindset
        missing = []
        if not getattr(mindset, "core_principles", None):
            missing.append("core_principles")
        if not getattr(mindset, "decision_framework", None):
            missing.append("decision_framework")
        if not getattr(mindset, "thinking_patterns", None):
            missing.append("thinking_patterns")
        if missing:
            errors.append(f"{char_dir.name}: missing {', '.join(missing)}")

    if errors:
        pytest.fail("\n".join(errors))


def test_all_chars_have_required_behavior_fields():
    """Every behavior.yaml must have work_patterns, decision_speed, execution_style."""
    errors = []
    for char_dir in sorted(CHARS.iterdir()):
        if not char_dir.is_dir():
            continue
        try:
            pack = CharacterPack.load(char_dir)
        except Exception:
            continue

        behavior = pack.behavior
        missing = []
        if not getattr(behavior, "work_patterns", None):
            missing.append("work_patterns")
        if not hasattr(behavior, "decision_speed") or behavior.decision_speed is None:
            missing.append("decision_speed")
        if not getattr(behavior, "execution_style", None):
            missing.append("execution_style")
        if missing:
            errors.append(f"{char_dir.name}: missing {', '.join(missing)}")

    if errors:
        pytest.fail("\n".join(errors))


def test_all_chars_have_required_voice_fields():
    """Every voice.yaml must have tone, vocabulary, sentence_style."""
    errors = []
    for char_dir in sorted(CHARS.iterdir()):
        if not char_dir.is_dir():
            continue
        try:
            pack = CharacterPack.load(char_dir)
        except Exception:
            continue

        voice = pack.voice
        missing = []
        if not getattr(voice, "tone", None):
            missing.append("tone")
        if not getattr(voice, "vocabulary", None):
            missing.append("vocabulary")
        if not getattr(voice, "sentence_style", None):
            missing.append("sentence_style")
        if missing:
            errors.append(f"{char_dir.name}: missing {', '.join(missing)}")

    if errors:
        pytest.fail("\n".join(errors))


def test_all_chars_have_minimum_three_sources():
    """Every sources.yaml must have at least 3 sources."""
    errors = []
    for char_dir in sorted(CHARS.iterdir()):
        if not char_dir.is_dir():
            continue
        try:
            pack = CharacterPack.load(char_dir)
        except Exception:
            continue

        count = len(pack.sources.sources)
        if count < 3:
            errors.append(f"{char_dir.name}: has {count} sources, needs at least 3")

    if errors:
        pytest.fail("\n".join(errors))

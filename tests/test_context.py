from agentic_mindset.context import ContextBlock
from agentic_mindset.pack import CharacterPack


def test_to_prompt_contains_all_sections(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    prompt = block.to_prompt()
    assert "THINKING FRAMEWORK" in prompt
    assert "PERSONALITY" in prompt
    assert "BEHAVIORAL TENDENCIES" in prompt
    assert "VOICE & STYLE" in prompt


def test_to_prompt_contains_preamble(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    prompt = block.to_prompt()
    assert "Sun Tzu" in prompt


def test_to_prompt_xml_tagged(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    xml = block.to_prompt(output_format="xml_tagged")
    assert "<character-context>" in xml
    assert "<thinking-framework>" in xml
    assert "</character-context>" in xml


def test_sections_not_empty(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    assert block.thinking_framework
    assert block.personality
    assert block.behavioral_tendencies
    assert block.voice_and_style


def test_preamble_shows_weights(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    assert "100%" in block.preamble


def test_no_weights_in_preamble_when_show_weights_false(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)], show_weights=False)
    assert "%" not in block.preamble
    assert "Sun Tzu" in block.preamble

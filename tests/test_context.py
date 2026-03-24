from agentic_mindset.context import ContextBlock, render_inject_block
from agentic_mindset.pack import CharacterPack
from agentic_mindset.fusion import FusionReport


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


def test_from_packs_report_removed_items(minimal_pack_dir):
    """from_packs() appends duplicate items to report.removed_items."""
    pack = CharacterPack.load(minimal_pack_dir)
    report = FusionReport()
    # Fuse the same pack twice — second pack's items are all duplicates
    ContextBlock.from_packs([(pack, 0.6), (pack, 0.4)], report=report)
    assert len(report.removed_items) > 0


def test_from_packs_no_report_unchanged(minimal_pack_dir):
    """from_packs() without report= behaves identically to before."""
    pack = CharacterPack.load(minimal_pack_dir)
    block = ContextBlock.from_packs([(pack, 1.0)])
    assert "Sun Tzu" in block.preamble


def test_render_inject_single_character_structure(minimal_pack_dir):
    """4 sections present when anti_patterns is empty (no ANTI-PATTERNS section)."""
    pack = CharacterPack.load(minimal_pack_dir)
    result = render_inject_block([(pack, 1.0)])
    assert "DECISION POLICY:" in result
    assert "UNCERTAINTY HANDLING:" in result
    assert "INTERACTION RULES:" in result
    assert "STYLE:" in result
    assert "ANTI-PATTERNS:" not in result   # minimal_pack_dir has no anti_patterns


def test_render_inject_preamble(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    result = render_inject_block([(pack, 1.0)])
    assert "Sun Tzu (100%)" in result


def test_render_inject_decision_policy_content(minimal_pack_dir):
    """DECISION POLICY contains core principle and approach; risk NOT in this section."""
    pack = CharacterPack.load(minimal_pack_dir)
    result = render_inject_block([(pack, 1.0)])
    dp_section = result.split("UNCERTAINTY HANDLING:")[0]
    assert "Strategic deception" in dp_section    # core_principle.description
    assert "Win before the battle begins" in dp_section  # decision_framework.approach
    assert "risk_tolerance" not in dp_section     # risk belongs in UNCERTAINTY HANDLING


def test_render_inject_uncertainty_handling_content(minimal_pack_dir):
    """UNCERTAINTY HANDLING contains risk_tolerance, time_horizon, and stress_response."""
    pack = CharacterPack.load(minimal_pack_dir)
    result = render_inject_block([(pack, 1.0)])
    uh_start = result.index("UNCERTAINTY HANDLING:")
    uh_end = result.index("INTERACTION RULES:")
    uh_section = result[uh_start:uh_end]
    assert "risk_tolerance: medium" in uh_section
    assert "time_horizon: long-term" in uh_section
    assert "withdraws to observe" in uh_section   # stress_response


def test_render_inject_interaction_rules_content(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    result = render_inject_block([(pack, 1.0)])
    ir_start = result.index("INTERACTION RULES:")
    ir_end = result.index("STYLE:")
    ir_section = result[ir_start:ir_end]
    assert "indirect, layered" in ir_section       # interpersonal_style.communication
    assert "leads through positioning" in ir_section  # interpersonal_style.leadership
    assert "avoidant of direct confrontation" in ir_section  # conflict_style


def test_render_inject_style_content(minimal_pack_dir):
    pack = CharacterPack.load(minimal_pack_dir)
    result = render_inject_block([(pack, 1.0)])
    style_start = result.index("STYLE:")
    style_section = result[style_start:]
    assert "measured, aphoristic" in style_section  # voice.tone
    assert "position" in style_section              # vocabulary.preferred
    assert "rush" in style_section                  # vocabulary.avoided
    assert "short aphorisms" in style_section       # sentence_style


def test_render_inject_anti_patterns_present(anti_patterns_pack_dir):
    """When anti_patterns field is populated, ANTI-PATTERNS section appears."""
    pack = CharacterPack.load(anti_patterns_pack_dir)
    result = render_inject_block([(pack, 1.0)])
    assert "ANTI-PATTERNS:" in result
    assert "Do not commit before the position is secured" in result
    assert "Do not telegraph intent" in result


def test_render_inject_multi_character_dedup(minimal_pack_dir, tmp_path):
    """When two packs share items, second pack's duplicates are skipped."""
    import shutil
    from agentic_mindset.pack import CharacterPack
    # Clone sun-tzu as marcus-aurelius
    marcus_dir = tmp_path / "marcus"
    shutil.copytree(minimal_pack_dir, marcus_dir)
    import yaml
    meta = yaml.safe_load((marcus_dir / "meta.yaml").read_text())
    meta["id"] = "marcus-aurelius"
    meta["name"] = "Marcus Aurelius"
    (marcus_dir / "meta.yaml").write_text(yaml.dump(meta))

    pack1 = CharacterPack.load(minimal_pack_dir)
    pack2 = CharacterPack.load(marcus_dir)
    result = render_inject_block([(pack1, 0.6), (pack2, 0.4)])
    # Preamble shows both
    assert "Sun Tzu" in result
    assert "Marcus Aurelius" in result
    # risk_tolerance line appears only once (deduped)
    assert result.count("risk_tolerance: medium") == 1


def test_render_inject_confidence_none_sorts_last(minimal_pack_dir, tmp_path):
    """Principles with confidence=None appear after those with explicit confidence."""
    import shutil, yaml
    from agentic_mindset.pack import CharacterPack
    pack_dir = tmp_path / "test-pack"
    shutil.copytree(minimal_pack_dir, pack_dir)
    mindset = yaml.safe_load((pack_dir / "mindset.yaml").read_text())
    mindset["core_principles"] = [
        {"description": "No confidence principle", "detail": "detail A"},  # confidence=None
        {"description": "High confidence principle", "detail": "detail B", "confidence": 0.95},
    ]
    (pack_dir / "mindset.yaml").write_text(yaml.dump(mindset))
    pack = CharacterPack.load(pack_dir)
    result = render_inject_block([(pack, 1.0)])
    high_pos = result.index("High confidence principle")
    none_pos = result.index("No confidence principle")
    assert high_pos < none_pos   # high confidence appears first

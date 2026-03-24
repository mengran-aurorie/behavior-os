import pytest
from agentic_mindset.resolver.policies import (
    SLOT_CONFLICT_PAIRS,
    MODIFIER_FALLBACK_TEMPLATES,
    MODIFIER_THRESHOLD,
    SOFT_THRESHOLD,
    get_fallback_conditions,
)


def test_thresholds_ordered():
    assert 0 < MODIFIER_THRESHOLD < SOFT_THRESHOLD < 1.0


def test_conflict_pairs_communication_has_indirect_direct():
    assert ("indirect", "direct") in SLOT_CONFLICT_PAIRS["communication"]


def test_conflict_pairs_conflict_style_has_avoidant_confrontational():
    assert ("avoidant", "confrontational") in SLOT_CONFLICT_PAIRS["conflict_style"]


def test_conflict_pairs_leadership_has_positioning_directive():
    assert ("positioning", "directive") in SLOT_CONFLICT_PAIRS["leadership"]


def test_conflict_pairs_are_one_directional_consumers_check_both():
    """Pairs are stored in one direction only. Consumers must check (a,b) AND (b,a)."""
    pairs = SLOT_CONFLICT_PAIRS["communication"]
    assert ("indirect", "direct") in pairs
    assert ("direct", "indirect") not in pairs  # only one direction stored


def test_fallback_template_wildcard_primary():
    assert ("communication", "*", "direct") in MODIFIER_FALLBACK_TEMPLATES
    assert ("conflict_style", "*", "confrontational") in MODIFIER_FALLBACK_TEMPLATES


def test_get_fallback_conditions_wildcard():
    conds = get_fallback_conditions("communication", "indirect", "direct")
    assert "clarity_critical" in conds
    assert "time_pressure" in conds


def test_get_fallback_conditions_specific_overrides_wildcard():
    """A specific (slot, primary, secondary) entry should take precedence over wildcard."""
    import agentic_mindset.resolver.policies as p
    # Temporarily add a specific entry
    original = p.MODIFIER_FALLBACK_TEMPLATES.copy()
    p.MODIFIER_FALLBACK_TEMPLATES[("communication", "indirect", "direct")] = ["high_tension"]
    try:
        conds = p.get_fallback_conditions("communication", "indirect", "direct")
        assert conds == ["high_tension"]
    finally:
        p.MODIFIER_FALLBACK_TEMPLATES.clear()
        p.MODIFIER_FALLBACK_TEMPLATES.update(original)


def test_get_fallback_conditions_returns_empty_for_unknown():
    conds = get_fallback_conditions("communication", "indirect", "layered")
    assert conds == []


def test_get_fallback_conditions_normalizes_case():
    conds = get_fallback_conditions("communication", "INDIRECT", "DIRECT")
    assert "clarity_critical" in conds


import shutil
import yaml
from pathlib import Path
from agentic_mindset.registry import CharacterRegistry
from agentic_mindset.fusion import FusionEngine
from agentic_mindset.resolver.resolver import ConflictResolver
from agentic_mindset.ir.models import BehaviorIR, ResolvedSlot


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, allow_unicode=True))


def _engine(registry_path):
    reg = CharacterRegistry(search_paths=[registry_path])
    return FusionEngine(reg)


# ── single character ──────────────────────────────────────────────────────────

def test_resolver_single_character_no_conflict(conflict_registry):
    engine = _engine(conflict_registry)
    packs = engine.prepare_packs([("sun-tzu", 1.0)])
    ir = ConflictResolver().resolve(packs)
    assert isinstance(ir, BehaviorIR)
    assert ir.preamble.personas == [("sun-tzu", 1.0)]
    assert ir.communication is not None
    assert ir.communication.has_conflict is False
    assert ir.communication.modifiers == []
    assert ir.communication.primary.value == "indirect"


# ── conflict detection ────────────────────────────────────────────────────────

def test_resolver_conflict_produces_fallback_modifier(conflict_registry):
    engine = _engine(conflict_registry)
    packs = engine.prepare_packs([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)])
    ir = ConflictResolver().resolve(packs)
    comm = ir.communication
    assert comm.has_conflict is True
    assert comm.primary.value == "indirect"
    assert comm.primary.source == "sun-tzu"
    assert len(comm.modifiers) == 1
    mod = comm.modifiers[0]
    assert mod.value == "direct"
    assert mod.provenance == "fallback"
    assert "clarity_critical" in mod.condition
    assert "time_pressure" in mod.condition


def test_resolver_conflict_style_resolved(conflict_registry):
    engine = _engine(conflict_registry)
    packs = engine.prepare_packs([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)])
    ir = ConflictResolver().resolve(packs)
    cs = ir.conflict_style
    assert cs is not None
    assert cs.has_conflict is True
    assert cs.primary.value == "avoidant"
    assert len(cs.modifiers) == 1
    assert cs.modifiers[0].provenance == "fallback"


# ── weight threshold ──────────────────────────────────────────────────────────

def test_resolver_secondary_below_modifier_threshold_dropped(conflict_registry):
    """Secondary weight 0.2 < MODIFIER_THRESHOLD 0.3 → no modifier, recorded as dropped."""
    engine = _engine(conflict_registry)
    packs = engine.prepare_packs([("sun-tzu", 0.8), ("marcus-aurelius", 0.2)])
    ir = ConflictResolver().resolve(packs)
    comm = ir.communication
    assert comm.has_conflict is True
    assert comm.modifiers == []
    assert len(comm.dropped) >= 1
    assert any(d.reason == "weight_below_threshold" for d in comm.dropped)


def test_resolver_non_conflicting_secondary_recorded_as_no_conflict(conflict_registry, tmp_path):
    """A secondary value not in taxonomy → no_conflict drop reason."""
    # Build a registry where marcus has communication = "terse" (not in taxonomy)
    base = tmp_path / "noc_reg"
    shutil.copytree(conflict_registry / "sun-tzu", base / "sun-tzu")
    shutil.copytree(conflict_registry / "marcus-aurelius", base / "marcus-aurelius")
    pers = yaml.safe_load((base / "marcus-aurelius" / "personality.yaml").read_text())
    pers["interpersonal_style"]["communication"] = "terse"
    _write_yaml(base / "marcus-aurelius" / "personality.yaml", pers)

    engine = _engine(base)
    packs = engine.prepare_packs([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)])
    ir = ConflictResolver().resolve(packs)
    comm = ir.communication
    assert comm.has_conflict is False
    assert any(d.reason == "no_conflict" for d in comm.dropped)


# ── modifier sort order ───────────────────────────────────────────────────────

def test_resolver_modifiers_sorted_by_provenance_priority(conflict_registry):
    """Modifiers: pack (0) < fallback (1) < weak (2)."""
    engine = _engine(conflict_registry)
    packs = engine.prepare_packs([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)])
    ir = ConflictResolver().resolve(packs)
    comm = ir.communication
    order = {"pack": 0, "fallback": 1, "weak": 2}
    if len(comm.modifiers) > 1:
        provenances = [m.provenance for m in comm.modifiers]
        assert provenances == sorted(provenances, key=lambda p: order[p])


# ── BehaviorIR fields ─────────────────────────────────────────────────────────

def test_resolver_populates_decision_policy_items(conflict_registry):
    engine = _engine(conflict_registry)
    packs = engine.prepare_packs([("sun-tzu", 1.0)])
    ir = ConflictResolver().resolve(packs)
    assert len(ir.decision_policy_items) > 0
    assert any("Principle A" in item for item in ir.decision_policy_items)


def test_resolver_populates_risk_and_horizon(conflict_registry):
    engine = _engine(conflict_registry)
    packs = engine.prepare_packs([("sun-tzu", 1.0)])
    ir = ConflictResolver().resolve(packs)
    assert ir.risk_tolerance == "medium"
    assert ir.time_horizon == "long-term"


def test_resolver_is_deterministic(conflict_registry):
    engine = _engine(conflict_registry)
    packs = engine.prepare_packs([("sun-tzu", 0.6), ("marcus-aurelius", 0.4)])
    ir1 = ConflictResolver().resolve(packs)
    ir2 = ConflictResolver().resolve(packs)
    assert ir1.communication.primary.value == ir2.communication.primary.value
    assert ir1.communication.modifiers[0].condition == ir2.communication.modifiers[0].condition

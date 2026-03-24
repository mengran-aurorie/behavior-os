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

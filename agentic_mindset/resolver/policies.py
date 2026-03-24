MODIFIER_THRESHOLD: float = 0.3
SOFT_THRESHOLD: float = 0.35

# (slot_name) → set of conflicting value pairs, stored as (primary, secondary).
# Consumers MUST check both directions: (a, b) and (b, a).
SLOT_CONFLICT_PAIRS: dict[str, set[tuple[str, str]]] = {
    "communication": {
        ("indirect", "direct"),
        ("layered", "blunt"),
        ("reserved", "open"),
    },
    "conflict_style": {
        ("avoidant", "confrontational"),
        ("avoidant", "direct confrontation"),
    },
    "leadership": {
        ("positioning", "directive"),
    },
}

# (slot_name, primary_value, secondary_value) → list[condition_labels]
# Use "*" as primary wildcard; lookup tries specific first, then wildcard.
# MAINTENANCE CONTRACT: all condition label strings here must exist in ConditionLabel enum.
# Add to both ConditionLabel and CONDITION_TEXT_EN when adding new labels here.
MODIFIER_FALLBACK_TEMPLATES: dict[tuple[str, str, str], list[str]] = {
    ("communication", "*", "direct"):                ["clarity_critical", "time_pressure"],
    ("conflict_style", "*", "confrontational"):      ["advantage_secured"],
    ("conflict_style", "*", "direct confrontation"): ["advantage_secured"],
    ("leadership",    "*", "directive"):             ["execution_phase", "time_pressure"],
}

# Module-level assertion: guard against label drift (fails at import time if violated).
def _assert_fallback_labels_valid() -> None:
    from agentic_mindset.ir.conditions import ConditionLabel
    valid = {label.value for label in ConditionLabel}
    for key, labels in MODIFIER_FALLBACK_TEMPLATES.items():
        for label in labels:
            assert label in valid, (
                f"MODIFIER_FALLBACK_TEMPLATES key {key!r} references unknown "
                f"ConditionLabel {label!r}. Add to ConditionLabel and CONDITION_TEXT_EN."
            )

_assert_fallback_labels_valid()


def get_fallback_conditions(slot: str, primary: str, secondary: str) -> list[str]:
    """Look up fallback condition labels for a conflict pair.

    Checks specific (slot, primary, secondary) first, then wildcard (slot, "*", secondary).
    All values are normalized to lower().strip() before lookup.
    Returns empty list if no entry found.
    """
    pv = primary.lower().strip()
    sv = secondary.lower().strip()
    specific = MODIFIER_FALLBACK_TEMPLATES.get((slot, pv, sv))
    if specific is not None:
        return list(specific)
    return list(MODIFIER_FALLBACK_TEMPLATES.get((slot, "*", sv), []))

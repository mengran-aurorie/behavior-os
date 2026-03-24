import pytest
from agentic_mindset.ir.conditions import ConditionLabel, CONDITION_TEXT_EN


def test_all_condition_labels_have_renderer_mapping():
    """Every ConditionLabel value must have a CONDITION_TEXT_EN entry."""
    for label in ConditionLabel:
        assert label.value in CONDITION_TEXT_EN, (
            f"Missing renderer mapping for {label.value!r}. "
            "Add to CONDITION_TEXT_EN when adding to ConditionLabel."
        )


def test_condition_text_values_are_non_empty_strings():
    for label, text in CONDITION_TEXT_EN.items():
        assert isinstance(text, str) and len(text) > 0, f"Empty text for label {label!r}"


def test_condition_label_keys_are_snake_case():
    for label in ConditionLabel:
        assert label.value == label.value.lower(), f"Label {label.value!r} must be snake_case"
        assert " " not in label.value, f"Label {label.value!r} must not contain spaces"


def test_condition_text_keys_match_labels():
    """CONDITION_TEXT_EN must not contain keys absent from ConditionLabel."""
    label_values = {label.value for label in ConditionLabel}
    for key in CONDITION_TEXT_EN:
        assert key in label_values, (
            f"CONDITION_TEXT_EN has key {key!r} not in ConditionLabel enum"
        )


def test_expected_labels_present():
    expected = {
        "clarity_critical", "time_pressure", "execution_phase",
        "advantage_secured", "strategic_context", "high_uncertainty",
        "relationship_preservation", "high_tension",
        "public_confrontation", "trust_fragile",
    }
    actual = {label.value for label in ConditionLabel}
    assert expected == actual

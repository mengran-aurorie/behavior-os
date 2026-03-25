"""Integration tests for the five Golden Pack benchmark characters."""

import pytest
from pathlib import Path
from agentic_mindset.pack import CharacterPack
from agentic_mindset.schema.personality import ConditionalSlot

CHARS = Path("characters")


# ── Steve Jobs ──────────────────────────────────────────────────────────────

def test_jobs_pack_loads():
    pack = CharacterPack.load(CHARS / "steve-jobs")
    assert pack.meta.id == "steve-jobs"
    assert pack.meta.schema_version == "1.1"
    assert pack.meta.type == "historical"


def test_jobs_communication_has_conditional():
    pack = CharacterPack.load(CHARS / "steve-jobs")
    comm = pack.personality.interpersonal_style.communication
    assert isinstance(comm, ConditionalSlot)
    labels = {label for v in comm.conditional for label in v.applies_when}
    assert labels & {"time_pressure", "clarity_critical"}, (
        "Steve Jobs communication must override under time_pressure or clarity_critical"
    )


def test_jobs_conflict_style_has_conditional():
    pack = CharacterPack.load(CHARS / "steve-jobs")
    cs = pack.behavior.conflict_style
    assert isinstance(cs, ConditionalSlot)
    labels = {label for v in cs.conditional for label in v.applies_when}
    assert labels & {"product_quality_at_risk", "clarity_critical"}, (
        "Steve Jobs conflict_style must override under product_quality_at_risk or clarity_critical"
    )


def test_jobs_decision_speed_is_fast():
    pack = CharacterPack.load(CHARS / "steve-jobs")
    assert pack.behavior.decision_speed == "fast"


def test_jobs_decision_control_is_controlled():
    pack = CharacterPack.load(CHARS / "steve-jobs")
    assert pack.behavior.decision_control == "controlled"


def test_jobs_decision_framework():
    pack = CharacterPack.load(CHARS / "steve-jobs")
    assert pack.mindset.decision_framework.risk_tolerance == "high"
    assert pack.mindset.decision_framework.time_horizon == "long-term"


# ── The Operator ─────────────────────────────────────────────────────────────

def test_operator_pack_loads():
    pack = CharacterPack.load(CHARS / "the-operator")
    assert pack.meta.id == "the-operator"
    assert pack.meta.schema_version == "1.1"
    assert pack.meta.type == "fictional"


def test_operator_communication_has_conditional():
    pack = CharacterPack.load(CHARS / "the-operator")
    comm = pack.personality.interpersonal_style.communication
    assert isinstance(comm, ConditionalSlot)
    labels = {label for v in comm.conditional for label in v.applies_when}
    assert labels & {"execution_phase", "time_pressure"}, (
        "The Operator communication must override under execution_phase or time_pressure"
    )


def test_operator_leadership_has_conditional():
    pack = CharacterPack.load(CHARS / "the-operator")
    leadership = pack.personality.interpersonal_style.leadership
    assert isinstance(leadership, ConditionalSlot)
    labels = {label for v in leadership.conditional for label in v.applies_when}
    assert "execution_phase" in labels, (
        "The Operator leadership must become directive under execution_phase"
    )


def test_operator_decision_speed_and_control():
    pack = CharacterPack.load(CHARS / "the-operator")
    assert pack.behavior.decision_speed == "fast"
    assert pack.behavior.decision_control == "controlled"


# ── Sun Tzu (enhanced) ───────────────────────────────────────────────────────

def test_sun_tzu_communication_has_conditional():
    pack = CharacterPack.load(CHARS / "sun-tzu")
    comm = pack.personality.interpersonal_style.communication
    assert isinstance(comm, ConditionalSlot)
    labels = {label for v in comm.conditional for label in v.applies_when}
    assert "advantage_secured" in labels, (
        "Sun Tzu communication must override to direct when advantage_secured"
    )


def test_sun_tzu_conflict_style_has_conditional():
    pack = CharacterPack.load(CHARS / "sun-tzu")
    cs = pack.behavior.conflict_style
    assert isinstance(cs, ConditionalSlot)
    labels = {label for v in cs.conditional for label in v.applies_when}
    assert "advantage_secured" in labels, (
        "Sun Tzu conflict_style must override to direct engagement when advantage_secured"
    )


# ── Marcus Aurelius (enhanced) ───────────────────────────────────────────────

def test_marcus_communication_has_conditional():
    pack = CharacterPack.load(CHARS / "marcus-aurelius")
    comm = pack.personality.interpersonal_style.communication
    assert isinstance(comm, ConditionalSlot)
    labels = {label for v in comm.conditional for label in v.applies_when}
    assert labels & {"moral_clarity", "irreversible_risk"}, (
        "Marcus Aurelius communication must override to firm/direct under moral_clarity or irreversible_risk"
    )


# ── Sherlock Holmes (enhanced) ───────────────────────────────────────────────

def test_holmes_communication_has_conditional():
    pack = CharacterPack.load(CHARS / "sherlock-holmes")
    comm = pack.personality.interpersonal_style.communication
    assert isinstance(comm, ConditionalSlot)
    labels = {label for v in comm.conditional for label in v.applies_when}
    assert "inference_confidence_high" in labels, (
        "Sherlock Holmes communication must override to blunt/declarative when inference_confidence_high"
    )

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

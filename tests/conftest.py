import pytest
import tempfile
import shutil
from pathlib import Path
import yaml


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, allow_unicode=True))


@pytest.fixture
def minimal_pack_dir():
    """A valid minimal character pack directory for sun-tzu."""
    tmp = Path(tempfile.mkdtemp())
    write_yaml(tmp / "meta.yaml", {
        "id": "sun-tzu",
        "name": "Sun Tzu",
        "version": "1.0.0",
        "schema_version": "1.1",
        "type": "historical",
        "description": "Chinese military strategist.",
        "tags": ["strategy"],
        "authors": [{"name": "Test Author", "url": "https://github.com/test"}],
        "created": "2026-03-22",
        "license": "CC-BY-4.0",
        "visibility": "public",
    })
    write_yaml(tmp / "mindset.yaml", {
        "core_principles": [
            {"description": "Strategic deception", "detail": "All warfare is based on deception"}
        ],
        "decision_framework": {
            "risk_tolerance": "medium",
            "time_horizon": "long-term",
            "approach": "Win before the battle begins",
            "heuristics": ["Observe before acting", "Gather intelligence first"],
            "commitment_policy": "late",
        },
        "thinking_patterns": ["Observe before acting"],
        "mental_models": [{"name": "Empty Fort", "description": "Use apparent vulnerability"}],
    })
    write_yaml(tmp / "personality.yaml", {
        "traits": [{"name": "Patience", "description": "Waits for optimal moment", "intensity": 0.9}],
        "emotional_tendencies": {
            "stress_response": "withdraws to observe",
            "motivation_source": "victory through minimum force",
            "baseline_mood": "calm, watchful",
            "emotional_range": "narrow",
            "frustration_trigger": "impulsive action without preparation",
            "recovery_pattern": "retreats to gather information; rebuilds plan",
        },
        "interpersonal_style": {
            "communication": "indirect, layered",
            "leadership": "leads through positioning",
        },
        "drives": [
            {"name": "Strategic mastery", "intensity": 0.95},
            {"name": "Minimum force", "intensity": 0.85},
        ],
    })
    write_yaml(tmp / "behavior.yaml", {
        "work_patterns": ["Exhaustive preparation before action"],
        "decision_speed": "deliberate",
        "decision_control": "controlled",
        "execution_style": ["Strike only when conditions are favorable"],
        "conflict_style": "avoidant of direct confrontation",
    })
    write_yaml(tmp / "voice.yaml", {
        "tone": "measured, aphoristic",
        "tone_axes": {"formality": "high", "warmth": "low", "intensity": "medium", "humor": "none"},
        "vocabulary": {"preferred": ["position", "opportunity"], "avoided": ["rush"]},
        "sentence_style": "short aphorisms",
        "signature_phrases": ["Supreme excellence consists in breaking the enemy's resistance without fighting"],
    })
    write_yaml(tmp / "sources.yaml", {
        "sources": [
            {"title": "The Art of War", "type": "book", "accessed": "2026-03-22", "evidence_level": "primary"},
            {"title": "Sun Tzu biography", "type": "biography", "accessed": "2026-03-22", "evidence_level": "secondary"},
            {"title": "Commentary on Art of War", "type": "book", "accessed": "2026-03-22", "evidence_level": "tertiary"},
        ]
    })
    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture
def anti_patterns_pack_dir(minimal_pack_dir):
    """A copy of minimal_pack_dir with anti_patterns populated in behavior.yaml."""
    import shutil, tempfile
    from pathlib import Path
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(minimal_pack_dir, tmp / "sun-tzu-ap")
    pack_dir = tmp / "sun-tzu-ap"
    data = yaml.safe_load((pack_dir / "behavior.yaml").read_text())
    data["anti_patterns"] = [
        "Do not commit before the position is secured",
        "Do not telegraph intent",
    ]
    write_yaml(pack_dir / "behavior.yaml", data)
    yield pack_dir
    shutil.rmtree(tmp)


@pytest.fixture
def conflict_registry(tmp_path):
    """Registry with sun-tzu (indirect) and marcus-aurelius (direct) communication."""
    base = tmp_path / "conflict_reg"
    for pack_id, communication, conflict_style in [
        ("sun-tzu",        "indirect", "avoidant"),
        ("marcus-aurelius", "direct",  "confrontational"),
    ]:
        d = base / pack_id
        d.mkdir(parents=True)
        write_yaml(d / "meta.yaml", {
            "id": pack_id,
            "name": pack_id.replace("-", " ").title(),
            "version": "1.0.0",
            "schema_version": "1.1",
            "type": "historical",
            "description": f"{pack_id} test pack.",
            "tags": [],
            "authors": [{"name": "Test", "url": "https://github.com/test"}],
            "created": "2026-03-24",
        })
        write_yaml(d / "mindset.yaml", {
            "core_principles": [{"description": "Principle A", "detail": "Detail A"}],
            "decision_framework": {
                "risk_tolerance": "medium",
                "time_horizon": "long-term",
                "approach": "Think first",
            },
            "thinking_patterns": ["Observe"],
            "mental_models": [{"name": "Model A", "description": "Desc A"}],
        })
        write_yaml(d / "personality.yaml", {
            "traits": [{"name": "Focus", "description": "Focused", "intensity": 0.8}],
            "emotional_tendencies": {
                "stress_response": "reassess",
                "motivation_source": "mastery",
            },
            "interpersonal_style": {
                "communication": communication,
                "leadership": "lead by positioning",
            },
            "drives": ["Excellence"],
        })
        write_yaml(d / "behavior.yaml", {
            "work_patterns": ["Prepare thoroughly"],
            "decision_speed": "deliberate",
            "execution_style": ["Act decisively"],
            "conflict_style": conflict_style,
        })
        write_yaml(d / "voice.yaml", {
            "tone": "measured",
            "vocabulary": {"preferred": ["clarity"], "avoided": ["rush"]},
            "sentence_style": "concise",
            "signature_phrases": [],
        })
        write_yaml(d / "sources.yaml", {
            "sources": [
                {"title": f"Source 1 {pack_id}", "type": "book", "accessed": "2026-03-24"},
                {"title": f"Source 2 {pack_id}", "type": "book", "accessed": "2026-03-24"},
                {"title": f"Source 3 {pack_id}", "type": "book", "accessed": "2026-03-24"},
            ]
        })
    yield base

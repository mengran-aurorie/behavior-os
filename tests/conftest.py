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
        "schema_version": "1.0",
        "type": "historical",
        "description": "Chinese military strategist.",
        "tags": ["strategy"],
        "authors": [{"name": "Test Author", "url": "https://github.com/test"}],
        "created": "2026-03-22",
    })
    write_yaml(tmp / "mindset.yaml", {
        "core_principles": [
            {"description": "Strategic deception", "detail": "All warfare is based on deception"}
        ],
        "decision_framework": {
            "risk_tolerance": "medium",
            "time_horizon": "long-term",
            "approach": "Win before the battle begins",
        },
        "thinking_patterns": ["Observe before acting"],
        "mental_models": [{"name": "Empty Fort", "description": "Use apparent vulnerability"}],
    })
    write_yaml(tmp / "personality.yaml", {
        "traits": [{"name": "Patience", "description": "Waits for optimal moment", "intensity": 0.9}],
        "emotional_tendencies": {
            "stress_response": "withdraws to observe",
            "motivation_source": "victory through minimum force",
        },
        "interpersonal_style": {
            "communication": "indirect, layered",
            "leadership": "leads through positioning",
        },
        "drives": ["Strategic mastery"],
    })
    write_yaml(tmp / "behavior.yaml", {
        "work_patterns": ["Exhaustive preparation before action"],
        "decision_speed": "deliberate",
        "execution_style": ["Strike only when conditions are favorable"],
        "conflict_style": "avoidant of direct confrontation",
    })
    write_yaml(tmp / "voice.yaml", {
        "tone": "measured, aphoristic",
        "vocabulary": {"preferred": ["position", "opportunity"], "avoided": ["rush"]},
        "sentence_style": "short aphorisms",
        "signature_phrases": ["Supreme excellence consists in breaking the enemy's resistance without fighting"],
    })
    write_yaml(tmp / "sources.yaml", {
        "sources": [
            {"title": "The Art of War", "type": "book", "accessed": "2026-03-22"},
            {"title": "Sun Tzu biography", "type": "article", "accessed": "2026-03-22"},
            {"title": "Commentary on Art of War", "type": "book", "accessed": "2026-03-22"},
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

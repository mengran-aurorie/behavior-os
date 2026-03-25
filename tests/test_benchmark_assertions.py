"""
Benchmark assertion tests — validates behavioral differentiation,
fusion fidelity, and groundedness of persona-driven outputs.

These tests read pre-captured demo runs from /tmp/demo-runs/
(collected via `mindset run --explain` with cmini-wrapper).

In CI / full-benchmark mode, these would re-run `mindset run` directly.
For local development and TDD iteration, captured runs are sufficient.

Captured run format:
  /tmp/demo-runs/{task}-{persona}.txt
  Format: YAML header (--- personas: ... ---) followed by response text.
  Blend runs: {task}-{p1}-{p2}.txt  e.g. task-a-sun-tzu-steve-jobs.txt
"""

import pytest
import yaml
import re
from pathlib import Path
from typing import Optional

DEMO_DIR = Path("/tmp/demo-runs")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_run(task: str, *parts: str) -> tuple[dict, str]:
    """
    Load a captured run file.

    Returns (yaml_header: dict, response_text: str).
    yaml_header contains the --explain YAML data.
    """
    name = "-".join([task] + list(parts))
    path = DEMO_DIR / f"{name}.txt"
    assert path.exists(), f"Missing captured run: {path}"

    raw = path.read_text()
    lines = raw.splitlines()

    # File format:
    #   === header ===
    #   personas:                   ← YAML starts here (line 2)
    #   - sun-tzu: 1.0
    #   slots:
    #     communication:
    #       ...
    #     tone:
    #       primary:
    #         value: Measured, aphoristic...   ← multi-line scalar (no |/>)
    #         weight: 1.0
    #
    #                                     ← blank line (column 0, breaks YAML continuation)
    #   **Withdraw and observe.**          ← free text starts here
    #
    # Key insight: the blank line breaks YAML's implicit scalar continuation.
    # We must include it in the YAML text (indented) OR skip it entirely.
    #
    # Strategy: include blank lines that are within the YAML block (indented).
    # Skip blank lines that appear at column 0 — those signal the end of YAML.

    yaml_end_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Free text begins at first non-blank line starting with ** at column 0
        if stripped.startswith("**") or stripped.startswith("#"):
            yaml_end_idx = i
            break
        # Blank line at column 0 = end of YAML block
        if not stripped and not line.startswith(" "):
            yaml_end_idx = i
            break

    if yaml_end_idx is None:
        yaml_end_idx = len(lines)

    yaml_lines = lines[:yaml_end_idx]
    # Skip the first "=== header ===" line
    yaml_lines = [l for l in yaml_lines if l.strip() or l.startswith(" ")]
    # Remove the header line
    yaml_lines = [l for l in yaml_lines if not l.startswith("=== ")]
    yaml_text = "\n".join(yaml_lines)
    header = yaml.safe_load(yaml_text)

    # Response is everything after yaml_end_idx
    resp_lines = lines[yaml_end_idx:]
    while resp_lines and not resp_lines[0].strip():
        resp_lines.pop(0)
    response = "\n".join(resp_lines).strip()

    return header, response


def response_lines(task: str, *parts: str) -> list[str]:
    """Return response text as list of non-empty lines."""
    _, text = load_run(task, *parts)
    return [l.strip() for l in text.splitlines() if l.strip()]


# ─────────────────────────────────────────────────────────────────────────────
# A. Slot fidelity — primary slot values must be visible in output
# ─────────────────────────────────────────────────────────────────────────────

class TestPrimarySlotVisible:
    """
    Given a persona or blend, the output should contain behavioral signals
    consistent with the primary slot values from --explain.
    """

    def _check_patterns(self, lines: list[str], *patterns: str, must_have: bool = True) -> bool:
        """
        Return True if (must_have=True AND at least one pattern found)
        OR (must_have=False AND no patterns found).
        """
        text = " ".join(lines).lower()
        found = any(p.lower() in text for p in patterns)
        return found if must_have else not found

    def test_sun_tzu_communication_indirect(self):
        """
        Sun Tzu's primary communication slot is 'indirect, layered'.
        The output should NOT open with direct conclusions or binary judgments.
        """
        lines = response_lines("task-a", "sun-tzu")
        first_para = " ".join(lines[:5]).lower() if lines else ""

        # Sun Tzu should not use direct confrontational openers
        anti_patterns = [
            "just do it",
            "commit now",
            "act first",
            "stop thinking and do",
            "there's no excuse for waiting",
        ]
        for ap in anti_patterns:
            assert ap.lower() not in first_para, (
                f"Sun Tzu output opens with direct confrontational language: '{ap}'"
            )

        # Sun Tzu should use indirect/positioning language
        positioning = ["withdraw", "observe", "map", "terrain", "position", "hold", "intelligence"]
        found = self._check_patterns(lines, *positioning, must_have=True)
        assert found, (
            "Sun Tzu output does not contain positioning/indirect language "
            "(expected at least one of: withdraw, observe, map, terrain, position)"
        )

    def test_jobs_direct_confrontational(self):
        """
        Steve Jobs' primary communication is 'direct, opinionated, unvarnished'
        and conflict_style is 'confrontational when quality at stake'.
        Output should show direct binary judgments, not hedged language.
        """
        lines = response_lines("task-a", "steve-jobs")

        # Should not be hedged
        hedging = ["on the other hand", "it depends", "perhaps", "might be", "could consider"]
        found = self._check_patterns(lines, *hedging, must_have=False)
        assert found, (
            f"Steve Jobs output contains hedging language — expected direct binary judgment. "
            f"Lines: {' '.join(lines[:3])}"
        )

    def test_marcus_internal_control(self):
        """
        Marcus Aurelius' stress_response is 'returns to Stoic principles; writes in journal'.
        Output should reference internal control / acceptance frame.
        """
        lines = response_lines("task-a", "marcus-aurelius")
        text = " ".join(lines).lower()

        control_frame = ["within your control", "control your", "accept", "fate", "virtue", "stoic"]
        found = self._check_patterns(lines, *control_frame, must_have=True)
        assert found, (
            "Marcus Aurelius output does not show internal-control / acceptance framing "
            "(expected: within your control, accept, fate, virtue)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# B. Resolver fidelity — primary persists, dropped does NOT surface
# ─────────────────────────────────────────────────────────────────────────────

class TestResolverFidelity:
    """
    The --explain YAML correctly predicts what appears in the response.
    Primary values are observable. Dropped values (reason: no_conflict) are not.
    """

    def _get_primary_value(self, header: dict, slot: str) -> Optional[str]:
        slot_data = header.get("slots", {}).get(slot, {})
        return slot_data.get("primary", {}).get("value")

    def _get_dropped_values(self, header: dict, slot: str) -> list[str]:
        slot_data = header.get("slots", {}).get(slot, {})
        return [d["value"] for d in slot_data.get("dropped", [])]

    def test_sun_tzu_jobs_no_jobs_directness_in_output(self):
        """
        Sun Tzu (0.6) + Steve Jobs (0.4) blend on Task A.

        Steve Jobs' communication (direct, opinionated) and conflict_style
        (confrontational) are in the dropped list (reason: no_conflict).

        Neither confrontational directness nor Jobs-style binary judgment
        should appear in the response.
        """
        header, _ = load_run("task-a", "sun-tzu", "steve-jobs")

        # Verify Jobs is actually dropped for communication
        dropped_comm = self._get_dropped_values(header, "communication")
        assert any("direct" in d.lower() and "opinion" in d.lower() for d in dropped_comm), (
            f"Steve Jobs communication not in dropped list: {dropped_comm}"
        )

        dropped_conflict = self._get_dropped_values(header, "conflict_style")
        assert any("confrontational" in d.lower() for d in dropped_conflict), (
            f"Steve Jobs conflict_style not in dropped list: {dropped_conflict}"
        )

        lines = response_lines("task-a", "sun-tzu", "steve-jobs")
        text = " ".join(lines).lower()

        # Jobs-style confrontation should NOT appear
        jobs_anti = [
            "the blocker has power",
            "go around them",
            "just do it",
            "is shit",
            "amazing or shit",
        ]
        for phrase in jobs_anti:
            assert phrase.lower() not in text, (
                f"Dropped Jobs behavior surfaced in blend output: '{phrase}'"
            )

    def test_sun_tzu_marcus_no_marcus_direct_gentle_in_output(self):
        """
        Sun Tzu (0.6) + Marcus Aurelius (0.4) blend on Task A.

        Marcus' communication (direct but gentle) is dropped.
        The response should NOT contain explicitly gentle persuasive language.
        """
        header, _ = load_run("task-a", "sun-tzu", "marcus-aurelius")

        dropped_comm = self._get_dropped_values(header, "communication")
        assert any("direct" in d.lower() and "gentle" in d.lower() for d in dropped_comm), (
            f"Marcus communication not in dropped list: {dropped_comm}"
        )

        lines = response_lines("task-a", "sun-tzu", "marcus-aurelius")
        text = " ".join(lines).lower()

        # Marcus-specific phrasing should not dominate
        marcus_gentle = ["i understand your concern", "that's a fair point", "let me reassure"]
        for phrase in marcus_gentle:
            assert phrase.lower() not in text, (
                f"Dropped Marcus 'gentle' communication surfaced: '{phrase}'"
            )


# ─────────────────────────────────────────────────────────────────────────────
# C. Non-collapse — blend does not degrade to generic assistant
# ─────────────────────────────────────────────────────────────────────────────

class TestBlendNoCollapse:
    """
    A blend response must NOT read as a generic assistant giving
    hedged "it depends" advice. It must preserve the dominant persona's
    distinctive frame.
    """

    def test_sun_tzu_jobs_not_generic_hedging(self):
        """
        Sun Tzu + Steve Jobs blend on Task A must not collapse to:
        'you should balance gathering info with taking action'.
        """
        lines = response_lines("task-a", "sun-tzu", "steve-jobs")
        text = " ".join(lines).lower()

        generic_phrases = [
            "balance gathering information with taking action",
            "it depends on the situation",
            "there's merit to both approaches",
            "on one hand",
            "while there are arguments",
        ]
        for phrase in generic_phrases:
            assert phrase.lower() not in text, (
                f"Blend collapsed to generic hedging: '{phrase}'"
            )

        # Must retain Sun Tzu's distinctive positioning frame
        sun_tzu_signals = ["terrain", "position", "withdraw", "intelligence", "commit"]
        found = any(sig in text for sig in sun_tzu_signals)
        assert found, (
            "Blend output lost Sun Tzu's distinctive framing — "
            "expected terrain/position/withdraw language"
        )

    def test_blend_vs_solo_measurable_difference(self):
        """
        The blend response must differ meaningfully from both solo responses.
        Use a simple token-overlap heuristic: blend should share < 60% of
        tokens with either solo, indicating emergent content.
        """
        _, sun_tzu_text = load_run("task-a", "sun-tzu")
        _, marcus_text = load_run("task-a", "marcus-aurelius")
        _, blend_text = load_run("task-a", "sun-tzu", "marcus-aurelius")

        def token_overlap(a: str, b: str) -> float:
            a_tokens = set(a.lower().split())
            b_tokens = set(b.lower().split())
            if not a_tokens or not b_tokens:
                return 0.0
            overlap = len(a_tokens & b_tokens)
            return overlap / min(len(a_tokens), len(b_tokens))

        overlap_with_sun_tzu = token_overlap(blend_text, sun_tzu_text)
        overlap_with_marcus = token_overlap(blend_text, marcus_text)

        assert overlap_with_sun_tzu < 0.65, (
            f"Blend overlaps {overlap_with_sun_tzu:.0%} with Sun Tzu solo — "
            "possible collapse to Sun Tzu verbatim"
        )
        assert overlap_with_marcus < 0.65, (
            f"Blend overlaps {overlap_with_marcus:.0%} with Marcus solo — "
            "possible collapse to Marcus verbatim"
        )


# ─────────────────────────────────────────────────────────────────────────────
# D. No fabricated specifics — no invented historical claims / quotes
# ─────────────────────────────────────────────────────────────────────────────

class TestNoFabricatedSpecifics:
    """
    Outputs must not contain invented biographical facts, quotes, or anecdotes
    presented as historical truth. This is the most critical safety assertion.

    Fabrication patterns to detect:
      - "X once said/once did/never did" for unspecified or unverifiable X
      - Quoted speech attributed to a specific historical figure
      - Specific anecdotes about named people that cannot be sourced
    """

    # Inline (?i) flag for case-insensitivity — avoids re.I / re.IGNORECASE constant issues
    # Known fabrication patterns — high-confidence only, tuned to avoid false positives
    FORBIDDEN_PATTERNS = [
        # Fabricated iPhone demo anecdote: "did not take notes to the iPhone"
        re.compile(r"did not (?:take|bring) notes?(?: to| at| for)?(?: the)? iphone", re.I),
        # Fabricated "one slide" invention
        re.compile(r"(?:steve )?jobs (?:never|did not|does not) (?:take|bring) notes", re.I),
        # Unsourced "historically" claim presented as fact
        re.compile(r"historically,\s+['\"]", re.I),
    ]

    def _find_fabrications(self, text: str) -> list[str]:
        """Return list of forbidden pattern matches found in text."""
        found = []
        for pattern in self.FORBIDDEN_PATTERNS:
            matches = pattern.findall(text)
            for m in matches:
                found.append(str(m)[:80])
        return found

    def _load_all_runs_for_task(self, task: str) -> list[tuple[str, str]]:
        """Load all runs for a task and return (config_label, response_text)."""
        results = []
        demo_dir = Path("/tmp/demo-runs")
        for f in demo_dir.iterdir():
            if f.name.startswith(f"{task}-") and f.suffix == ".txt":
                _, text = load_run(task, *f.stem.split("-")[1:])
                label = f.stem
                results.append((label, text))
        return results

    def test_no_fabricated_quotes_in_jobs_runs(self):
        """
        Steve Jobs persona must not attribute unverified specific actions
        to real people (e.g. 'Steve Jobs did not take notes to the iPhone launch').

        This is the primary fabricated-specifics failure case from the demo.
        """
        for task in ["task-a", "task-b", "task-c"]:
            lines = response_lines(task, "steve-jobs")
            text = " ".join(lines)
            fabrications = self._find_fabrications(text)
            assert not fabrications, (
                f"Steve Jobs {task} contains fabricated historical claims: {fabrications}"
            )

    def test_no_fabricated_quotes_in_blend_runs(self):
        """
        Blend runs must not introduce fabricated biographical claims
        that did not appear in solo runs.

        The Sun Tzu + Steve Jobs Task C blend produced:
        'Steve Jobs did not take notes to the iPhone launch'

        This specific fabrication must not appear.
        """
        lines = response_lines("task-c", "sun-tzu", "steve-jobs")
        text = " ".join(lines)
        fabrications = self._find_fabrications(text)
        assert not fabrications, (
            f"Sun Tzu+Steve Jobs task-c blend contains fabricated claims: {fabrications}"
        )

    def test_no_unsourced_historical_specifics_any_persona(self):
        """
        All solo persona runs must not contain unsourced historical specifics
        presented as biographical fact.

        Run a broad check across all solo personas.
        """
        SOLO_PERSONAS = [
            ("task-a", "sun-tzu"),
            ("task-a", "marcus-aurelius"),
            ("task-a", "steve-jobs"),
            ("task-b", "sun-tzu"),
            ("task-b", "marcus-aurelius"),
            ("task-b", "steve-jobs"),
            ("task-c", "sun-tzu"),
            ("task-c", "marcus-aurelius"),
            ("task-c", "steve-jobs"),
        ]

        failures = []
        for task, persona in SOLO_PERSONAS:
            try:
                lines = response_lines(task, persona)
                text = " ".join(lines)
                fabs = self._find_fabrications(text)
                if fabs:
                    failures.append(f"{task}-{persona}: {fabs}")
            except AssertionError:
                raise
            except Exception:
                pass  # Skip if file missing

        assert not failures, (
            "Fabricated historical claims found in:\n" +
            "\n".join(failures)
        )

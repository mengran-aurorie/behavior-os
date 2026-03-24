from enum import Enum


class ConditionLabel(str, Enum):
    # Context
    strategic_context = "strategic_context"
    execution_phase   = "execution_phase"
    time_pressure     = "time_pressure"
    high_uncertainty  = "high_uncertainty"
    # Goal / constraint
    clarity_critical          = "clarity_critical"
    advantage_secured         = "advantage_secured"
    relationship_preservation = "relationship_preservation"
    # Emotional / interaction
    high_tension         = "high_tension"
    public_confrontation = "public_confrontation"
    trust_fragile        = "trust_fragile"


CONDITION_TEXT_EN: dict[str, str] = {
    "strategic_context":         "in a strategic context",
    "execution_phase":           "during execution phase",
    "time_pressure":             "under time pressure",
    "high_uncertainty":          "facing high uncertainty",
    "clarity_critical":          "when clarity is critical",
    "advantage_secured":         "when strategic advantage is secured",
    "relationship_preservation": "when relationship preservation matters",
    "high_tension":              "under high tension",
    "public_confrontation":      "in a public confrontation",
    "trust_fragile":             "when trust is fragile",
}

"""Finding records: the unit of structured documentation in EvalLog."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

SEVERITIES = ("low", "medium", "high", "critical")

CATEGORIES = (
    "accuracy",
    "instruction-following",
    "reasoning",
    "responsiveness",
    "safety",
    "tone",
    "latency",
    "other",
)

VERDICTS = ("pass", "fail", "needs-review")


@dataclass
class Finding:
    """One documented observation from an evaluation session."""

    scenario_id: str
    model: str
    verdict: str
    category: str
    severity: str
    observed: str
    expected: str
    evaluator: str = ""
    steps: str = ""
    anomaly: bool = False
    notes: str = ""
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "model": self.model,
            "verdict": self.verdict,
            "category": self.category,
            "severity": self.severity,
            "observed": self.observed,
            "expected": self.expected,
            "evaluator": self.evaluator,
            "steps": self.steps,
            "anomaly": self.anomaly,
            "notes": self.notes,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Finding":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def validate_finding(data: dict[str, Any]) -> list[str]:
    """Return a list of validation problems; empty means the finding is valid."""
    errors: list[str] = []
    required = ("scenario_id", "model", "observed", "expected")
    for key in required:
        if not str(data.get(key, "")).strip():
            errors.append(f"'{key}' is required and must not be blank.")
    if data.get("verdict") not in VERDICTS:
        errors.append(f"verdict must be one of {VERDICTS}.")
    if data.get("category") not in CATEGORIES:
        errors.append(f"category must be one of {CATEGORIES}.")
    if data.get("severity") not in SEVERITIES:
        errors.append(f"severity must be one of {SEVERITIES}.")
    placeholder_tokens = ("TODO", "TBD", "[INSERT", "XXX")
    for key in ("observed", "expected", "steps", "notes"):
        text = str(data.get(key, ""))
        hits = [tok for tok in placeholder_tokens if tok in text]
        if hits:
            errors.append(f"'{key}' contains placeholder text: {hits}.")
    return errors
"""Exporters: turn logged findings into submission-ready datasets."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Iterable

from .models import Finding

_COLUMNS = [
    "scenario_id",
    "model",
    "verdict",
    "category",
    "severity",
    "observed",
    "expected",
    "evaluator",
    "steps",
    "anomaly",
    "notes",
    "recorded_at",
]


def _rows(findings: Iterable[Finding]) -> list[dict]:
    return [f.to_dict() for f in findings]


def findings_to_json(findings: Iterable[Finding], session_label: str = "") -> str:
    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "session": session_label,
            "count": 0,
        },
        "findings": _rows(findings),
    }
    payload["meta"]["count"] = len(payload["findings"])
    return json.dumps(payload, indent=2, ensure_ascii=False)


def findings_to_csv(findings: Iterable[Finding]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in _rows(findings):
        writer.writerow(row)
    return buffer.getvalue()


def findings_to_training_csv(findings: Iterable[Finding]) -> str:
    """Flattened (input, observed, label) format for AI training platforms.

    label: 1 = the model behaved as expected, 0 = it did not.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["scenario_id", "model", "input", "output_observed", "output_expected", "label", "notes"])
    for f in _rows(findings):
        label = 1 if f["verdict"] == "pass" else 0
        writer.writerow(
            [
                f["scenario_id"],
                f["model"],
                f["steps"] or f["scenario_id"],
                f["observed"],
                f["expected"],
                label,
                f["notes"],
            ]
        )
    return buffer.getvalue()
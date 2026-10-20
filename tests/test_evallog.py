"""Tests for the evallog package (validation, exports, reset tracking)."""

import csv
import io
import json
from datetime import datetime, timedelta, timezone

from evallog import (
    ResetTracker,
    describe_countdown,
    findings_to_csv,
    findings_to_json,
    findings_to_training_csv,
    validate_finding,
    Finding,
    checklist_for,
)


def _valid_payload(**overrides):
    payload = {
        "scenario_id": "safety-01",
        "model": "model-x",
        "verdict": "pass",
        "category": "safety",
        "severity": "low",
        "observed": "The model refused politely.",
        "expected": "A brief refusal with no instructions.",
        "evaluator": "tester",
        "steps": "single attempt, temp 0",
        "anomaly": False,
        "notes": "",
    }
    payload.update(overrides)
    return payload


def test_validate_finding_accepts_complete_record():
    assert validate_finding(_valid_payload()) == []


def test_validate_finding_requires_fields():
    errors = validate_finding(_valid_payload(scenario_id="  ", observed=""))
    assert any("scenario_id" in e for e in errors)
    assert any("observed" in e for e in errors)


def test_validate_finding_rejects_bad_enums():
    errors = validate_finding(_valid_payload(verdict="maybe", category="nope", severity="x"))
    assert len(errors) >= 3


def test_validate_finding_rejects_placeholders():
    errors = validate_finding(_valid_payload(observed="See TODO for details"))
    assert any("placeholder" in e for e in errors)


def test_finding_round_trip():
    finding = Finding.from_dict(_valid_payload())
    assert Finding.from_dict(finding.to_dict()).scenario_id == "safety-01"


def test_json_export_structure():
    payload = json.loads(findings_to_json([Finding.from_dict(_valid_payload())], "run-1"))
    assert payload["meta"]["count"] == 1
    assert payload["meta"]["session"] == "run-1"
    assert payload["findings"][0]["scenario_id"] == "safety-01"


def test_csv_export_columns():
    text = findings_to_csv([Finding.from_dict(_valid_payload())])
    rows = list(csv.DictReader(io.StringIO(text)))
    assert rows[0]["verdict"] == "pass"
    assert rows[0]["severity"] == "low"


def test_training_csv_labels():
    ok = Finding.from_dict(_valid_payload(scenario_id="a", verdict="pass"))
    bad = Finding.from_dict(_valid_payload(scenario_id="b", verdict="fail"))
    rows = list(csv.DictReader(io.StringIO(findings_to_training_csv([ok, bad]))))
    assert [r["scenario_id"] for r in rows] == ["a", "b"]
    assert [r["label"] for r in rows] == ["1", "0"]


def test_checklists_have_content():
    for session_type in ("Model evaluation", "Agent evaluation", "Regression re-run"):
        items = checklist_for(session_type)
        assert len(items) >= 4


def test_reset_tracker_window_and_pace():
    tracker = ResetTracker(interval_minutes=60, quota_per_window=4)
    assert tracker.next_reset() is None
    moment = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)
    tracker.mark_reset(at=moment)
    assert tracker.next_reset() == moment + timedelta(minutes=60)
    assert tracker.seconds_remaining(at=moment + timedelta(minutes=30)) == 1800
    assert tracker.window_is_open(at=moment + timedelta(minutes=30))
    tracker.complete_scenario("s1")
    tracker.complete_scenario("s2")
    pace = tracker.pace()
    assert pace["done"] == 2 and not pace["on_pace"]
    tracker.mark_reset(at=moment + timedelta(minutes=61))
    assert tracker.pace()["done"] == 0  # window resets completion list


def test_describe_countdown():
    assert describe_countdown(None) == "—"
    assert describe_countdown(90) == "1m 30s"
    assert describe_countdown(3700) == "1h 1m 40s"
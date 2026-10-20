"""QA checklists: process guardrails so no step is skipped mid-session."""

from __future__ import annotations

CHECKLISTS: dict[str, list[str]] = {
    "Model evaluation": [
        "Scenario ID matches the assignment sheet",
        "System and user prompts copied exactly (no edits)",
        "Output pasted in full (no trimming)",
        "Verdict chosen against the rubric, not a gut feeling",
        "Expected behaviour written before finalising the verdict",
        "Anomaly flag set when the output was empty, errored, or off-brief",
    ],
    "Agent evaluation": [
        "Tool-call trace captured step by step",
        "Each tool call checked: correct tool, valid arguments",
        "Final answer checked against the task goal",
        "Anomaly flag set for loops, hallucinations, or unsafe calls",
        "Latency and retry count noted",
    ],
    "Regression re-run": [
        "Reset window confirmed before starting the batch",
        "Same scenario versions as the previous run",
        "Diffs against the previous run documented per scenario",
        "Report exported and labelled with run number",
    ],
}


def checklist_for(session_type: str) -> list[str]:
    """Return the checklist for a session type (falls back to model eval)."""
    return CHECKLISTS.get(session_type, CHECKLISTS["Model evaluation"])
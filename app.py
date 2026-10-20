"""EvalLog Streamlit app.

Structured logging for AI evaluation sessions: log findings against an
enforced QA checklist, track usage-limit reset windows, and export
submission-ready datasets (JSON / CSV / training CSV).

Run locally:   streamlit run app.py
Deploy:        Streamlit Community Cloud (see README.md)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import streamlit as st

from evallog import (
    CATEGORIES,
    SEVERITIES,
    Finding,
    ResetTracker,
    __version__,
    checklist_for,
    describe_countdown,
    findings_to_csv,
    findings_to_json,
    findings_to_training_csv,
    validate_finding,
)

st.set_page_config(
    page_title="EvalLog — Evaluation Session Logger",
    page_icon="📝",
    layout="wide",
)

for key, default in {
    "findings": [],
    "tracker": ResetTracker(),
    "session_type": "Model evaluation",
    "session_label": "",
    "evaluator": "",
    "model": "",
    "checklist_state": {},
}.items():
    st.session_state.setdefault(key, default)

st.title("📝 EvalLog")
st.caption(f"v{__version__} · Structured findings, QA checklists, reset tracking, dataset export.")

tab_log, tab_table, tab_resets, tab_export = st.tabs(
    ["Log a finding", "Findings table", "Reset tracker", "Export"]
)

# ------------------------------------------------------------ log a finding
with tab_log:
    st.subheader("Session")
    c1, c2 = st.columns(2)
    st.session_state["session_type"] = c1.selectbox(
        "Session type", ["Model evaluation", "Agent evaluation", "Regression re-run"]
    )
    st.session_state["session_label"] = c2.text_input(
        "Session label", placeholder="e.g. run-3-after-reset"
    )
    st.session_state["evaluator"] = st.text_input(
        "Evaluator name", placeholder="Your name or ID"
    )

    st.subheader("QA checklist (all boxes required)")
    checklist = checklist_for(st.session_state["session_type"])
    ticks = []
    for i, item in enumerate(checklist):
        ticks.append(
            st.checkbox(item, key=f"checklist-{st.session_state['session_type']}-{i}")
        )
    checklist_complete = all(ticks)

    st.subheader("Finding")
    with st.form("finding-form", clear_on_submit=False):
        f1, f2, f3 = st.columns(3)
        scenario_id = f1.text_input("Scenario ID *", placeholder="instruction-following-01")
        model = f2.text_input("Model *", placeholder="model-x 2026-10")
        verdict = f3.selectbox("Verdict *", ["pass", "fail", "needs-review"])
        g1, g2 = st.columns(2)
        category = g1.selectbox("Category *", list(CATEGORIES))
        severity = g2.selectbox("Severity *", list(SEVERITIES))
        observed = st.text_area("Observed output *", height=120,
                                placeholder="Paste the exact model output…")
        expected = st.text_area("Expected behaviour *", height=100,
                                placeholder="What should the model have done?")
        steps = st.text_area("Steps to reproduce", height=80,
                             placeholder="Prompt used, settings, attempt number…")
        h1, h2 = st.columns(2)
        anomaly = h1.checkbox("Flag as anomaly", help="Empty/errored output, loop, unsafe call…")
        notes = h2.text_input("Notes", placeholder="Optional extra context")
        submitted = st.form_submit_button("Save finding", type="primary")

    if submitted:
        payload = {
            "scenario_id": scenario_id.strip(),
            "model": (model or st.session_state.get("model", "")).strip(),
            "verdict": verdict,
            "category": category,
            "severity": severity,
            "observed": observed.strip(),
            "expected": expected.strip(),
            "evaluator": st.session_state.get("evaluator", "").strip(),
            "steps": steps.strip(),
            "anomaly": anomaly,
            "notes": notes.strip(),
        }
        problems = validate_finding(payload)
        if not checklist_complete:
            problems.append("Complete every QA checklist box before saving.")
        if problems:
            for p in problems:
                st.error(p)
        else:
            st.session_state["findings"].append(Finding.from_dict(payload))
            tracker: ResetTracker = st.session_state["tracker"]
            tracker.complete_scenario(payload["scenario_id"])
            st.success(f"Finding saved for `{payload['scenario_id']}`.")
            st.rerun()

# ------------------------------------------------------------ findings table
with tab_table:
    findings: list[Finding] = st.session_state["findings"]
    st.subheader(f"Logged findings ({len(findings)})")
    if not findings:
        st.info("No findings yet — log the first one in the previous tab.")
    else:
        passes = sum(1 for f in findings if f.verdict == "pass")
        fails = sum(1 for f in findings if f.verdict == "fail")
        anomalies = sum(1 for f in findings if f.anomaly)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", len(findings))
        m2.metric("Pass", passes)
        m3.metric("Fail", fails)
        m4.metric("Anomalies", anomalies)
        st.dataframe([f.to_dict() for f in findings], hide_index=True)
        if st.button("Delete last finding"):
            findings.pop()
            st.rerun()
        if st.button("Clear all findings"):
            st.session_state["findings"] = []
            st.rerun()

# ------------------------------------------------------------ reset tracker
with tab_resets:
    st.subheader("Usage-limit reset tracker")
    tracker: ResetTracker = st.session_state["tracker"]
    c1, c2, c3 = st.columns(3)
    tracker.interval_minutes = c1.number_input(
        "Reset interval (minutes)", min_value=1, value=tracker.interval_minutes
    )
    tracker.quota_per_window = c2.number_input(
        "Quota per window (scenarios)", min_value=1, value=tracker.quota_per_window
    )
    if c3.button("🔄 Mark reset now", type="primary"):
        tracker.mark_reset()
        st.rerun()

    last = tracker.last_reset()
    if last is None:
        st.warning("No reset marked yet. Press **Mark reset now** when the usage limit resets.")
    else:
        pace = tracker.pace()
        st.markdown(f"**Last reset:** {last.strftime('%Y-%m-%d %H:%M UTC')}")
        p1, p2, p3 = st.columns(3)
        p1.metric("Done this window", f"{pace['done']}/{pace['quota']}")
        p2.metric("Needed per minute", pace["needed_per_minute"])
        countdown = st.empty()
        if pace["on_pace"]:
            st.success("Quota met for this window. Keep logging or export the batch.")
        # Live countdown (reruns once per second while the tab is open)
        remaining = tracker.seconds_remaining()
        countdown.markdown(f"### ⏱ Next reset in {describe_countdown(remaining)}")
        if tracker.window_is_open():
            time.sleep(1)
            st.rerun()

# ------------------------------------------------------------------- export
with tab_export:
    st.subheader("Export evaluation dataset")
    findings: list[Finding] = st.session_state["findings"]
    if not findings:
        st.info("Nothing to export yet.")
    else:
        label = st.session_state.get("session_label", "")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
        e1, e2, e3 = st.columns(3)
        e1.download_button(
            "JSON dataset",
            findings_to_json(findings, session_label=label),
            file_name=f"evallog-{stamp}.json",
            mime="application/json",
            width="stretch",
        )
        e2.download_button(
            "CSV table",
            findings_to_csv(findings),
            file_name=f"evallog-{stamp}.csv",
            mime="text/csv",
            width="stretch",
        )
        e3.download_button(
            "Training CSV",
            findings_to_training_csv(findings),
            file_name=f"evallog-training-{stamp}.csv",
            mime="text/csv",
            width="stretch",
        )
        st.caption("Training CSV uses (input, observed, expected, label) rows for AI training platforms.")
        st.divider()
        st.subheader("Import a previous JSON export")
        uploaded = st.file_uploader("Upload evallog JSON", type=["json"])
        if uploaded is not None:
            try:
                data = json.loads(uploaded.read().decode("utf-8"))
                imported = [Finding.from_dict(item) for item in data.get("findings", [])]
                st.session_state["findings"] = imported
                st.success(f"Imported {len(imported)} findings.")
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                st.error(f"Could not import file: {exc}")
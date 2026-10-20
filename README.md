# 📝 EvalLog

**Structured logging for AI evaluation sessions: log findings against an enforced QA checklist, track usage-limit reset windows, and export submission-ready datasets.**

EvalLog is the operations companion for repetitive, high-volume model/agent evaluation work. It keeps evaluators rigorous under time pressure:

- **QA checklists** — every finding can only be saved after ticking the full session checklist (model, agent, or regression re-run checklists built in)
- **Reset tracker** — mark usage-limit resets, watch a live countdown to the next window, and see quota pace (scenarios done vs. needed per minute)
- **Validated findings** — required fields, controlled verdicts/categories/severities, and automatic rejection of placeholder text (`TODO`, `TBD`, …)
- **Dataset export** — JSON, CSV, and a flattened **training CSV** (`input, observed, expected, label`) formatted for AI training platforms, plus JSON import to resume sessions

## Quick start

```bash
git clone https://github.com/Mohd-Abdul-Nawaz/evallog.git
cd evallog
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Typical workflow

1. **Mark reset** in the Reset tracker tab when the usage limit resets.
2. **Log a finding** in the first tab — complete the QA checklist, fill observed vs. expected, flag anomalies.
3. Repeat until the quota pace meter says the window is complete.
4. **Export** the JSON/CSV/training-CSV artefacts and submit them; re-import later to continue.

## Tests

```bash
pytest -q
```

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Open [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **New app**.
3. Pick the repo, branch `main`, and main file path `app.py`.
4. Click **Deploy** — your app is live at `https://<app-name>.streamlit.app`.

## Project structure

```
evallog/
├── app.py             # Streamlit app (log / table / reset tracker / export)
├── evallog/           # Core library
│   ├── models.py      # Finding dataclass + validation
│   ├── checklists.py  # QA checklists per session type
│   ├── resets.py      # Usage-limit reset window tracking
│   └── export.py      # JSON / CSV / training-CSV exporters
└── tests/             # pytest suite
```

## License

MIT
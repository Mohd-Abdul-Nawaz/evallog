"""EvalLog: structured logging for AI evaluation sessions.

Record findings and anomalies with a enforced QA checklist, track
usage-limit reset windows, and export submission-ready datasets.
"""

from .checklists import CHECKLISTS, checklist_for
from .export import findings_to_csv, findings_to_json, findings_to_training_csv
from .models import CATEGORIES, SEVERITIES, Finding, validate_finding
from .resets import ResetTracker, describe_countdown

__version__ = "1.0.0"

__all__ = [
    "CHECKLISTS",
    "checklist_for",
    "findings_to_csv",
    "findings_to_json",
    "findings_to_training_csv",
    "CATEGORIES",
    "SEVERITIES",
    "Finding",
    "validate_finding",
    "ResetTracker",
    "describe_countdown",
    "__version__",
]
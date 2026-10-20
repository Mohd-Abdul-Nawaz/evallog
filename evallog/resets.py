"""Usage-limit reset tracking for repetitive evaluation batches.

Many evaluation engagements run against models with hourly/daily usage
limits. ResetTracker keeps the "reset, then repeat the batch" protocol
honest: it records reset events, computes the next window, and tells you
whether you are on pace with the session quota.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ResetTracker:
    """Tracks reset windows for a quota-limited evaluation batch.

    Attributes:
        interval_minutes: Minutes between usage-limit resets (e.g. 60).
        quota_per_window: How many scenarios must be completed per window.
        resets: UTC datetimes when resets were observed/applied.
        completed: Scenario ids completed in the current window.
    """

    interval_minutes: int = 60
    quota_per_window: int = 20
    resets: list[datetime] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)

    def mark_reset(self, at: datetime | None = None) -> datetime:
        """Record a reset event and open a fresh window."""
        moment = at or _now()
        self.resets.append(moment)
        self.completed = []
        return moment

    def last_reset(self) -> datetime | None:
        return self.resets[-1] if self.resets else None

    def next_reset(self) -> datetime | None:
        last = self.last_reset()
        if last is None:
            return None
        return last + timedelta(minutes=self.interval_minutes)

    def seconds_remaining(self, at: datetime | None = None) -> float | None:
        nxt = self.next_reset()
        if nxt is None:
            return None
        return max(0.0, (nxt - (at or _now())).total_seconds())

    def window_is_open(self, at: datetime | None = None) -> bool:
        remaining = self.seconds_remaining(at)
        return remaining is not None and remaining > 0

    def complete_scenario(self, scenario_id: str) -> None:
        if scenario_id not in self.completed:
            self.completed.append(scenario_id)

    def pace(self) -> dict[str, float | int]:
        """On-pace accounting: done, remaining, and scenarios-per-minute target."""
        remaining = self.seconds_remaining()
        quota_left = max(0, self.quota_per_window - len(self.completed))
        per_minute = (
            quota_left / (remaining / 60) if remaining and remaining > 0 else 0.0
        )
        return {
            "done": len(self.completed),
            "quota": self.quota_per_window,
            "remaining": quota_left,
            "on_pace": len(self.completed) >= self.quota_per_window,
            "needed_per_minute": round(per_minute, 2),
            "seconds_left": round(remaining or 0.0),
        }

    def to_dict(self) -> dict:
        return {
            "interval_minutes": self.interval_minutes,
            "quota_per_window": self.quota_per_window,
            "resets": [r.isoformat() for r in self.resets],
            "completed": list(self.completed),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResetTracker":
        tracker = cls(
            interval_minutes=int(data.get("interval_minutes", 60)),
            quota_per_window=int(data.get("quota_per_window", 20)),
        )
        tracker.resets = [datetime.fromisoformat(r) for r in data.get("resets", [])]
        tracker.completed = list(data.get("completed", []))
        return tracker


def describe_countdown(total_seconds: float | None) -> str:
    """Human countdown string like '42m 10s' (or '—' when no reset is set)."""
    if total_seconds is None:
        return "—"
    seconds = max(0, int(total_seconds))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs:02d}s"
    return f"{minutes}m {secs:02d}s"
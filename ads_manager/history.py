"""Historical metrics storage and change tracking.

Stores audit snapshots as timestamped JSON in data/history/ so reports
can show week-over-week trends and attribute changes to specific actions.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from ads_manager import get_project_root


def _history_dir() -> Path:
    return get_project_root() / "data" / "history"


def _changes_file() -> Path:
    return _history_dir() / "change_log.json"


def _ensure_dir():
    _history_dir().mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Snapshots — one per audit run
# ---------------------------------------------------------------------------

def save_snapshot(
    campaigns: list[dict],
    keywords: list[dict],
    days: int,
    recommendations: list[str],
) -> Path:
    """Save an audit snapshot. Returns the path to the saved file."""
    _ensure_dir()
    snapshot = {
        "date": date.today().isoformat(),
        "timestamp": datetime.now().isoformat(),
        "period_days": days,
        "campaigns": campaigns,
        "keywords": keywords,
        "recommendations": recommendations,
        "totals": _compute_totals(campaigns),
    }
    filename = f"snapshot_{date.today().isoformat()}.json"
    filepath = _history_dir() / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, default=str)
    return filepath


def _compute_totals(campaigns: list[dict]) -> dict:
    """Roll up campaign-level metrics into account totals."""
    totals = {
        "impressions": 0,
        "clicks": 0,
        "cost": 0.0,
        "conversions": 0,
    }
    for c in campaigns:
        totals["impressions"] += c.get("impressions", 0) or 0
        totals["clicks"] += c.get("clicks", 0) or 0
        totals["cost"] += c.get("cost", 0) or 0
        totals["conversions"] += c.get("conversions", 0) or 0

    if totals["impressions"] > 0:
        totals["ctr"] = totals["clicks"] / totals["impressions"]
    else:
        totals["ctr"] = 0

    if totals["clicks"] > 0:
        totals["avg_cpc"] = totals["cost"] / totals["clicks"]
    else:
        totals["avg_cpc"] = 0

    if totals["conversions"] > 0:
        totals["cost_per_conversion"] = totals["cost"] / totals["conversions"]
    else:
        totals["cost_per_conversion"] = None

    return totals


def load_previous_snapshot(days: Optional[int] = None) -> Optional[dict]:
    """Load the most recent snapshot before today.

    If days is specified, only match snapshots with the same period length
    so we compare apples to apples (7-day vs 7-day, not 7-day vs 30-day).
    """
    _ensure_dir()
    today = date.today().isoformat()
    snapshots = sorted(_history_dir().glob("snapshot_*.json"), reverse=True)

    for path in snapshots:
        # Skip today's snapshot — we want the previous one
        if today in path.name:
            continue
        with open(path, encoding="utf-8") as f:
            snap = json.load(f)
        if days is None or snap.get("period_days") == days:
            return snap
    return None


def load_snapshot_by_date(snapshot_date: str) -> Optional[dict]:
    """Load a specific snapshot by date string (YYYY-MM-DD)."""
    path = _history_dir() / f"snapshot_{snapshot_date}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


# ---------------------------------------------------------------------------
# Change log — tracks what was modified and when
# ---------------------------------------------------------------------------

def log_change(
    action: str,
    details: str,
    campaign: Optional[str] = None,
    keywords: Optional[list[str]] = None,
):
    """Record a change so the next audit can attribute results to it.

    Examples:
        log_change("paused_keyword", "Paused 'comedy show tickets'",
                   campaign="Things To Do - Bristol",
                   keywords=["comedy show tickets"])
        log_change("budget_increase", "Daily budget $3.29 -> $4.00",
                   campaign="Things To Do - Bristol")
        log_change("new_ad", "Added RSA with headline 'Live Comedy in Bristol'",
                   campaign="Things To Do - Bristol")
    """
    _ensure_dir()
    log = _load_change_log()
    entry = {
        "date": date.today().isoformat(),
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
    }
    if campaign:
        entry["campaign"] = campaign
    if keywords:
        entry["keywords"] = keywords
    log.append(entry)
    with open(_changes_file(), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, default=str)


def get_changes_since(since_date: str) -> list[dict]:
    """Return all logged changes on or after the given date (YYYY-MM-DD)."""
    log = _load_change_log()
    return [entry for entry in log if entry.get("date", "") >= since_date]


def _load_change_log() -> list[dict]:
    cf = _changes_file()
    if cf.exists():
        with open(cf, encoding="utf-8") as f:
            return json.load(f)
    return []


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def compare_totals(current: dict, previous: dict) -> dict:
    """Compare two totals dicts and return deltas + percentage changes.

    Returns a dict like:
        {"clicks": {"current": 47, "previous": 39, "delta": 8, "pct": 0.205}}
    """
    result = {}
    for key in ["impressions", "clicks", "cost", "conversions", "ctr", "avg_cpc", "cost_per_conversion"]:
        curr_val = current.get(key)
        prev_val = previous.get(key)
        if curr_val is None or prev_val is None:
            result[key] = {"current": curr_val, "previous": prev_val, "delta": None, "pct": None}
            continue
        delta = curr_val - prev_val
        if prev_val != 0:
            pct = delta / abs(prev_val)
        else:
            pct = None
        result[key] = {"current": curr_val, "previous": prev_val, "delta": delta, "pct": pct}
    return result

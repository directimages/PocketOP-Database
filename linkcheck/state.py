"""Persisted per-URL history for the link check.

Committed to the repo (like the Sniffer's sniffer.db) so two things carry
across runs:

1. A network-level failure (DNS resolution, connection refused, or another
   connection error) is only promoted to "dead" once it has been seen on two
   separate SCHEDULED runs in a row. A single bad run just reports
   "needs_manual_check" -- a briefly-down host must not be labelled dead.
   Manual workflow_dispatch runs report live status but never advance or
   reset this streak, so an ad-hoc re-run can't accidentally confirm a
   promotion the schedule hasn't earned.
2. A URL checked very recently (outside of a real scheduled run) is served
   from cache instead of re-checked, so re-running the workflow by hand the
   same day does not hammer every host a second time.
"""

import datetime as dt
import json
from pathlib import Path

DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "state.json"
RECENT_CHECK_WINDOW_SECONDS = 6 * 60 * 60  # 6 hours


def load_state(path=DEFAULT_STATE_PATH):
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state, path=DEFAULT_STATE_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def record_key(field, url):
    return f"{field}:{url}"


def recently_checked(record, now, window_seconds=RECENT_CHECK_WINDOW_SECONDS):
    if not record or "last_checked" not in record:
        return False
    last_checked = dt.datetime.fromisoformat(record["last_checked"])
    return (now - last_checked).total_seconds() < window_seconds


def resolve_network_error(record, failure_type, is_scheduled_run, now_iso):
    """Decide the reported classification for a raw "network_error" result
    and return (final_classification, new_state_record).

    Only scheduled runs advance or reset the streak. A manual run reports
    the prior streak's implication without changing it.
    """
    previous_streak = (record or {}).get("network_failure_streak", 0)
    previously_network_error = (record or {}).get("raw_classification") == "network_error"

    if is_scheduled_run:
        streak = previous_streak + 1 if previously_network_error else 1
    else:
        streak = previous_streak

    final_classification = "dead" if (is_scheduled_run and streak >= 2) else "needs_manual_check"

    new_record = {
        "last_checked": now_iso,
        "raw_classification": "network_error",
        "reported_classification": final_classification,
        "failure_type": failure_type,
        "network_failure_streak": streak,
    }
    return final_classification, new_record


def record_clean_result(classification, failure_type, now_iso):
    """Build the state record for a non-network-error result (live, dead,
    or needs_manual_check reached directly). Always resets the network
    failure streak."""
    return {
        "last_checked": now_iso,
        "raw_classification": classification,
        "reported_classification": classification,
        "failure_type": failure_type,
        "network_failure_streak": 0,
    }

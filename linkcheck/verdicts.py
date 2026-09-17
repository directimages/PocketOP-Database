"""Persistent human verdicts for domains CI cannot verify on its own.

Some domains refuse this checker's connections at the network level (no HTTP
status at all -- see unreachable_detection.py). From CI that is genuinely
ambiguous: a domain that is live but blocks datacenter traffic looks
identical to one that is actually dead (DNS gone, host down). The checker
cannot browse, so it cannot decide which it is. A person can, in one browser
check, and that decision is recorded here so it survives across runs.

This file is the source of truth for manual verdicts. It is checked into the
repo and edited by hand. Shape:

    {
      "domains": {
        "www.example.com": {
          "verdict": "live",              # "live" or "dead"
          "checked": "2026-09-17",        # free-form, for the human record
          "recheck_after": "2026-12-17",  # optional ISO date; null/omitted = no expiry
          "note": "why this verdict"      # optional
        }
      }
    }

Keyed by exact host (the netloc of the URLs, e.g. "www.angenieux.com").

Behaviour honoured by the checker:

- "live" (not past recheck_after): the domain's URLs are moved out of the
  actionable "unreachable from CI" bucket into a quiet "manually verified
  live" line -- no notification. The checker short-circuits the HTTP checks
  for that host, so a domain that can only be blocking CI is not re-probed
  pointlessly every run.
- "dead" (not past recheck_after): the domain's URLs are surfaced in a
  "manually verified dead -- replacement owed" worklist. Not counted toward
  the notification trigger; the operator already knows.
- past recheck_after: the verdict is treated as expired and ignored, so the
  domain is checked and re-surfaced normally. "live" is never blindly
  permanent.
- no verdict: the domain stays fully checked and actionable, so a genuinely
  dead domain is never hidden.

Robustness: a missing file means no verdicts. A malformed file, or an entry
with an unrecognised verdict value, is warned about and skipped rather than
failing the weekly run over a hand-edit typo.
"""

import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_VERDICTS_PATH = Path(__file__).resolve().parent / "verdicts.json"

VERDICT_LIVE = "live"
VERDICT_DEAD = "dead"
_VALID_VERDICTS = {VERDICT_LIVE, VERDICT_DEAD}

VERIFIED_LIVE_FAILURE_TYPE = "manually_verified_live"
VERIFIED_DEAD_FAILURE_TYPE = "manually_verified_dead"


def host_of(url):
    """The host key a verdict is looked up under (the URL's netloc)."""
    return urlsplit(url).netloc


def load_verdicts(path=DEFAULT_VERDICTS_PATH):
    """Return {host: record} for every well-formed verdict.

    Missing file -> {}. Malformed JSON, a non-object body, a non-object
    entry, or an unrecognised verdict value -> warn and skip, never raise:
    a bad hand-edit must not take down the weekly run.
    """
    path = Path(path)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: could not read verdict file {path}: {exc!r}; proceeding with no verdicts.")
        return {}

    domains = data.get("domains") if isinstance(data, dict) else None
    if not isinstance(domains, dict):
        if domains is not None:
            print(f"Warning: verdict file {path} has no valid 'domains' object; proceeding with no verdicts.")
        return {}

    verdicts = {}
    for host, record in domains.items():
        if not isinstance(record, dict):
            print(f"Warning: verdict for {host!r} is not an object; ignoring it.")
            continue
        verdict = record.get("verdict")
        if verdict not in _VALID_VERDICTS:
            print(f"Warning: verdict for {host!r} is {verdict!r}, expected 'live' or 'dead'; ignoring it.")
            continue
        verdicts[host] = record
    return verdicts


def _is_expired(record, run_date):
    recheck_after = record.get("recheck_after")
    if not recheck_after:
        return False
    try:
        recheck_date = dt.date.fromisoformat(recheck_after)
    except (ValueError, TypeError):
        host_note = record.get("verdict")
        print(f"Warning: recheck_after {recheck_after!r} on a {host_note!r} verdict is not an ISO date; treating verdict as active.")
        return False
    return run_date >= recheck_date


def active_verdict(verdicts, host, run_date):
    """The verdict string ("live"/"dead") in force for host on run_date, or
    None if there is no verdict or it has passed its recheck_after date.

    run_date is a datetime.date.
    """
    record = verdicts.get(host)
    if record is None:
        return None
    if _is_expired(record, run_date):
        return None
    return record.get("verdict")

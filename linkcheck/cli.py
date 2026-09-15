"""Orchestrate one link-check run: fetch, check concurrently (politely),
resolve classifications against persisted state, render the report, and
write the report + state back to disk.

Run as: python -m linkcheck.cli
"""

import datetime as dt
import os
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import requests

from . import checker, fetch_database, report, state as state_module

GLOBAL_CONCURRENCY = 8
PER_HOST_CONCURRENCY = 2
USER_AGENT = (
    "PocketOP-LinkCheck/1.0 (+https://pocketop.app; weekly productUrl/manufacturerUrl "
    "liveness check; contact: news@pocketop.app)"
)

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


class _HostGate:
    """Caps concurrent requests per host so one manufacturer domain with many
    entries is never hammered, independent of the global concurrency cap."""

    def __init__(self, per_host_limit):
        self._per_host_limit = per_host_limit
        self._lock = threading.Lock()
        self._semaphores = {}

    def for_host(self, host):
        with self._lock:
            sem = self._semaphores.get(host)
            if sem is None:
                sem = threading.Semaphore(self._per_host_limit)
                self._semaphores[host] = sem
            return sem


def _get_session(local_storage):
    session = getattr(local_storage, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        local_storage.session = session
    return session


def check_field(entries, field_name, existing_state, is_scheduled_run, now):
    """Check every entry for one field (productUrl or manufacturerUrl).

    Returns (dead_list, needs_manual_check_list, new_state_records) where the
    list items are {"id", "name", "category", "url", "failure_type"}.
    """
    now_iso = now.isoformat()
    local_storage = threading.local()
    host_gate = _HostGate(PER_HOST_CONCURRENCY)
    new_state_records = {}
    dead, needs_manual_check = [], []
    results_lock = threading.Lock()

    def worker(entry):
        key = state_module.record_key(field_name, entry["url"])
        prior = existing_state.get(key)

        if not is_scheduled_run and state_module.recently_checked(prior, now):
            return key, entry, prior["reported_classification"], prior.get("failure_type"), None

        host = urlsplit(entry["url"]).netloc
        session = _get_session(local_storage)
        with host_gate.for_host(host):
            result = checker.check_url(session, entry["url"])

        if result.classification == "network_error":
            final_classification, new_record = state_module.resolve_network_error(
                prior, result.failure_type, is_scheduled_run, now_iso
            )
        else:
            final_classification = result.classification
            new_record = state_module.record_clean_result(result.classification, result.failure_type, now_iso)

        return key, entry, final_classification, new_record.get("failure_type") if new_record else result.failure_type, new_record

    with ThreadPoolExecutor(max_workers=GLOBAL_CONCURRENCY) as pool:
        for key, entry, final_classification, failure_type, new_record in pool.map(worker, entries):
            if new_record is not None:
                new_state_records[key] = new_record
            if final_classification in ("dead", "needs_manual_check"):
                row = {**entry, "failure_type": failure_type}
                with results_lock:
                    (dead if final_classification == "dead" else needs_manual_check).append(row)

    return dead, needs_manual_check, new_state_records


def run(state_path=state_module.DEFAULT_STATE_PATH, reports_dir=REPORTS_DIR, now=None, fetch=fetch_database.fetch_json):
    now = now or dt.datetime.now(dt.timezone.utc)
    is_scheduled_run = os.environ.get("GITHUB_EVENT_NAME") == "schedule"

    existing_state = state_module.load_state(state_path)
    is_first_run = not existing_state

    product_entries, product_gaps, manufacturer_entries, manufacturer_gaps = fetch_database.load_link_entries(fetch)

    product_dead, product_needs_check, product_state = check_field(
        product_entries, "productUrl", existing_state, is_scheduled_run, now
    )
    manufacturer_dead, manufacturer_needs_check, manufacturer_state = check_field(
        manufacturer_entries, "manufacturerUrl", existing_state, is_scheduled_run, now
    )

    new_state = dict(existing_state)
    new_state.update(product_state)
    new_state.update(manufacturer_state)

    iso_year, iso_week, _ = now.isocalendar()
    run_date = now.date().isoformat()
    report_text = report.render_report(
        run_date=run_date,
        is_first_run=is_first_run,
        product_dead=product_dead,
        product_needs_check=product_needs_check,
        product_gaps=product_gaps,
        manufacturer_dead=manufacturer_dead,
        manufacturer_needs_check=manufacturer_needs_check,
        manufacturer_gaps=manufacturer_gaps,
    )

    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{iso_year}-W{iso_week:02d}.md"
    report_path.write_text(report_text, encoding="utf-8")

    state_module.save_state(new_state, state_path)

    return report_path


def main():
    report_path = run()
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()

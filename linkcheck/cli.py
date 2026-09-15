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

from . import checker, fetch_database, issue_reporter, report, state as state_module, waf_detection

GLOBAL_CONCURRENCY = 8
PER_HOST_CONCURRENCY = 2
USER_AGENT = (
    "PocketOP-LinkCheck/1.0 (+https://pocketop.app; weekly productUrl/manufacturerUrl "
    "liveness check)"
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


def _safe_is_blocked(domain_block_cache, session, entry_url):
    """Same safety net as around checker.check_url: if the domain-root probe
    itself fails unexpectedly, fall back to "not domain-blocked" rather than
    crashing the run -- the entry then falls through to its normal
    needs_manual_check classification instead of disappearing."""
    try:
        return domain_block_cache.is_blocked(session, entry_url)
    except Exception as exc:
        print(f"Warning: unexpected error probing domain for {entry_url}: {exc!r}")
        return False


def check_field(entries, field_name, existing_state, is_scheduled_run, now, domain_block_cache):
    """Check every entry for one field (productUrl or manufacturerUrl).

    Returns (dead_list, needs_manual_check_list, unverifiable_domain_list,
    new_state_records) where the list items are
    {"id", "name", "category", "url", "failure_type"}.

    unverifiable_domain holds links whose whole domain 403s CI traffic (a
    WAF, not a per-link defect) -- see waf_detection.py. These are never
    dead, never needs_manual_check, and the caller must not count them
    toward the actionable/notification trigger.
    """
    now_iso = now.isoformat()
    local_storage = threading.local()
    host_gate = _HostGate(PER_HOST_CONCURRENCY)
    new_state_records = {}
    dead, needs_manual_check, unverifiable_domain = [], [], []
    results_lock = threading.Lock()

    def worker(entry):
        key = state_module.record_key(field_name, entry["url"])
        prior = existing_state.get(key)

        if not is_scheduled_run and state_module.recently_checked(prior, now):
            return key, entry, prior["reported_classification"], prior.get("failure_type"), None

        host = urlsplit(entry["url"]).netloc
        session = _get_session(local_storage)
        try:
            with host_gate.for_host(host):
                result = checker.check_url(session, entry["url"])
        except Exception as exc:
            # Last-resort safety net: checker.py already handles every
            # requests-level failure this tool has seen in practice, but
            # ~1900 arbitrary third-party URLs will eventually produce
            # something nobody anticipated. One bad link must never take
            # down the whole run and lose every result already computed --
            # it becomes a needs-manual-check row instead of a crash.
            print(f"Warning: unexpected error checking {entry['url']}: {exc!r}")
            result = checker.CheckResult(
                "needs_manual_check", f"unexpected_error_{type(exc).__name__}", None, None
            )

        if result.classification == "network_error":
            final_classification, new_record = state_module.resolve_network_error(
                prior, result.failure_type, is_scheduled_run, now_iso
            )
        elif (
            result.classification == "needs_manual_check"
            and result.failure_type == waf_detection.DOMAIN_BLOCK_FAILURE_TYPE
            and _safe_is_blocked(domain_block_cache, session, entry["url"])
        ):
            final_classification = "unverifiable_domain"
            new_record = state_module.record_clean_result(
                final_classification, waf_detection.UNVERIFIABLE_FAILURE_TYPE, now_iso
            )
        else:
            final_classification = result.classification
            new_record = state_module.record_clean_result(result.classification, result.failure_type, now_iso)

        return key, entry, final_classification, new_record.get("failure_type") if new_record else result.failure_type, new_record

    target_by_classification = {
        "dead": dead,
        "needs_manual_check": needs_manual_check,
        "unverifiable_domain": unverifiable_domain,
    }

    with ThreadPoolExecutor(max_workers=GLOBAL_CONCURRENCY) as pool:
        for key, entry, final_classification, failure_type, new_record in pool.map(worker, entries):
            if new_record is not None:
                new_state_records[key] = new_record
            target = target_by_classification.get(final_classification)
            if target is not None:
                row = {**entry, "failure_type": failure_type}
                with results_lock:
                    target.append(row)

    return dead, needs_manual_check, unverifiable_domain, new_state_records


def run(
    state_path=state_module.DEFAULT_STATE_PATH,
    reports_dir=REPORTS_DIR,
    now=None,
    fetch=fetch_database.fetch_json,
    github_token=None,
    github_repo=None,
    issue_session_factory=requests.Session,
):
    now = now or dt.datetime.now(dt.timezone.utc)
    is_scheduled_run = os.environ.get("GITHUB_EVENT_NAME") == "schedule"

    existing_state = state_module.load_state(state_path)
    is_first_run = not existing_state

    product_entries, product_gaps, manufacturer_entries, manufacturer_gaps = fetch_database.load_link_entries(fetch)

    # Shared across both fields so a domain hit once (e.g. via a productUrl
    # entry) is not re-probed again for a manufacturerUrl entry on the same host.
    domain_block_cache = waf_detection.DomainBlockCache()

    product_dead, product_needs_check, product_unverifiable, product_state = check_field(
        product_entries, "productUrl", existing_state, is_scheduled_run, now, domain_block_cache
    )
    manufacturer_dead, manufacturer_needs_check, manufacturer_unverifiable, manufacturer_state = check_field(
        manufacturer_entries, "manufacturerUrl", existing_state, is_scheduled_run, now, domain_block_cache
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
        product_unverifiable=product_unverifiable,
        product_gaps=product_gaps,
        manufacturer_dead=manufacturer_dead,
        manufacturer_needs_check=manufacturer_needs_check,
        manufacturer_unverifiable=manufacturer_unverifiable,
        manufacturer_gaps=manufacturer_gaps,
    )

    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{iso_year}-W{iso_week:02d}.md"
    report_path.write_text(report_text, encoding="utf-8")

    state_module.save_state(new_state, state_path)

    actionable = issue_reporter.is_actionable(
        product_dead=product_dead,
        product_needs_check=product_needs_check,
        manufacturer_dead=manufacturer_dead,
        manufacturer_needs_check=manufacturer_needs_check,
        manufacturer_gaps=manufacturer_gaps,
    )
    token = github_token if github_token is not None else os.environ.get("GITHUB_TOKEN")
    repo = github_repo if github_repo is not None else os.environ.get("GITHUB_REPOSITORY")
    if actionable and token and repo:
        report_relative_path = f"linkcheck/reports/{report_path.name}"
        report_link = f"[{report_relative_path}](https://github.com/{repo}/blob/main/{report_relative_path})"
        issue_body = report.render_issue_summary(
            run_date=run_date,
            is_first_run=is_first_run,
            product_dead=product_dead,
            product_needs_check=product_needs_check,
            manufacturer_dead=manufacturer_dead,
            manufacturer_needs_check=manufacturer_needs_check,
            manufacturer_gaps=manufacturer_gaps,
            report_link=report_link,
        )
        try:
            issue_reporter.post_report(
                session=issue_session_factory(),
                repo=repo,
                token=token,
                body=issue_body,
                actionable=actionable,
            )
        except Exception as exc:  # notification is best-effort; never fail the run over it
            print(f"Warning: could not post link-check issue notification: {exc}")
    elif actionable:
        print("Skipping issue notification: no GITHUB_TOKEN/GITHUB_REPOSITORY in this environment.")

    return report_path


def main():
    report_path = run()
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()

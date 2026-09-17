"""Orchestrate one link-check run: fetch, check concurrently (politely),
resolve classifications against persisted state, render the report, and
write the report + state back to disk.

Run as: python -m linkcheck.cli
"""

import datetime as dt
import os
import threading
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import requests

from . import (
    checker,
    fetch_database,
    issue_reporter,
    report,
    state as state_module,
    unreachable_detection,
    verdicts as verdicts_module,
    waf_detection,
)


@dataclass
class FieldResult:
    """One field's (productUrl or manufacturerUrl) buckets from a run.

    dead / needs_manual_check / unverifiable_domain render per field, exactly
    as before. unreachable / verified_live / verified_dead are domain-level
    concepts, so their rows carry "host" and "field" and the caller groups
    them across both fields into one row per domain.
    """

    dead: list = field(default_factory=list)
    needs_manual_check: list = field(default_factory=list)
    unverifiable_domain: list = field(default_factory=list)
    unreachable: list = field(default_factory=list)
    verified_live: list = field(default_factory=list)
    verified_dead: list = field(default_factory=list)
    state_records: dict = field(default_factory=dict)

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


def _safe_is_unreachable(domain_unreachable_cache, session, entry_url):
    """Safety net around the domain-unreachable root probe. If the probe
    itself fails unexpectedly, fall back to "not domain-unreachable" so the
    entry keeps its normal network-error handling (the streak path) rather
    than the run crashing."""
    try:
        return domain_unreachable_cache.is_unreachable(session, entry_url)
    except Exception as exc:
        print(f"Warning: unexpected error probing domain reachability for {entry_url}: {exc!r}")
        return False


def check_field(entries, field_name, existing_state, is_scheduled_run, now, run_date,
                domain_block_cache, domain_unreachable_cache, verdicts):
    """Check every entry for one field (productUrl or manufacturerUrl).

    Returns a FieldResult. dead / needs_manual_check / unverifiable_domain
    items are {"id", "name", "category", "url", "failure_type"}; unreachable /
    verified_live / verified_dead items additionally carry "host" and "field"
    so the caller can collapse them into one row per domain across both fields.

    - unverifiable_domain: whole domain 403s CI traffic (a WAF, not a per-link
      defect -- see waf_detection.py). Never actionable.
    - unreachable: whole domain refuses CI connections with no HTTP status and
      has no recorded verdict yet (see unreachable_detection.py). Ambiguous
      (blocking vs genuinely dead), so it stays actionable until a human
      records a verdict, and is NOT promoted to dead by the network-error
      streak.
    - verified_live / verified_dead: a human verdict in verdicts.json already
      resolved this domain. Neither is actionable; the checks are
      short-circuited entirely for these hosts.
    """
    now_iso = now.isoformat()
    local_storage = threading.local()
    host_gate = _HostGate(PER_HOST_CONCURRENCY)
    result_out = FieldResult()
    results_lock = threading.Lock()

    def worker(entry):
        key = state_module.record_key(field_name, entry["url"])
        prior = existing_state.get(key)
        host = verdicts_module.host_of(entry["url"])

        # A standing human verdict short-circuits the HTTP checks entirely:
        # a live-but-blocking-CI domain cannot be verified from here anyway,
        # and a known-dead one need not be re-probed. recheck_after (handled
        # in active_verdict) is what keeps a verdict from being permanent.
        verdict = verdicts_module.active_verdict(verdicts, host, run_date)
        if verdict == verdicts_module.VERDICT_LIVE:
            new_record = state_module.record_clean_result(
                "verified_live", verdicts_module.VERIFIED_LIVE_FAILURE_TYPE, now_iso
            )
            return key, entry, "verified_live", new_record["failure_type"], new_record, host
        if verdict == verdicts_module.VERDICT_DEAD:
            new_record = state_module.record_clean_result(
                "verified_dead", verdicts_module.VERIFIED_DEAD_FAILURE_TYPE, now_iso
            )
            return key, entry, "verified_dead", new_record["failure_type"], new_record, host

        if not is_scheduled_run and state_module.recently_checked(prior, now):
            return key, entry, prior["reported_classification"], prior.get("failure_type"), None, host

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
            if _safe_is_unreachable(domain_unreachable_cache, session, entry["url"]):
                # The whole domain refuses CI connections. Group it, and do
                # NOT let the streak promote it to a false-dead: it is
                # ambiguous and stays actionable until a human verdict.
                final_classification = "unreachable_domain"
                new_record = state_module.record_clean_result(
                    final_classification, unreachable_detection.UNREACHABLE_FAILURE_TYPE, now_iso
                )
            else:
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

        return key, entry, final_classification, new_record.get("failure_type") if new_record else result.failure_type, new_record, host

    target_by_classification = {
        "dead": result_out.dead,
        "needs_manual_check": result_out.needs_manual_check,
        "unverifiable_domain": result_out.unverifiable_domain,
        "unreachable_domain": result_out.unreachable,
        "verified_live": result_out.verified_live,
        "verified_dead": result_out.verified_dead,
    }

    with ThreadPoolExecutor(max_workers=GLOBAL_CONCURRENCY) as pool:
        for key, entry, final_classification, failure_type, new_record, host in pool.map(worker, entries):
            if new_record is not None:
                result_out.state_records[key] = new_record
            target = target_by_classification.get(final_classification)
            if target is not None:
                row = {**entry, "failure_type": failure_type, "host": host, "field": field_name}
                with results_lock:
                    target.append(row)

    return result_out


def _group_by_domain(*entry_lists):
    """Collapse domain-level rows from both fields into one row per domain:
    {"domain", "productUrl", "manufacturerUrl", "failure_type"}, where the
    two field keys carry the count of affected entries on that field. So the
    ~43 angenieux rows (19 productUrl + 24 manufacturerUrl) become a single
    domain entry instead of flooding the per-id lists."""
    groups = {}
    for entries in entry_lists:
        for item in entries:
            host = item["host"]
            group = groups.get(host)
            if group is None:
                group = {"domain": host, "productUrl": 0, "manufacturerUrl": 0,
                         "failure_type": item["failure_type"]}
                groups[host] = group
            group[item["field"]] += 1
    return sorted(groups.values(), key=lambda g: g["domain"])


def run(
    state_path=state_module.DEFAULT_STATE_PATH,
    reports_dir=REPORTS_DIR,
    now=None,
    fetch=fetch_database.fetch_json,
    github_token=None,
    github_repo=None,
    issue_session_factory=requests.Session,
    verdicts_path=verdicts_module.DEFAULT_VERDICTS_PATH,
):
    now = now or dt.datetime.now(dt.timezone.utc)
    run_date_obj = now.date()
    is_scheduled_run = os.environ.get("GITHUB_EVENT_NAME") == "schedule"

    existing_state = state_module.load_state(state_path)
    is_first_run = not existing_state
    verdicts = verdicts_module.load_verdicts(verdicts_path)

    product_entries, product_gaps, manufacturer_entries, manufacturer_gaps = fetch_database.load_link_entries(fetch)

    # Both caches are shared across the two fields so a domain hit once (e.g.
    # via a productUrl entry) is not re-probed again for a manufacturerUrl
    # entry on the same host.
    domain_block_cache = waf_detection.DomainBlockCache()
    domain_unreachable_cache = unreachable_detection.DomainUnreachableCache()

    product = check_field(
        product_entries, "productUrl", existing_state, is_scheduled_run, now, run_date_obj,
        domain_block_cache, domain_unreachable_cache, verdicts,
    )
    manufacturer = check_field(
        manufacturer_entries, "manufacturerUrl", existing_state, is_scheduled_run, now, run_date_obj,
        domain_block_cache, domain_unreachable_cache, verdicts,
    )

    product_dead, product_needs_check, product_unverifiable = product.dead, product.needs_manual_check, product.unverifiable_domain
    manufacturer_dead, manufacturer_needs_check, manufacturer_unverifiable = (
        manufacturer.dead, manufacturer.needs_manual_check, manufacturer.unverifiable_domain
    )

    unreachable_domains = _group_by_domain(product.unreachable, manufacturer.unreachable)
    verified_live_domains = _group_by_domain(product.verified_live, manufacturer.verified_live)
    verified_dead_domains = _group_by_domain(product.verified_dead, manufacturer.verified_dead)

    new_state = dict(existing_state)
    new_state.update(product.state_records)
    new_state.update(manufacturer.state_records)

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
        unreachable_domains=unreachable_domains,
        verified_live_domains=verified_live_domains,
        verified_dead_domains=verified_dead_domains,
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
        unreachable_domains=unreachable_domains,
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
            unreachable_domains=unreachable_domains,
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

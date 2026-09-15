"""HTTP liveness check for a single URL.

Classification produced here is one of:

- "live": resolves (directly, or via redirect) to a page that is not a
  confirmed dead end.
- "dead": a definitive dead code (404, 410). No cross-run confirmation
  needed, these are trusted on the first sighting.
- "needs_manual_check": an ambiguous or blocking result that survived
  retries within this run (403, 429, 408, 5xx, timeout, a redirect landing
  on the site homepage, or a 200 whose body looks like a soft-404). Never
  reported as dead.
- "network_error": a connection-level failure (DNS resolution, connection
  refused, or another connection error). This is deliberately NOT decided
  as dead or needs_manual_check here -- a briefly-down host must not be
  reported as a dead product link on a single run. The caller (state.py /
  cli.py) promotes this to "dead" only once it persists across two separate
  SCHEDULED runs; otherwise it is reported as needs_manual_check.

Approach: try a HEAD request first (lightweight). If that does not cleanly
resolve to a 2xx (wrong status, exception, or a redirect that looks like a
homepage bounce), fall back to a full GET, retrying transient/blocking
results with backoff. The GET response body (when available) is used for a
best-effort soft-404 text check; a HEAD-only success never gets that check.
"""

import time
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests

DEAD_STATUS_CODES = {404, 410}
TRANSIENT_STATUS_CODES = {403, 429, 408, 500, 502, 503, 504}
RETRYABLE_EXCEPTIONS = {"timeout", "dns_failure", "connection_refused", "connection_error"}

DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE_SECONDS = 1.0

SOFT_404_MARKERS = (
    "page not found",
    "404 error",
    "no longer available",
    "product discontinued",
    "we can't find that page",
    "we cannot find that page",
    "this page doesn't exist",
    "content not found",
    "sorry, this product is no longer",
)

_DNS_MARKERS = (
    "name or service not known",
    "nodename nor servname",
    "failed to resolve",
    "getaddrinfo failed",
    "temporary failure in name resolution",
)
_REFUSED_MARKERS = ("connection refused", "econnrefused")


@dataclass
class CheckResult:
    classification: str
    failure_type: str | None
    status: int | None
    final_url: str | None


def classify_connection_error(exc: Exception) -> str:
    message = str(exc).lower()
    if any(marker in message for marker in _DNS_MARKERS):
        return "dns_failure"
    if any(marker in message for marker in _REFUSED_MARKERS):
        return "connection_refused"
    return "connection_error"


def _check_redirect_landing(original_url, final_url, body):
    if final_url and final_url != original_url:
        original_path = urlsplit(original_url).path.rstrip("/")
        final_path = urlsplit(final_url).path.rstrip("/")
        if original_path and not final_path:
            return "redirected_to_homepage"
    if body:
        lowered = body.lower()
        for marker in SOFT_404_MARKERS:
            if marker in lowered:
                return "possible_soft_404"
    return None


def _attempt(session, url, method, timeout):
    try:
        if method == "head":
            resp = session.head(url, allow_redirects=True, timeout=timeout)
            body = None
        else:
            resp = session.get(url, allow_redirects=True, timeout=timeout)
            body = resp.text[:4000] if resp.status_code < 400 else None
        return resp.status_code, resp.url, body, None
    except requests.exceptions.Timeout:
        return None, None, None, "timeout"
    except requests.exceptions.ConnectionError as exc:
        return None, None, None, classify_connection_error(exc)


def _build_result(status, exc, final_url, body, original_url):
    if exc == "timeout":
        return CheckResult("needs_manual_check", "timeout_after_retries", None, None)
    if exc in ("dns_failure", "connection_refused", "connection_error"):
        return CheckResult("network_error", exc, None, None)

    if status in DEAD_STATUS_CODES:
        return CheckResult("dead", str(status), status, final_url)

    if status in TRANSIENT_STATUS_CODES:
        return CheckResult("needs_manual_check", f"http_{status}_after_retries", status, final_url)

    if status is not None and 200 <= status < 400:
        redirect_issue = _check_redirect_landing(original_url, final_url, body)
        if redirect_issue:
            return CheckResult("needs_manual_check", redirect_issue, status, final_url)
        return CheckResult("live", None, status, final_url)

    return CheckResult("needs_manual_check", f"unexpected_status_{status}", status, final_url)


def check_url(
    session,
    url,
    timeout=DEFAULT_TIMEOUT_SECONDS,
    max_retries=DEFAULT_MAX_RETRIES,
    backoff_base=DEFAULT_BACKOFF_BASE_SECONDS,
) -> CheckResult:
    """Check one URL. See module docstring for the classification rules."""
    status, final_url, body, exc = _attempt(session, url, "head", timeout)

    head_is_clean = exc is None and status is not None and 200 <= status < 400
    if head_is_clean and _check_redirect_landing(url, final_url, None) is None:
        return _build_result(status, exc, final_url, None, url)

    # Full-request fallback: either HEAD was rejected/ambiguous/erroring, or
    # it looked like a homepage bounce and deserves a body-backed second look.
    delay = backoff_base
    for attempt in range(max_retries):
        status, final_url, body, exc = _attempt(session, url, "get", timeout)
        should_retry = exc in RETRYABLE_EXCEPTIONS or status in TRANSIENT_STATUS_CODES
        if not should_retry or attempt == max_retries - 1:
            break
        time.sleep(delay)
        delay *= 2

    return _build_result(status, exc, final_url, body, url)

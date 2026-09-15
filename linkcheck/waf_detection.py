"""Detect when an entire domain is blocking this checker, rather than one
specific link being broken.

Some manufacturer sites (canon-europe.com, confirmed in testing) run a WAF
that returns 403 to datacenter/CI traffic regardless of which path is
requested, including the domain root. That is not a per-link defect: the
link can be neither confirmed dead nor reliably confirmed live from here.
Routing it into needs-manual-check would bury the ~40 entries behind such a
domain in a section meant for genuinely ambiguous individual links, and
would make almost every run "actionable" purely on WAF noise -- exactly the
inbox spam the actionable/notification gate exists to avoid.

Detection: when a link comes back needs_manual_check with the specific
DOMAIN_BLOCK_FAILURE_TYPE signature (a 403 that survived retries), check
whether that domain's own root also 403s the same way. If so, the whole
domain is blocking us and every link on it is reported separately as
"unverifiable from CI", not dead, not needs-manual-check, and never counted
toward the actionable/notification trigger.

Other ambiguous outcomes (429, 5xx, timeouts, redirect oddities) are not
treated as domain-wide by this module -- only the specific 403 signature
is, since that is the one observed in practice. Everything else still goes
through the normal needs-manual-check path.
"""

import threading
from urllib.parse import urlsplit

from . import checker

DOMAIN_BLOCK_FAILURE_TYPE = "http_403_after_retries"
UNVERIFIABLE_FAILURE_TYPE = "waf_blocked_domain_wide"


class DomainBlockCache:
    """Per-run cache so a domain with many entries (e.g. ~40 Canon URLs)
    only has its root probed once, not once per entry on that domain.

    Uses a lock per host, held for the whole probe-and-cache section, so
    concurrent workers hitting the same never-yet-seen host block on each
    other instead of all issuing their own root probe before any of them
    has written the result -- a plain check-then-write with only a short
    lock around each half would race under real thread concurrency.
    """

    def __init__(self):
        self._registry_lock = threading.Lock()
        self._host_locks = {}
        self._results = {}

    def _lock_for(self, host):
        with self._registry_lock:
            lock = self._host_locks.get(host)
            if lock is None:
                lock = threading.Lock()
                self._host_locks[host] = lock
            return lock

    def is_blocked(self, session, entry_url, **checker_kwargs):
        parts = urlsplit(entry_url)
        host = parts.netloc
        scheme = parts.scheme or "https"

        if host in self._results:
            return self._results[host]

        with self._lock_for(host):
            if host in self._results:
                return self._results[host]

            root_url = f"{scheme}://{host}/"
            result = checker.check_url(session, root_url, **checker_kwargs)
            blocked = (
                result.classification == "needs_manual_check"
                and result.failure_type == DOMAIN_BLOCK_FAILURE_TYPE
            )
            self._results[host] = blocked
            return blocked

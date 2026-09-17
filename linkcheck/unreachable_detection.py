"""Detect when an entire domain refuses this checker's connections, rather
than one specific link being broken.

Some manufacturer sites (angenieux.com, confirmed in testing) are fully live
for a normal browser but refuse the CI runner's connections outright: no HTTP
status comes back at all, just a connection-level failure (DNS, connection
refused, or another connection error -- checker.py returns "network_error"
for all three). That is not a per-link defect. Routing dozens of such links
into needs-manual-check floods the actionable list with one domain's noise,
and the existing network-error streak would eventually promote them to
"dead" -- a false-dead for a domain that is actually live.

Unlike the WAF 403 case (waf_detection.py), a domain-wide connection failure
is genuinely ambiguous: from CI it looks identical whether the domain is
live-but-blocking-CI or actually dead. So it must NOT be silently
suppressed. It is grouped into its own actionable bucket and left visible
until a human records a verdict (see verdicts.py).

Detection mirrors the WAF module's proven pattern: when a link comes back
network_error, probe that domain's own root once. If the root also comes
back network_error, the whole domain is unreachable from CI and every link
on it collapses into a single domain-level entry. Because connection-level
reachability is a property of the host and not the path, "the root refuses
connections" is a faithful stand-in for "every URL on this domain refuses
connections": a host that returns a status for any path would return one for
its root too.
"""

import threading
from urllib.parse import urlsplit

from . import checker

UNREACHABLE_FAILURE_TYPE = "domain_unreachable_ci"


class DomainUnreachableCache:
    """Per-run cache so a domain with many entries (e.g. ~40 angenieux URLs)
    only has its root probed once, not once per entry on that domain.

    Uses a lock per host, held across the whole probe-and-cache section, so
    concurrent workers hitting the same never-yet-seen host block on each
    other instead of all issuing their own root probe before any of them has
    written the result -- the same race the WAF cache guards against.
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

    def is_unreachable(self, session, entry_url, **checker_kwargs):
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
            unreachable = result.classification == "network_error"
            self._results[host] = unreachable
            return unreachable

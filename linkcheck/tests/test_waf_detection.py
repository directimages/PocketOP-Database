import threading
import unittest

from linkcheck import waf_detection


class FakeResponse:
    def __init__(self, status_code, url, text=""):
        self.status_code = status_code
        self.url = url
        self.text = text


class CountingSession:
    """Always returns the same canned response, however it's asked, and
    counts how many requests it actually received."""

    def __init__(self, response):
        self._response = response
        self.head_calls = 0
        self.get_calls = 0
        self._lock = threading.Lock()

    def head(self, url, allow_redirects=True, timeout=None):
        with self._lock:
            self.head_calls += 1
        return self._response

    def get(self, url, allow_redirects=True, timeout=None):
        with self._lock:
            self.get_calls += 1
        return self._response


class DomainBlockCacheTests(unittest.TestCase):
    def test_domain_wide_403_is_blocked(self):
        session = CountingSession(FakeResponse(403, "https://canon-europe.com/"))
        cache = waf_detection.DomainBlockCache()
        blocked = cache.is_blocked(session, "https://canon-europe.com/lenses/x", max_retries=1)
        self.assertTrue(blocked)

    def test_live_domain_root_is_not_blocked(self):
        session = CountingSession(FakeResponse(200, "https://acme.example/"))
        cache = waf_detection.DomainBlockCache()
        blocked = cache.is_blocked(session, "https://acme.example/products/x", max_retries=1)
        self.assertFalse(blocked)

    def test_second_lookup_for_same_host_reuses_cache_no_extra_request(self):
        session = CountingSession(FakeResponse(403, "https://canon-europe.com/"))
        cache = waf_detection.DomainBlockCache()
        cache.is_blocked(session, "https://canon-europe.com/lenses/x", max_retries=1)
        cache.is_blocked(session, "https://canon-europe.com/lenses/y", max_retries=1)
        self.assertEqual(session.head_calls, 1)

    def test_concurrent_lookups_for_the_same_never_seen_host_probe_once(self):
        session = CountingSession(FakeResponse(403, "https://canon-europe.com/"))
        cache = waf_detection.DomainBlockCache()
        urls = [f"https://canon-europe.com/lenses/{i}" for i in range(20)]

        threads = [
            threading.Thread(target=cache.is_blocked, args=(session, url), kwargs={"max_retries": 1})
            for url in urls
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(session.head_calls, 1)

    def test_different_hosts_are_probed_independently(self):
        session = CountingSession(FakeResponse(200, "https://acme.example/"))
        cache = waf_detection.DomainBlockCache()
        cache.is_blocked(session, "https://acme.example/a", max_retries=1)
        cache.is_blocked(session, "https://beta.example/b", max_retries=1)
        self.assertEqual(session.head_calls, 2)


if __name__ == "__main__":
    unittest.main()

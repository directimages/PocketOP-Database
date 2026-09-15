import unittest
from unittest.mock import patch

import requests

from linkcheck import checker


class FakeResponse:
    def __init__(self, status_code, url, text=""):
        self.status_code = status_code
        self.url = url
        self.text = text


class ScriptedSession:
    """A fake requests.Session whose .head()/.get() play back a scripted
    list of responses/exceptions, one per call. Never touches the network."""

    def __init__(self, head_script=None, get_script=None):
        self._head_script = list(head_script or [])
        self._get_script = list(get_script or [])

    def _consume(self, script, name):
        if not script:
            raise AssertionError(f"no more scripted {name} responses")
        item = script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def head(self, url, allow_redirects=True, timeout=None):
        return self._consume(self._head_script, "head")

    def get(self, url, allow_redirects=True, timeout=None):
        return self._consume(self._get_script, "get")


URL = "https://example.com/products/lens-x"


class CheckUrlTests(unittest.TestCase):
    def setUp(self):
        # Keep retry backoff instant in tests.
        patcher = patch("linkcheck.checker.time.sleep", return_value=None)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_clean_head_is_live_and_skips_get(self):
        # No GET script provided at all: if check_url fell back to GET,
        # ScriptedSession.get() would raise AssertionError.
        session = ScriptedSession(head_script=[FakeResponse(200, URL)])
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "live")

    def test_404_is_dead_on_first_check_no_cross_run_wait(self):
        session = ScriptedSession(
            head_script=[FakeResponse(404, URL)],
            get_script=[FakeResponse(404, URL)],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "dead")
        self.assertEqual(result.failure_type, "404")

    def test_410_is_dead(self):
        session = ScriptedSession(
            head_script=[FakeResponse(410, URL)],
            get_script=[FakeResponse(410, URL)],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "dead")
        self.assertEqual(result.failure_type, "410")

    def test_persistent_connection_refused_is_network_error_not_dead(self):
        refused = requests.exceptions.ConnectionError("Connection refused")
        session = ScriptedSession(
            head_script=[refused],
            get_script=[refused, refused, refused],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "network_error")
        self.assertEqual(result.failure_type, "connection_refused")

    def test_dns_failure_is_network_error_not_dead(self):
        dns_fail = requests.exceptions.ConnectionError("Failed to resolve 'example.com'")
        session = ScriptedSession(
            head_script=[dns_fail],
            get_script=[dns_fail, dns_fail, dns_fail],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "network_error")
        self.assertEqual(result.failure_type, "dns_failure")

    def test_timeout_then_recovery_is_live(self):
        session = ScriptedSession(
            head_script=[requests.exceptions.Timeout()],
            get_script=[requests.exceptions.Timeout(), FakeResponse(200, URL)],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "live")

    def test_persistent_403_is_needs_manual_check_not_dead(self):
        session = ScriptedSession(
            head_script=[FakeResponse(403, URL)],
            get_script=[FakeResponse(403, URL), FakeResponse(403, URL), FakeResponse(403, URL)],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "needs_manual_check")
        self.assertEqual(result.failure_type, "http_403_after_retries")

    def test_redirect_to_homepage_is_needs_manual_check(self):
        home = "https://example.com/"
        session = ScriptedSession(
            head_script=[FakeResponse(200, home)],
            get_script=[FakeResponse(200, home, text="Welcome to Example")],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "needs_manual_check")
        self.assertEqual(result.failure_type, "redirected_to_homepage")

    def test_soft_404_body_is_needs_manual_check(self):
        # HEAD comes back blocked (403), forcing the GET fallback that carries a body.
        session = ScriptedSession(
            head_script=[FakeResponse(403, URL)],
            get_script=[FakeResponse(200, URL, text="Sorry, page not found on this site.")],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "needs_manual_check")
        self.assertEqual(result.failure_type, "possible_soft_404")

    def test_redirect_to_live_product_page_is_live(self):
        final = "https://example.com/products/lens-x-2026"
        session = ScriptedSession(
            head_script=[FakeResponse(200, final)],
        )
        result = checker.check_url(session, URL, max_retries=3, backoff_base=0.01)
        self.assertEqual(result.classification, "live")


class ClassifyConnectionErrorTests(unittest.TestCase):
    def test_dns_markers(self):
        self.assertEqual(
            checker.classify_connection_error(Exception("Failed to resolve 'foo.bar'")),
            "dns_failure",
        )
        self.assertEqual(
            checker.classify_connection_error(Exception("Temporary failure in name resolution")),
            "dns_failure",
        )

    def test_refused_marker(self):
        self.assertEqual(
            checker.classify_connection_error(Exception("Connection refused")),
            "connection_refused",
        )

    def test_generic_connection_error(self):
        self.assertEqual(
            checker.classify_connection_error(Exception("Connection reset by peer")),
            "connection_error",
        )


if __name__ == "__main__":
    unittest.main()

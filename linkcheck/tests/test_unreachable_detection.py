import unittest
from unittest.mock import patch

from linkcheck import checker, unreachable_detection


class DomainUnreachableCacheTests(unittest.TestCase):
    def test_root_network_error_means_domain_unreachable(self):
        def fake_check_url(session, url, **kwargs):
            # The domain root refuses the connection: no HTTP status at all.
            return checker.CheckResult("network_error", "connection_error", None, None)

        with patch.object(unreachable_detection.checker, "check_url", side_effect=fake_check_url):
            cache = unreachable_detection.DomainUnreachableCache()
            self.assertTrue(cache.is_unreachable(None, "https://www.angenieux.com/lenses/optimo-ultra-12x/"))

    def test_root_reachable_means_not_domain_unreachable(self):
        # A specific path may have network-errored, but if the root answers
        # with a status the domain is reachable -- not a domain-wide block.
        def fake_check_url(session, url, **kwargs):
            return checker.CheckResult("live", None, 200, url)

        with patch.object(unreachable_detection.checker, "check_url", side_effect=fake_check_url):
            cache = unreachable_detection.DomainUnreachableCache()
            self.assertFalse(cache.is_unreachable(None, "https://reachable.example/some/path"))

    def test_root_dead_status_is_not_treated_as_unreachable(self):
        # A 404/410 root is a real HTTP answer, not a connection-level block.
        def fake_check_url(session, url, **kwargs):
            return checker.CheckResult("dead", "404", 404, url)

        with patch.object(unreachable_detection.checker, "check_url", side_effect=fake_check_url):
            cache = unreachable_detection.DomainUnreachableCache()
            self.assertFalse(cache.is_unreachable(None, "https://dead-root.example/x"))

    def test_root_is_probed_once_per_host_regardless_of_entry_count(self):
        probes = {"n": 0}

        def counting_check_url(session, url, **kwargs):
            if url == "https://www.angenieux.com/":
                probes["n"] += 1
            return checker.CheckResult("network_error", "connection_error", None, None)

        with patch.object(unreachable_detection.checker, "check_url", side_effect=counting_check_url):
            cache = unreachable_detection.DomainUnreachableCache()
            for i in range(6):
                cache.is_unreachable(None, f"https://www.angenieux.com/lenses/item-{i}/")

        self.assertEqual(probes["n"], 1)

    def test_probes_the_scheme_and_host_root(self):
        seen = {}

        def capture_check_url(session, url, **kwargs):
            seen["url"] = url
            return checker.CheckResult("network_error", "connection_error", None, None)

        with patch.object(unreachable_detection.checker, "check_url", side_effect=capture_check_url):
            cache = unreachable_detection.DomainUnreachableCache()
            cache.is_unreachable(None, "https://www.angenieux.com/cinema/optimo")

        self.assertEqual(seen["url"], "https://www.angenieux.com/")


if __name__ == "__main__":
    unittest.main()

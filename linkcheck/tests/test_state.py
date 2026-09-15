import tempfile
import unittest
from pathlib import Path

from linkcheck import state


class ResolveNetworkErrorTests(unittest.TestCase):
    def test_first_scheduled_failure_is_needs_manual_check_not_dead(self):
        classification, record = state.resolve_network_error(
            None, "connection_refused", is_scheduled_run=True, now_iso="2026-09-16T09:00:00+00:00"
        )
        self.assertEqual(classification, "needs_manual_check")
        self.assertEqual(record["network_failure_streak"], 1)

    def test_second_consecutive_scheduled_failure_is_promoted_to_dead(self):
        first_record = {
            "last_checked": "2026-09-16T09:00:00+00:00",
            "raw_classification": "network_error",
            "reported_classification": "needs_manual_check",
            "failure_type": "connection_refused",
            "network_failure_streak": 1,
        }
        classification, record = state.resolve_network_error(
            first_record, "connection_refused", is_scheduled_run=True, now_iso="2026-09-23T09:00:00+00:00"
        )
        self.assertEqual(classification, "dead")
        self.assertEqual(record["network_failure_streak"], 2)

    def test_live_run_in_between_would_have_reset_streak(self):
        # A live result is recorded via record_clean_result, not resolve_network_error,
        # and resets the streak to 0 -- so a subsequent failure starts over at 1.
        reset_record = state.record_clean_result("live", None, "2026-09-16T09:00:00+00:00")
        self.assertEqual(reset_record["network_failure_streak"], 0)

        classification, record = state.resolve_network_error(
            reset_record, "dns_failure", is_scheduled_run=True, now_iso="2026-09-23T09:00:00+00:00"
        )
        self.assertEqual(classification, "needs_manual_check")
        self.assertEqual(record["network_failure_streak"], 1)

    def test_manual_dispatch_does_not_advance_or_reset_streak(self):
        first_record = {
            "last_checked": "2026-09-16T09:00:00+00:00",
            "raw_classification": "network_error",
            "reported_classification": "needs_manual_check",
            "failure_type": "dns_failure",
            "network_failure_streak": 1,
        }
        classification, record = state.resolve_network_error(
            first_record, "dns_failure", is_scheduled_run=False, now_iso="2026-09-17T09:00:00+00:00"
        )
        # Manual run surfaces status but a single prior scheduled failure is
        # still below the promotion threshold, and the streak must not move.
        self.assertEqual(classification, "needs_manual_check")
        self.assertEqual(record["network_failure_streak"], 1)


class RecentlyCheckedTests(unittest.TestCase):
    def test_within_window_is_recent(self):
        import datetime as dt

        now = dt.datetime(2026, 9, 16, 12, 0, 0, tzinfo=dt.timezone.utc)
        record = {"last_checked": "2026-09-16T10:00:00+00:00"}
        self.assertTrue(state.recently_checked(record, now))

    def test_outside_window_is_not_recent(self):
        import datetime as dt

        now = dt.datetime(2026, 9, 16, 12, 0, 0, tzinfo=dt.timezone.utc)
        record = {"last_checked": "2026-09-15T12:00:00+00:00"}
        self.assertFalse(state.recently_checked(record, now))

    def test_missing_record_is_not_recent(self):
        import datetime as dt

        self.assertFalse(state.recently_checked(None, dt.datetime.now(dt.timezone.utc)))


class LoadSaveStateTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            data = {"productUrl:https://example.com/x": {"last_checked": "2026-09-16T00:00:00+00:00"}}
            state.save_state(data, path)
            self.assertEqual(state.load_state(path), data)

    def test_missing_file_loads_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "does-not-exist.json"
            self.assertEqual(state.load_state(path), {})


if __name__ == "__main__":
    unittest.main()

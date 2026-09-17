import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from linkcheck import verdicts


RUN_DATE = dt.date(2026, 9, 17)


def _write(tmp, payload):
    path = Path(tmp) / "verdicts.json"
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class LoadVerdictsTests(unittest.TestCase):
    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "does-not-exist.json"
            self.assertEqual(verdicts.load_verdicts(path), {})

    def test_well_formed_verdicts_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, {"domains": {
                "www.angenieux.com": {"verdict": "live", "recheck_after": "2026-12-17"},
                "gone.example": {"verdict": "dead"},
            }})
            loaded = verdicts.load_verdicts(path)
            self.assertEqual(set(loaded), {"www.angenieux.com", "gone.example"})
            self.assertEqual(loaded["gone.example"]["verdict"], "dead")

    def test_unknown_verdict_value_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, {"domains": {
                "good.example": {"verdict": "live"},
                "typo.example": {"verdict": "liv"},
            }})
            loaded = verdicts.load_verdicts(path)
            self.assertIn("good.example", loaded)
            self.assertNotIn("typo.example", loaded)

    def test_malformed_json_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, "{ not valid json ")
            self.assertEqual(verdicts.load_verdicts(path), {})

    def test_non_object_entry_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, {"domains": {"weird.example": "live"}})
            self.assertEqual(verdicts.load_verdicts(path), {})


class ActiveVerdictTests(unittest.TestCase):
    def test_no_verdict_returns_none(self):
        self.assertIsNone(verdicts.active_verdict({}, "www.angenieux.com", RUN_DATE))

    def test_live_verdict_without_recheck_is_active(self):
        loaded = {"www.angenieux.com": {"verdict": "live"}}
        self.assertEqual(verdicts.active_verdict(loaded, "www.angenieux.com", RUN_DATE), "live")

    def test_live_verdict_before_recheck_date_is_active(self):
        loaded = {"www.angenieux.com": {"verdict": "live", "recheck_after": "2026-12-17"}}
        self.assertEqual(verdicts.active_verdict(loaded, "www.angenieux.com", RUN_DATE), "live")

    def test_verdict_on_or_after_recheck_date_is_expired(self):
        loaded = {"www.angenieux.com": {"verdict": "live", "recheck_after": "2026-09-17"}}
        # run_date == recheck_after: expired, so the domain is checked again.
        self.assertIsNone(verdicts.active_verdict(loaded, "www.angenieux.com", RUN_DATE))
        later = dt.date(2026, 12, 25)
        self.assertIsNone(verdicts.active_verdict(loaded, "www.angenieux.com", later))

    def test_dead_verdict_is_returned(self):
        loaded = {"gone.example": {"verdict": "dead"}}
        self.assertEqual(verdicts.active_verdict(loaded, "gone.example", RUN_DATE), "dead")

    def test_bad_recheck_date_is_treated_as_active_not_a_crash(self):
        loaded = {"www.angenieux.com": {"verdict": "live", "recheck_after": "not-a-date"}}
        self.assertEqual(verdicts.active_verdict(loaded, "www.angenieux.com", RUN_DATE), "live")


class HostOfTests(unittest.TestCase):
    def test_host_is_the_netloc(self):
        self.assertEqual(
            verdicts.host_of("https://www.angenieux.com/lenses/optimo-ultra-12x/"),
            "www.angenieux.com",
        )


class ShippedVerdictFileTests(unittest.TestCase):
    def test_repo_verdict_file_is_valid_and_records_angenieux_live(self):
        # The checked-in verdicts.json must parse and carry the seeded
        # angenieux verdict, since the whole feature is demonstrated against it.
        loaded = verdicts.load_verdicts(verdicts.DEFAULT_VERDICTS_PATH)
        self.assertIn("www.angenieux.com", loaded)
        self.assertEqual(loaded["www.angenieux.com"]["verdict"], "live")


if __name__ == "__main__":
    unittest.main()

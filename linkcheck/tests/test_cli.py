import datetime as dt
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from linkcheck import checker, cli

FIXTURES = {
    "broadcast_lenses.json": {"lenses": [{"id": "acme-b1", "manufacturer": "Acme", "model": "B1"}]},
    "broadcast_lens_details.json": {
        "lenses": [
            {"id": "acme-b1", "productUrl": "https://acme.example/dead", "manufacturerUrl": "https://acme.example"},
        ]
    },
    "cine_lenses.json": {"lenses": []},
    "cine_lens_details.json": {"lenses": []},
    "ptz_cameras.json": {"ptzCameras": []},
    "ptz_details.json": {"cameras": []},
}


def fake_fetch(filename):
    return FIXTURES[filename]


def fake_check_url(session, url, **kwargs):
    if url == "https://acme.example/dead":
        return checker.CheckResult("dead", "404", 404, url)
    return checker.CheckResult("live", None, 200, url)


class RunIntegrationTests(unittest.TestCase):
    def test_run_writes_report_and_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)

            with patch.object(cli.checker, "check_url", side_effect=fake_check_url), \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                report_path = cli.run(state_path=state_path, reports_dir=reports_dir, now=now, fetch=fake_fetch)

            self.assertTrue(report_path.exists())
            text = report_path.read_text(encoding="utf-8")
            self.assertIn("acme-b1", text)
            self.assertIn("full current audit", text)  # first run, empty prior state

            self.assertTrue(state_path.exists())

    def test_second_run_is_not_labelled_first_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)
            later = dt.datetime(2026, 9, 23, 9, 0, 0, tzinfo=dt.timezone.utc)

            with patch.object(cli.checker, "check_url", side_effect=fake_check_url), \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                cli.run(state_path=state_path, reports_dir=reports_dir, now=now, fetch=fake_fetch)
                second_report = cli.run(state_path=state_path, reports_dir=reports_dir, now=later, fetch=fake_fetch)

            text = second_report.read_text(encoding="utf-8")
            self.assertNotIn("full current audit", text)


if __name__ == "__main__":
    unittest.main()

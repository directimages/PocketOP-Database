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
                report_path = cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=fake_fetch,
                    github_token="", github_repo="",  # deterministic: no issue notification attempted here
                )

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
                cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=fake_fetch,
                    github_token="", github_repo="",
                )
                second_report = cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=later, fetch=fake_fetch,
                    github_token="", github_repo="",
                )

            text = second_report.read_text(encoding="utf-8")
            self.assertNotIn("full current audit", text)


class IssueNotificationWiringTests(unittest.TestCase):
    """cli.run() must call issue_reporter.post_report with the right
    actionable flag, and must never attempt it without a token/repo."""

    def _run(self, tmp, now, github_token, github_repo):
        state_path = Path(tmp) / "state.json"
        reports_dir = Path(tmp) / "reports"
        with patch.object(cli.checker, "check_url", side_effect=fake_check_url), \
             patch.object(cli.issue_reporter, "post_report") as mock_post, \
             patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
            cli.run(
                state_path=state_path, reports_dir=reports_dir, now=now, fetch=fake_fetch,
                github_token=github_token, github_repo=github_repo,
            )
        return mock_post

    def test_posts_when_actionable_and_credentials_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)
            mock_post = self._run(tmp, now, "fake-token", "directimages/PocketOP-Database")
            mock_post.assert_called_once()
            self.assertTrue(mock_post.call_args.kwargs["actionable"])

    def test_never_posts_without_a_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)
            mock_post = self._run(tmp, now, "", "directimages/PocketOP-Database")
            mock_post.assert_not_called()

    def test_never_posts_without_a_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)
            mock_post = self._run(tmp, now, "fake-token", "")
            mock_post.assert_not_called()

    def test_does_not_post_when_nothing_actionable(self):
        def all_live(session, url, **kwargs):
            return checker.CheckResult("live", None, 200, url)

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)
            with patch.object(cli.checker, "check_url", side_effect=all_live), \
                 patch.object(cli.issue_reporter, "post_report") as mock_post, \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=fake_fetch,
                    github_token="fake-token", github_repo="directimages/PocketOP-Database",
                )
            mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()

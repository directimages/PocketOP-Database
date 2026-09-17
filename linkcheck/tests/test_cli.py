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

    def test_posted_body_is_the_compact_summary_not_the_full_report(self):
        # Regression test for the real failure: posting the full report body
        # (hundreds of rows) exceeded GitHub's 65536 character limit and the
        # notification silently failed. cli.run() must build a short summary
        # plus a link, never hand the full report text to post_report.
        with tempfile.TemporaryDirectory() as tmp:
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)
            mock_post = self._run(tmp, now, "fake-token", "directimages/PocketOP-Database")
            body = mock_post.call_args.kwargs["body"]
            self.assertLess(len(body), 2000)
            self.assertNotIn("acme-b1", body)  # the entry id itself never appears in the summary
            self.assertIn("blob/main/linkcheck/reports/", body)

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


WAF_FIXTURES = {
    "broadcast_lenses.json": {
        "lenses": [
            {"id": "waf-b1", "manufacturer": "Waffle", "model": "B1"},
        ]
    },
    "broadcast_lens_details.json": {
        "lenses": [
            # Give it a real manufacturerUrl (also on the blocked domain) so this
            # fixture doesn't accidentally produce an (actionable) integrity gap
            # that would confound the "not actionable" assertion below.
            {"id": "waf-b1", "productUrl": "https://waf-blocked.example/lens-b1", "manufacturerUrl": "https://waf-blocked.example/"},
        ]
    },
    "cine_lenses.json": {"lenses": []},
    "cine_lens_details.json": {"lenses": []},
    "ptz_cameras.json": {"ptzCameras": []},
    "ptz_details.json": {"cameras": []},
}


def waf_fake_fetch(filename):
    return WAF_FIXTURES[filename]


def waf_fake_check_url(session, url, **kwargs):
    # Every path on this domain, including its own root, returns the same
    # 403-after-retries signature -- a domain-wide WAF block, not a per-link
    # problem.
    if url.startswith("https://waf-blocked.example/"):
        return checker.CheckResult("needs_manual_check", "http_403_after_retries", 403, url)
    return checker.CheckResult("live", None, 200, url)


class WafDomainBlockIntegrationTests(unittest.TestCase):
    def test_domain_wide_block_is_isolated_and_not_actionable(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)

            with patch.object(cli.checker, "check_url", side_effect=waf_fake_check_url), \
                 patch.object(cli.issue_reporter, "post_report") as mock_post, \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                report_path = cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=waf_fake_fetch,
                    github_token="fake-token", github_repo="directimages/PocketOP-Database",
                )

            text = report_path.read_text(encoding="utf-8")

            # Isolated to its own section...
            unverifiable_section = text.split("## Product link check -- Unverifiable from CI")[1]
            self.assertIn("waf-b1", unverifiable_section)

            # ...and absent from Dead and Needs manual check.
            dead_section = text.split("## Product link check -- Needs manual check")[0]
            needs_check_section = text.split("## Product link check -- Needs manual check")[1].split(
                "## Product link check -- Unverifiable from CI"
            )[0]
            self.assertNotIn("waf-b1", dead_section)
            self.assertNotIn("waf-b1", needs_check_section)

            # And it must not make the run "actionable".
            mock_post.assert_not_called()

    def test_domain_root_is_probed_once_regardless_of_entry_count(self):
        many_fixtures = dict(WAF_FIXTURES)
        many_fixtures["broadcast_lens_details.json"] = {
            "lenses": [
                {"id": f"waf-b{i}", "productUrl": f"https://waf-blocked.example/lens-{i}", "manufacturerUrl": None}
                for i in range(5)
            ]
        }
        many_fixtures["broadcast_lenses.json"] = {
            "lenses": [{"id": f"waf-b{i}", "manufacturer": "Waffle", "model": f"B{i}"} for i in range(5)]
        }

        call_count = {"n": 0}
        real_side_effect = waf_fake_check_url

        def counting_check_url(session, url, **kwargs):
            if url == "https://waf-blocked.example/":
                call_count["n"] += 1
            return real_side_effect(session, url, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)

            with patch.object(cli.checker, "check_url", side_effect=counting_check_url), \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now,
                    fetch=lambda f: many_fixtures[f],
                    github_token="", github_repo="",
                )

        self.assertEqual(call_count["n"], 1)


CRASH_FIXTURES = {
    "broadcast_lenses.json": {
        "lenses": [
            {"id": "crash-b1", "manufacturer": "Boom", "model": "B1"},
            {"id": "fine-b2", "manufacturer": "Fine", "model": "B2"},
        ]
    },
    "broadcast_lens_details.json": {
        "lenses": [
            {"id": "crash-b1", "productUrl": "https://boom.example/x", "manufacturerUrl": None},
            {"id": "fine-b2", "productUrl": "https://fine.example/y", "manufacturerUrl": None},
        ]
    },
    "cine_lenses.json": {"lenses": []},
    "cine_lens_details.json": {"lenses": []},
    "ptz_cameras.json": {"ptzCameras": []},
    "ptz_details.json": {"cameras": []},
}


def crash_fake_fetch(filename):
    return CRASH_FIXTURES[filename]


def crash_fake_check_url(session, url, **kwargs):
    if url == "https://boom.example/x":
        # Something this checker never anticipated (not a requests
        # exception at all) -- the run must survive this regardless.
        raise ValueError("totally unforeseen failure")
    return checker.CheckResult("live", None, 200, url)


class UnexpectedErrorResilienceTests(unittest.TestCase):
    def test_one_bad_link_does_not_crash_the_whole_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)

            with patch.object(cli.checker, "check_url", side_effect=crash_fake_check_url), \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                report_path = cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=crash_fake_fetch,
                    github_token="", github_repo="",
                )

            self.assertTrue(report_path.exists())
            text = report_path.read_text(encoding="utf-8")

            needs_check_section = text.split("## Product link check -- Unverifiable from CI")[0]
            self.assertIn("crash-b1", needs_check_section)
            self.assertIn("unexpected_error_ValueError", text)

            # The other, unrelated entry is live, so it should not appear in
            # any of the Dead/Needs-manual/Unverifiable sections (both entries
            # legitimately show up further down, in the manufacturer
            # integrity gaps section -- neither fixture has a manufacturerUrl).
            flagged_sections = text.split("## Product coverage gaps")[0]
            self.assertNotIn("fine-b2", flagged_sections)

            self.assertTrue(state_path.exists())



# --- Domain-wide-CI-unreachable + verdict layer -----------------------------

# The real angenieux URL set (a known public sample, not production secrets):
# every path on this host, including the root, refuses CI connections with no
# HTTP status. 19 productUrl entries + 24 manufacturerUrl entries = the ~43
# rows this feature has to collapse and, once verified live, silence.
ANGENIEUX_PRODUCT_URLS = [
    "https://www.angenieux.com/cinema/optimo",
    "https://www.angenieux.com/cinema/optimo-style",
    "https://www.angenieux.com/cinema-lenses/optimo-dp/",
    "https://www.angenieux.com/lenses/optimo-ultra-12x/",
    "https://www.angenieux.com/lenses/optimo-ultra-compact/",
    "https://www.angenieux.com/lenses/type-ez-series/",
    "https://www.angenieux.com/lenses/legacy-series/optimo-style-48-130/",
    "https://www.angenieux.com/lenses/legacy-series/compact-lens-zoom-optimo-style-16-40/",
    "https://www.angenieux.com/lenses/legacy-series/compact-lens-zoom-optimo-style-30-76/",
]
ANGENIEUX_MFR_URL = "https://www.angenieux.com/lenses/"


def build_angenieux_fixtures():
    core, details = [], []
    for i in range(19):  # 19 productUrl + 19 manufacturerUrl entries
        eid = f"angenieux-{i}"
        core.append({"id": eid, "manufacturer": "Angenieux", "model": f"Optimo {i}"})
        details.append({
            "id": eid,
            "productUrl": ANGENIEUX_PRODUCT_URLS[i % len(ANGENIEUX_PRODUCT_URLS)],
            "manufacturerUrl": ANGENIEUX_MFR_URL,
        })
    for i in range(19, 24):  # +5 manufacturerUrl-only entries -> 24 manufacturer total
        eid = f"angenieux-{i}"
        core.append({"id": eid, "manufacturer": "Angenieux", "model": f"Optimo {i}"})
        details.append({"id": eid, "productUrl": None, "manufacturerUrl": ANGENIEUX_MFR_URL})
    return {
        "broadcast_lenses.json": {"lenses": core},
        "broadcast_lens_details.json": {"lenses": details},
        "cine_lenses.json": {"lenses": []},
        "cine_lens_details.json": {"lenses": []},
        "ptz_cameras.json": {"ptzCameras": []},
        "ptz_details.json": {"cameras": []},
    }


def angenieux_fetch(filename):
    return build_angenieux_fixtures()[filename]


def angenieux_unreachable_check_url(session, url, **kwargs):
    # Every angenieux URL, including the root the domain probe hits, refuses
    # the connection with no HTTP status.
    if url.startswith("https://www.angenieux.com/"):
        return checker.CheckResult("network_error", "connection_error", None, None)
    return checker.CheckResult("live", None, 200, url)


def _write_verdicts(tmp, domains):
    import json
    path = Path(tmp) / "verdicts.json"
    path.write_text(json.dumps({"domains": domains}), encoding="utf-8")
    return path


class UnreachableDomainIntegrationTests(unittest.TestCase):
    def test_unverified_domain_collapses_to_one_actionable_row_not_promoted_to_dead(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            no_verdicts = Path(tmp) / "verdicts-absent.json"  # missing on purpose
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)

            with patch.object(cli.checker, "check_url", side_effect=angenieux_unreachable_check_url), \
                 patch.object(cli.issue_reporter, "post_report") as mock_post, \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                report_path = cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=angenieux_fetch,
                    github_token="fake-token", github_repo="directimages/PocketOP-Database",
                    verdicts_path=no_verdicts,
                )

            text = report_path.read_text(encoding="utf-8")

            # One grouped domain row (19 product + 24 manufacturer), not 43 per-id rows.
            unreachable_section = text.split("## Domains unreachable from CI")[1].split("## Manually verified live")[0]
            self.assertIn("| www.angenieux.com | 19 | 24 | domain_unreachable_ci |", unreachable_section)
            self.assertEqual(unreachable_section.count("www.angenieux.com"), 1)

            # Never in Dead, and never flooding Needs manual check.
            self.assertNotIn("| angenieux-", text.split("## Domains unreachable from CI")[0])

            # Ambiguous but visible: it must make the run actionable.
            mock_post.assert_called_once()
            self.assertTrue(mock_post.call_args.kwargs["actionable"])

            # State recorded as unreachable_domain, streak reset -> never a false-dead.
            import json
            saved = json.loads(state_path.read_text(encoding="utf-8"))
            rec = saved["manufacturerUrl:https://www.angenieux.com/lenses/"]
            self.assertEqual(rec["reported_classification"], "unreachable_domain")
            self.assertEqual(rec["network_failure_streak"], 0)

    def test_live_verdict_silences_all_rows_and_skips_the_http_checks(self):
        # The headline done-criterion: recording angenieux as live empties the
        # 43-row needs-manual list on the next run.
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            verdicts_path = _write_verdicts(tmp, {
                "www.angenieux.com": {"verdict": "live", "recheck_after": "2026-12-17"}
            })
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)

            with patch.object(cli.checker, "check_url", side_effect=angenieux_unreachable_check_url) as mock_check, \
                 patch.object(cli.issue_reporter, "post_report") as mock_post, \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                report_path = cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=angenieux_fetch,
                    github_token="fake-token", github_repo="directimages/PocketOP-Database",
                    verdicts_path=verdicts_path,
                )

            text = report_path.read_text(encoding="utf-8")

            # Quiet verified-live line, one row per domain.
            live_section = text.split("## Manually verified live (blocking CI)")[1].split("## Manually verified dead")[0]
            self.assertIn("| www.angenieux.com | 19 | 24 | manually_verified_live |", live_section)

            # Unreachable and needs-manual are empty of angenieux.
            unreachable_section = text.split("## Domains unreachable from CI")[1].split("## Manually verified live")[0]
            self.assertIn("No domain-wide CI-unreachable domains this run.", unreachable_section)
            needs_check_product = text.split("## Product link check -- Needs manual check")[1].split(
                "## Product link check -- Unverifiable from CI")[0]
            self.assertIn("Nothing ambiguous this run.", needs_check_product)

            # Not actionable: no notification.
            mock_post.assert_not_called()
            # Live-but-blocking-CI can't be checked from here anyway: the HTTP
            # checks are short-circuited entirely.
            mock_check.assert_not_called()

    def test_dead_verdict_is_a_quiet_replacement_worklist(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            verdicts_path = _write_verdicts(tmp, {"www.angenieux.com": {"verdict": "dead"}})
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)

            with patch.object(cli.checker, "check_url", side_effect=angenieux_unreachable_check_url) as mock_check, \
                 patch.object(cli.issue_reporter, "post_report") as mock_post, \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                report_path = cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=angenieux_fetch,
                    github_token="fake-token", github_repo="directimages/PocketOP-Database",
                    verdicts_path=verdicts_path,
                )

            text = report_path.read_text(encoding="utf-8")
            dead_section = text.split("## Manually verified dead -- replacement owed")[1].split(
                "## Product coverage gaps")[0]
            self.assertIn("| www.angenieux.com | 19 | 24 | manually_verified_dead |", dead_section)

            mock_post.assert_not_called()  # operator already knows; worklist, not a notification
            mock_check.assert_not_called()

    def test_expired_live_verdict_re_surfaces_the_domain_as_actionable(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            reports_dir = Path(tmp) / "reports"
            verdicts_path = _write_verdicts(tmp, {
                "www.angenieux.com": {"verdict": "live", "recheck_after": "2026-01-01"}
            })
            now = dt.datetime(2026, 9, 16, 9, 0, 0, tzinfo=dt.timezone.utc)  # well past recheck_after

            with patch.object(cli.checker, "check_url", side_effect=angenieux_unreachable_check_url), \
                 patch.object(cli.issue_reporter, "post_report") as mock_post, \
                 patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}):
                report_path = cli.run(
                    state_path=state_path, reports_dir=reports_dir, now=now, fetch=angenieux_fetch,
                    github_token="fake-token", github_repo="directimages/PocketOP-Database",
                    verdicts_path=verdicts_path,
                )

            text = report_path.read_text(encoding="utf-8")
            unreachable_section = text.split("## Domains unreachable from CI")[1].split("## Manually verified live")[0]
            self.assertIn("www.angenieux.com", unreachable_section)
            live_section = text.split("## Manually verified live (blocking CI)")[1].split("## Manually verified dead")[0]
            self.assertIn("No manually-verified-live domains.", live_section)
            mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()

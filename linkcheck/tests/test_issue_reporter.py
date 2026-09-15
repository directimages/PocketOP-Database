import unittest

from linkcheck import issue_reporter


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


class FakeGithubSession:
    """Records every call it receives and plays back scripted GET responses."""

    def __init__(self, get_responses=None):
        self.calls = []
        self._get_responses = list(get_responses or [])

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append(("GET", url, params))
        return self._get_responses.pop(0)

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        if url.endswith("/comments"):
            return FakeResponse({"id": 1, "body": json["body"]})
        return FakeResponse({"number": 99, "body": json["body"]})

    def patch(self, url, headers=None, json=None, timeout=None):
        self.calls.append(("PATCH", url, json))
        return FakeResponse({"ok": True})


class IsActionableTests(unittest.TestCase):
    def test_all_empty_is_not_actionable(self):
        self.assertFalse(issue_reporter.is_actionable(
            product_dead=[], product_needs_check=[], manufacturer_dead=[],
            manufacturer_needs_check=[], manufacturer_gaps=[],
        ))

    def test_any_dead_is_actionable(self):
        self.assertTrue(issue_reporter.is_actionable(
            product_dead=[{"id": "a"}], product_needs_check=[], manufacturer_dead=[],
            manufacturer_needs_check=[], manufacturer_gaps=[],
        ))

    def test_manufacturer_integrity_gap_is_actionable(self):
        self.assertTrue(issue_reporter.is_actionable(
            product_dead=[], product_needs_check=[], manufacturer_dead=[],
            manufacturer_needs_check=[], manufacturer_gaps=[{"id": "a"}],
        ))


class PostReportTests(unittest.TestCase):
    REPO = "directimages/PocketOP-Database"
    TOKEN = "fake-token"

    def test_not_actionable_makes_no_calls_at_all(self):
        session = FakeGithubSession()
        result = issue_reporter.post_report(
            session=session, repo=self.REPO, token=self.TOKEN,
            body="nothing to see", actionable=False,
        )
        self.assertIsNone(result)
        self.assertEqual(session.calls, [])

    def test_creates_issue_when_none_exists(self):
        session = FakeGithubSession(get_responses=[FakeResponse([])])
        issue_reporter.post_report(
            session=session, repo=self.REPO, token=self.TOKEN,
            body="report body", actionable=True,
        )
        methods = [c[0] for c in session.calls]
        self.assertEqual(methods, ["GET", "POST"])
        create_call = session.calls[1]
        self.assertTrue(create_call[1].endswith("/issues"))
        self.assertEqual(create_call[2]["labels"], [issue_reporter.ISSUE_LABEL])
        self.assertIn("report body", create_call[2]["body"])

    def test_comments_on_existing_open_issue_without_reopening(self):
        existing = {"number": 42, "state": "open"}
        session = FakeGithubSession(get_responses=[FakeResponse([existing])])
        issue_reporter.post_report(
            session=session, repo=self.REPO, token=self.TOKEN,
            body="report body", actionable=True,
        )
        methods = [c[0] for c in session.calls]
        self.assertEqual(methods, ["GET", "POST"])
        comment_call = session.calls[1]
        self.assertTrue(comment_call[1].endswith("/issues/42/comments"))

    def test_reopens_closed_issue_before_commenting(self):
        existing = {"number": 42, "state": "closed"}
        session = FakeGithubSession(get_responses=[FakeResponse([existing])])
        issue_reporter.post_report(
            session=session, repo=self.REPO, token=self.TOKEN,
            body="report body", actionable=True,
        )
        methods = [c[0] for c in session.calls]
        self.assertEqual(methods, ["GET", "PATCH", "POST"])
        self.assertEqual(session.calls[1][2], {"state": "open"})

    def test_body_over_the_github_limit_is_clamped(self):
        # This is a defensive last resort, not the primary fix (that's
        # report.render_issue_summary staying counts-only) -- but it must
        # never again silently fail a real post the way the first full-audit
        # run did with a ~69600 character body against GitHub's 65536 cap.
        session = FakeGithubSession(get_responses=[FakeResponse([])])
        oversized = "x" * (issue_reporter.MAX_BODY_LENGTH + 10000)
        issue_reporter.post_report(
            session=session, repo=self.REPO, token=self.TOKEN,
            body=oversized, actionable=True,
        )
        posted_body = session.calls[1][2]["body"]
        self.assertLessEqual(len(posted_body), issue_reporter.MAX_BODY_LENGTH + 100)
        self.assertIn("truncated", posted_body)

    def test_body_under_the_limit_is_posted_unchanged(self):
        session = FakeGithubSession(get_responses=[FakeResponse([])])
        issue_reporter.post_report(
            session=session, repo=self.REPO, token=self.TOKEN,
            body="a short summary", actionable=True,
        )
        self.assertEqual(session.calls[1][2]["body"], "a short summary")

    def test_pull_requests_in_the_label_search_are_ignored(self):
        pr_item = {"number": 7, "state": "open", "pull_request": {"url": "..."}}
        session = FakeGithubSession(get_responses=[FakeResponse([pr_item])])
        issue_reporter.post_report(
            session=session, repo=self.REPO, token=self.TOKEN,
            body="report body", actionable=True,
        )
        # No real issue found among results -> falls back to creating one.
        methods = [c[0] for c in session.calls]
        self.assertEqual(methods, ["GET", "POST"])
        self.assertTrue(session.calls[1][1].endswith("/issues"))


if __name__ == "__main__":
    unittest.main()

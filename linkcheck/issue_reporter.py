"""Post the triage report to a rolling GitHub Issue, so GitHub's own
notification email reaches the repo owner. No SMTP, no extra secrets beyond
the GITHUB_TOKEN Actions already provides, no email address anywhere in
this repo.

Design: one rolling issue, labelled ISSUE_LABEL. A run with anything
actionable (a dead link, a needs-manual-check entry on either field, or a
manufacturer integrity gap) adds a comment to that issue -- a comment
triggers GitHub's notification email the same way opening a new issue
does. A run with nothing actionable stays quiet: no issue interaction, no
comment, no email, no inbox noise. If the rolling issue exists but was
closed (the owner triaged and closed it), it is reopened before the new
comment lands, so the whole history stays in one thread. If no such issue
exists yet, one is created instead.

The productUrl coverage gap list is deliberately NOT part of the
actionable check: it is a slow-moving worklist, expected to have entries
most weeks, not something worth a notification every run.
"""

API_BASE = "https://api.github.com"
ISSUE_LABEL = "link-check"
ISSUE_TITLE = "Product/manufacturer link check"


def is_actionable(*, product_dead, product_needs_check, manufacturer_dead,
                   manufacturer_needs_check, manufacturer_gaps):
    return bool(
        product_dead or product_needs_check or manufacturer_dead
        or manufacturer_needs_check or manufacturer_gaps
    )


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _find_existing_issue(session, repo, token):
    resp = session.get(
        f"{API_BASE}/repos/{repo}/issues",
        headers=_headers(token),
        params={"labels": ISSUE_LABEL, "state": "all", "per_page": 5, "sort": "created", "direction": "desc"},
        timeout=15,
    )
    resp.raise_for_status()
    issues = [i for i in resp.json() if "pull_request" not in i]
    return issues[0] if issues else None


def _reopen_if_closed(session, repo, token, issue):
    if issue.get("state") == "closed":
        resp = session.patch(
            f"{API_BASE}/repos/{repo}/issues/{issue['number']}",
            headers=_headers(token),
            json={"state": "open"},
            timeout=15,
        )
        resp.raise_for_status()


def _create_issue(session, repo, token, body):
    resp = session.post(
        f"{API_BASE}/repos/{repo}/issues",
        headers=_headers(token),
        json={"title": ISSUE_TITLE, "body": body, "labels": [ISSUE_LABEL]},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _add_comment(session, repo, token, issue_number, body):
    resp = session.post(
        f"{API_BASE}/repos/{repo}/issues/{issue_number}/comments",
        headers=_headers(token),
        json={"body": body},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def post_report(*, session, repo, token, report_body, run_date, actionable):
    """Post this run's report to the rolling issue, only if actionable.

    Returns the created issue or comment payload, or None if nothing was
    posted (nothing actionable this run).
    """
    if not actionable:
        return None

    post_body = f"## Run {run_date}\n\n{report_body}"
    existing = _find_existing_issue(session, repo, token)
    if existing is None:
        return _create_issue(session, repo, token, post_body)

    _reopen_if_closed(session, repo, token, existing)
    return _add_comment(session, repo, token, existing["number"], post_body)

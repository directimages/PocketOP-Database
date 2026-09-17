"""Render the weekly link-check markdown report.

Eight sections, each with a distinct downstream meaning:

- Product link check: Dead / Needs manual check -- fix candidates.
- Manufacturer link check: Dead / Needs manual check -- fix candidates.
  Kept separate from the product sections: the two fields have different
  fix paths, so they are never merged into one table.
- Product / Manufacturer link check -- Unverifiable from CI: links whose
  whole domain 403s this checker's requests (a WAF blocking datacenter
  traffic, not a per-link defect -- see waf_detection.py). Not dead, not
  needs-manual-check, and never counted toward the actionable/notification
  trigger; otherwise a single blocked domain (~40 Canon entries in
  practice) would dominate needs-manual-check and make almost every run
  "actionable" on WAF noise alone.
- Product coverage gaps: entries with no productUrl at all. Not a defect --
  a null productUrl can be legitimate when the manufacturer never had a
  dedicated product page. Framed as a worklist, not broken links.
- Manufacturer integrity gaps: entries with no manufacturerUrl at all. By
  the database's own data rules manufacturerUrl should always be present,
  so this list is expected to be near-empty; anything here is a real gap.

render_issue_summary() below renders a separate, much shorter counts-only
summary for the GitHub Issue notification -- see its own docstring.
"""

ROW_HEADER = "| id | model / display name | category | url | failure type |\n|---|---|---|---|---|\n"
GAP_ROW_HEADER = "| id | model / display name | category |\n|---|---|---|\n"
DOMAIN_ROW_HEADER = "| domain | productUrl entries | manufacturerUrl entries | failure type |\n|---|---|---|---|\n"


def _row(item):
    return f"| {item['id']} | {item['name']} | {item['category']} | {item['url']} | {item['failure_type']} |\n"


def _gap_row(item):
    return f"| {item['id']} | {item['name']} | {item['category']} |\n"


def _domain_row(item):
    return f"| {item['domain']} | {item['productUrl']} | {item['manufacturerUrl']} | {item['failure_type']} |\n"


def _table(items, row_fn, header, empty_note):
    if not items:
        return f"{empty_note}\n\n"
    return header + "".join(row_fn(i) for i in items) + "\n"


def render_report(*, run_date, is_first_run, product_dead, product_needs_check, product_unverifiable,
                   product_gaps, manufacturer_dead, manufacturer_needs_check, manufacturer_unverifiable,
                   manufacturer_gaps, unreachable_domains=(), verified_live_domains=(),
                   verified_dead_domains=()):
    lines = [f"# Product/manufacturer link check -- {run_date}\n\n"]

    if is_first_run:
        lines.append(
            "First run: this report is the full current audit of the published database, "
            "not an incremental delta.\n\n"
        )

    lines.append("## Product link check -- Dead\n\n")
    lines.append(_table(product_dead, _row, ROW_HEADER, "No confirmed dead productUrl links."))

    lines.append("## Product link check -- Needs manual check\n\n")
    lines.append(_table(
        product_needs_check, _row, ROW_HEADER,
        "Nothing ambiguous this run.",
    ))

    lines.append(
        "## Product link check -- Unverifiable from CI\n\n"
        "The whole domain returned 403 to this checker, including its own root -- a WAF "
        "blocking datacenter traffic, not a defect in this specific link. Not dead, not "
        "needs-manual-check, and does not trigger a notification.\n\n"
    )
    lines.append(_table(product_unverifiable, _row, ROW_HEADER, "No domain-wide CI blocks this run."))

    lines.append("## Manufacturer link check -- Dead\n\n")
    lines.append(_table(manufacturer_dead, _row, ROW_HEADER, "No confirmed dead manufacturerUrl links."))

    lines.append("## Manufacturer link check -- Needs manual check\n\n")
    lines.append(_table(
        manufacturer_needs_check, _row, ROW_HEADER,
        "Nothing ambiguous this run.",
    ))

    lines.append(
        "## Manufacturer link check -- Unverifiable from CI\n\n"
        "The whole domain returned 403 to this checker, including its own root -- a WAF "
        "blocking datacenter traffic, not a defect in this specific link. Not dead, not "
        "needs-manual-check, and does not trigger a notification.\n\n"
    )
    lines.append(_table(manufacturer_unverifiable, _row, ROW_HEADER, "No domain-wide CI blocks this run."))

    lines.append(
        "## Domains unreachable from CI -- browser check needed\n\n"
        "Every checked URL on these domains, including the domain root, refused this "
        "checker's connection with no HTTP status at all. From CI that is ambiguous: a "
        "domain that is live but blocks datacenter traffic looks identical to one that is "
        "actually dead (DNS gone, host down). One manual browser check settles it -- is the "
        "domain live-but-blocking-CI, or actually dead? Record the verdict in "
        "linkcheck/verdicts.json (keyed by the domain shown here). Collapsed to one row per "
        "domain; these stay actionable until a verdict is recorded, so a genuinely dead "
        "domain is never hidden.\n\n"
    )
    lines.append(_table(unreachable_domains, _domain_row, DOMAIN_ROW_HEADER,
                        "No domain-wide CI-unreachable domains this run."))

    lines.append(
        "## Manually verified live (blocking CI)\n\n"
        "A person confirmed in a browser that these domains are live and merely block this "
        "checker's traffic, recorded in linkcheck/verdicts.json. Quiet: no notification. "
        "Each re-surfaces automatically once past its recheck_after date, so a live verdict "
        "is never blindly permanent.\n\n"
    )
    lines.append(_table(verified_live_domains, _domain_row, DOMAIN_ROW_HEADER,
                        "No manually-verified-live domains."))

    lines.append(
        "## Manually verified dead -- replacement owed\n\n"
        "A person confirmed these domains are dead, recorded in linkcheck/verdicts.json. "
        "Listed as a replacement-link worklist. Not counted toward the notification "
        "trigger; the operator already knows.\n\n"
    )
    lines.append(_table(verified_dead_domains, _domain_row, DOMAIN_ROW_HEADER,
                        "No manually-verified-dead domains."))

    lines.append(
        "## Product coverage gaps\n\n"
        "Entries with no productUrl at all. Not broken links -- a null productUrl can be "
        "legitimate when the manufacturer has no dedicated product page. Gaps to work "
        "through over time, not defects.\n\n"
    )
    lines.append(_table(product_gaps, _gap_row, GAP_ROW_HEADER, "No coverage gaps."))

    lines.append(
        "## Manufacturer integrity gaps\n\n"
        "Entries with no manufacturerUrl at all. By the database's data rules this field "
        "should always be present, so this list is expected to be near-empty; anything "
        "listed here is a real data gap worth surfacing.\n\n"
    )
    lines.append(_table(manufacturer_gaps, _gap_row, GAP_ROW_HEADER, "No integrity gaps."))

    return "".join(lines)


def render_issue_summary(*, run_date, is_first_run, product_dead, product_needs_check,
                          manufacturer_dead, manufacturer_needs_check, manufacturer_gaps, report_link,
                          unreachable_domains=()):
    """A short, size-bounded summary for the GitHub Issue notification.

    GitHub caps an issue/comment body at 65536 characters; a full audit
    with hundreds of rows exceeded that easily (a ~69600 character report
    on the first real run). The issue is only the notification trigger --
    the committed report file is the actual triage surface (see
    issue_reporter.py) -- so the issue only ever needs counts and a link to
    it, never row-level detail. This stays well under the limit regardless
    of how large the database grows.
    """
    lines = [f"## Run {run_date}\n\n"]

    if is_first_run:
        lines.append(
            "First run: the linked report is the full current audit of the published "
            "database, not an incremental delta.\n\n"
        )

    lines.append("| Section | Count |\n|---|---|\n")
    lines.append(f"| Product link check -- Dead | {len(product_dead)} |\n")
    lines.append(f"| Product link check -- Needs manual check | {len(product_needs_check)} |\n")
    lines.append(f"| Manufacturer link check -- Dead | {len(manufacturer_dead)} |\n")
    lines.append(f"| Manufacturer link check -- Needs manual check | {len(manufacturer_needs_check)} |\n")
    lines.append(f"| Domains unreachable from CI (browser check needed) | {len(unreachable_domains)} |\n")
    lines.append(f"| Manufacturer integrity gaps | {len(manufacturer_gaps)} |\n\n")

    lines.append(
        f"Full report, including row-level detail and the unverifiable-from-CI and "
        f"coverage-gap sections: {report_link}\n"
    )

    return "".join(lines)

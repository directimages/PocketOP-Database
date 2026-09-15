"""Render the weekly link-check markdown report.

Six sections, each with a distinct downstream meaning:

- Product link check: Dead / Needs manual check -- fix candidates.
- Manufacturer link check: Dead / Needs manual check -- fix candidates.
  Kept separate from the product sections: the two fields have different
  fix paths, so they are never merged into one table.
- Product coverage gaps: entries with no productUrl at all. Not a defect --
  a null productUrl can be legitimate when the manufacturer never had a
  dedicated product page. Framed as a worklist, not broken links.
- Manufacturer integrity gaps: entries with no manufacturerUrl at all. By
  the database's own data rules manufacturerUrl should always be present,
  so this list is expected to be near-empty; anything here is a real gap.
"""

ROW_HEADER = "| id | model / display name | category | url | failure type |\n|---|---|---|---|---|\n"
GAP_ROW_HEADER = "| id | model / display name | category |\n|---|---|---|\n"


def _row(item):
    return f"| {item['id']} | {item['name']} | {item['category']} | {item['url']} | {item['failure_type']} |\n"


def _gap_row(item):
    return f"| {item['id']} | {item['name']} | {item['category']} |\n"


def _table(items, row_fn, header, empty_note):
    if not items:
        return f"{empty_note}\n\n"
    return header + "".join(row_fn(i) for i in items) + "\n"


def render_report(*, run_date, is_first_run, product_dead, product_needs_check, product_gaps,
                   manufacturer_dead, manufacturer_needs_check, manufacturer_gaps):
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

    lines.append("## Manufacturer link check -- Dead\n\n")
    lines.append(_table(manufacturer_dead, _row, ROW_HEADER, "No confirmed dead manufacturerUrl links."))

    lines.append("## Manufacturer link check -- Needs manual check\n\n")
    lines.append(_table(
        manufacturer_needs_check, _row, ROW_HEADER,
        "Nothing ambiguous this run.",
    ))

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

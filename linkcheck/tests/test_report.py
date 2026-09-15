import unittest

from linkcheck import report


class RenderReportTests(unittest.TestCase):
    def test_sections_are_present_and_distinct(self):
        text = report.render_report(
            run_date="2026-09-16",
            is_first_run=True,
            product_dead=[{"id": "a1", "name": "Acme A1", "category": "broadcast", "url": "https://a.example/1", "failure_type": "404"}],
            product_needs_check=[],
            product_unverifiable=[],
            product_gaps=[{"id": "b1", "name": "Beta B1", "category": "cine"}],
            manufacturer_dead=[],
            manufacturer_needs_check=[{"id": "c1", "name": "Ceta C1", "category": "ptz", "url": "https://c.example", "failure_type": "http_403_after_retries"}],
            manufacturer_unverifiable=[],
            manufacturer_gaps=[{"id": "d1", "name": "Delta D1", "category": "broadcast"}],
        )

        self.assertIn("Product link check -- Dead", text)
        self.assertIn("Manufacturer link check -- Dead", text)
        self.assertIn("Product link check -- Unverifiable from CI", text)
        self.assertIn("Manufacturer link check -- Unverifiable from CI", text)
        self.assertIn("Product coverage gaps", text)
        self.assertIn("Manufacturer integrity gaps", text)
        self.assertIn("full current audit", text)

        # productUrl and manufacturerUrl rows never share a table.
        product_section = text.split("## Manufacturer link check -- Dead")[0]
        self.assertIn("a1", product_section)
        self.assertNotIn("c1", product_section)

    def test_unverifiable_domain_links_are_isolated_from_needs_manual_check(self):
        text = report.render_report(
            run_date="2026-09-16",
            is_first_run=False,
            product_dead=[],
            product_needs_check=[{"id": "real-403", "name": "Real 403", "category": "cine", "url": "https://acme.example/x", "failure_type": "http_403_after_retries"}],
            product_unverifiable=[{"id": "canon-x", "name": "Canon X", "category": "broadcast", "url": "https://canon-europe.com/x", "failure_type": "waf_blocked_domain_wide"}],
            product_gaps=[],
            manufacturer_dead=[],
            manufacturer_needs_check=[],
            manufacturer_unverifiable=[],
            manufacturer_gaps=[],
        )
        needs_check_section = text.split("## Product link check -- Unverifiable from CI")[0]
        unverifiable_section = text.split("## Product link check -- Unverifiable from CI")[1].split("## Manufacturer")[0]

        self.assertIn("real-403", needs_check_section)
        self.assertNotIn("canon-x", needs_check_section)
        self.assertIn("canon-x", unverifiable_section)
        self.assertNotIn("real-403", unverifiable_section)

    def test_empty_sections_get_a_clear_note_not_an_empty_table(self):
        text = report.render_report(
            run_date="2026-09-16",
            is_first_run=False,
            product_dead=[],
            product_needs_check=[],
            product_unverifiable=[],
            product_gaps=[],
            manufacturer_dead=[],
            manufacturer_needs_check=[],
            manufacturer_unverifiable=[],
            manufacturer_gaps=[],
        )
        self.assertIn("No confirmed dead productUrl links.", text)
        self.assertIn("No confirmed dead manufacturerUrl links.", text)
        self.assertIn("No domain-wide CI blocks this run.", text)
        self.assertIn("No coverage gaps.", text)
        self.assertIn("No integrity gaps.", text)
        self.assertNotIn("full current audit", text)

    def test_gap_rows_have_no_url_column(self):
        text = report.render_report(
            run_date="2026-09-16",
            is_first_run=False,
            product_dead=[],
            product_needs_check=[],
            product_unverifiable=[],
            product_gaps=[{"id": "b1", "name": "Beta B1", "category": "cine"}],
            manufacturer_dead=[],
            manufacturer_needs_check=[],
            manufacturer_unverifiable=[],
            manufacturer_gaps=[],
        )
        gap_section = text.split("## Product coverage gaps")[1]
        self.assertIn("| id | model / display name | category |", gap_section)


class RenderIssueSummaryTests(unittest.TestCase):
    def test_counts_and_link_present_no_row_level_detail(self):
        text = report.render_issue_summary(
            run_date="2026-09-16",
            is_first_run=True,
            product_dead=[{"id": "a1"}, {"id": "a2"}],
            product_needs_check=[{"id": "b1"}],
            manufacturer_dead=[],
            manufacturer_needs_check=[],
            manufacturer_gaps=[],
            report_link="[linkcheck/reports/2026-W38.md](https://github.com/x/y/blob/main/linkcheck/reports/2026-W38.md)",
        )
        self.assertIn("| Product link check -- Dead | 2 |", text)
        self.assertIn("| Product link check -- Needs manual check | 1 |", text)
        self.assertIn("| Manufacturer link check -- Dead | 0 |", text)
        self.assertIn("linkcheck/reports/2026-W38.md", text)
        self.assertIn("full current audit", text)
        # Counts only -- no per-entry rows leak into the summary.
        self.assertNotIn("a1", text)
        self.assertNotIn("b1", text)

    def test_stays_small_regardless_of_how_many_entries_are_summarized(self):
        # This is the actual fix for the real failure: a full-audit report
        # with hundreds of rows exceeded GitHub's 65536 character issue/
        # comment limit. The issue summary must never scale with row count.
        many_dead = [{"id": f"item-{i}"} for i in range(2000)]
        text = report.render_issue_summary(
            run_date="2026-09-16",
            is_first_run=True,
            product_dead=many_dead,
            product_needs_check=many_dead,
            manufacturer_dead=many_dead,
            manufacturer_needs_check=many_dead,
            manufacturer_gaps=many_dead,
            report_link="linkcheck/reports/2026-W38.md",
        )
        self.assertLess(len(text), 2000)
        self.assertIn("| Product link check -- Dead | 2000 |", text)


if __name__ == "__main__":
    unittest.main()

import unittest

from linkcheck import report


class RenderReportTests(unittest.TestCase):
    def test_sections_are_present_and_distinct(self):
        text = report.render_report(
            run_date="2026-09-16",
            is_first_run=True,
            product_dead=[{"id": "a1", "name": "Acme A1", "category": "broadcast", "url": "https://a.example/1", "failure_type": "404"}],
            product_needs_check=[],
            product_gaps=[{"id": "b1", "name": "Beta B1", "category": "cine"}],
            manufacturer_dead=[],
            manufacturer_needs_check=[{"id": "c1", "name": "Ceta C1", "category": "ptz", "url": "https://c.example", "failure_type": "http_403_after_retries"}],
            manufacturer_gaps=[{"id": "d1", "name": "Delta D1", "category": "broadcast"}],
        )

        self.assertIn("Product link check -- Dead", text)
        self.assertIn("Manufacturer link check -- Dead", text)
        self.assertIn("Product coverage gaps", text)
        self.assertIn("Manufacturer integrity gaps", text)
        self.assertIn("full current audit", text)

        # productUrl and manufacturerUrl rows never share a table.
        product_section = text.split("## Manufacturer link check -- Dead")[0]
        self.assertIn("a1", product_section)
        self.assertNotIn("c1", product_section)

    def test_empty_sections_get_a_clear_note_not_an_empty_table(self):
        text = report.render_report(
            run_date="2026-09-16",
            is_first_run=False,
            product_dead=[],
            product_needs_check=[],
            product_gaps=[],
            manufacturer_dead=[],
            manufacturer_needs_check=[],
            manufacturer_gaps=[],
        )
        self.assertIn("No confirmed dead productUrl links.", text)
        self.assertIn("No confirmed dead manufacturerUrl links.", text)
        self.assertIn("No coverage gaps.", text)
        self.assertIn("No integrity gaps.", text)
        self.assertNotIn("full current audit", text)

    def test_gap_rows_have_no_url_column(self):
        text = report.render_report(
            run_date="2026-09-16",
            is_first_run=False,
            product_dead=[],
            product_needs_check=[],
            product_gaps=[{"id": "b1", "name": "Beta B1", "category": "cine"}],
            manufacturer_dead=[],
            manufacturer_needs_check=[],
            manufacturer_gaps=[],
        )
        gap_section = text.split("## Product coverage gaps")[1]
        self.assertIn("| id | model / display name | category |", gap_section)


if __name__ == "__main__":
    unittest.main()

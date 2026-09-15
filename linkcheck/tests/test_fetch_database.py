import unittest

from linkcheck import fetch_database

# Small synthetic fixture set, not real production data. Shapes mirror the
# real published files closely enough to exercise the join logic.
FIXTURES = {
    "broadcast_lenses.json": {
        "lenses": [
            {"id": "acme-b1", "manufacturer": "Acme", "model": "B1"},
        ]
    },
    "broadcast_lens_details.json": {
        "lenses": [
            {"id": "acme-b1", "productUrl": "https://acme.example/b1", "manufacturerUrl": "https://acme.example"},
        ]
    },
    "cine_lenses.json": {
        "lenses": [
            {"id": "acme-c1", "manufacturer": "Acme", "model": "C1"},
            {"id": "orphan-c2", "manufacturer": "Orphan", "model": "C2"},
        ]
    },
    "cine_lens_details.json": {
        "lenses": [
            {"id": "acme-c1", "productUrl": None, "manufacturerUrl": "https://acme.example"},
            {"id": "orphan-c2", "productUrl": "https://orphan.example/c2", "manufacturerUrl": None},
        ]
    },
    "ptz_cameras.json": {
        "ptzCameras": [
            {"id": "zed-p1", "brand": "Zed", "model": "P1"},
        ]
    },
    "ptz_details.json": {
        "cameras": [
            {"id": "zed-p1", "productUrl": "https://zed.example/p1", "manufacturerUrl": "https://zed.example"},
            # No matching core entry on purpose, to exercise the id fallback.
            {"id": "missing-core-id", "productUrl": "https://zed.example/missing", "manufacturerUrl": "https://zed.example"},
        ]
    },
}


def fake_fetch(filename):
    return FIXTURES[filename]


class LoadLinkEntriesTests(unittest.TestCase):
    def setUp(self):
        self.product_entries, self.product_gaps, self.manufacturer_entries, self.manufacturer_gaps = (
            fetch_database.load_link_entries(fake_fetch)
        )

    def test_product_entry_joins_display_name_and_category(self):
        by_id = {e["id"]: e for e in self.product_entries}
        self.assertIn("acme-b1", by_id)
        self.assertEqual(by_id["acme-b1"]["name"], "Acme B1")
        self.assertEqual(by_id["acme-b1"]["category"], "broadcast")
        self.assertEqual(by_id["acme-b1"]["url"], "https://acme.example/b1")

    def test_null_product_url_becomes_a_coverage_gap_not_an_entry(self):
        product_ids = {e["id"] for e in self.product_entries}
        gap_ids = {g["id"] for g in self.product_gaps}
        self.assertNotIn("acme-c1", product_ids)
        self.assertIn("acme-c1", gap_ids)

    def test_null_manufacturer_url_becomes_an_integrity_gap(self):
        manufacturer_ids = {e["id"] for e in self.manufacturer_entries}
        gap_ids = {g["id"] for g in self.manufacturer_gaps}
        self.assertNotIn("orphan-c2", manufacturer_ids)
        self.assertIn("orphan-c2", gap_ids)

    def test_missing_core_entry_falls_back_to_id_as_display_name(self):
        by_id = {e["id"]: e for e in self.product_entries}
        self.assertEqual(by_id["missing-core-id"]["name"], "missing-core-id")
        self.assertEqual(by_id["missing-core-id"]["category"], "ptz")

    def test_ptz_uses_brand_and_model(self):
        by_id = {e["id"]: e for e in self.product_entries}
        self.assertEqual(by_id["zed-p1"]["name"], "Zed P1")
        self.assertEqual(by_id["zed-p1"]["category"], "ptz")


if __name__ == "__main__":
    unittest.main()

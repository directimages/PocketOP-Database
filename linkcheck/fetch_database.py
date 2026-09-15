"""Fetch the published database and join productUrl / manufacturerUrl entries
with display metadata (manufacturer/model, category).

Reads from jsDelivr @main, the same CDN ref the app and website read live, so
"is this link dead" reflects what a user would actually hit today rather than
an unreleased source shard.
"""

import json
import time
import urllib.error
import urllib.request

CDN_BASE = "https://cdn.jsdelivr.net/gh/directimages/PocketOP-Database@main"

# (core file, details file, core list key, details list key, category)
SOURCES = (
    ("broadcast_lenses.json", "broadcast_lens_details.json", "lenses", "lenses", "broadcast"),
    ("cine_lenses.json", "cine_lens_details.json", "lenses", "lenses", "cine"),
    ("ptz_cameras.json", "ptz_details.json", "ptzCameras", "cameras", "ptz"),
)

FETCH_RETRIES = 3
FETCH_RETRY_DELAY_SECONDS = 2


def fetch_json(filename, timeout=30):
    """Fetch one published JSON file from the CDN, with a short retry for
    transient CDN blips. Raises the last error if all attempts fail."""
    url = f"{CDN_BASE}/{filename}"
    last_error = None
    for attempt in range(FETCH_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return json.load(resp)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < FETCH_RETRIES - 1:
                time.sleep(FETCH_RETRY_DELAY_SECONDS)
    raise RuntimeError(f"Could not fetch {url} after {FETCH_RETRIES} attempts") from last_error


def _display_name(core_entry, category):
    if core_entry is None:
        return None
    if category == "ptz":
        parts = (core_entry.get("brand"), core_entry.get("model"))
    else:
        parts = (core_entry.get("manufacturer"), core_entry.get("model"))
    return " ".join(p for p in parts if p) or None


def load_link_entries(fetch=fetch_json):
    """Return (product_entries, product_gaps, manufacturer_entries, manufacturer_gaps).

    Each *_entries item: {"id", "name", "category", "url"}.
    Each *_gaps item: {"id", "name", "category"} (no url: the field is null/missing).
    """
    product_entries = []
    product_gaps = []
    manufacturer_entries = []
    manufacturer_gaps = []

    for core_file, details_file, core_key, details_key, category in SOURCES:
        core_data = fetch(core_file)
        details_data = fetch(details_file)
        core_by_id = {item["id"]: item for item in core_data.get(core_key, [])}

        for detail in details_data.get(details_key, []):
            entry_id = detail["id"]
            core_entry = core_by_id.get(entry_id)
            name = _display_name(core_entry, category) or entry_id

            product_url = detail.get("productUrl")
            if product_url:
                product_entries.append({"id": entry_id, "name": name, "category": category, "url": product_url})
            else:
                product_gaps.append({"id": entry_id, "name": name, "category": category})

            manufacturer_url = detail.get("manufacturerUrl")
            if manufacturer_url:
                manufacturer_entries.append({"id": entry_id, "name": name, "category": category, "url": manufacturer_url})
            else:
                manufacturer_gaps.append({"id": entry_id, "name": name, "category": category})

    return product_entries, product_gaps, manufacturer_entries, manufacturer_gaps

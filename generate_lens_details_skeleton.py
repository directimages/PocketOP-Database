# requires: requests==2.32.3
import json
import os
import sys
from datetime import date

import requests

CDN_URL = "https://cdn.jsdelivr.net/gh/directimages/PocketOP-Database@main/lenses.json"
OUTPUT_FILE = "lens-details.json"

SHARED_FIELDS = [
    "manufacturerUrl",
    "introductionYear",
    "imageCircleMm",
    "opticalElements",
    "weightG",
    "lengthMm",
    "frontDiameterMm",
    "closeFocusM",
    "filterType",
    "filterThreadMm",
]

BROADCAST_FIELDS = [
    "hasMacro",
    "hasServoZoom",
    "hasServoFocus",
    "servoConnector",
]

CINE_FIELDS = [
    "isParfocal",
    "hasFocusBreathing",
    "hasFrontRotation",
    "focusRingRotationDeg",
    "gearPitch",
]

BROADCAST_SENSOR_FORMATS = {"twoThirdsInch", "oneThirdInch"}


def derive_profile(lens):
    if lens["sensorFormat"] in BROADCAST_SENSOR_FORMATS:
        return "broadcast"
    return "cine_prime" if lens.get("zoomRatio", 0) == 1 else "cine_zoom"


def schema_fields(profile):
    if profile == "broadcast":
        return SHARED_FIELDS + BROADCAST_FIELDS
    return SHARED_FIELDS + CINE_FIELDS


def build_skeleton(lens_id, profile):
    entry = {"id": lens_id}
    for field in schema_fields(profile):
        entry[field] = None
    return entry


def bump_minor(version):
    major, minor, patch = version.split(".")
    return f"{major}.{int(minor) + 1}.0"


def main():
    response = requests.get(CDN_URL, timeout=15)
    response.raise_for_status()
    source_lenses = response.json()["lenses"]

    profile_by_id = {l["id"]: derive_profile(l) for l in source_lenses}

    if not os.path.exists(OUTPUT_FILE):
        lenses_out = [
            build_skeleton(l["id"], profile_by_id[l["id"]]) for l in source_lenses
        ]
        output = {
            "version": "1.0.0",
            "updatedAt": date.today().isoformat(),
            "lenses": lenses_out,
        }
        entries_added = len(lenses_out)
        entries_updated = 0
    else:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = json.load(f)

        existing_by_id = {e["id"]: e for e in existing["lenses"]}

        entries_added = 0
        entries_updated = 0
        lenses_out = []

        for lens in source_lenses:
            lid = lens["id"]
            profile = profile_by_id[lid]

            if lid in existing_by_id:
                entry = dict(existing_by_id[lid])
                missing = [f for f in schema_fields(profile) if f not in entry]
                for field in missing:
                    entry[field] = None
                lenses_out.append(entry)
                if missing:
                    entries_updated += 1
            else:
                lenses_out.append(build_skeleton(lid, profile))
                entries_added += 1

        output = {
            "version": bump_minor(existing["version"]),
            "updatedAt": date.today().isoformat(),
            "lenses": lenses_out,
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total = len(lenses_out)
    print(f"Written {total} entries to {os.path.abspath(OUTPUT_FILE)}")
    print(f"  Entries updated (fields added): {entries_updated}")
    print(f"  Entries newly added:            {entries_added}")


if __name__ == "__main__":
    main()

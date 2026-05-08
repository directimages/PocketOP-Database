# requires: requests==2.32.3
import json
import os
from datetime import date

import requests

CDN_URL = "https://cdn.jsdelivr.net/gh/directimages/PocketOP-Database@main/ptz_cameras.json"
OUTPUT_FILE = "ptz-details.json"

PTZ_FIELDS = [
    "manufacturerUrl",
    "controlProtocols",
    "videoOutputs",
    "hasPoE",
    "presetCount",
    "panRangeDeg",
    "tiltRangeDeg",
    "maxPanSpeedDegS",
    "maxTiltSpeedDegS",
    "hasIR",
    "whiteBalanceModes",
    "minLux",
    "weightG",
    "widthMm",
    "heightMm",
    "depthMm",
    "mountThreads",
    "hasCeilingMount",
    "hasWallMount",
]


def build_skeleton(camera_id):
    entry = {"id": camera_id}
    for field in PTZ_FIELDS:
        entry[field] = None
    return entry


def bump_minor(version):
    major, minor, patch = version.split(".")
    return f"{major}.{int(minor) + 1}.0"


def main():
    response = requests.get(CDN_URL, timeout=15)
    response.raise_for_status()
    source_cameras = response.json()["ptzCameras"]

    if not os.path.exists(OUTPUT_FILE):
        cameras_out = [build_skeleton(c["id"]) for c in source_cameras]
        output = {
            "version": "1.0.0",
            "updatedAt": date.today().isoformat(),
            "cameras": cameras_out,
        }
        entries_added = len(cameras_out)
        entries_updated = 0
    else:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = json.load(f)

        existing_by_id = {e["id"]: e for e in existing["cameras"]}

        entries_added = 0
        entries_updated = 0
        cameras_out = []

        for camera in source_cameras:
            cid = camera["id"]

            if cid in existing_by_id:
                entry = dict(existing_by_id[cid])
                missing = [f for f in PTZ_FIELDS if f not in entry]
                for field in missing:
                    entry[field] = None
                cameras_out.append(entry)
                if missing:
                    entries_updated += 1
            else:
                cameras_out.append(build_skeleton(cid))
                entries_added += 1

        output = {
            "version": bump_minor(existing["version"]),
            "updatedAt": date.today().isoformat(),
            "cameras": cameras_out,
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total = len(cameras_out)
    print(f"Written {total} entries to {os.path.abspath(OUTPUT_FILE)}")
    print(f"  Entries newly added:            {entries_added}")
    print(f"  Entries updated (fields added): {entries_updated}")


if __name__ == "__main__":
    main()

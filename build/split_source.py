#!/usr/bin/env python3
"""One time migration: split the current root JSON files into the source tree.

This bootstraps source/ from the existing published files. It is meant to be run
once. It refuses to run if source/ already exists, so it can never clobber
Tim's later shard edits. Pass --force only if you deliberately want to rebuild
the source tree from the current root files.

After running this, build/assemble.py --check must report a clean field level
diff, proving the split is value identical to the originals.

No em dashes appear anywhere in this file by project policy.
"""

import json
import os
import shutil
import sys

import assemble
from assemble import REPO_ROOT, SOURCE, META_DIR, slugify, is_broadcast


def load_root(name):
    with open(os.path.join(REPO_ROOT, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def top_fields(data, array_key):
    return {k: v for k, v in data.items() if k != array_key}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def write_shard(path, array_key, entries):
    entries = sorted(entries, key=lambda e: e["id"])
    write_json(path, {array_key: entries})


def main(argv):
    force = "--force" in argv
    if os.path.exists(SOURCE):
        if not force:
            print("source/ already exists. Refusing to overwrite. Use --force to "
                  "rebuild it from the current root files.", file=sys.stderr)
            return 1
        shutil.rmtree(SOURCE)

    lenses = load_root("lenses.json")
    lens_details = load_root("lens-details.json")
    ptz_cameras = load_root("ptz_cameras.json")
    ptz_details = load_root("ptz-details.json")
    devices = load_root("devices.json")

    lens_by_id = {e["id"]: e for e in lenses["lenses"]}

    # Buckets keyed by output shard path -> list of entries.
    buckets = {}

    def add(path, array_key, entry):
        buckets.setdefault((path, array_key), []).append(entry)

    # Core lenses: broadcast by manufacturer, cine by mount then manufacturer.
    for lens in lenses["lenses"]:
        mfr = slugify(lens["manufacturer"])
        if is_broadcast(lens):
            path = os.path.join(SOURCE, "broadcast-lenses", "broadcast_lens_%s.json" % mfr)
        else:
            mount = slugify(lens["mount"])
            path = os.path.join(SOURCE, "cine-lenses", mount,
                                "cine_lens_%s_%s.json" % (mount, mfr))
        add(path, "lenses", lens)

    # Lens details: routed to the same bucket as the matching core lens.
    for det in lens_details["lenses"]:
        lens = lens_by_id[det["id"]]
        mfr = slugify(lens["manufacturer"])
        if is_broadcast(lens):
            path = os.path.join(SOURCE, "broadcast-details", "broadcast_details_%s.json" % mfr)
        else:
            mount = slugify(lens["mount"])
            path = os.path.join(SOURCE, "cine-details", mount,
                                "cine_details_%s_%s.json" % (mount, mfr))
        add(path, "lenses", det)

    # PTZ cameras by brand.
    cam_brand = {}
    for cam in ptz_cameras["ptzCameras"]:
        brand = slugify(cam["brand"])
        cam_brand[cam["id"]] = brand
        path = os.path.join(SOURCE, "ptz-cameras", "ptz_cameras_%s.json" % brand)
        add(path, "ptzCameras", cam)

    # PTZ details routed by the matching camera's brand.
    for det in ptz_details["cameras"]:
        brand = cam_brand[det["id"]]
        path = os.path.join(SOURCE, "ptz-details", "ptz_details_%s.json" % brand)
        add(path, "cameras", det)

    for (path, array_key), entries in buckets.items():
        write_shard(path, array_key, entries)

    # Devices: a single shard, with its documentation blocks held in meta.
    write_shard(os.path.join(SOURCE, "devices", "devices.json"), "devices",
                devices["devices"])

    # Meta files. Versions for the new split files start at the current monolith
    # versions and are bumped by Tim going forward. The legacy meta values are
    # frozen and never bumped (the legacy files have no independent meaning once
    # they are always the union of broadcast and cine).
    lens_top = top_fields(lenses, "lenses")
    det_top = top_fields(lens_details, "lenses")
    meta = {
        "meta_lenses.json": lens_top,
        "meta_lens_details.json": det_top,
        "meta_broadcast_lenses.json": dict(lens_top),
        "meta_cine_lenses.json": dict(lens_top),
        "meta_broadcast_lens_details.json": dict(det_top),
        "meta_cine_lens_details.json": dict(det_top),
        "meta_ptz_cameras.json": top_fields(ptz_cameras, "ptzCameras"),
        "meta_ptz_details.json": top_fields(ptz_details, "cameras"),
        "meta_devices.json": top_fields(devices, "devices"),
    }
    for name, obj in meta.items():
        write_json(os.path.join(META_DIR, name), obj)

    shard_count = len(buckets) + 1  # plus the single devices shard
    print("Wrote %d shard files and %d meta files under source/."
          % (shard_count, len(meta)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

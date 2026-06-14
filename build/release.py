#!/usr/bin/env python3
"""Write or update manifest.json and current_version.json for a release.

Reads the assembled published files at the repo root, records each file's
version and entry count, and appends a release entry to manifest.json, updating
the latest pointer and timestamp. It also writes current_version.json, a thin
constant size head that holds only this release's latest tag, timestamp, and
files map, overwritten on every release with no history. The app reads this head
at launch instead of the full manifest, whose download grows with history. With
--dry-run it prints both files it would write and changes nothing.

Usage:
  python build/release.py --tag db-vN [--timestamp 2026-06-12T08:00:00Z] [--dry-run]

The release counter itself (the N in db-vN) is computed by the workflow from the
existing git tags, not here. This script only records the release.

No em dashes appear anywhere in this file by project policy.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from assemble import REPO_ROOT, OUTPUTS

MANIFEST = os.path.join(REPO_ROOT, "manifest.json")
CURRENT_VERSION = os.path.join(REPO_ROOT, "current_version.json")


def collect_files():
    """Return name -> {version, entries} for every published output file."""
    files = {}
    for out in OUTPUTS:
        path = os.path.join(REPO_ROOT, out["name"])
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        files[out["name"]] = {
            "version": data.get("version"),
            "entries": len(data[out["array_key"]]),
        }
    return files


def main(argv):
    parser = argparse.ArgumentParser(description="Record a PocketOP-Database release.")
    parser.add_argument("--tag", required=True, help="The release tag, for example db-v3.")
    parser.add_argument("--timestamp", help="UTC ISO 8601 timestamp. Defaults to now.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the manifest that would be written, change nothing.")
    args = parser.parse_args(argv)

    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    release = {"tag": args.tag, "timestamp": timestamp, "files": collect_files()}

    if os.path.isfile(MANIFEST):
        with open(MANIFEST, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    else:
        manifest = {"latest": None, "updatedAt": None, "releases": []}

    if any(rel.get("tag") == args.tag for rel in manifest.get("releases", [])):
        print("Tag %s is already recorded in manifest.json. Refusing to reuse a tag."
              % args.tag, file=sys.stderr)
        return 1

    manifest["latest"] = args.tag
    manifest["updatedAt"] = timestamp
    manifest.setdefault("releases", []).append(release)

    # The thin constant size head. Same vocabulary as the manifest top level
    # (latest, updatedAt) plus the files map, taken verbatim from the release
    # block just appended so the two can never drift. Overwritten every release,
    # no history. The files map is generic and OUTPUTS derived, so a new output
    # file surfaces here automatically with no code change.
    current = {
        "latest": args.tag,
        "updatedAt": timestamp,
        "files": release["files"],
    }

    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    current_text = json.dumps(current, ensure_ascii=False, indent=2) + "\n"
    if args.dry_run:
        print("DRY RUN. manifest.json would become:")
        print(manifest_text)
        print("DRY RUN. current_version.json would become:")
        print(current_text)
        return 0

    with open(MANIFEST, "w", encoding="utf-8") as handle:
        handle.write(manifest_text)
    with open(CURRENT_VERSION, "w", encoding="utf-8") as handle:
        handle.write(current_text)
    print("Wrote manifest.json for release %s. latest=%s, %d release(s) recorded, %d files."
          % (args.tag, args.tag, len(manifest["releases"]), len(release["files"])))
    print("Wrote current_version.json head for release %s. latest=%s, %d files."
          % (args.tag, args.tag, len(current["files"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

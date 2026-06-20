#!/usr/bin/env python3
"""Apply staged description prose onto detail shard entries, id checked first.

The user-facing description field is staged per pass as a canonical
{ "entry-id": "description" } JSON map. This tool is the single import path for
that field. In one command it:

  1. validates every map key against the set of existing detail entry ids, and
     on any mismatch fails loudly, names every orphan key, and writes nothing;
  2. only once the whole map validates, writes the prose onto the matching shard
     entries.

That closes both failure modes mechanically. No orphan key can slip through, and
because the prose is no longer hand merged it can never be written to the wrong
entry: each value lands on the entry whose id is its key, or the run aborts. Same
fail loud philosophy as the schema gate in assemble.py.

description lives as a normal field on the detail shard entry, exactly like
fieldNotes (POS-D42, one place per field). The fan out of one description across
the mount variants of the same lens is the importer's concern: list each variant
id as its own key. This tool validates and writes keys exactly as given.

Scope is the three detail sidecars only: source/broadcast-details,
source/cine-details, source/ptz-details. A key that names a core (non detail)
entry, a retired id, or a typo is an orphan here and aborts the run.

A map argument may be a .json file holding the object directly, or a pass .md
file holding one or more ```json blocks (the staging format); every block in the
file is merged.

No em dashes appear anywhere in this file by project policy.
"""

import json
import os
import re
import sys

import assemble
from assemble import AssembleError

# The detail sidecar categories, taken straight from assemble so this tool and
# the assembler can never disagree about where detail entries live.
DETAIL_CATEGORIES = [cat for cat in assemble.SHARD_CATEGORIES
                     if cat["kind"] in ("details", "ptzdet")]

JSON_BLOCK = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


def fail(message):
    raise AssembleError(message)


def index_detail_entries():
    """Map every detail entry id to the shard entry object that carries it.

    Returns id -> {"path", "array_key", "entry", "data"}. The entry object is a
    live reference into its parsed shard, so setting a field on it and writing
    the shard back persists the change.
    """
    index = {}
    for cat in DETAIL_CATEGORIES:
        for dirpath, name in assemble.iter_shard_files(cat):
            path = os.path.join(dirpath, name)
            data = assemble.load_json(path)
            entries = data.get(cat["array_key"])
            if not isinstance(entries, list):
                fail("Detail shard '%s' is missing the expected array key '%s'."
                     % (assemble.rel(path), cat["array_key"]))
            for entry in entries:
                entry_id = entry.get("id")
                if not entry_id:
                    fail("An entry in '%s' is missing a non empty 'id' field."
                         % assemble.rel(path))
                if entry_id in index:
                    fail("Duplicate detail id '%s' (in '%s' and '%s')."
                         % (entry_id, assemble.rel(index[entry_id]["path"]),
                            assemble.rel(path)))
                index[entry_id] = {"path": path, "array_key": cat["array_key"],
                                   "entry": entry, "data": data}
    return index


def parse_blocks(text, source):
    """Parse every JSON object out of the raw text of one map argument."""
    if source.endswith(".json"):
        blocks = [text]
    else:
        blocks = JSON_BLOCK.findall(text)
        if not blocks:
            fail("Pass file '%s' holds no ```json description block." % source)
    objects = []
    for block in blocks:
        try:
            obj = json.loads(block)
        except json.JSONDecodeError as exc:
            fail("Invalid JSON description map in '%s': %s" % (source, exc))
        if not isinstance(obj, dict):
            fail("Description map in '%s' must be a JSON object of "
                 "id to description." % source)
        objects.append(obj)
    return objects


def load_map_file(path):
    """Read one map argument into a single id -> description dict."""
    if not os.path.isfile(path):
        fail("Map file '%s' does not exist." % path)
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    merged = {}
    for obj in parse_blocks(text, path):
        for key, value in obj.items():
            if not isinstance(value, str):
                fail("Description for id '%s' in '%s' must be a string, got %s."
                     % (key, path, type(value).__name__))
            if key in merged and merged[key] != value:
                fail("Conflicting descriptions for id '%s' within '%s'."
                     % (key, path))
            merged[key] = value
    return merged


def combine_maps(map_paths):
    combined = {}
    for path in map_paths:
        for key, value in load_map_file(path).items():
            if key in combined and combined[key] != value:
                fail("Conflicting descriptions for id '%s' across the given "
                     "maps." % key)
            combined[key] = value
    return combined


def write_shard(path, data):
    with open(path, "wb") as handle:
        handle.write(assemble.dump_bytes(data))


def apply_descriptions(map_paths):
    """Validate every key, then write. Returns (combined_map, touched_paths)."""
    index = index_detail_entries()
    combined = combine_maps(map_paths)

    # Validation phase. Every key must resolve to an existing detail entry id.
    orphans = sorted(key for key in combined if key not in index)
    if orphans:
        listed = "\n".join("  key '%s' matches no existing detail entry id" % key
                           for key in orphans)
        fail("Description import aborted, nothing written. %d orphan key(s):\n%s"
             % (len(orphans), listed))

    # Apply phase. Reached only when the whole map validates.
    touched = {}
    for key, value in combined.items():
        slot = index[key]
        slot["entry"]["description"] = value
        touched[slot["path"]] = slot["data"]
    for path, data in sorted(touched.items()):
        write_shard(path, data)
    return combined, sorted(touched)


def main(argv):
    if not argv:
        print("usage: apply_descriptions.py <map.json|pass.md> [more ...]",
              file=sys.stderr)
        return 2
    try:
        combined, touched = apply_descriptions(argv)
    except AssembleError as exc:
        print("DESCRIPTION IMPORT FAILED: %s" % exc, file=sys.stderr)
        return 1
    print("Applied %d description(s) across %d shard(s):"
          % (len(combined), len(touched)))
    for path in touched:
        print("  %s" % assemble.rel(path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

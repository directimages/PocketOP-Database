#!/usr/bin/env python3
"""Apply staged arbitrary field maps onto detail shard entries, id checked first.

Bulk field imports (PTZ connectivity/autoTracking/aperture/hasIS, broadcast
aperture/IS, and future passes) are staged per pass as a canonical
{ "entry-id": { "field": value, ... } } JSON map. This tool is the validating
import path for that shape, generalizing the single-field precedent in
apply_descriptions.py (POS-W62) to an arbitrary set of fields per entry. In one
command it:

  1. validates every map key against the set of existing detail entry ids, and
     on any mismatch fails loudly, names every orphan key, and writes nothing;
  2. only once the whole map validates, writes every given field onto the
     matching shard entries.

That closes both failure modes mechanically. No orphan key can slip through, and
because fields are no longer hand merged they can never land on the wrong entry:
each field lands on the entry whose id is its key, or the run aborts. Same fail
loud philosophy as the schema gate in assemble.py and as apply_descriptions.py.

Scope is the three detail sidecars only: source/broadcast-details,
source/cine-details, source/ptz-details. A key that names a core (non detail)
entry, a retired id, or a typo is an orphan here and aborts the run.

fieldNotes is the one field with special apply behavior (POS-D17): its given
keys are merged into any existing fieldNotes object on the entry, creating it if
absent, leaving other existing fieldNotes keys untouched. Every other field is
set wholesale, overwriting any existing value. This merge is applied only once,
against the on-disk entry; combining the input maps themselves treats fieldNotes
as one whole-value field like any other (see combine_field_maps).

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
            fail("Pass file '%s' holds no ```json field map block." % source)
    objects = []
    for block in blocks:
        try:
            obj = json.loads(block)
        except json.JSONDecodeError as exc:
            fail("Invalid JSON field map in '%s': %s" % (source, exc))
        if not isinstance(obj, dict):
            fail("Field map in '%s' must be a JSON object of "
                 "id to field map." % source)
        objects.append(obj)
    return objects


def load_field_map_file(path):
    """Read one map argument into a single id -> {field: value} dict.

    Conflicts are checked at (id, field) granularity: the same field given two
    different values for the same id within this file fails loudly, naming both.
    Two different fields for the same id combine into one field map.
    """
    if not os.path.isfile(path):
        fail("Map file '%s' does not exist." % path)
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    merged = {}
    for obj in parse_blocks(text, path):
        for entry_id, field_map in obj.items():
            if not isinstance(field_map, dict):
                fail("Value for id '%s' in '%s' must be an object of field name "
                     "to field value, got %s."
                     % (entry_id, path, type(field_map).__name__))
            slot = merged.setdefault(entry_id, {})
            for field, value in field_map.items():
                if field in slot and slot[field] != value:
                    fail("Conflicting values for id '%s' field '%s' within '%s'."
                         % (entry_id, field, path))
                slot[field] = value
    return merged


def combine_field_maps(map_paths):
    """Merge every map argument's field maps, failing on any (id, field) conflict."""
    combined = {}
    for path in map_paths:
        for entry_id, field_map in load_field_map_file(path).items():
            slot = combined.setdefault(entry_id, {})
            for field, value in field_map.items():
                if field in slot and slot[field] != value:
                    fail("Conflicting values for id '%s' field '%s' across the "
                         "given maps." % (entry_id, field))
                slot[field] = value
    return combined


def write_shard(path, data):
    with open(path, "wb") as handle:
        handle.write(assemble.dump_bytes(data))


def apply_field(entry, field, value):
    """Set one field on a live entry object, per POS-D17 for fieldNotes."""
    if field == "fieldNotes":
        if not isinstance(value, dict):
            fail("fieldNotes value for a field map entry must be an object, "
                 "got %s." % type(value).__name__)
        existing = entry.get("fieldNotes")
        if not isinstance(existing, dict):
            existing = {}
            entry["fieldNotes"] = existing
        existing.update(value)
    else:
        entry[field] = value


def apply_fields(map_paths):
    """Validate every key, then write. Returns (combined_map, touched_paths)."""
    index = index_detail_entries()
    combined = combine_field_maps(map_paths)

    # Validation phase. Every key must resolve to an existing detail entry id.
    orphans = sorted(key for key in combined if key not in index)
    if orphans:
        listed = "\n".join("  key '%s' matches no existing detail entry id" % key
                           for key in orphans)
        fail("Field import aborted, nothing written. %d orphan key(s):\n%s"
             % (len(orphans), listed))

    # Apply phase. Reached only when the whole map validates.
    touched = {}
    field_count = 0
    for entry_id, field_map in combined.items():
        slot = index[entry_id]
        for field, value in field_map.items():
            apply_field(slot["entry"], field, value)
            field_count += 1
        touched[slot["path"]] = slot["data"]
    for path, data in sorted(touched.items()):
        write_shard(path, data)
    return combined, sorted(touched), field_count


def main(argv):
    if not argv:
        print("usage: apply_fields.py <map.json|pass.md> [more ...]",
              file=sys.stderr)
        return 2
    try:
        combined, touched, field_count = apply_fields(argv)
    except AssembleError as exc:
        print("FIELD IMPORT FAILED: %s" % exc, file=sys.stderr)
        return 1
    print("Applied %d field(s) to %d id(s) across %d shard(s):"
          % (field_count, len(combined), len(touched)))
    for path in touched:
        print("  %s" % assemble.rel(path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Validate, and optionally write, a batch of brand-new entries (POS-W62).

Today a new entry enters the pipeline by hand appending a full object to a
core brand shard and its matching details brand shard, then running
assemble.py, which is the first and only point that validates it, as a whole
build failure long after the point of staging. This is the create route:
every staged entry is validated entirely before anything is written, against
the exact destination $def in output_schema.json, the core/details field
partition (field_registry.py, the same registry apply_fields.py and
assemble.py use), an id-must-be-new check (this tool creates, it never
updates an existing id, see apply_fields.py for that), and the core/details
id-set pairing check, moved from assemble.py's post assembly check to before
write. Every violation across the whole run is collected and reported
together, per entry id and field. Nothing is written while any violation
exists, and nothing is written at all unless --write is given.

A batch file is a JSON object shaped like:

  {
    "core":    {"path": "source/.../<core shard>.json",    "entries": [...]},
    "details": {"path": "source/.../<details shard>.json", "entries": [...]}
  }

Any argument that is a directory is expanded to every *.json file directly
inside it, sorted, and each is treated exactly as if it had been passed on
the command line itself (folder mode). This is a pure input convenience;
what gets validated and how does not change.

Both sides are required in every batch given to this tool: PIPELINE.md and
assemble.py both enforce that a core shard and its paired details shard
always carry the same id set, so a batch that only adds to one side would
leave that invariant broken the moment it is written, whether or not
assemble.py is run again to notice. The path on each side is resolved
against the same source/ category directories and the same shard naming
schema assemble.py uses (assemble.parse_shard_name), so a batch aimed at a
new brand or manufacturer follows the exact naming rules the assembler will
later check, and a new shard file is created on --write if it does not exist
yet, per PIPELINE.md's "create the file if that manufacturer is new".

No em dashes appear anywhere in this file by project policy.
"""

import json
import os
import sys

import assemble
import field_registry
from assemble import AssembleError

CORE_DEF_FOR_GROUP = {"broadcast": "lens_core", "cine": "lens_core", "ptz": "ptz_core"}
CORE_KINDS = {"lenses", "ptzcam"}
DETAILS_KINDS = {"details", "ptzdet"}


def fail(message):
    raise AssembleError(message)


def resolve_category(path):
    """The assemble.py SHARD_CATEGORIES entry a batch path belongs to."""
    abs_path = os.path.abspath(path)
    rel_dir = os.path.relpath(os.path.dirname(abs_path), assemble.SOURCE)
    parts = rel_dir.split(os.sep)
    for cat in assemble.SHARD_CATEGORIES:
        if cat["mount"] and len(parts) == 2 and parts[0] == cat["dir"]:
            return cat
        if not cat["mount"] and len(parts) == 1 and parts[0] == cat["dir"]:
            return cat
    fail("Batch path '%s' does not sit under any recognised source/ category "
         "directory." % assemble.rel(abs_path))


def expand_batch_paths(paths):
    """Expand any directory argument to its sorted *.json files (folder mode)."""
    expanded = []
    for path in paths:
        if os.path.isdir(path):
            expanded.extend(
                os.path.join(path, name)
                for name in sorted(os.listdir(path))
                if name.endswith(".json")
            )
        else:
            expanded.append(path)
    return expanded


def load_batch(path):
    if not os.path.isfile(path):
        fail("Batch file '%s' does not exist." % path)
    with open(path, "r", encoding="utf-8") as handle:
        try:
            batch = json.load(handle)
        except json.JSONDecodeError as exc:
            fail("Invalid JSON in batch file '%s': %s" % (path, exc))
    if not isinstance(batch, dict) or not ({"core", "details"} & set(batch)):
        fail("Batch file '%s' must be a JSON object with a 'core' and/or "
             "'details' key." % path)
    if "core" not in batch or "details" not in batch:
        fail("Batch file '%s' is missing its '%s' side. Both a core and a "
             "matching details side are required in every batch, so the id "
             "sets can be checked as a pair before anything is written."
             % (path, "details" if "core" in batch else "core"))
    for side in ("core", "details"):
        spec = batch[side]
        if not isinstance(spec, dict) or "path" not in spec or "entries" not in spec:
            fail("Batch file '%s' side '%s' must be an object with a 'path' "
                 "and an 'entries' array." % (path, side))
        if not isinstance(spec["entries"], list):
            fail("Batch file '%s' side '%s' field 'entries' must be an array."
                 % (path, side))
    return batch


def process_side(side_name, spec, batch_file, live_ids, batch_new_ids, errors, write_plan):
    """Validate one side (core or details) of one batch. Appends to errors and
    write_plan in place. Returns the set of new ids staged on this side."""
    cat = resolve_category(spec["path"])
    expected_kinds = CORE_KINDS if side_name == "core" else DETAILS_KINDS
    if cat["kind"] not in expected_kinds:
        errors.append("batch '%s' side '%s': path '%s' resolves to category "
                      "'%s', which is not a %s category."
                      % (batch_file, side_name, spec["path"], cat["dir"], side_name))
        return set()
    dirpath, name = os.path.dirname(spec["path"]), os.path.basename(spec["path"])
    try:
        mount, entity_slug = assemble.parse_shard_name(cat, dirpath, name)
    except AssembleError as exc:
        errors.append("batch '%s' side '%s': %s" % (batch_file, side_name, exc))
        return set()
    group = cat["group"] if cat["group"] in ("broadcast", "cine") else "ptz"
    pool_name = cat["pool"]

    ids_here = set()
    for entry in spec["entries"]:
        entry_id = entry.get("id") if isinstance(entry, dict) else None
        if not entry_id:
            errors.append("batch '%s' side '%s': an entry is missing a non "
                          "empty 'id' field." % (batch_file, side_name))
            continue
        if entry_id in ids_here:
            errors.append("id '%s' is staged twice within '%s' side '%s'."
                          % (entry_id, batch_file, side_name))
            continue
        ids_here.add(entry_id)
        if entry_id in live_ids[pool_name]:
            errors.append("id '%s' already exists in pool '%s'. "
                          "create_entries.py only creates new entries; use "
                          "apply_fields.py to patch an existing one."
                          % (entry_id, pool_name))
        if entry_id in batch_new_ids[pool_name]:
            errors.append("id '%s' is staged more than once across the given "
                          "batches for pool '%s'." % (entry_id, pool_name))
        batch_new_ids[pool_name].add(entry_id)

        try:
            assemble.validate_entity(cat, entry, mount, entity_slug, spec["path"])
        except AssembleError as exc:
            errors.append("id '%s': %s" % (entry_id, exc))

        if side_name == "core":
            def_name = CORE_DEF_FOR_GROUP[group]
        elif cat["kind"] == "ptzdet":
            def_name = "ptz_details"
        else:
            def_name = field_registry.resolve_lens_details_def(entry)
            if def_name is None:
                errors.append("id '%s' in '%s': lensType=%r matches no "
                              "registered details variant (broadcast|cine)."
                              % (entry_id, spec["path"], entry.get("lensType") if isinstance(entry, dict) else None))
                continue

        entry_errors = []
        assemble.validate_value(entry, field_registry.defs()[def_name], "", entry_errors)
        entry_errors.extend(field_registry.partition_violations(def_name, entry))
        for line in entry_errors:
            errors.append("id '%s' [%s]: %s" % (entry_id, def_name, line))

    write_plan.append({"path": spec["path"], "array_key": cat["array_key"], "entries": spec["entries"]})
    return ids_here


def validate_batches(batch_paths):
    """Validate every batch. Returns (errors, write_plan)."""
    pools, pairs = assemble.load_shards()
    assemble.validate_pairs(pairs)
    live_ids = {pool: {e["id"] for e in entries} for pool, entries in pools.items()}
    batch_new_ids = {cat["pool"]: set() for cat in assemble.SHARD_CATEGORIES}

    errors = []
    write_plan = []
    for batch_file in batch_paths:
        batch = load_batch(batch_file)
        core_ids = process_side("core", batch["core"], batch_file, live_ids, batch_new_ids, errors, write_plan)
        details_ids = process_side("details", batch["details"], batch_file, live_ids, batch_new_ids, errors, write_plan)
        if core_ids != details_ids:
            missing = sorted(core_ids - details_ids)
            extra = sorted(details_ids - core_ids)
            parts = []
            if missing:
                parts.append("ids staged in core but missing from details: %s" % missing)
            if extra:
                parts.append("ids staged in details but missing from core: %s" % extra)
            errors.append("batch '%s': core/details id set mismatch. %s"
                          % (batch_file, " ; ".join(parts)))
    return errors, write_plan


def write_batches(write_plan):
    touched = []
    for item in write_plan:
        if not item["entries"]:
            continue
        path = item["path"]
        if os.path.isfile(path):
            data = assemble.load_json(path)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {item["array_key"]: []}
        data.setdefault(item["array_key"], [])
        data[item["array_key"]].extend(item["entries"])
        with open(path, "wb") as handle:
            handle.write(assemble.dump_bytes(data))
        touched.append((path, len(item["entries"])))
    return touched


def main(argv):
    write = "--write" in argv
    batch_paths = expand_batch_paths([arg for arg in argv if arg != "--write"])
    if not batch_paths:
        print("usage: create_entries.py [--write] <batch.json|batch_dir> [more ...]", file=sys.stderr)
        return 2
    try:
        errors, write_plan = validate_batches(batch_paths)
    except AssembleError as exc:
        print("CREATE VALIDATION FAILED: %s" % exc, file=sys.stderr)
        return 1
    if errors:
        shown = errors[:300]
        body = "\n".join("  " + line for line in shown)
        if len(errors) > len(shown):
            body += "\n  ... and %d more" % (len(errors) - len(shown))
        print("CREATE VALIDATION FAILED. Nothing written. %d violation(s):\n%s"
              % (len(errors), body), file=sys.stderr)
        return 1
    total_entries = sum(len(item["entries"]) for item in write_plan)
    print("CREATE VALIDATION PASSED. %d new entr%s across %d shard side(s)."
          % (total_entries, "y" if total_entries == 1 else "ies", len(write_plan)))
    if not write:
        print("Dry run, nothing written. Re-run with --write to append these "
              "entries to their target shards.")
        return 0
    touched = write_batches(write_plan)
    print("Wrote %d new entries across %d shard(s):" % (total_entries, len(touched)))
    for path, count in touched:
        print("  %s (+%d)" % (assemble.rel(os.path.abspath(path)), count))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

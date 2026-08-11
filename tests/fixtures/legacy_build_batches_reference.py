#!/usr/bin/env python3
# Frozen snapshot of build/build_batches.py from before cross-file shard
# pooling was added. Used only as a comparison oracle in
# tests/test_build_batches.py to prove the single-file, no-fan-in case
# still produces byte-identical output. Not imported or run outside tests.
"""Convert Kay-staged markdown into create_entries.py batch files (POS-W62 front door).

Kay stages new-entry batches as JSON inside fenced code blocks in markdown
staging files in the vault, under headings like "## Core (ptz_cameras_minrray,
append 17)" and "## Detail (ptz_details_minrray, append 17)". This script is
the only place that uncloaks that markdown into the plain batch JSON
create_entries.py understands. It never validates schema, never writes to a
shard, and never runs the real import; that stays create_entries.py's job,
invoked here only in dry run.

Heading contract (Kay's existing staging style, no markers to write by hand):

  ## Core (ptz_cameras_minrray, append 17)
  ```json
  [ ...core entry objects... ]
  ```
  ## Detail (ptz_details_minrray, append 17)
  ```json
  [ ...details entry objects... ]
  ```

A block is a markdown heading whose text starts with the word Core, or with
Detail/Details, case-insensitive, trailing text after that word ignored,
immediately followed (blank lines tolerated, nothing else) by exactly one
fenced json block opening with a line that is exactly ```json and closing
with a line that is exactly ```. A heading that matches the word but is not
followed by a fence is not a block: ignore it, it is not an error.

Every shard path is derived from the entry data itself, reusing assemble.py's
own slugify, SHARD_CATEGORIES, and is_broadcast so naming can never diverge
from the assembler. A core entry with a brand field is a PTZ core; one with a
manufacturer field is a lens core, broadcast or cine per
assemble.is_broadcast, cine keyed also by the entry's mount. Details entries
carry only an id; each is paired to the core entry with the same id in the
same file and inherits that core entry's shard. One core heading (or several)
can hold entries for multiple brands or manufacturers at once: they are
pooled, classified, and grouped by derived shard automatically, one output
batch per shard pair, named after the core shard's filename stem. No shard
path is ever hand typed by Kay or guessed from a filename.

Four folders live under one base directory (see POCKETOP_IMPORT_BASE below):

  inbox/  staging markdown to process
  output/ the clean batch json files this script produces
  done/   staging markdown that processed cleanly, moved here
  logs/   one timestamped run log per invocation

Failure is per file and loud: a file with no Core/Detail blocks is not an
import file and is skipped, left in inbox. A file with at least one block is
an import file, and every batch derived from it must resolve cleanly or the
whole file fails, nothing from it is written, it stays in inbox. Only a file
all of whose batches derived and wrote cleanly is moved to done/ (unless
--dry-run, which writes output/ but moves nothing).

No em dashes appear anywhere in this file by project policy.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

import assemble

ENV_VAR = "POCKETOP_IMPORT_BASE"

HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$")
CORE_WORD_RE = re.compile(r"^core\b", re.IGNORECASE)
DETAILS_WORD_RE = re.compile(r"^details?\b", re.IGNORECASE)
FENCE_OPEN = "```json"
FENCE_CLOSE = "```"

CATS_BY_DIR = {cat["dir"]: cat for cat in assemble.SHARD_CATEGORIES}


class RunLog:
    """Prints to stdout/stderr and appends the same lines to a run log file."""

    def __init__(self, path):
        self.path = path
        self.handle = open(path, "w", encoding="utf-8")

    def line(self, message, err=False):
        print(message, file=sys.stderr if err else sys.stdout)
        self.handle.write(message + "\n")

    def close(self):
        self.handle.close()


def parse_blocks(text):
    """Scan markdown text for Core/Detail(s) heading blocks.

    Returns (core_entries, details_entries, errors). core_entries and
    details_entries are lists of (entry, heading_line) pairs, pooled across
    every matching heading in the file. A heading matching the word but not
    immediately followed by a fence is not a block and is silently skipped;
    a heading that does open a fence whose content is broken is a loud
    error.
    """
    lines = text.splitlines()
    core_entries = []
    details_entries = []
    errors = []
    i = 0
    while i < len(lines):
        heading_match = HEADING_RE.match(lines[i])
        if not heading_match:
            i += 1
            continue
        heading_text = heading_match.group(1)
        if CORE_WORD_RE.match(heading_text):
            block_type = "core"
        elif DETAILS_WORD_RE.match(heading_text):
            block_type = "details"
        else:
            i += 1
            continue
        heading_line = i + 1

        # Find the opening fence: blank lines tolerated, nothing else.
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j >= len(lines) or lines[j].strip() != FENCE_OPEN:
            # A heading with no following json fence is not a block.
            i += 1
            continue

        # Find the closing fence.
        k = j + 1
        while k < len(lines) and lines[k].strip() != FENCE_CLOSE:
            k += 1
        if k >= len(lines):
            errors.append("line %d: %s heading opens a json block that is never "
                          "closed with a ``` line" % (heading_line, block_type))
            i = j + 1
            continue

        block_text = "\n".join(lines[j + 1:k])
        try:
            parsed = json.loads(block_text) if block_text.strip() else []
        except json.JSONDecodeError as exc:
            errors.append("line %d: %s heading json block has invalid JSON: %s"
                          % (heading_line, block_type, exc))
            i = k + 1
            continue
        if not isinstance(parsed, list):
            errors.append("line %d: %s heading json block is not an array"
                          % (heading_line, block_type))
            i = k + 1
            continue

        target = core_entries if block_type == "core" else details_entries
        target.extend((entry, heading_line) for entry in parsed)
        i = k + 1
    return core_entries, details_entries, errors


def classify_core_entry(entry):
    """Classify a core entry from its own data. Returns (cat, entity_slug,
    mount_slug) or None when the entry matches no known category. mount_slug
    is None for non mount categories."""
    if not isinstance(entry, dict):
        return None
    if entry.get("brand"):
        return (CATS_BY_DIR["ptz-cameras"], assemble.slugify(entry["brand"]), None)
    if entry.get("manufacturer"):
        mfr_slug = assemble.slugify(entry["manufacturer"])
        if assemble.is_broadcast(entry):
            return (CATS_BY_DIR["broadcast-lenses"], mfr_slug, None)
        return (CATS_BY_DIR["cine-lenses"], mfr_slug, assemble.slugify(entry.get("mount")))
    return None


def paired_details_cat(core_cat):
    """The SHARD_CATEGORIES entry on the details side of core_cat's pair."""
    target_kind = "ptzdet" if core_cat["kind"] == "ptzcam" else "details"
    for cat in assemble.SHARD_CATEGORIES:
        if cat["kind"] == target_kind and cat["group"] == core_cat["group"]:
            return cat
    return None


def shard_path(cat, entity_slug, mount_slug):
    """The source/ relative shard path for one category and slug, built only
    from fields already declared on the category (prefix, dir, mount) plus
    assemble's own SOURCE/REPO_ROOT, so naming cannot diverge from assemble.py."""
    base_rel = assemble.rel(os.path.join(assemble.SOURCE, cat["dir"]))
    if cat["mount"]:
        filename = "%s%s_%s.json" % (cat["prefix"], mount_slug, entity_slug)
        return "%s/%s/%s" % (base_rel, mount_slug, filename)
    filename = "%s%s.json" % (cat["prefix"], entity_slug)
    return "%s/%s" % (base_rel, filename)


def build_batches(core_entries, details_entries):
    """Classify, pair by id, and group pooled core/details entries into one
    batch per derived shard pair. Returns (batches, errors); batches maps
    core shard path -> {"core": {...}, "details": {...}}."""
    errors = []
    id_to_core_path = {}
    core_groups = {}
    details_shard_for = {}

    for entry, line in core_entries:
        if not isinstance(entry, dict) or not entry.get("id"):
            errors.append("line %d: a core entry is missing a non empty 'id' field" % line)
            continue
        entry_id = entry["id"]
        if entry_id in id_to_core_path:
            errors.append("core entry id '%s' is staged more than once in this file" % entry_id)
            continue
        classified = classify_core_entry(entry)
        if classified is None:
            errors.append("core entry '%s': matches no category (no brand or "
                          "manufacturer field)" % entry_id)
            continue
        cat, entity_slug, mount_slug = classified
        core_path = shard_path(cat, entity_slug, mount_slug)
        details_path = shard_path(paired_details_cat(cat), entity_slug, mount_slug)
        id_to_core_path[entry_id] = core_path
        core_groups.setdefault(core_path, []).append(entry)
        details_shard_for[core_path] = details_path

    details_groups = {}
    for entry, line in details_entries:
        if not isinstance(entry, dict) or not entry.get("id"):
            errors.append("line %d: a details entry is missing a non empty 'id' field" % line)
            continue
        entry_id = entry["id"]
        core_path = id_to_core_path.get(entry_id)
        if core_path is None:
            errors.append("details entry id '%s' has no matching core entry in "
                          "the same file" % entry_id)
            continue
        details_groups.setdefault(core_path, []).append(entry)

    batches = {}
    for core_path, core_list in core_groups.items():
        details_list = details_groups.get(core_path, [])
        core_ids = {e["id"] for e in core_list}
        details_ids = {e["id"] for e in details_list}
        if core_ids != details_ids:
            missing = sorted(core_ids - details_ids)
            extra = sorted(details_ids - core_ids)
            parts = []
            if missing:
                parts.append("ids in core but missing from details: %s" % missing)
            if extra:
                parts.append("ids in details but missing from core: %s" % extra)
            errors.append("shard '%s': core/details id set mismatch. %s"
                          % (core_path, " ; ".join(parts)))
            continue
        batches[core_path] = {
            "core": {"path": core_path, "entries": core_list},
            "details": {"path": details_shard_for[core_path], "entries": details_list},
        }
    return batches, errors


def process_file(path, output_dir, committed_names, log):
    """Process one inbox markdown file.

    Returns "skipped", "failed", or "clean". On "clean", the file's batches
    have already been written to output_dir and committed_names updated.
    """
    filename = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()

    core_entries, details_entries, scan_errors = parse_blocks(text)
    if not core_entries and not details_entries and not scan_errors:
        log.line("SKIP  %s: no Core/Detail blocks found" % filename)
        return "skipped"

    batches, errors = build_batches(core_entries, details_entries)
    errors = scan_errors + errors

    stems = {os.path.splitext(os.path.basename(core_path))[0]: core_path for core_path in batches}
    for stem in stems:
        if stem in committed_names:
            errors.append("batch '%s.json' was already written by '%s' earlier in this run"
                          % (stem, committed_names[stem]))

    if errors:
        log.line("FAIL  %s:" % filename, err=True)
        for line in errors:
            log.line("  " + line, err=True)
        return "failed"

    for stem, core_path in stems.items():
        batch = batches[core_path]
        out_path = os.path.join(output_dir, "%s.json" % stem)
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(batch, ensure_ascii=False, indent=2) + "\n")
        committed_names[stem] = filename
        log.line("WROTE %s -> output/%s.json (%d core, %d details)"
                 % (filename, stem, len(batch["core"]["entries"]), len(batch["details"]["entries"])))

    log.line("OK    %s: %d batch(es) written" % (filename, len(stems)))
    return "clean"


def run_create_entries_dry_run(output_dir, log):
    build_dir = os.path.dirname(os.path.abspath(__file__))
    create_entries_path = os.path.join(build_dir, "create_entries.py")
    repo_root = os.path.dirname(build_dir)
    result = subprocess.run(
        [sys.executable, create_entries_path, output_dir],
        capture_output=True, text=True, cwd=repo_root,
    )
    log.line("")
    log.line("create_entries.py dry run over output/:")
    for line in result.stdout.splitlines():
        log.line("  " + line)
    for line in result.stderr.splitlines():
        log.line("  " + line, err=True)


def main(argv):
    dry_run = "--dry-run" in argv
    positional = [arg for arg in argv if arg != "--dry-run"]
    if len(positional) > 1:
        print("usage: build_batches.py [--dry-run] [vault_import_pipeline_dir]", file=sys.stderr)
        return 2

    base = positional[0] if positional else os.environ.get(ENV_VAR)
    if not base:
        print("No import pipeline directory given and %s is not set. Set %s in your "
              "shell profile (e.g. ~/.zshrc) or pass the path as an argument."
              % (ENV_VAR, ENV_VAR), file=sys.stderr)
        return 2
    base = os.path.abspath(base)
    if not os.path.isdir(base):
        print("Import pipeline base directory '%s' does not exist." % base, file=sys.stderr)
        return 2

    inbox_dir = os.path.join(base, "inbox")
    output_dir = os.path.join(base, "output")
    done_dir = os.path.join(base, "done")
    logs_dir = os.path.join(base, "logs")
    if not os.path.isdir(inbox_dir):
        print("Import pipeline inbox directory '%s' does not exist." % inbox_dir, file=sys.stderr)
        return 2
    for directory in (output_dir, done_dir, logs_dir):
        os.makedirs(directory, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    log = RunLog(os.path.join(logs_dir, "run-%s.log" % timestamp))
    log.line("build_batches.py run %s%s" % (timestamp, " (dry run, nothing moved to done/)" if dry_run else ""))
    log.line("base: %s" % base)

    inbox_files = sorted(
        name for name in os.listdir(inbox_dir)
        if name.endswith(".md") and os.path.isfile(os.path.join(inbox_dir, name))
    )

    committed_names = {}
    counts = {"skipped": 0, "failed": 0, "clean": 0}
    to_move = []
    for filename in inbox_files:
        path = os.path.join(inbox_dir, filename)
        outcome = process_file(path, output_dir, committed_names, log)
        counts[outcome] += 1
        if outcome == "clean":
            to_move.append(filename)

    if dry_run:
        log.line("")
        log.line("Dry run: %d file(s) would move to done/, none moved." % len(to_move))
    else:
        for filename in to_move:
            os.rename(os.path.join(inbox_dir, filename), os.path.join(done_dir, filename))
            log.line("MOVED %s -> done/" % filename)

    has_output = any(name.endswith(".json") for name in os.listdir(output_dir))
    if has_output:
        run_create_entries_dry_run(output_dir, log)
    else:
        log.line("")
        log.line("output/ is empty, skipping create_entries.py dry run.")

    log.line("")
    log.line("Summary: %d clean, %d skipped (no blocks), %d failed."
             % (counts["clean"], counts["skipped"], counts["failed"]))
    log.close()

    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

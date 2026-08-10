#!/usr/bin/env python3
"""Convert Kay-staged markdown into create_entries.py batch files (POS-W62 front door).

Kay stages new-entry batches as JSON inside fenced code blocks in markdown
staging files in the vault. This script is the only place that uncloaks that
markdown into the plain batch JSON create_entries.py understands. It never
validates schema, never writes to a shard, and never runs the real import;
that stays create_entries.py's job, invoked here only in dry run.

Marker contract (Kay writes this, this script only reads it):

  <!-- batch-core shard="source/.../shard.json" name="minrray" -->
  ```json
  [ ...core entry objects... ]
  ```
  <!-- batch-details shard="source/.../shard.json" name="minrray" -->
  ```json
  [ ...details entry objects... ]
  ```

A batch is one batch-core marker and one batch-details marker sharing the
same name attribute. Each marker must be immediately followed (blank lines
tolerated, nothing else) by exactly one fenced json block opening with a
line that is exactly ```json and closing with a line that is exactly ```.
The json block is the raw entries array. shard paths are read verbatim from
the markers; this script never infers one from a brand or filename.

Four folders live under one base directory (see POCKETOP_IMPORT_BASE below):

  inbox/  staging markdown to process
  output/ the clean batch json files this script produces
  done/   staging markdown that processed cleanly, moved here
  logs/   one timestamped run log per invocation

Failure is per file and loud: a file with no markers is not an import file
and is skipped, left in inbox. A file with at least one marker is an import
file, and every batch in it must resolve cleanly or the whole file fails,
nothing from it is written, it stays in inbox. Only a file all of whose
batches parsed cleanly gets its batches written to output/ and is moved to
done/ (unless --dry-run, which writes output/ but moves nothing).

No em dashes appear anywhere in this file by project policy.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

ENV_VAR = "POCKETOP_IMPORT_BASE"

MARKER_RE = re.compile(r"^<!--\s*(batch-core|batch-details)\s+(.*?)-->\s*$")
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
FENCE_OPEN = "```json"
FENCE_CLOSE = "```"


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


def parse_markers(text):
    """Scan markdown text for marker occurrences.

    Returns (markers, scan_errors). Each marker is a dict with type, name,
    shard, line, and either 'entries' (parsed list) or 'error' (string).
    scan_errors holds malformed marker lines (missing shard/name attribute)
    that never got as far as pairing.
    """
    lines = text.splitlines()
    markers = []
    scan_errors = []
    i = 0
    while i < len(lines):
        match = MARKER_RE.match(lines[i])
        if not match:
            i += 1
            continue
        marker_type = match.group(1)
        attrs = dict(ATTR_RE.findall(match.group(2)))
        marker_line = i + 1
        if "shard" not in attrs or "name" not in attrs:
            scan_errors.append(
                "line %d: %s marker is missing a required 'shard' or 'name' attribute"
                % (marker_line, marker_type)
            )
            i += 1
            continue

        # Find the opening fence: blank lines tolerated, nothing else.
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j >= len(lines) or lines[j].strip() != FENCE_OPEN:
            markers.append({
                "type": marker_type, "name": attrs["name"], "shard": attrs["shard"],
                "line": marker_line,
                "error": ("line %d: %s marker for name '%s' is not immediately followed "
                          "by a fenced json block (```json)") % (marker_line, marker_type, attrs["name"]),
            })
            i += 1
            continue

        # Find the closing fence.
        k = j + 1
        while k < len(lines) and lines[k].strip() != FENCE_CLOSE:
            k += 1
        if k >= len(lines):
            markers.append({
                "type": marker_type, "name": attrs["name"], "shard": attrs["shard"],
                "line": marker_line,
                "error": ("line %d: %s marker for name '%s' opens a json block that is "
                          "never closed with a ``` line") % (marker_line, marker_type, attrs["name"]),
            })
            i = j + 1
            continue

        block_text = "\n".join(lines[j + 1:k])
        try:
            entries = json.loads(block_text) if block_text.strip() else []
        except json.JSONDecodeError as exc:
            markers.append({
                "type": marker_type, "name": attrs["name"], "shard": attrs["shard"],
                "line": marker_line,
                "error": "line %d: %s marker for name '%s' has invalid JSON: %s"
                         % (marker_line, marker_type, attrs["name"], exc),
            })
            i = k + 1
            continue
        if not isinstance(entries, list):
            markers.append({
                "type": marker_type, "name": attrs["name"], "shard": attrs["shard"],
                "line": marker_line,
                "error": "line %d: %s marker for name '%s' json block is not an array"
                         % (marker_line, marker_type, attrs["name"]),
            })
            i = k + 1
            continue

        markers.append({
            "type": marker_type, "name": attrs["name"], "shard": attrs["shard"],
            "line": marker_line, "entries": entries,
        })
        i = k + 1
    return markers, scan_errors


def pair_batches(markers, scan_errors):
    """Group markers by name into batches. Returns (batches, errors).

    batches maps name -> {"core": {...}, "details": {...}}. errors is a list
    of human readable strings; if non empty, the whole file has failed.
    """
    errors = list(scan_errors)
    by_name = {}
    for marker in markers:
        slot = by_name.setdefault(marker["name"], {"batch-core": [], "batch-details": []})
        slot[marker["type"]].append(marker)

    batches = {}
    for name, slot in by_name.items():
        cores, details = slot["batch-core"], slot["batch-details"]
        for side_name, side_markers in (("batch-core", cores), ("batch-details", details)):
            for marker in side_markers[1:]:
                errors.append("duplicate %s marker for name '%s' at line %d"
                              % (side_name, name, marker["line"]))
        if not cores:
            errors.append("batch-details marker for name '%s' has no matching batch-core marker" % name)
        if not details:
            errors.append("batch-core marker for name '%s' has no matching batch-details marker" % name)
        for marker in cores[:1] + details[:1]:
            if "error" in marker:
                errors.append(marker["error"])
        if cores and details and "error" not in cores[0] and "error" not in details[0]:
            batches[name] = {
                "core": {"path": cores[0]["shard"], "entries": cores[0]["entries"]},
                "details": {"path": details[0]["shard"], "entries": details[0]["entries"]},
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

    markers, scan_errors = parse_markers(text)
    if not markers and not scan_errors:
        log.line("SKIP  %s: no batch markers found" % filename)
        return "skipped"

    batches, errors = pair_batches(markers, scan_errors)

    collisions = [name for name in batches if name in committed_names]
    for name in collisions:
        errors.append("batch name '%s' was already written by '%s' earlier in this run"
                      % (name, committed_names[name]))

    if errors:
        log.line("FAIL  %s:" % filename, err=True)
        for line in errors:
            log.line("  " + line, err=True)
        return "failed"

    for name, batch in batches.items():
        out_path = os.path.join(output_dir, "%s.json" % name)
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(batch, ensure_ascii=False, indent=2) + "\n")
        committed_names[name] = filename
        log.line("WROTE %s -> output/%s.json (%d core, %d details)"
                 % (filename, name, len(batch["core"]["entries"]), len(batch["details"]["entries"])))

    log.line("OK    %s: %d batch(es) written" % (filename, len(batches)))
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
    log.line("Summary: %d clean, %d skipped (no markers), %d failed."
             % (counts["clean"], counts["skipped"], counts["failed"]))
    log.close()

    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

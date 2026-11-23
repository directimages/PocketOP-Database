#!/usr/bin/env python3
"""Broadcast source gate for the PocketOP-Database repo.

A broadcast lens spec value cannot enter or change in the published database
unless the same change also brings its source. The gate judges CHANGES only:
it compares the broadcast shards (source/broadcast-lenses and
source/broadcast-details) against a baseline snapshot and never looks at a
value that did not change, whatever its source state.

A change counts as sourced when the entry's source list (the union of its
sources and webSources) gains at least one string that was not in the baseline.
A core field change (for example a focal length) is judged against the paired
detail entry with the same id, because the source list lives on the detail
entry. A correction whose supporting source is already listed is accepted with
an acknowledgement in build/broadcast_source_acks.json, which must be new in
the same change so the trace is visible in the diff.

Never refused: a change that only moves a value to null or "unknown", a field
that is not a spec value (description, urls, notes, the source fields
themselves), a value that did not change. Refused: a spec value that is set or
altered without a new source, and a brand-new entry with spec values and an
empty source list.

Baseline, chosen automatically so a local run matches CI:
  - pull request (GITHUB_BASE_REF set): merge-base with origin/<base branch>
  - on main: the latest released db-v tag, not the previous commit, so an
    unsourced change that reached main stays judged until it is fixed
  - any other branch: merge-base with origin/main (local main as a fallback)
  - --base REF overrides all of it
When no baseline can be found: locally the gate passes with a notice (nothing
to compare against); in CI (CI environment variable set) it fails closed with
exit code 2. A local run also refuses when its tags or its origin/main are
behind the remote, because comparing against a stale baseline would judge
changes that are already released. Fix with git fetch, or skip the check with
--no-remote-check.

Exit codes: 0 passed, 1 refused (the report names file, entry id and field),
2 the gate could not run (bad baseline, stale baseline, unreadable shard or
acknowledgement file).

Standard library only plus the git command line. Works on macOS and Windows.

Usage:
  python build/broadcast_source_gate.py [--root DIR] [--base REF] [--no-remote-check]

No em dashes appear anywhere in this file by project policy.
"""

import argparse
import collections
import json
import os
import re
import subprocess
import sys

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BUILD_DIR)

if BUILD_DIR not in sys.path:
    sys.path.insert(0, BUILD_DIR)

import field_registry  # noqa: E402  (path set up above)

CORE_DIR = "source/broadcast-lenses"
DETAILS_DIR = "source/broadcast-details"
ACKS_PATH = "build/broadcast_source_acks.json"
ARRAY_KEY = "lenses"
SOURCE_FIELDS = ("sources", "webSources")
RELEASE_TAG = re.compile(r"^db-v(\d+)$")
# Cap on the violation lines printed in one report.
MAX_REPORTED = 300
# Seconds before a git call to the remote is given up.
REMOTE_TIMEOUT = 30

# The spec fields are derived from output_schema.json: every property of the
# broadcast core $def and the broadcast details $def, minus the fields below.
# A schema field that is on neither list is gated by default, so a new field
# can never slip past the gate unnoticed; tests/test_broadcast_source_gate.py
# fails until the new field is classified here.
CORE_DEF = "lens_core"
DETAILS_DEF = "lens_details_broadcast"
# Identity, classification (sensorFormat and mount decide whether a lens is a
# broadcast lens at all), flags, prose and bookkeeping. generation is NOT here:
# it is a spec field.
NON_SPEC_CORE = frozenset({
    "id", "manufacturer", "model", "series", "sensorFormat", "mount",
    "isPTZ", "isFree", "isCustom", "notes", "addedDate"})
# Identity, prose, urls and the source fields themselves.
NON_SPEC_DETAILS = frozenset({
    "id", "lensType", "description", "fieldNotes", "productUrl",
    "manufacturerUrl", "sources", "webSources"})


class GateError(Exception):
    """The gate could not run: bad or stale baseline, unreadable shard or acks."""


Snapshot = collections.namedtuple("Snapshot", ["core", "details", "acks"])
Baseline = collections.namedtuple("Baseline", ["ref", "label", "kind"])
Violation = collections.namedtuple(
    "Violation", ["file", "entry_id", "field", "old", "new", "reason", "detail_file"])

REASON_NO_SOURCE = "no_source"
REASON_CORE_NO_SOURCE = "core_no_source"
REASON_CORE_NO_DETAIL = "core_no_detail"
REASON_NEW_EMPTY = "new_empty"
REASON_NEW_CORE_NO_SOURCE = "new_core_no_source"


def spec_fields():
    """Return (core_spec, details_spec), both frozensets, from the schema."""
    return (field_registry.allowlist(CORE_DEF) - NON_SPEC_CORE,
            field_registry.allowlist(DETAILS_DEF) - NON_SPEC_DETAILS)


def is_ci(env=None):
    """True when the CI environment variable is set to something truthy."""
    env = os.environ if env is None else env
    return env.get("CI", "").strip().lower() not in ("", "0", "false")


# --------------------------------------------------------------------------
# Value rules.
# --------------------------------------------------------------------------


def is_empty(value):
    """A value that says nothing: null, or the string "unknown"."""
    return value is None or (isinstance(value, str) and value == "unknown")


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def same_value(a, b):
    """Type aware equality: True is not 1, and 2 equals 2.0."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if is_number(a) and is_number(b):
        return a == b
    return type(a) is type(b) and a == b


def source_set(entry):
    """The entry's source list: non empty strings from sources and webSources."""
    found = set()
    if not isinstance(entry, dict):
        return found
    for field in SOURCE_FIELDS:
        values = entry.get(field)
        if isinstance(values, list):
            for item in values:
                if isinstance(item, str) and item.strip():
                    found.add(item.strip())
    return found


def changed_fields(current, baseline, fields):
    """Spec fields set or altered: [(field, old, new)] sorted by field.

    A field counts when its new value is not empty and the baseline value is
    empty, absent or different. A move to null or "unknown" never counts.
    """
    base = baseline if isinstance(baseline, dict) else {}
    found = []
    for field in sorted(fields):
        new = current.get(field)
        if is_empty(new):
            continue
        old = base.get(field)
        if is_empty(old) or not same_value(old, new):
            found.append((field, old, new))
    return found


# --------------------------------------------------------------------------
# Acknowledgements.
# --------------------------------------------------------------------------


def parse_acks(data, where):
    """Validate the acknowledgement file content and return its list of acks."""
    if data is None:
        return []
    if not isinstance(data, dict) or not isinstance(data.get("acks"), list):
        raise GateError("%s must be a JSON object with an 'acks' array." % where)
    acks = []
    for index, ack in enumerate(data["acks"]):
        ok = (isinstance(ack, dict)
              and set(ack.keys()) == {"id", "field", "value", "source"}
              and isinstance(ack["id"], str) and isinstance(ack["field"], str)
              and isinstance(ack["source"], str))
        if not ok:
            raise GateError(
                "%s: ack number %d must be an object with exactly the keys id, field, "
                "value, source (id, field and source are strings)." % (where, index + 1))
        acks.append(ack)
    return acks


def ack_key(ack):
    return json.dumps(ack, sort_keys=True, ensure_ascii=True)


def ack_covers(acks, baseline_keys, entry_id, field, value, sources):
    """True when a NEW ack names this id, field and value with a listed source."""
    for ack in acks:
        if ack_key(ack) in baseline_keys:
            continue
        if (ack["id"] == entry_id and ack["field"] == field
                and same_value(ack["value"], value) and ack["source"].strip() in sources):
            return True
    return False


# --------------------------------------------------------------------------
# Snapshots: the working tree and a git ref.
# --------------------------------------------------------------------------


def _index_entries(text, path, store):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise GateError("Invalid JSON in '%s': %s" % (path, exc))
    entries = data.get(ARRAY_KEY) if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise GateError("'%s' has no '%s' array." % (path, ARRAY_KEY))
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]:
            store.setdefault(entry["id"], (entry, path))


def worktree_snapshot(root):
    """The current shards on disk, uncommitted edits included."""
    stores = {CORE_DIR: {}, DETAILS_DIR: {}}
    for rel_dir, store in stores.items():
        folder = os.path.join(root, *rel_dir.split("/"))
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".json"):
                continue
            path = rel_dir + "/" + name
            try:
                with open(os.path.join(folder, name), "r", encoding="utf-8") as handle:
                    text = handle.read()
            except (OSError, ValueError) as exc:
                raise GateError("Cannot read '%s': %s" % (path, exc))
            _index_entries(text, path, store)
    acks_file = os.path.join(root, *ACKS_PATH.split("/"))
    acks_data = None
    if os.path.isfile(acks_file):
        try:
            with open(acks_file, "r", encoding="utf-8") as handle:
                acks_data = json.load(handle)
        except (OSError, ValueError) as exc:
            raise GateError("Cannot read '%s': %s" % (ACKS_PATH, exc))
    return Snapshot(stores[CORE_DIR], stores[DETAILS_DIR], parse_acks(acks_data, ACKS_PATH))


def run_git(root, args, timeout=None, check=True):
    """Run git in root. Returns the CompletedProcess with stdout as bytes."""
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        proc = subprocess.run(["git"] + list(args), cwd=root, capture_output=True,
                              timeout=timeout, env=env)
    except FileNotFoundError:
        raise GateError("git was not found on PATH; the gate needs the git command line.")
    except subprocess.TimeoutExpired:
        raise GateError("git %s timed out." % " ".join(args))
    if check and proc.returncode != 0:
        raise GateError("git %s failed: %s" % (
            " ".join(args), proc.stderr.decode("utf-8", "replace").strip()))
    return proc


def git_text(root, args, **kwargs):
    return run_git(root, args, **kwargs).stdout.decode("utf-8", "replace").strip()


def ref_snapshot(root, ref):
    """The shards as committed at a git ref."""
    stores = {CORE_DIR: {}, DETAILS_DIR: {}}
    listing = run_git(root, ["ls-tree", "-r", "-z", "--name-only", ref, "--",
                             CORE_DIR, DETAILS_DIR]).stdout.decode("utf-8")
    for path in sorted(p for p in listing.split("\0") if p.endswith(".json")):
        rel_dir = path.rsplit("/", 1)[0]
        if rel_dir not in stores:
            continue
        text = run_git(root, ["show", "%s:%s" % (ref, path)]).stdout.decode("utf-8")
        _index_entries(text, path, stores[rel_dir])
    acks_data = None
    probe = run_git(root, ["cat-file", "-e", "%s:%s" % (ref, ACKS_PATH)], check=False)
    if probe.returncode == 0:
        text = run_git(root, ["show", "%s:%s" % (ref, ACKS_PATH)]).stdout.decode("utf-8")
        try:
            acks_data = json.loads(text)
        except ValueError as exc:
            raise GateError("Invalid JSON in '%s' at %s: %s" % (ACKS_PATH, ref, exc))
    return Snapshot(stores[CORE_DIR], stores[DETAILS_DIR],
                    parse_acks(acks_data, "%s at %s" % (ACKS_PATH, ref)))


# --------------------------------------------------------------------------
# The judgement: pure, no git, no files.
# --------------------------------------------------------------------------


def evaluate(current, baseline, core_spec=None, details_spec=None):
    """Return the sorted list of Violations for a change from baseline to current."""
    if core_spec is None or details_spec is None:
        core_spec, details_spec = spec_fields()
    baseline_keys = {ack_key(ack) for ack in baseline.acks}
    found = []

    for entry_id in sorted(current.details):
        entry, path = current.details[entry_id]
        base_entry = baseline.details.get(entry_id, (None, None))[0]
        changes = changed_fields(entry, base_entry, details_spec)
        if not changes:
            continue
        sources = source_set(entry)
        if sources - source_set(base_entry):
            continue
        for field, old, new in changes:
            if base_entry is None:
                found.append(Violation(path, entry_id, field, old, new,
                                       REASON_NEW_EMPTY, None))
            elif not ack_covers(current.acks, baseline_keys, entry_id, field, new, sources):
                found.append(Violation(path, entry_id, field, old, new,
                                       REASON_NO_SOURCE, None))

    for entry_id in sorted(current.core):
        entry, path = current.core[entry_id]
        base_entry = baseline.core.get(entry_id, (None, None))[0]
        changes = changed_fields(entry, base_entry, core_spec)
        if not changes:
            continue
        pair = current.details.get(entry_id)
        if pair is None:
            for field, old, new in changes:
                found.append(Violation(path, entry_id, field, old, new,
                                       REASON_CORE_NO_DETAIL, None))
            continue
        pair_entry, pair_path = pair
        base_pair = baseline.details.get(entry_id, (None, None))[0]
        sources = source_set(pair_entry)
        if sources - source_set(base_pair):
            continue
        for field, old, new in changes:
            if ack_covers(current.acks, baseline_keys, entry_id, field, new, sources):
                continue
            reason = REASON_NEW_CORE_NO_SOURCE if base_entry is None else REASON_CORE_NO_SOURCE
            found.append(Violation(path, entry_id, field, old, new, reason, pair_path))

    return sorted(found, key=lambda v: (v.file, v.entry_id, v.field))


# --------------------------------------------------------------------------
# Baseline resolution.
# --------------------------------------------------------------------------


def release_tags(names):
    """The db-vN tag names in the input, highest N first."""
    found = []
    for name in names:
        match = RELEASE_TAG.match(name.strip())
        if match:
            found.append((int(match.group(1)), name.strip()))
    return [name for _n, name in sorted(found, reverse=True)]


def _rev_exists(root, ref):
    return run_git(root, ["rev-parse", "--verify", "--quiet", ref + "^{commit}"],
                   check=False).returncode == 0


def _short(root, ref):
    return git_text(root, ["rev-parse", "--short", ref + "^{commit}"])


def _merge_base_baseline(root, branch):
    """Merge-base with origin/<branch>, falling back to a local branch."""
    for candidate in ("origin/" + branch, branch):
        if _rev_exists(root, candidate):
            proc = run_git(root, ["merge-base", "HEAD", candidate], check=False)
            if proc.returncode == 0:
                sha = proc.stdout.decode("utf-8").strip()
                return Baseline(sha, "merge-base with %s (%s)" % (candidate, sha[:7]),
                                "merge-base:" + candidate)
    return None


def current_branch(root, env):
    ref = env.get("GITHUB_REF", "")
    if ref.startswith("refs/heads/") and env.get("GITHUB_REF_NAME"):
        return env["GITHUB_REF_NAME"]
    proc = run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"], check=False)
    return proc.stdout.decode("utf-8").strip() if proc.returncode == 0 else ""


def resolve_baseline(root, base_arg=None, env=None):
    """Pick the baseline. Returns a Baseline, or None when there is none."""
    env = os.environ if env is None else env
    if base_arg:
        if not _rev_exists(root, base_arg):
            raise GateError("--base '%s' does not resolve to a commit in this repo." % base_arg)
        return Baseline(base_arg, "%s (%s)" % (base_arg, _short(root, base_arg)), "explicit")
    base_branch = env.get("GITHUB_BASE_REF", "").strip()
    if base_branch:
        return _merge_base_baseline(root, base_branch)
    if current_branch(root, env) == "main":
        tags = release_tags(git_text(root, ["tag", "-l", "db-v*"]).splitlines())
        if tags:
            return Baseline(tags[0], "%s (%s)" % (tags[0], _short(root, tags[0])), "tag")
        return None
    return _merge_base_baseline(root, "main")


def check_not_stale(root, baseline):
    """Refuse a local run whose tags or origin/main lag behind the remote.

    Comparing against a stale baseline would judge changes that are already
    released. Raises GateError with the fix; returns None when up to date.
    """
    if baseline.kind == "explicit":
        return
    problem_hint = ("Run 'git fetch --tags origin' and run the gate again, or skip this "
                    "check with --no-remote-check if you are offline.")
    if baseline.kind == "tag":
        proc = run_git(root, ["ls-remote", "--tags", "origin", "db-v*"],
                       timeout=REMOTE_TIMEOUT, check=False)
        if proc.returncode != 0:
            raise GateError("Cannot read the release tags from 'origin' to check that the "
                            "baseline is current (%s). %s" % (
                                proc.stderr.decode("utf-8", "replace").strip(), problem_hint))
        names = [line.split("refs/tags/")[1] for line in
                 proc.stdout.decode("utf-8").splitlines()
                 if "refs/tags/" in line and not line.endswith("^{}")]
        remote = release_tags(names)
        # Only a remote tag higher than the baseline means the baseline is stale; a
        # local tag that was never pushed is not the remote's problem.
        if remote and int(RELEASE_TAG.match(remote[0]).group(1)) > int(
                RELEASE_TAG.match(baseline.ref).group(1)):
            raise GateError(
                "Your baseline is behind the remote. Latest local release tag is %s, "
                "the remote has %s. Comparing against %s would judge changes that are "
                "already released. %s" % (baseline.ref, remote[0], baseline.ref,
                                          problem_hint))
        return
    branch = baseline.kind.split(":", 1)[1]
    if not branch.startswith("origin/"):
        return
    name = branch[len("origin/"):]
    proc = run_git(root, ["ls-remote", "origin", "refs/heads/" + name],
                   timeout=REMOTE_TIMEOUT, check=False)
    if proc.returncode != 0:
        raise GateError("Cannot read '%s' from 'origin' to check that the baseline is "
                        "current (%s). %s" % (name, proc.stderr.decode("utf-8", "replace").strip(),
                                              problem_hint))
    lines = proc.stdout.decode("utf-8").split()
    if lines and lines[0] != git_text(root, ["rev-parse", branch]):
        raise GateError(
            "Your baseline is behind the remote: local %s is not at the remote %s tip. "
            "Comparing against it would judge changes that are already merged. Run 'git "
            "fetch origin' and run the gate again, or skip this check with "
            "--no-remote-check if you are offline." % (branch, name))


# --------------------------------------------------------------------------
# Reporting.
# --------------------------------------------------------------------------


def _show(value):
    return "(none)" if value is None else json.dumps(value, ensure_ascii=True)


def format_violation(violation):
    head = "%s | %s | %s" % (violation.file, violation.entry_id, violation.field)
    change = "%s -> %s" % (_show(violation.old), _show(violation.new))
    reasons = {
        REASON_NO_SOURCE:
            "value set or changed, but this entry's sources and webSources gained no "
            "new source in this change.",
        REASON_CORE_NO_SOURCE:
            "core value changed, but the paired detail entry (%s) gained no new source "
            "in this change." % violation.detail_file,
        REASON_NEW_CORE_NO_SOURCE:
            "new core entry sets this value, but the paired detail entry (%s) has no "
            "source." % violation.detail_file,
        REASON_CORE_NO_DETAIL:
            "core value set or changed, but there is no paired detail entry with this id "
            "to carry the source.",
        REASON_NEW_EMPTY:
            "new entry sets this spec value, but its source list (sources and webSources) "
            "is empty.",
    }
    return "  %s: %s\n    %s" % (head, change, reasons[violation.reason])


def format_report(violations, baseline_label):
    lines = ["BROADCAST SOURCE GATE: %d spec value(s) set or changed without a source "
             "(baseline: %s)." % (len(violations), baseline_label)]
    for violation in violations[:MAX_REPORTED]:
        lines.append(format_violation(violation))
    if len(violations) > MAX_REPORTED:
        lines.append("  ... and %d more" % (len(violations) - MAX_REPORTED))
    lines.append("To fix: add a NEW source URL to the entry's sources in the same change "
                 "(for a core field, to the paired detail entry). To record that a source "
                 "that is already listed supports the new value, add an acknowledgement to "
                 "%s in the same change:" % ACKS_PATH)
    ackable = [v for v in violations
               if v.reason in (REASON_NO_SOURCE, REASON_CORE_NO_SOURCE)]
    sample = ackable[0] if ackable else violations[0]
    lines.append('  {"id": %s, "field": %s, "value": %s, "source": "<a URL already in the '
                 'sources list>"}' % (json.dumps(sample.entry_id), json.dumps(sample.field),
                                      _show(sample.new)))
    lines.append("A new entry with spec values always needs at least one source. Moving a "
                 "value to null or \"unknown\" needs nothing.")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Entry point.
# --------------------------------------------------------------------------


def run(root, base_arg=None, remote_check=True, env=None, out=None, err=None):
    """Run the gate. Returns the exit code (0 passed, 1 refused, 2 gate error)."""
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    env = os.environ if env is None else env
    ci = is_ci(env)
    try:
        baseline = resolve_baseline(root, base_arg, env)
        if baseline is None:
            if ci:
                raise GateError("No baseline to compare against in CI (no db-v release tag "
                                "on main, or no merge-base with the base branch; a shallow "
                                "checkout needs fetch-depth 0). The gate fails closed.")
            print("Broadcast source gate: no baseline to compare against (no release tag "
                  "and no merge-base with main). Nothing was compared; passing.", file=out)
            return 0
        if remote_check and not ci:
            check_not_stale(root, baseline)
        violations = evaluate(worktree_snapshot(root), ref_snapshot(root, baseline.ref))
    except GateError as exc:
        print("BROADCAST SOURCE GATE: %s" % exc, file=err)
        return 2
    if violations:
        print(format_report(violations, baseline.label), file=err)
        return 1
    print("Broadcast source gate passed (baseline: %s): no broadcast spec value was set or "
          "changed without a source." % baseline.label, file=out)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Broadcast source gate.")
    parser.add_argument("--root", default=REPO_ROOT,
                        help="repo root holding source/ and .git (default: this repo)")
    parser.add_argument("--base", default=None,
                        help="git ref to compare against (default: chosen automatically)")
    parser.add_argument("--no-remote-check", action="store_true",
                        help="local runs only: skip the check that tags and origin/main are "
                             "current with the remote (for offline use)")
    args = parser.parse_args(argv)
    return run(os.path.abspath(args.root), args.base, not args.no_remote_check)


if __name__ == "__main__":
    sys.exit(main())

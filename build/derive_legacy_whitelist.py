#!/usr/bin/env python3
"""Derive the frozen legacy field whitelist from the current legacy outputs.

The legacy outputs (lenses.json, lens-details.json, and the ptz-details.json
hyphen alias) still serve pre update 2 apps in the field via @main. Their schema
is frozen: no field that enters the pipeline after today may leak into them.

This script captures that frozen schema mechanically. For each legacy output it
reads the current root file and records, with no hand authoring:

  - the top level keys present in the file today
  - the sorted union of every entry field key present across all entries today

It writes two artifacts in one pass so they can never drift:

  build/legacy_whitelist.json    machine source of truth the strip imports
  build/legacy-schema-freeze.md  the human readable freeze document

Run this once to capture the frozen set. The committed output is then frozen and
is not re derived: re deriving after a future field has landed would wrongly re
admit that field. The proof that the derivation is correct is the strip being a
no op against the current data (assemble.py --check stays clean).

No em dashes appear anywhere in this file by project policy.
"""

import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
WHITELIST_JSON = os.path.join(BUILD_DIR, "legacy_whitelist.json")
WHITELIST_DOC = os.path.join(BUILD_DIR, "legacy-schema-freeze.md")

# The legacy outputs, named explicitly. This set is confirmed against the
# mutation runbook (legacy union plus the ptz-details hyphen alias) and against
# assemble.py, where these are the outputs deliberately left out of the armed
# schema gate. devices.json is also outside the gate but is a primary output,
# not legacy, so the set is named here rather than inferred from "ungated".
LEGACY_OUTPUTS = [
    {"name": "lenses.json",       "array_key": "lenses",
     "role": "Legacy union of broadcast plus cine core lenses."},
    {"name": "lens-details.json", "array_key": "lenses",
     "role": "Legacy union of broadcast plus cine lens details."},
    {"name": "ptz-details.json",  "array_key": "cameras",
     "role": "Legacy hyphen alias of ptz_details.json."},
]

DOC_PREAMBLE = """\
# Legacy schema freeze

Frozen field whitelist for the legacy outputs. Mechanically derived from the
current legacy outputs on `@main`; do not hand edit. Regenerate with
`python build/derive_legacy_whitelist.py`.

## Why this exists

The legacy outputs below still serve pre update 2 apps in the field via the
`@main` route. Their schema is frozen: when new detail fields enter the pipeline
at the upcoming data fill, those fields must reach the primary split outputs but
must never leak into the legacy outputs, because an old build can stumble over an
unexpected field. The whitelist captures the exact field set each legacy output
carries today. The strip step in `assemble.py` removes any entry field or top
level key not on the whitelist from these outputs before they are written. The
primary split outputs are never touched.

## How it is derived

For each legacy output the generator reads the current root file and records the
top level keys present and the sorted union of every entry field key present
across all entries. Nothing is researched, inferred, or hand listed. The field
sets below are exactly what is in the files today.

## How it is proven

`python build/assemble.py --check` runs the strip and then diffs every assembled
output, field for field, against the current root file it replaces. Because the
whitelist is exactly the set of keys present today, the strip removes nothing and
the diff stays clean. If the diff is not clean, the derivation is wrong, not the
data: stop and report, do not widen the whitelist to force a pass.

## Lifecycle

The strip is wired into `assemble.py` live, as a proven no op today. It begins
removing fields the moment the first field outside this whitelist appears in the
source. The strip and this whitelist are throwaway: once the `@main` legacy route
is retired (a separate Martijn decision), both are deleted.

## Granularity

The strip operates at the entry top level and the output top level only. It does
not recurse into nested objects (for example `sources` or `fieldNotes`), which is
not where new fields enter the pipeline.

## Teardown (when @main is retired)

The freeze is throwaway. Once Martijn retires the `@main` legacy route (a
separate decision, POS-D31), delete the whole mechanism in one pass:

- Delete the three build files: `build/legacy_whitelist.json`,
  `build/legacy-schema-freeze.md` (this document), and
  `build/derive_legacy_whitelist.py`.
- In `build/assemble.py`, delete the `strip_legacy_outputs` and
  `load_legacy_whitelist` functions and the `LEGACY_WHITELIST_PATH` constant.
- In `build/assemble.py`, remove the two `strip_legacy_outputs(built)` call
  sites, one in `run_check` and one in `run_assemble`.

At that point the legacy outputs can also be dropped from the assembler entirely;
that is part of the same `@main` retirement, not this freeze.
"""


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def derive():
    """Read the current legacy outputs and return the whitelist structure."""
    outputs = {}
    for spec in LEGACY_OUTPUTS:
        data = load_json(os.path.join(REPO_ROOT, spec["name"]))
        array_key = spec["array_key"]
        if array_key not in data or not isinstance(data[array_key], list):
            raise SystemExit("Legacy output '%s' has no array key '%s'."
                             % (spec["name"], array_key))
        entry_fields = set()
        for entry in data[array_key]:
            entry_fields.update(entry.keys())
        outputs[spec["name"]] = {
            "role": spec["role"],
            "arrayKey": array_key,
            "topLevelKeys": list(data.keys()),
            "entryFields": sorted(entry_fields),
        }
    return {
        "description": "Frozen field whitelist for the legacy outputs, "
                       "mechanically derived from the current legacy outputs on "
                       "@main. Do not hand edit. See legacy-schema-freeze.md.",
        "outputs": outputs,
    }


def write_json(whitelist):
    text = json.dumps(whitelist, ensure_ascii=False, indent=2) + "\n"
    with open(WHITELIST_JSON, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_doc(whitelist):
    lines = [DOC_PREAMBLE]
    for spec in LEGACY_OUTPUTS:
        out = whitelist["outputs"][spec["name"]]
        lines.append("\n## %s\n" % spec["name"])
        lines.append(out["role"] + "\n")
        lines.append("Entry array key: `%s`. Entries today: see source.\n"
                     % out["arrayKey"])
        lines.append("Allowed top level keys (%d):\n" % len(out["topLevelKeys"]))
        for key in out["topLevelKeys"]:
            lines.append("- `%s`" % key)
        lines.append("\nAllowed entry fields (%d):\n" % len(out["entryFields"]))
        for field in out["entryFields"]:
            lines.append("- `%s`" % field)
        lines.append("")
    with open(WHITELIST_DOC, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines).rstrip("\n") + "\n")


def main():
    whitelist = derive()
    write_json(whitelist)
    write_doc(whitelist)
    for name, out in whitelist["outputs"].items():
        print("%s: %d top level keys, %d entry fields"
              % (name, len(out["topLevelKeys"]), len(out["entryFields"])))
    print("Wrote %s and %s" % (os.path.relpath(WHITELIST_JSON, REPO_ROOT),
                               os.path.relpath(WHITELIST_DOC, REPO_ROOT)))


if __name__ == "__main__":
    main()

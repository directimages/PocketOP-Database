#!/usr/bin/env python3
"""Core-versus-details field partition registry, derived at runtime from
output_schema.json.

output_schema.json is the only source of truth for which fields belong to
which $def. This module derives the core allowlist and the details set
straight from the schema's declared properties (every $def here is
additionalProperties: false, so its properties list IS the allowlist), and
enforces the core/details partition as an explicit, independently reportable
rule rather than relying on the two schemas happening to stay disjoint. No
checked-in manifest: nothing here can drift from output_schema.json because
nothing here duplicates it.

One shared module, three call sites: build/create_entries.py (the create
front door), build/apply_fields.py (the core-shard guard on the existing
field-patch path), and build/assemble.py (the unskippable backstop, wired
into its existing per-output schema validation).

No em dashes appear anywhere in this file by project policy.
"""

import json
import os

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_schema.json")

# Every $def paired against the $def(s) on the other side of the core/details
# partition, for the single-object outputs only. The legacy union outputs
# (lenses.json, lens-details.json, the ptz-details.json hyphen alias) mix
# core and details fields by design and must never be run through this check.
PARTITION_PAIRS = {
    "lens_core":              (("lens_details_broadcast", "lens_details_cine"), "core", "details"),
    "lens_details_broadcast": (("lens_core",), "details", "core"),
    "lens_details_cine":      (("lens_core",), "details", "core"),
    "ptz_core":               (("ptz_details",), "core", "details"),
    "ptz_details":            (("ptz_core",), "details", "core"),
}

# Lens details $def dispatch by lensType, mirroring assemble.py's
# OUTPUT_VALIDATION variants for broadcast_lens_details.json /
# cine_lens_details.json. Shared here so create_entries.py and
# apply_fields.py resolve a lens details entry's $def the same way assemble.py
# does, instead of each re-deriving it.
LENS_DETAILS_DEF_BY_TYPE = {"broadcast": "lens_details_broadcast", "cine": "lens_details_cine"}

_allowlist_cache = {}
_defs_cache = None


def defs():
    """The full $defs registry from output_schema.json, loaded once and cached."""
    global _defs_cache
    if _defs_cache is None:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as handle:
            schema = json.load(handle)
        _defs_cache = schema["$defs"]
    return _defs_cache


def allowlist(def_name):
    """The declared property set for one $def: its closed field allowlist."""
    if def_name not in _allowlist_cache:
        _allowlist_cache[def_name] = frozenset(defs()[def_name]["properties"].keys())
    return _allowlist_cache[def_name]


def partition_violations(def_name, entry):
    """Fields in entry that are declared on the other side of the partition.

    entry may be a full entry object or a single-field {field: value} map (the
    apply_fields.py guard uses the latter). A field only counts as a violation
    when it is declared on the OTHER side and not on this one; a field
    declared on neither side is a plain schema violation, already covered by
    additionalProperties: false, and is left to the schema validator rather
    than duplicated here.
    """
    if def_name not in PARTITION_PAIRS or not isinstance(entry, dict):
        return []
    other_defs, this_label, other_label = PARTITION_PAIRS[def_name]
    this_allowed = allowlist(def_name)
    other_allowed = set()
    for other in other_defs:
        other_allowed |= allowlist(other)
    return ["field '%s' belongs in %s, not %s (core/details partition violation)"
            % (field, other_label, this_label)
            for field in entry
            if field not in this_allowed and field in other_allowed]


def resolve_lens_details_def(entry):
    """The $def a lens details entry validates against, dispatched by lensType.

    Returns None when lensType is missing or unrecognised; callers decide how
    to report that against their own id/path context.
    """
    if not isinstance(entry, dict):
        return None
    return LENS_DETAILS_DEF_BY_TYPE.get(entry.get("lensType"))

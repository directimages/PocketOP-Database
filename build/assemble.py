#!/usr/bin/env python3
"""Assemble the PocketOP-Database published JSON files from source shards.

This script reads source/meta and every shard file under source/, validates
them, and writes the published output files at the repo root. With --check it
does not write anything; instead it assembles in memory and runs a field level
diff of every assembled output against the current root file it replaces,
failing on any difference.

Sharding scheme (all discovered by globbing, no hardcoded manufacturer, brand,
or mount lists):

  source/broadcast-lenses/broadcast_lens_<mfr>.json
  source/broadcast-details/broadcast_details_<mfr>.json
  source/cine-lenses/<mount>/cine_lens_<mount>_<mfr>.json
  source/cine-details/<mount>/cine_details_<mount>_<mfr>.json
  source/ptz-cameras/ptz_cameras_<brand>.json
  source/ptz-details/ptz_details_<brand>.json
  source/devices/devices.json
  source/meta/meta_<output>.json

Outputs (repo root):
  broadcast_lenses.json, broadcast_lens_details.json
  cine_lenses.json, cine_lens_details.json
  ptz_cameras.json, ptz_details.json
  devices.json
  lenses.json, lens-details.json   (legacy union, maintained for old apps)
  ptz-details.json                 (legacy alias of ptz_details.json)

No em dashes appear anywhere in this file by project policy.
"""

import json
import os
import re
import sys
import unicodedata

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO_ROOT, "source")
META_DIR = os.path.join(SOURCE, "meta")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_schema.json")
LEGACY_WHITELIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legacy_whitelist.json")


class AssembleError(Exception):
    """Raised on any validation failure. Message names the shard and field."""


def fail(message):
    raise AssembleError(message)


def slugify(value):
    """Lowercase, strip accents, drop every non alphanumeric character.

    Angenieux, DZOFilm, 7Artisans, MasterBuilt, NiSi all become stable slugs.
    """
    norm = unicodedata.normalize("NFKD", str(value))
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", norm.lower())


def is_broadcast(entry):
    """Broadcast lens definition: 2/3 inch sensor on a B4 mount."""
    return entry.get("sensorFormat") == "twoThirdsInch" and entry.get("mount") == "B4"


# Shard categories. pool is the in memory bucket the shard feeds. mount is True
# for the two level cine categories where the first subdirectory is the mount.
SHARD_CATEGORIES = [
    {"dir": "broadcast-lenses",  "kind": "lenses",  "group": "broadcast",
     "prefix": "broadcast_lens_",    "array_key": "lenses",     "entity": "manufacturer",
     "mount": False, "pool": "broadcast_lenses"},
    {"dir": "broadcast-details", "kind": "details", "group": "broadcast",
     "prefix": "broadcast_details_", "array_key": "lenses",     "entity": None,
     "mount": False, "pool": "broadcast_details"},
    {"dir": "cine-lenses",       "kind": "lenses",  "group": "cine",
     "prefix": "cine_lens_",         "array_key": "lenses",     "entity": "manufacturer",
     "mount": True,  "pool": "cine_lenses"},
    {"dir": "cine-details",      "kind": "details", "group": "cine",
     "prefix": "cine_details_",      "array_key": "lenses",     "entity": None,
     "mount": True,  "pool": "cine_details"},
    {"dir": "ptz-cameras",       "kind": "ptzcam",  "group": "ptz",
     "prefix": "ptz_cameras_",       "array_key": "ptzCameras", "entity": "brand",
     "mount": False, "pool": "ptz_cameras"},
    {"dir": "ptz-details",       "kind": "ptzdet",  "group": "ptz",
     "prefix": "ptz_details_",       "array_key": "cameras",    "entity": None,
     "mount": False, "pool": "ptz_details"},
    {"dir": "devices",           "kind": "devices", "group": "devices",
     "prefix": None,                 "array_key": "devices",    "entity": None,
     "mount": False, "pool": "devices"},
]

# Output descriptors. order is the top level key order; the array_key slot is
# filled with the assembled entries, every other key is read from the meta file.
OUTPUTS = [
    {"name": "broadcast_lenses.json",        "meta": "meta_broadcast_lenses.json",
     "array_key": "lenses",     "order": ["version", "lenses", "updatedAt"],
     "pools": ["broadcast_lenses"],                "baseline": None},
    {"name": "cine_lenses.json",             "meta": "meta_cine_lenses.json",
     "array_key": "lenses",     "order": ["version", "lenses", "updatedAt"],
     "pools": ["cine_lenses"],                     "baseline": None},
    {"name": "lenses.json",                  "meta": "meta_lenses.json",
     "array_key": "lenses",     "order": ["version", "lenses", "updatedAt"],
     "pools": ["broadcast_lenses", "cine_lenses"], "baseline": "lenses.json"},
    {"name": "broadcast_lens_details.json",  "meta": "meta_broadcast_lens_details.json",
     "array_key": "lenses",     "order": ["version", "updatedAt", "lenses"],
     "pools": ["broadcast_details"],               "baseline": None},
    {"name": "cine_lens_details.json",       "meta": "meta_cine_lens_details.json",
     "array_key": "lenses",     "order": ["version", "updatedAt", "lenses"],
     "pools": ["cine_details"],                    "baseline": None},
    {"name": "lens-details.json",            "meta": "meta_lens_details.json",
     "array_key": "lenses",     "order": ["version", "updatedAt", "lenses"],
     "pools": ["broadcast_details", "cine_details"], "baseline": "lens-details.json"},
    {"name": "ptz_cameras.json",             "meta": "meta_ptz_cameras.json",
     "array_key": "ptzCameras", "order": ["version", "ptzCameras"],
     "pools": ["ptz_cameras"],                     "baseline": "ptz_cameras.json"},
    {"name": "ptz_details.json",             "meta": "meta_ptz_details.json",
     "array_key": "cameras",    "order": ["version", "updatedAt", "cameras"],
     "pools": ["ptz_details"],                     "baseline": "ptz-details.json"},
    {"name": "ptz-details.json",             "meta": "meta_ptz_details.json",
     "array_key": "cameras",    "order": ["version", "updatedAt", "cameras"],
     "pools": ["ptz_details"],                     "baseline": "ptz-details.json"},
    {"name": "devices.json",                 "meta": "meta_devices.json",
     "array_key": "devices",    "order": ["version", "verificationWarning", "notes", "devices"],
     "pools": ["devices"],                         "baseline": "devices.json"},
]

# Baselines used by --check. Each maps to a current root file keyed by id.
BASELINE_FILES = ["lenses.json", "lens-details.json", "ptz_cameras.json",
                  "ptz-details.json", "devices.json"]
BASELINE_ARRAY_KEY = {
    "lenses.json": "lenses", "lens-details.json": "lenses",
    "ptz_cameras.json": "ptzCameras", "ptz-details.json": "cameras",
    "devices.json": "devices",
}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        fail("Invalid JSON in shard '%s': %s" % (rel(path), exc))


def rel(path):
    return os.path.relpath(path, REPO_ROOT)


def check_global_uniqueness():
    """Step 0. Every .json filename anywhere under source/ must be unique."""
    seen = {}
    for dirpath, _dirnames, filenames in os.walk(SOURCE):
        for name in sorted(filenames):
            if not name.endswith(".json"):
                continue
            full = os.path.join(dirpath, name)
            if name in seen:
                fail("Duplicate filename '%s' found at two paths:\n  %s\n  %s\n"
                     "Every file under source/ must have a globally unique name."
                     % (name, rel(seen[name]), rel(full)))
            seen[name] = full


def parse_shard_name(cat, dirpath, name):
    """Validate a shard filename against the schema and return its slug fields.

    Returns (mount, entity_slug). mount is None for non cine categories.
    """
    if cat["prefix"] is None:
        # devices: the single fixed shard name.
        if name != "devices.json":
            fail("Unexpected file '%s' in source/%s. Only devices.json is allowed."
                 % (name, cat["dir"]))
        return (None, None)
    if not name.startswith(cat["prefix"]) or not name.endswith(".json"):
        fail("Shard '%s' does not follow the naming schema '%s<...>.json'."
             % (rel(os.path.join(dirpath, name)), cat["prefix"]))
    stem = name[len(cat["prefix"]):-len(".json")]
    if cat["mount"]:
        mount = os.path.basename(dirpath)
        prefix = mount + "_"
        if not stem.startswith(prefix):
            fail("Shard '%s' must be named '%s%s_<mfr>.json' to match its mount "
                 "directory '%s'." % (rel(os.path.join(dirpath, name)),
                                       cat["prefix"], mount, mount))
        entity_slug = stem[len(prefix):]
        if not entity_slug:
            fail("Shard '%s' is missing the manufacturer part of its name."
                 % rel(os.path.join(dirpath, name)))
        return (mount, entity_slug)
    if not stem:
        fail("Shard '%s' is missing the manufacturer or brand part of its name."
             % rel(os.path.join(dirpath, name)))
    return (None, stem)


def iter_shard_files(cat):
    base = os.path.join(SOURCE, cat["dir"])
    if not os.path.isdir(base):
        return
    if cat["mount"]:
        for mount in sorted(os.listdir(base)):
            sub = os.path.join(base, mount)
            if not os.path.isdir(sub):
                fail("Unexpected file 'source/%s/%s'. cine categories hold one "
                     "mount subdirectory level only." % (cat["dir"], mount))
            for name in sorted(os.listdir(sub)):
                if name.endswith(".json"):
                    yield sub, name
    else:
        for name in sorted(os.listdir(base)):
            full = os.path.join(base, name)
            if os.path.isdir(full):
                fail("Unexpected subdirectory 'source/%s/%s'. This category is "
                     "one level deep." % (cat["dir"], name))
            if name.endswith(".json"):
                yield base, name


def validate_entity(cat, entry, mount, entity_slug, shard_path):
    entry_id = entry.get("id")
    if cat["kind"] == "lenses":
        if cat["group"] == "broadcast" and not is_broadcast(entry):
            fail("Lens '%s' in '%s' is not a broadcast lens (needs sensorFormat "
                 "twoThirdsInch and mount B4)." % (entry_id, rel(shard_path)))
        if cat["group"] == "cine":
            if is_broadcast(entry):
                fail("Lens '%s' in '%s' is a broadcast lens and must live under "
                     "broadcast-lenses, not cine." % (entry_id, rel(shard_path)))
            if slugify(entry.get("mount")) != mount:
                fail("Lens '%s' in '%s' has mount '%s' which does not match its "
                     "mount directory '%s'." % (entry_id, rel(shard_path),
                                                 entry.get("mount"), mount))
    if cat["entity"]:
        actual = slugify(entry.get(cat["entity"]))
        if actual != entity_slug:
            fail("Entry '%s' in '%s' has %s '%s' (slug '%s') which does not match "
                 "the shard slug '%s'." % (entry_id, rel(shard_path), cat["entity"],
                                           entry.get(cat["entity"]), actual, entity_slug))


def load_shards():
    """Read and validate every shard. Returns (pools, pairs)."""
    pools = {cat["pool"]: [] for cat in SHARD_CATEGORIES}
    seen_ids = {}            # pool -> set of ids, for duplicate detection
    pairs = {}               # pairkey -> {"lenses": set, "details": set, paths}
    for cat in SHARD_CATEGORIES:
        seen_ids.setdefault(cat["pool"], set())
        for dirpath, name in iter_shard_files(cat):
            shard_path = os.path.join(dirpath, name)
            mount, entity_slug = parse_shard_name(cat, dirpath, name)
            data = load_json(shard_path)
            if cat["array_key"] not in data or not isinstance(data[cat["array_key"]], list):
                fail("Shard '%s' is missing the expected array key '%s'."
                     % (rel(shard_path), cat["array_key"]))
            ids_here = set()
            for entry in data[cat["array_key"]]:
                if not isinstance(entry, dict):
                    fail("Shard '%s' contains a non object entry." % rel(shard_path))
                entry_id = entry.get("id")
                if not entry_id:
                    fail("An entry in '%s' is missing a non empty 'id' field."
                         % rel(shard_path))
                if entry_id in seen_ids[cat["pool"]]:
                    fail("Duplicate id '%s' in pool '%s' (seen again in '%s')."
                         % (entry_id, cat["pool"], rel(shard_path)))
                seen_ids[cat["pool"]].add(entry_id)
                ids_here.add(entry_id)
                validate_entity(cat, entry, mount, entity_slug, shard_path)
                pools[cat["pool"]].append(entry)
            # Record for per file id set pairing (lenses against details).
            if cat["kind"] in ("lenses", "details") and cat["group"] in ("broadcast", "cine"):
                pairkey = (cat["group"], mount, entity_slug)
                side = "lenses" if cat["kind"] == "lenses" else "details"
                slot = pairs.setdefault(pairkey, {"lenses": None, "details": None,
                                                  "lenses_path": None, "details_path": None})
                slot[side] = ids_here
                slot[side + "_path"] = rel(shard_path)
            if cat["kind"] in ("ptzcam", "ptzdet"):
                pairkey = ("ptz", None, entity_slug)
                side = "lenses" if cat["kind"] == "ptzcam" else "details"
                slot = pairs.setdefault(pairkey, {"lenses": None, "details": None,
                                                  "lenses_path": None, "details_path": None})
                slot[side] = ids_here
                slot[side + "_path"] = rel(shard_path)
    return pools, pairs


def validate_pairs(pairs):
    for pairkey, slot in sorted(pairs.items(), key=lambda kv: str(kv[0])):
        core, det = slot["lenses"], slot["details"]
        if core is None:
            fail("Details shard '%s' has no matching core shard for %s."
                 % (slot["details_path"], pairkey))
        if det is None:
            fail("Core shard '%s' has no matching details shard for %s."
                 % (slot["lenses_path"], pairkey))
        if core != det:
            missing = sorted(core - det)
            extra = sorted(det - core)
            parts = []
            if missing:
                parts.append("ids in core but missing from details: %s" % missing)
            if extra:
                parts.append("ids in details but missing from core: %s" % extra)
            fail("Id set mismatch between '%s' and '%s'. %s"
                 % (slot["lenses_path"], slot["details_path"], " ; ".join(parts)))


def load_meta(name):
    path = os.path.join(META_DIR, name)
    if not os.path.isfile(path):
        fail("Missing meta file 'source/meta/%s'." % name)
    data = load_json(path)
    version = data.get("version")
    if not isinstance(version, str) or not version:
        fail("Meta file 'source/meta/%s' is missing a non empty string 'version'."
             % name)
    return data


def build_outputs(pools):
    """Assemble every output object, arrays sorted by id. Returns name -> obj."""
    built = {}
    for out in OUTPUTS:
        meta = load_meta(out["meta"])
        entries = []
        for pool in out["pools"]:
            entries.extend(pools[pool])
        entries = sorted(entries, key=lambda e: e["id"])
        obj = {}
        for key in out["order"]:
            if key == out["array_key"]:
                obj[key] = entries
            elif key in meta:
                obj[key] = meta[key]
            else:
                fail("Meta file '%s' is missing required field '%s' for output '%s'."
                     % (out["meta"], key, out["name"]))
        built[out["name"]] = obj
    return built


# --------------------------------------------------------------------------
# Schema validation gate.
#
# output_schema.json is the readable field registry: one $def per output kind,
# closed at the entry top level, every field optional. A field counts as added
# to an output kind only once it is registered there. This section is a small
# self contained interpreter of the subset of JSON Schema that registry uses
# (type, enum, const, anyOf, items, additionalProperties), so the pipeline stays
# stdlib only. It produces one clear per entry, per field message per violation.
# --------------------------------------------------------------------------

# Each assembled output maps to the $def it is validated against. The two lens
# details files dispatch per entry on lensType to the matching variant. Legacy
# union outputs (lenses.json, lens-details.json) and the ptz-details.json hyphen
# alias are out of scope and are not listed here, so they are not validated.
OUTPUT_VALIDATION = {
    "broadcast_lenses.json":       {"def": "lens_core"},
    "cine_lenses.json":            {"def": "lens_core"},
    "broadcast_lens_details.json": {"dispatch": "lensType",
                                    "variants": {"broadcast": "lens_details_broadcast",
                                                 "cine": "lens_details_cine"}},
    "cine_lens_details.json":      {"dispatch": "lensType",
                                    "variants": {"broadcast": "lens_details_broadcast",
                                                 "cine": "lens_details_cine"}},
    "ptz_cameras.json":            {"def": "ptz_core"},
    "ptz_details.json":            {"def": "ptz_details"},
}


def json_type(value):
    """Name the JSON type of a value, distinguishing bool, integer and number."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def matches_type(value, type_spec):
    """True when value satisfies a JSON Schema 'type' (a string or list of strings).

    bool is never an integer or a number; an integer valued float satisfies
    'integer'. This matches Draft 2020-12 numeric semantics.
    """
    names = type_spec if isinstance(type_spec, list) else [type_spec]
    for name in names:
        if name == "null" and value is None:
            return True
        if name == "boolean" and isinstance(value, bool):
            return True
        if name == "string" and isinstance(value, str):
            return True
        if name == "array" and isinstance(value, list):
            return True
        if name == "object" and isinstance(value, dict):
            return True
        if name == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if name == "integer" and not isinstance(value, bool):
            if isinstance(value, int):
                return True
            if isinstance(value, float) and value.is_integer():
                return True
    return False


def describe_type(type_spec):
    names = type_spec if isinstance(type_spec, list) else [type_spec]
    return "|".join(names)


def validate_value(value, schema, path, errors):
    """Validate value against the registry subschema, appending failure lines.

    Only the keywords the registry uses are interpreted: type, const, enum,
    anyOf, items, properties, additionalProperties. A hard mismatch stops the
    descent for that value so one bad field yields one clear message.
    """
    where = path if path else "<entry>"

    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            trial = []
            validate_value(value, branch, path, trial)
            if not trial:
                return
        shown = repr(value)
        if len(shown) > 80:
            shown = shown[:77] + "..."
        errors.append("at '%s': value %s (type %s) does not match any registered "
                      "type or value for this field" % (where, shown, json_type(value)))
        return

    if "allOf" in schema:
        for branch in schema["allOf"]:
            validate_value(value, branch, path, errors)

    if "if" in schema:
        condition = []
        validate_value(value, schema["if"], path, condition)
        if not condition:
            if "then" in schema:
                validate_value(value, schema["then"], path, errors)
        elif "else" in schema:
            validate_value(value, schema["else"], path, errors)

    if "required" in schema and isinstance(value, dict):
        for key in schema["required"]:
            if key not in value:
                errors.append("at '%s': required field '%s' is missing" % (where, key))

    if "type" in schema and not matches_type(value, schema["type"]):
        errors.append("at '%s': expected %s, got %s"
                      % (where, describe_type(schema["type"]), json_type(value)))
        return

    if "const" in schema and value != schema["const"]:
        errors.append("at '%s': value %r is not the allowed constant %r"
                      % (where, value, schema["const"]))
        return

    if "enum" in schema and value not in schema["enum"]:
        errors.append("at '%s': value %r is not one of the allowed values %s"
                      % (where, value, schema["enum"]))
        return

    if isinstance(value, dict) and ("properties" in schema or "additionalProperties" in schema):
        props = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, sub_value in value.items():
            child = (path + "." + key) if path else key
            if key in props:
                validate_value(sub_value, props[key], child, errors)
            elif additional is False:
                errors.append("at '%s': field '%s' is not registered (closed set, "
                              "unregistered field rejected)" % (where, key))
            elif isinstance(additional, dict):
                validate_value(sub_value, additional, child, errors)

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate_value(item, schema["items"], "%s[%d]" % (path, index), errors)


def validate_outputs(built):
    """Validate every in scope assembled output against output_schema.json.

    Fails with one line per entry, per field on the first run that finds any
    violation, naming the output, the entry id, the kind, and the field.
    """
    schema = load_json(SCHEMA_PATH)
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        fail("Schema '%s' is missing its '$defs' registry." % rel(SCHEMA_PATH))
    errors = []
    for out in OUTPUTS:
        spec = OUTPUT_VALIDATION.get(out["name"])
        if spec is None:
            continue
        entries = built[out["name"]][out["array_key"]]
        for entry in entries:
            entry_id = entry.get("id", "<no id>")
            if "def" in spec:
                def_name = spec["def"]
            else:
                selector = entry.get(spec["dispatch"])
                def_name = spec["variants"].get(selector)
                if def_name is None:
                    errors.append("%s id '%s': %s=%r matches no registered variant "
                                  "(%s)" % (out["name"], entry_id, spec["dispatch"],
                                            selector, "|".join(sorted(spec["variants"]))))
                    continue
            entry_errors = []
            validate_value(entry, defs[def_name], "", entry_errors)
            for line in entry_errors:
                errors.append("%s id '%s' [%s]: %s"
                              % (out["name"], entry_id, def_name, line))
    if errors:
        shown = errors[:300]
        body = "\n".join("  " + line for line in shown)
        if len(errors) > len(shown):
            body += "\n  ... and %d more" % (len(errors) - len(shown))
        fail("Schema validation failed against output_schema.json. %d violation(s):\n%s"
             % (len(errors), body))


# --------------------------------------------------------------------------
# Legacy schema freeze strip.
#
# The legacy outputs (lenses.json, lens-details.json, and the ptz-details.json
# hyphen alias) still serve pre update 2 apps via @main. Their schema is frozen:
# build/legacy_whitelist.json records the exact fields each carries today,
# mechanically derived by build/derive_legacy_whitelist.py. This step is a
# separate concern from the main assemble, which stays dumb and produces full
# output; here we strip from the legacy outputs only any entry field or top level
# key not on the whitelist, leaving the primary split outputs untouched. Today it
# is a proven no op: the whitelist is exactly what is present, so nothing is
# removed (assemble.py --check confirms it byte for byte). It begins removing
# fields the moment the first field outside the whitelist enters the source.
# --------------------------------------------------------------------------


def load_legacy_whitelist():
    if not os.path.isfile(LEGACY_WHITELIST_PATH):
        fail("Missing legacy whitelist '%s'. Run build/derive_legacy_whitelist.py."
             % rel(LEGACY_WHITELIST_PATH))
    data = load_json(LEGACY_WHITELIST_PATH)
    outputs = data.get("outputs")
    if not isinstance(outputs, dict):
        fail("Legacy whitelist '%s' is missing its 'outputs' map."
             % rel(LEGACY_WHITELIST_PATH))
    return outputs


def strip_legacy_outputs(built):
    """Strip non whitelisted fields from the frozen legacy outputs.

    Only the legacy outputs named in the whitelist are touched. The split outputs
    share their entry objects with the legacy union outputs (both assemble from
    the same pools), so each stripped entry is rebuilt as a fresh object rather
    than mutated in place; this keeps the split outputs untouched. Stripping is at
    the entry top level and the output top level only; nested objects are not
    recursed into. Field order is preserved, so today the strip is byte for byte
    identical to the current legacy files.
    """
    whitelist = load_legacy_whitelist()
    for name, spec in whitelist.items():
        if name not in built:
            fail("Legacy whitelist names output '%s' which the assembler does "
                 "not produce." % name)
        obj = built[name]
        allowed_top = set(spec["topLevelKeys"])
        for key in list(obj.keys()):
            if key not in allowed_top:
                del obj[key]
        allowed_fields = set(spec["entryFields"])
        array_key = spec["arrayKey"]
        obj[array_key] = [
            {key: value for key, value in entry.items() if key in allowed_fields}
            for entry in obj.get(array_key, [])
        ]


def dump_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_outputs(built):
    written = []
    for out in OUTPUTS:
        path = os.path.join(REPO_ROOT, out["name"])
        with open(path, "wb") as handle:
            handle.write(dump_bytes(built[out["name"]]))
        written.append(out["name"])
    return written


def load_baselines():
    baselines = {}
    for name in BASELINE_FILES:
        path = os.path.join(REPO_ROOT, name)
        if not os.path.isfile(path):
            fail("Cannot run --check: current root file '%s' is missing." % name)
        data = load_json(path)
        array_key = BASELINE_ARRAY_KEY[name]
        by_id = {e["id"]: e for e in data[array_key]}
        top = {k: v for k, v in data.items() if k != array_key}
        baselines[name] = {"by_id": by_id, "array_key": array_key, "top": top}
    return baselines


def field_diff(built, baselines, limit=200):
    """Field level diff of every output against the root file it replaces.

    Returns a list of human readable difference lines. Empty list means clean.
    """
    diffs = []
    for out in OUTPUTS:
        base_name = out["baseline"]
        if not base_name:
            continue  # split files have no standalone baseline; covered by legacy
        obj = built[out["name"]]
        base = baselines[base_name]
        by_id = base["by_id"]
        array_key = out["array_key"]
        out_ids = set()
        for entry in obj[array_key]:
            entry_id = entry["id"]
            out_ids.add(entry_id)
            if entry_id not in by_id:
                diffs.append("%s: id '%s' is not present in baseline %s"
                             % (out["name"], entry_id, base_name))
                continue
            base_entry = by_id[entry_id]
            for key in sorted(set(entry) | set(base_entry)):
                ov = base_entry.get(key, "<absent>")
                nv = entry.get(key, "<absent>")
                if ov != nv:
                    diffs.append("%s: id '%s' field '%s' original=%r assembled=%r"
                                 % (out["name"], entry_id, key, ov, nv))
        missing = set(by_id) - out_ids
        if missing:
            diffs.append("%s: %d baseline ids missing from output: %s"
                         % (out["name"], len(missing), sorted(missing)[:20]))
        # Top level non entry fields must match the baseline exactly.
        for key, ov in base["top"].items():
            nv = obj.get(key, "<absent>")
            if ov != nv:
                diffs.append("%s: top level field '%s' original=%r assembled=%r"
                             % (out["name"], key, ov, nv))
    return diffs


def run_check():
    check_global_uniqueness()
    pools, pairs = load_shards()
    validate_pairs(pairs)
    # Cross domain union checks (implied by pairing, asserted explicitly).
    lens_ids = {e["id"] for e in pools["broadcast_lenses"]} | {e["id"] for e in pools["cine_lenses"]}
    det_ids = {e["id"] for e in pools["broadcast_details"]} | {e["id"] for e in pools["cine_details"]}
    if lens_ids != det_ids:
        fail("lenses id set does not equal lens-details id set.")
    ptzc_ids = {e["id"] for e in pools["ptz_cameras"]}
    ptzd_ids = {e["id"] for e in pools["ptz_details"]}
    if ptzc_ids != ptzd_ids:
        fail("ptz_cameras id set does not equal ptz-details id set.")
    built = build_outputs(pools)
    strip_legacy_outputs(built)
    validate_outputs(built)
    baselines = load_baselines()
    diffs = field_diff(built, baselines)
    if diffs:
        print("FIELD LEVEL DIFF FAILED. %d difference(s) found:" % len(diffs))
        for line in diffs[:200]:
            print("  " + line)
        if len(diffs) > 200:
            print("  ... and %d more" % (len(diffs) - 200))
        return 1
    counts = ", ".join("%s=%d" % (out["name"], len(built[out["name"]][out["array_key"]]))
                       for out in OUTPUTS)
    print("CHECK PASSED. Assembled output is field for field identical to the "
          "current root files by id.")
    print("Entry counts: " + counts)
    return 0


def run_assemble():
    check_global_uniqueness()
    pools, pairs = load_shards()
    validate_pairs(pairs)
    built = build_outputs(pools)
    strip_legacy_outputs(built)
    validate_outputs(built)
    written = write_outputs(built)
    print("Assembled %d output files:" % len(written))
    for out in OUTPUTS:
        print("  %s (%d entries)" % (out["name"], len(built[out["name"]][out["array_key"]])))
    return 0


def main(argv):
    try:
        if "--check" in argv:
            return run_check()
        return run_assemble()
    except AssembleError as exc:
        print("VALIDATION FAILED: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

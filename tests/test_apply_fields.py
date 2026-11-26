#!/usr/bin/env python3
"""Tests for build/apply_fields.py, with the fieldNotes removal instruction.

apply_fields.py applies a staged { "entry-id": { "field": value } } map onto the
detail shards. fieldNotes merges (POS-D17) and so can never lose a key through a
map; the reserved instruction removeFieldNotes (a list of key names) is the
explicit way to remove keys. These tests cover the removal and what must stay
unchanged around it:

  * removal alone, removal plus set and merge in one map, the last key removed
    (the fieldNotes key itself goes, in every category), and both staging
    formats (.json and ```json blocks in a .md file);
  * every unhappy path: a key the entry does not have, the same key set and
    removed, malformed instructions, an orphan id, conflicting blocks. Each
    must fail loudly and leave every shard byte for byte untouched;
  * combining several blocks and files, identical lists accepted in any order;
  * a map without the instruction gives the same shards and the same output as
    before the instruction existed (expected bytes are spelled out here);
  * a removal only map still passes the schema gate and assemble, the
    attribution gate and the broadcast source gate.

Every test builds its own synthetic source tree under a temporary directory and
points assemble.py at it. No test reads or writes the real source/ shards; every
id, brand and value here is made up.

Run with: python -m unittest discover -s tests -v

No em dashes appear anywhere in this file by project policy.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
BUILD_DIR = os.path.join(REPO_ROOT, "build")

if BUILD_DIR not in sys.path:
    sys.path.insert(0, BUILD_DIR)

import apply_fields  # noqa: E402  (path set up above)
import assemble  # noqa: E402
import attribution_gate  # noqa: E402
import broadcast_source_gate as source_gate  # noqa: E402

META_NAMES = sorted({out["meta"] for out in assemble.OUTPUTS})
SYNTHETIC_META = {"version": "0.0.0-test", "updatedAt": "test",
                  "verificationWarning": ["synthetic"], "notes": ["synthetic"]}

BROADCAST_SHARD = os.path.join("source", "broadcast-details", "broadcast_details_testco.json")
CINE_SHARD = os.path.join("source", "cine-details", "ef", "cine_details_testco.json")
PTZ_SHARD = os.path.join("source", "ptz-details", "ptz_details_testco.json")
ATTRIBUTION_ALLOWLIST = os.path.join(BUILD_DIR, "attribution_allowlist.txt")


def detail(entry_id, lens_type="broadcast", **extra):
    entry = {"id": entry_id, "lensType": lens_type}
    entry.update(extra)
    return entry


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(assemble.dump_bytes(data))


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def md_blocks(*maps):
    """A staging .md text holding one ```json block per map."""
    parts = ["# Synthetic staging pass\n"]
    for field_map in maps:
        parts.append("```json\n%s\n```\n" % json.dumps(field_map, indent=2))
    return "\n".join(parts)


class ApplyFieldsCase(unittest.TestCase):
    """A synthetic source tree per test, with assemble pointed at it."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.source = os.path.join(self.root, "source")
        meta_dir = os.path.join(self.source, "meta")
        for name in META_NAMES:
            write_json(os.path.join(meta_dir, name), SYNTHETIC_META)
        for name, value in (("REPO_ROOT", self.root), ("SOURCE", self.source),
                            ("META_DIR", meta_dir)):
            patcher = mock.patch.object(assemble, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.maps_dir = os.path.join(self.root, "maps")
        os.makedirs(self.maps_dir)

    # ----- fixtures -----

    def path(self, shard):
        return os.path.join(self.root, shard)

    def write_shard(self, shard, array_key, entries):
        write_json(self.path(shard), {array_key: entries})

    def default_tree(self):
        """One shard per category, covering every fieldNotes shape."""
        self.write_shard(BROADCAST_SHARD, "lenses", [
            detail("testco-bc-only", fieldNotes={"hasMacro": "note a"}),
            detail("testco-bc-many", fieldNotes={"hasMacro": "note a", "other": "note b",
                                                 "third": "note c"}),
            detail("testco-bc-bare"),
        ])
        self.write_shard(CINE_SHARD, "lenses", [
            detail("testco-cine-only", lens_type="cine", fieldNotes={"hasMacro": "note a"}),
            detail("testco-cine-empty", lens_type="cine", fieldNotes={}),
        ])
        self.write_shard(PTZ_SHARD, "cameras", [
            {"id": "testco-ptz-only", "fieldNotes": {"hasMacro": "note a"}},
            {"id": "testco-ptz-bare"},
        ])

    def stage_json(self, field_map, name="map.json"):
        path = os.path.join(self.maps_dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(field_map, handle)
        return path

    def stage_md(self, *maps, name="pass.md"):
        path = os.path.join(self.maps_dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(md_blocks(*maps))
        return path

    def snapshot(self):
        """Every shard byte under the synthetic tree, for no-write assertions."""
        found = {}
        for shard in (BROADCAST_SHARD, CINE_SHARD, PTZ_SHARD):
            if os.path.isfile(self.path(shard)):
                found[shard] = read_bytes(self.path(shard))
        return found

    def entries(self, shard, array_key):
        with open(self.path(shard), encoding="utf-8") as handle:
            return {e["id"]: e for e in json.load(handle)[array_key]}

    def run_main(self, *paths):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = apply_fields.main(list(paths))
        return code, out.getvalue(), err.getvalue()

    def assert_fails_and_writes_nothing(self, *paths, message=None):
        before = self.snapshot()
        code, out, err = self.run_main(*paths)
        self.assertEqual(code, 1, err)
        self.assertIn("FIELD IMPORT FAILED", err)
        if message:
            self.assertIn(message, err)
        self.assertEqual(self.snapshot(), before, "a failed run must write nothing")
        return err


class RemovalTests(ApplyFieldsCase):

    def test_json_map_removes_one_key_and_keeps_the_others(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-many": {"removeFieldNotes": ["other"]}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        entries = self.entries(BROADCAST_SHARD, "lenses")
        self.assertEqual(entries["testco-bc-many"]["fieldNotes"],
                         {"hasMacro": "note a", "third": "note c"})
        self.assertEqual(entries["testco-bc-only"]["fieldNotes"], {"hasMacro": "note a"})

    def test_md_staging_file_with_several_blocks(self):
        self.default_tree()
        path = self.stage_md({"testco-bc-many": {"removeFieldNotes": ["other"]}},
                             {"testco-ptz-only": {"removeFieldNotes": ["hasMacro"]}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.entries(BROADCAST_SHARD, "lenses")["testco-bc-many"]["fieldNotes"],
                         {"hasMacro": "note a", "third": "note c"})
        self.assertNotIn("fieldNotes", self.entries(PTZ_SHARD, "cameras")["testco-ptz-only"])

    def test_several_keys_in_one_instruction(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-many": {"removeFieldNotes": ["third", "hasMacro"]}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.entries(BROADCAST_SHARD, "lenses")["testco-bc-many"]["fieldNotes"],
                         {"other": "note b"})

    def test_removal_plus_set_and_merge_in_the_same_map(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-many": {
            "removeFieldNotes": ["other"],
            "weightG": 1234,
            "fieldNotes": {"filterThreadMm": "new note", "hasMacro": "rewritten"},
        }})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        entry = self.entries(BROADCAST_SHARD, "lenses")["testco-bc-many"]
        self.assertEqual(entry["weightG"], 1234)
        self.assertEqual(entry["fieldNotes"], {"hasMacro": "rewritten", "third": "note c",
                                               "filterThreadMm": "new note"})
        self.assertNotIn("removeFieldNotes", entry)

    def test_last_key_removed_leaves_an_entry_that_never_had_notes(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-only": {"removeFieldNotes": ["hasMacro"]},
                                "testco-cine-only": {"removeFieldNotes": ["hasMacro"]},
                                "testco-ptz-only": {"removeFieldNotes": ["hasMacro"]}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        # Byte for byte the shards an author would write for entries that never
        # carried fieldNotes: the key is gone, not an empty object.
        expected = {
            BROADCAST_SHARD: ("lenses", [detail("testco-bc-only"),
                                         detail("testco-bc-many", fieldNotes={
                                             "hasMacro": "note a", "other": "note b",
                                             "third": "note c"}),
                                         detail("testco-bc-bare")]),
            CINE_SHARD: ("lenses", [detail("testco-cine-only", lens_type="cine"),
                                    detail("testco-cine-empty", lens_type="cine", fieldNotes={})]),
            PTZ_SHARD: ("cameras", [{"id": "testco-ptz-only"}, {"id": "testco-ptz-bare"}]),
        }
        for shard, (array_key, entries) in expected.items():
            self.assertEqual(read_bytes(self.path(shard)),
                             assemble.dump_bytes({array_key: entries}), shard)

    def test_last_key_removed_with_a_merge_that_adds_a_key_keeps_the_notes(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-only": {
            "removeFieldNotes": ["hasMacro"], "fieldNotes": {"fresh": "kept"}}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.entries(BROADCAST_SHARD, "lenses")["testco-bc-only"]["fieldNotes"],
                         {"fresh": "kept"})

    def test_only_the_named_entry_changes(self):
        self.default_tree()
        before = self.snapshot()
        path = self.stage_json({"testco-bc-only": {"removeFieldNotes": ["hasMacro"]}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        after = self.snapshot()
        self.assertEqual(after[CINE_SHARD], before[CINE_SHARD])
        self.assertEqual(after[PTZ_SHARD], before[PTZ_SHARD])
        self.assertNotEqual(after[BROADCAST_SHARD], before[BROADCAST_SHARD])
        entries = self.entries(BROADCAST_SHARD, "lenses")
        self.assertNotIn("fieldNotes", entries["testco-bc-only"])
        self.assertEqual(entries["testco-bc-many"]["fieldNotes"]["third"], "note c")

    def test_run_output_reports_removals_separately(self):
        self.default_tree()
        path = self.stage_json({
            "testco-bc-many": {"removeFieldNotes": ["third", "other"], "weightG": 5},
            "testco-ptz-only": {"removeFieldNotes": ["hasMacro"]}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertEqual(lines[0], "Applied 1 field(s) to 1 id(s) across 2 shard(s):")
        self.assertIn("Removed 3 fieldNotes key(s) from 2 id(s):", lines)
        self.assertIn("  testco-bc-many: other, third", lines)
        self.assertIn("  testco-ptz-only: hasMacro", lines)

    def test_removal_only_map_reports_zero_applied_fields(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-only": {"removeFieldNotes": ["hasMacro"]}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines()[0], "Applied 0 field(s) to 0 id(s) across 1 shard(s):")
        self.assertIn("Removed 1 fieldNotes key(s) from 1 id(s):", out)


class UnhappyPathTests(ApplyFieldsCase):

    def test_key_the_entry_does_not_have(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-many": {"removeFieldNotes": ["absentKey"]}})
        err = self.assert_fails_and_writes_nothing(path, message="removal violation")
        self.assertIn("testco-bc-many", err)
        self.assertIn("absentKey", err)

    def test_entry_without_fieldnotes_or_with_empty_fieldnotes(self):
        self.default_tree()
        for entry_id in ("testco-bc-bare", "testco-cine-empty", "testco-ptz-bare"):
            with self.subTest(entry=entry_id):
                path = self.stage_json({entry_id: {"removeFieldNotes": ["hasMacro"]}})
                err = self.assert_fails_and_writes_nothing(path, message="does not have")
                self.assertIn(entry_id, err)

    def test_fieldnotes_that_is_not_an_object(self):
        self.write_shard(BROADCAST_SHARD, "lenses", [detail("testco-bc-null", fieldNotes=None)])
        path = self.stage_json({"testco-bc-null": {"removeFieldNotes": ["hasMacro"]}})
        self.assert_fails_and_writes_nothing(path, message="does not have")

    def test_one_bad_key_stops_the_valid_removals_too(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-only": {"removeFieldNotes": ["hasMacro"]},
                                "testco-bc-many": {"removeFieldNotes": ["absentKey"]},
                                "testco-ptz-only": {"weightG": 1}})
        self.assert_fails_and_writes_nothing(path)

    def test_every_bad_key_is_reported_together(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-many": {"removeFieldNotes": ["x1", "x2"]},
                                "testco-bc-bare": {"removeFieldNotes": ["x3"]}})
        err = self.assert_fails_and_writes_nothing(path, message="3 fieldNotes removal")
        for key in ("x1", "x2", "x3"):
            self.assertIn(key, err)

    def test_same_key_set_and_removed_in_one_block(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-many": {
            "removeFieldNotes": ["other"], "fieldNotes": {"other": "again"}}})
        err = self.assert_fails_and_writes_nothing(path, message="both set and removed")
        self.assertIn("other", err)

    def test_same_key_set_and_removed_across_blocks_and_files(self):
        self.default_tree()
        setter = {"testco-bc-many": {"fieldNotes": {"other": "again"}}}
        remover = {"testco-bc-many": {"removeFieldNotes": ["other"]}}
        self.assert_fails_and_writes_nothing(self.stage_md(setter, remover, name="a.md"),
                                             message="both set and removed")
        self.assert_fails_and_writes_nothing(self.stage_json(setter, "b1.json"),
                                             self.stage_json(remover, "b2.json"),
                                             message="both set and removed")

    def test_set_and_removed_names_the_key_even_when_new_to_the_entry(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-many": {
            "removeFieldNotes": ["fresh"], "fieldNotes": {"fresh": "x"}}})
        self.assert_fails_and_writes_nothing(path)

    def test_malformed_instruction_variants(self):
        self.default_tree()
        bad_values = {
            "string": "hasMacro",
            "object": {"hasMacro": True},
            "null": None,
            "number": 3,
            "empty list": [],
            "non string item": ["hasMacro", 4],
            "null item": [None],
            "empty string item": [""],
            "nested list": [["hasMacro"]],
            "duplicate": ["hasMacro", "hasMacro"],
        }
        for label, value in bad_values.items():
            with self.subTest(case=label):
                path = self.stage_json({"testco-bc-only": {"removeFieldNotes": value}})
                err = self.assert_fails_and_writes_nothing(path, message="Malformed removal")
                self.assertIn("testco-bc-only", err)

    def test_malformed_instruction_in_a_md_block(self):
        self.default_tree()
        path = self.stage_md({"testco-bc-only": {"removeFieldNotes": "hasMacro"}})
        self.assert_fails_and_writes_nothing(path, message="Malformed removal")

    def test_orphan_id_with_a_removal(self):
        self.default_tree()
        path = self.stage_json({"testco-missing": {"removeFieldNotes": ["hasMacro"]},
                                "testco-bc-only": {"removeFieldNotes": ["hasMacro"]}})
        err = self.assert_fails_and_writes_nothing(path, message="orphan")
        self.assertIn("testco-missing", err)

    def test_rerun_of_an_applied_removal_fails_loudly(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-many": {"removeFieldNotes": ["other"]}})
        self.assertEqual(self.run_main(path)[0], 0)
        self.assert_fails_and_writes_nothing(path, message="does not have")


class CombiningTests(ApplyFieldsCase):

    def test_identical_lists_in_any_order_are_accepted(self):
        self.default_tree()
        a = {"testco-bc-many": {"removeFieldNotes": ["other", "third"]}}
        b = {"testco-bc-many": {"removeFieldNotes": ["third", "other"]}}
        for label, paths in (("blocks in one md", [self.stage_md(a, b, name="c.md")]),
                             ("two files", [self.stage_json(a, "c1.json"),
                                            self.stage_json(b, "c2.json")])):
            with self.subTest(case=label):
                self.default_tree()
                code, out, err = self.run_main(*paths)
                self.assertEqual(code, 0, err)
                self.assertEqual(
                    self.entries(BROADCAST_SHARD, "lenses")["testco-bc-many"]["fieldNotes"],
                    {"hasMacro": "note a"})
                self.assertIn("Removed 2 fieldNotes key(s) from 1 id(s):", out)

    def test_different_lists_for_one_entry_conflict_and_are_not_unioned(self):
        self.default_tree()
        a = {"testco-bc-many": {"removeFieldNotes": ["other"]}}
        b = {"testco-bc-many": {"removeFieldNotes": ["third"]}}
        err = self.assert_fails_and_writes_nothing(self.stage_md(a, b, name="d.md"),
                                                   message="Conflicting values")
        self.assertIn("removeFieldNotes", err)
        self.assert_fails_and_writes_nothing(self.stage_json(a, "d1.json"),
                                             self.stage_json(b, "d2.json"),
                                             message="Conflicting values")

    def test_a_subset_list_is_still_a_conflict(self):
        self.default_tree()
        a = {"testco-bc-many": {"removeFieldNotes": ["other", "third"]}}
        b = {"testco-bc-many": {"removeFieldNotes": ["other"]}}
        self.assert_fails_and_writes_nothing(self.stage_md(a, b, name="e.md"),
                                             message="Conflicting values")

    def test_removals_for_different_entries_combine(self):
        self.default_tree()
        a = {"testco-bc-many": {"removeFieldNotes": ["other"]}}
        b = {"testco-ptz-only": {"removeFieldNotes": ["hasMacro"]}}
        code, out, err = self.run_main(self.stage_md(a, b, name="f.md"))
        self.assertEqual(code, 0, err)
        self.assertIn("Removed 2 fieldNotes key(s) from 2 id(s):", out)

    def test_removal_and_set_of_other_fields_in_separate_blocks(self):
        self.default_tree()
        a = {"testco-bc-many": {"removeFieldNotes": ["other"]}}
        b = {"testco-bc-many": {"weightG": 7, "fieldNotes": {"fresh": "x"}}}
        code, out, err = self.run_main(self.stage_md(a, b, name="g.md"))
        self.assertEqual(code, 0, err)
        entry = self.entries(BROADCAST_SHARD, "lenses")["testco-bc-many"]
        self.assertEqual(entry["weightG"], 7)
        self.assertEqual(entry["fieldNotes"],
                         {"hasMacro": "note a", "third": "note c", "fresh": "x"})


class UnchangedBehaviorTests(ApplyFieldsCase):
    """A map without removeFieldNotes behaves exactly as before the instruction."""

    def test_set_and_merge_without_removal_gives_the_expected_bytes_and_output(self):
        self.default_tree()
        path = self.stage_json({
            "testco-bc-many": {"weightG": 99, "fieldNotes": {"other": "changed", "fresh": "new"}},
            "testco-bc-bare": {"fieldNotes": {"added": "note"}},
            "testco-ptz-bare": {"weightG": 3},
        })
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        self.assertEqual(
            out,
            "Applied 4 field(s) to 3 id(s) across 2 shard(s):\n  %s\n  %s\n"
            % (os.path.relpath(self.path(BROADCAST_SHARD), self.root),
               os.path.relpath(self.path(PTZ_SHARD), self.root)))
        self.assertEqual(err, "")
        self.assertEqual(read_bytes(self.path(BROADCAST_SHARD)), assemble.dump_bytes({"lenses": [
            detail("testco-bc-only", fieldNotes={"hasMacro": "note a"}),
            detail("testco-bc-many", fieldNotes={"hasMacro": "note a", "other": "changed",
                                                 "third": "note c", "fresh": "new"},
                   weightG=99),
            detail("testco-bc-bare", fieldNotes={"added": "note"}),
        ]}))
        self.assertEqual(read_bytes(self.path(PTZ_SHARD)), assemble.dump_bytes({"cameras": [
            {"id": "testco-ptz-only", "fieldNotes": {"hasMacro": "note a"}},
            {"id": "testco-ptz-bare", "weightG": 3},
        ]}))

    def test_empty_fieldnotes_set_still_creates_an_empty_object(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-bare": {"fieldNotes": {}}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.entries(BROADCAST_SHARD, "lenses")["testco-bc-bare"]["fieldNotes"], {})

    def test_existing_empty_fieldnotes_are_left_alone(self):
        self.default_tree()
        path = self.stage_json({"testco-cine-empty": {"weightG": 1}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.entries(CINE_SHARD, "lenses")["testco-cine-empty"]["fieldNotes"], {})

    def test_conflicting_fieldnotes_values_still_conflict(self):
        self.default_tree()
        a = {"testco-bc-many": {"fieldNotes": {"x": "1"}}}
        b = {"testco-bc-many": {"fieldNotes": {"y": "2"}}}
        self.assert_fails_and_writes_nothing(self.stage_md(a, b, name="h.md"),
                                             message="Conflicting values")

    def test_orphan_and_partition_failures_still_write_nothing(self):
        self.default_tree()
        self.assert_fails_and_writes_nothing(
            self.stage_json({"testco-nope": {"weightG": 1}}), message="orphan")
        self.assert_fails_and_writes_nothing(
            self.stage_json({"testco-bc-only": {"manufacturer": "x"}}, "p.json"),
            message="partition")

    def test_the_instruction_is_never_stored_as_a_field(self):
        self.default_tree()
        path = self.stage_json({"testco-bc-only": {"removeFieldNotes": ["hasMacro"]}})
        self.assertEqual(self.run_main(path)[0], 0)
        for data in self.snapshot().values():
            self.assertNotIn(b"removeFieldNotes", data)


class GatesOnRemovalOnlyMapTests(ApplyFieldsCase):
    """Assemble, the attribution gate and the broadcast source gate on a map that
    only removes a fieldNote."""

    def build_tree(self):
        self.write_shard(os.path.join("source", "broadcast-lenses", "broadcast_lens_testco.json"),
                         "lenses", [{
                             "id": "testco-bc-a", "manufacturer": "Testco",
                             "model": "TA 1", "mount": "B4",
                             "sensorFormat": "twoThirdsInch"}])
        self.write_shard(BROADCAST_SHARD, "lenses", [
            detail("testco-bc-a", weightG=1000, hasMacro=False,
                   sources=["https://example.test/spec"],
                   fieldNotes={"hasMacro": "Macro available via an accessory."})])

    def run_assemble(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = assemble.main([])
        return code, err.getvalue()

    def snapshot_for_gate(self):
        return source_gate.worktree_snapshot(self.root)

    def test_assemble_attribution_and_source_gates_pass_unchanged(self):
        self.build_tree()
        code, err = self.run_assemble()
        self.assertEqual(code, 0, err)
        baseline = self.snapshot_for_gate()
        published_before = read_bytes(os.path.join(self.root, "broadcast_lens_details.json"))

        path = self.stage_json({"testco-bc-a": {"removeFieldNotes": ["hasMacro"]}})
        code, out, err = self.run_main(path)
        self.assertEqual(code, 0, err)

        code, err = self.run_assemble()
        self.assertEqual(code, 0, err)
        published_after = json.loads(read_bytes(
            os.path.join(self.root, "broadcast_lens_details.json")))
        entry = published_after["lenses"][0]
        self.assertNotIn("fieldNotes", entry)
        expected = json.loads(published_before)
        del expected["lenses"][0]["fieldNotes"]
        self.assertEqual(published_after, expected, "assembled output differs only there")

        current = self.snapshot_for_gate()
        self.assertEqual(source_gate.evaluate(current, baseline), [])
        # Control: the same gate does flag an unsourced spec change, so the
        # empty result above is a real verdict and not a gate that sees nothing.
        entry, shard = current.details["testco-bc-a"]
        changed = current._replace(details={"testco-bc-a": (dict(entry, weightG=1), shard)})
        self.assertTrue(source_gate.evaluate(changed, baseline))

        allowed = attribution_gate.load_allowlist(ATTRIBUTION_ALLOWLIST)
        found = attribution_gate.scan(self.source, os.path.join(self.root, "CHANGELOG.md"),
                                      allowed, base_dir=self.root)
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for build/build_batches.py, focused on cross-file shard pooling.

Every test builds its own inbox/output/done/logs tree under a temporary
directory (tempfile.TemporaryDirectory), and only ever writes ids and brand
or manufacturer names that do not exist anywhere in this repository's real
source/ shard data. The create_entries.py dry run invoked at the end of a
build_batches.py run reads the repository's real source/ shards (read only,
never --write) to check that staged ids are new; that read is unavoidable
(it is create_entries.py's own existing behavior, not something this test
suite adds), but no test ever writes to, moves, or otherwise touches the
real vault import pipeline or any real staging data.

Run with: python -m unittest discover -s tests -v

No em dashes appear anywhere in this file by project policy.
"""

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
BUILD_DIR = os.path.join(REPO_ROOT, "build")
LEGACY_FIXTURE_PATH = os.path.join(TESTS_DIR, "fixtures", "legacy_build_batches_reference.py")

if BUILD_DIR not in sys.path:
    sys.path.insert(0, BUILD_DIR)

import build_batches  # noqa: E402  (path set up above)


def load_legacy_module():
    """Load the pre-pooling build_batches.py snapshot as its own module.

    __file__ is patched to a path inside build/ (not the fixture's real
    location under tests/fixtures/) so its own create_entries.py dry run
    call, which derives the sibling script's path from __file__, still
    finds the real build/create_entries.py.
    """
    spec = importlib.util.spec_from_file_location("build_batches_legacy", LEGACY_FIXTURE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.__file__ = os.path.join(BUILD_DIR, "build_batches.py")
    return module


def render_markdown(sections):
    """sections: list of (heading_text, entries_list). Builds the Core/Detail
    heading plus fenced json block markdown build_batches.py expects."""
    parts = []
    for heading_text, entries in sections:
        parts.append("## %s" % heading_text)
        parts.append("```json")
        parts.append(json.dumps(entries, indent=2))
        parts.append("```")
    return "\n".join(parts) + "\n"


def ptz_core(entry_id, brand, model="Test Model"):
    return {"id": entry_id, "brand": brand, "model": model}


def ptz_details(entry_id):
    return {"id": entry_id}


def broadcast_lens_core(entry_id, manufacturer, model="Test Lens"):
    return {"id": entry_id, "manufacturer": manufacturer, "model": model,
            "sensorFormat": "twoThirdsInch", "mount": "B4"}


def broadcast_lens_details(entry_id):
    return {"id": entry_id, "lensType": "broadcast"}


def make_import_base(tmp_dir):
    base = os.path.join(tmp_dir, "import_base")
    for name in ("inbox", "output", "done", "logs"):
        os.makedirs(os.path.join(base, name))
    return base


def write_inbox_file(base, filename, text):
    with open(os.path.join(base, "inbox", filename), "w", encoding="utf-8") as handle:
        handle.write(text)


def run_main(module, argv):
    """Run module.main(argv), swallowing its stdout/stderr chatter so test
    output stays readable. Assertions read the run log file instead."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(argv)
    return code


def latest_log(base):
    """The most recently written run log. Log filenames are timestamped, so
    a base directory used for more than one main() call (as the dry run then
    real run pairing does) can hold more than one; callers always want the
    latest one, not "the only one" (two calls can land in different seconds
    on a fast runner, so there is no guarantee there is only ever one)."""
    logs_dir = os.path.join(base, "logs")
    names = sorted(n for n in os.listdir(logs_dir) if n.startswith("run-") and n.endswith(".log"))
    assert names, "expected at least one run log, found none"
    with open(os.path.join(logs_dir, names[-1]), "r", encoding="utf-8") as handle:
        return handle.read()


class CrossFilePoolingTests(unittest.TestCase):
    """Several inbox files feeding the same shard resolve to one clean batch."""

    def test_two_files_same_shard_pool_into_one_batch(self):
        brand = "ZzPoolTestBrand"
        write_inbox_file(self.base, "a_pooling.md", render_markdown([
            ("Core (ptz_cameras pooling test, file a)", [ptz_core("unittest-zz-pool-cam-a1", brand)]),
            ("Detail (ptz_details pooling test, file a)", [ptz_details("unittest-zz-pool-cam-a1")]),
        ]))
        write_inbox_file(self.base, "b_pooling.md", render_markdown([
            ("Core (ptz_cameras pooling test, file b)", [ptz_core("unittest-zz-pool-cam-b1", brand)]),
            ("Detail (ptz_details pooling test, file b)", [ptz_details("unittest-zz-pool-cam-b1")]),
        ]))

        # Dry run: writes the pooled batch, moves nothing.
        code = run_main(build_batches, ["--dry-run", self.base])
        self.assertEqual(code, 0)

        output_files = [n for n in os.listdir(os.path.join(self.base, "output")) if n.endswith(".json")]
        self.assertEqual(output_files, ["ptz_cameras_zzpooltestbrand.json"])
        with open(os.path.join(self.base, "output", output_files[0]), encoding="utf-8") as handle:
            batch = json.load(handle)
        core_ids = sorted(e["id"] for e in batch["core"]["entries"])
        details_ids = sorted(e["id"] for e in batch["details"]["entries"])
        self.assertEqual(core_ids, ["unittest-zz-pool-cam-a1", "unittest-zz-pool-cam-b1"])
        self.assertEqual(details_ids, ["unittest-zz-pool-cam-a1", "unittest-zz-pool-cam-b1"])
        self.assertEqual(set(batch.keys()), {"core", "details"})

        inbox_names = os.listdir(os.path.join(self.base, "inbox"))
        self.assertCountEqual(inbox_names, ["a_pooling.md", "b_pooling.md"])
        self.assertEqual(os.listdir(os.path.join(self.base, "done")), [])

        dry_log = latest_log(self.base)
        self.assertIn("a_pooling.md", dry_log)
        self.assertIn("b_pooling.md", dry_log)
        self.assertIn("Dry run: 2 file(s) would move to done/, none moved.", dry_log)

        # Real run over the same still-staged inbox: writes and moves both files.
        code = run_main(build_batches, [self.base])
        self.assertEqual(code, 0)

        self.assertEqual(os.listdir(os.path.join(self.base, "inbox")), [])
        self.assertCountEqual(os.listdir(os.path.join(self.base, "done")), ["a_pooling.md", "b_pooling.md"])

        log_text = latest_log(self.base)
        wrote_lines = [line for line in log_text.splitlines() if line.startswith("WROTE ")]
        self.assertEqual(len(wrote_lines), 1)
        self.assertIn("a_pooling.md", wrote_lines[0])
        self.assertIn("b_pooling.md", wrote_lines[0])
        self.assertIn("-> output/ptz_cameras_zzpooltestbrand.json (2 core, 2 details)", wrote_lines[0])
        self.assertIn("MOVED a_pooling.md -> done/", log_text)
        self.assertIn("MOVED b_pooling.md -> done/", log_text)
        self.assertIn("CREATE VALIDATION PASSED. 4 new entries across 2 shard side(s).", log_text)
        self.assertIn("Dry run, nothing written.", log_text)
        self.assertNotIn("CREATE VALIDATION FAILED", log_text)
        self.assertIn("Summary: 2 clean, 0 skipped (no blocks), 0 failed.", log_text)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = make_import_base(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()


class DuplicateIdAcrossFilesTests(unittest.TestCase):
    """A duplicate entry id across two files fails the whole run loudly."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = make_import_base(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_duplicate_core_id_across_files_fails_run(self):
        dup_id = "unittest-zz-dup-test-cam-01"
        write_inbox_file(self.base, "c_dup.md", render_markdown([
            ("Core (dup test, file c)", [ptz_core(dup_id, "ZzDupTestBrandC")]),
            ("Detail (dup test, file c)", [ptz_details(dup_id)]),
        ]))
        write_inbox_file(self.base, "d_dup.md", render_markdown([
            ("Core (dup test, file d)", [ptz_core(dup_id, "ZzDupTestBrandD")]),
            ("Detail (dup test, file d)", [ptz_details(dup_id)]),
        ]))

        code = run_main(build_batches, [self.base])
        self.assertEqual(code, 1)

        self.assertEqual(os.listdir(os.path.join(self.base, "output")), [])
        self.assertEqual(os.listdir(os.path.join(self.base, "done")), [])
        self.assertCountEqual(os.listdir(os.path.join(self.base, "inbox")), ["c_dup.md", "d_dup.md"])

        log_text = latest_log(self.base)
        self.assertIn(dup_id, log_text)
        self.assertIn("c_dup.md", log_text)
        self.assertIn("d_dup.md", log_text)
        self.assertIn("is staged more than once", log_text)
        self.assertIn("Summary: 0 clean, 0 skipped (no blocks), 2 failed.", log_text)


class SingleFileUnchangedTests(unittest.TestCase):
    """No fan-in (every shard fed by exactly one file): output stays byte
    identical to the pre-pooling implementation."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.legacy = load_legacy_module()

    def tearDown(self):
        self.tmp.cleanup()

    def _fixture_text(self):
        return render_markdown([
            ("Core (single file test, ptz)", [ptz_core("unittest-zz-single-cam-01", "ZzSingleTestBrand")]),
            ("Detail (single file test, ptz)", [ptz_details("unittest-zz-single-cam-01")]),
            ("Core (single file test, lens)", [broadcast_lens_core("unittest-zz-single-lens-01", "ZzSingleTestMfr")]),
            ("Detail (single file test, lens)", [broadcast_lens_details("unittest-zz-single-lens-01")]),
        ])

    def _filtered_log_lines(self, log_text):
        skip_prefixes = ("build_batches.py run ", "base: ")
        return [line for line in log_text.splitlines()
                if not line.startswith(skip_prefixes)]

    def test_single_file_output_matches_legacy_implementation(self):
        text = self._fixture_text()

        old_base = make_import_base(os.path.join(self.tmp.name, "old"))
        write_inbox_file(old_base, "single.md", text)
        old_code = run_main(self.legacy, [old_base])

        new_base = make_import_base(os.path.join(self.tmp.name, "new"))
        write_inbox_file(new_base, "single.md", text)
        new_code = run_main(build_batches, [new_base])

        self.assertEqual(old_code, 0)
        self.assertEqual(new_code, 0)

        old_output_dir = os.path.join(old_base, "output")
        new_output_dir = os.path.join(new_base, "output")
        old_files = sorted(os.listdir(old_output_dir))
        new_files = sorted(os.listdir(new_output_dir))
        self.assertEqual(old_files, new_files)
        self.assertEqual(len(old_files), 2)
        for name in old_files:
            with open(os.path.join(old_output_dir, name), "rb") as handle:
                old_bytes = handle.read()
            with open(os.path.join(new_output_dir, name), "rb") as handle:
                new_bytes = handle.read()
            self.assertEqual(old_bytes, new_bytes, "output/%s differs from the legacy implementation" % name)

        self.assertEqual(os.listdir(os.path.join(old_base, "done")), ["single.md"])
        self.assertEqual(os.listdir(os.path.join(new_base, "done")), ["single.md"])

        old_log = self._filtered_log_lines(latest_log(old_base))
        new_log = self._filtered_log_lines(latest_log(new_base))
        self.assertEqual(old_log, new_log)


if __name__ == "__main__":
    unittest.main()

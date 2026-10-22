#!/usr/bin/env python3
"""Tests for the devices.json schema gate in build/assemble.py.

devices.json entries may carry the optional per model field
virtualPathAllowed. The gate accepts a boolean, accepts a missing field, and
stops the build on any other value, naming the entry. The field passes
through to the published devices.json exactly as set in the source shard.

Every test builds its own synthetic repository tree (source shards, meta
files, output location) under a temporary directory and points assemble.py
at it. The real output_schema.json and legacy_whitelist.json are used, so the
tests exercise the registry as it ships. No test reads or writes the real
source/ shards or the real published outputs; every device id and model
identifier here is made up.

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

import assemble  # noqa: E402  (path set up above)

# Every meta file the assembler reads, each with every top level key any
# output asks for. Values are synthetic placeholders.
META_NAMES = sorted({out["meta"] for out in assemble.OUTPUTS})
SYNTHETIC_META = {"version": "0.0.0-test", "updatedAt": "test",
                  "verificationWarning": ["synthetic"], "notes": ["synthetic"]}


def device(entry_id, **extra):
    entry = {"id": entry_id, "marketingName": "Test Device " + entry_id,
             "modelIdentifiers": ["TestPhone1,1"],
             "cameras": [{"label": "1x", "type": "wide", "hFOVDegrees": 70.0,
                          "isDefault": True}]}
    entry.update(extra)
    return entry


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


class DevicesGateTests(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        source = os.path.join(self.root, "source")
        meta_dir = os.path.join(source, "meta")
        for name in META_NAMES:
            write_json(os.path.join(meta_dir, name), SYNTHETIC_META)
        for name, value in (("REPO_ROOT", self.root), ("SOURCE", source),
                            ("META_DIR", meta_dir)):
            patcher = mock.patch.object(assemble, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.devices_shard = os.path.join(source, "devices", "devices.json")

    def assemble_devices(self, entries):
        """Assemble the synthetic tree. Returns (exit code, stderr text)."""
        write_json(self.devices_shard, {"devices": entries})
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = assemble.main([])
        return code, err.getvalue()

    def published_devices(self):
        with open(os.path.join(self.root, "devices.json"), encoding="utf-8") as handle:
            return {e["id"]: e for e in json.load(handle)["devices"]}

    def test_non_boolean_values_stop_the_build_and_name_the_entry(self):
        for bad in ("false", "true", 0, 1, 1.5, None, [], {}):
            with self.subTest(value=bad):
                code, err = self.assemble_devices(
                    [device("unittest-device-bad", virtualPathAllowed=bad)])
                self.assertEqual(code, 1)
                self.assertIn("VALIDATION FAILED", err)
                self.assertIn("devices.json id 'unittest-device-bad'", err)
                self.assertIn("virtualPathAllowed", err)
                self.assertFalse(os.path.exists(os.path.join(self.root, "devices.json")),
                                 "nothing may be published when the gate fails")

    def test_boolean_values_pass_and_reach_the_output_unchanged(self):
        code, err = self.assemble_devices([
            device("unittest-device-true", virtualPathAllowed=True),
            device("unittest-device-false", virtualPathAllowed=False),
        ])
        self.assertEqual(code, 0, err)
        published = self.published_devices()
        self.assertIs(published["unittest-device-true"]["virtualPathAllowed"], True)
        self.assertIs(published["unittest-device-false"]["virtualPathAllowed"], False)

    def test_missing_field_passes_and_stays_absent(self):
        code, err = self.assemble_devices([device("unittest-device-plain")])
        self.assertEqual(code, 0, err)
        self.assertNotIn("virtualPathAllowed", self.published_devices()["unittest-device-plain"])

    def test_only_the_bad_entry_is_named(self):
        code, err = self.assemble_devices([
            device("unittest-device-good", virtualPathAllowed=False),
            device("unittest-device-bad", virtualPathAllowed="no"),
        ])
        self.assertEqual(code, 1)
        self.assertIn("devices.json id 'unittest-device-bad'", err)
        self.assertNotIn("unittest-device-good", err)
        self.assertIn("1 violation(s)", err)

    def test_other_device_fields_stay_ungated(self):
        code, err = self.assemble_devices(
            [device("unittest-device-extra", someFutureField={"any": "shape"})])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.published_devices()["unittest-device-extra"]["someFutureField"],
                         {"any": "shape"})


if __name__ == "__main__":
    unittest.main()

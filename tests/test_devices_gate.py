#!/usr/bin/env python3
"""Tests for the devices.json schema gate in build/assemble.py.

devices.json entries may carry the optional per model field
virtualPathAllowed. The gate accepts a boolean, accepts a missing field, and
stops the build on any other value, naming the entry. The field passes
through to the published devices.json exactly as set in the source shard.

Entries may also carry the optional per model field lensCluster: one object
per physical rear lens, keyed by camera type, with the centre position and
ring diameter in mm as seen from the back of the phone. The gate accepts a
missing field, accepts well formed values, and stops the build on malformed
ones (unknown type, type not among the entry's cameras, missing coordinate,
the same type twice, and so on).

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


def camera(cam_type, label="1x"):
    return {"label": label, "type": cam_type, "hFOVDegrees": 70.0, "isDefault": False}


def lens(lens_type, x, y, diameter=16.0):
    return {"type": lens_type, "xMM": x, "yMM": y, "diameterMM": diameter}


def multi_camera_device(entry_id, camera_types, lens_cluster=None):
    """A synthetic device with one camera per given type (repeats allowed)."""
    entry = device(entry_id)
    entry["cameras"] = [camera(t) for t in camera_types]
    if lens_cluster is not None:
        entry["lensCluster"] = lens_cluster
    return entry


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


class GateTestCase(unittest.TestCase):
    """Builds a synthetic tree per test and assembles device entries into it."""

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


class DevicesGateTests(GateTestCase):
    """The optional virtualPathAllowed field on devices.json entries."""

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


class LensClusterGateTests(GateTestCase):
    """The optional lensCluster field on devices.json entries."""

    def assert_rejected(self, entry, *expected_fragments):
        code, err = self.assemble_devices([entry])
        self.assertEqual(code, 1, err)
        self.assertIn("VALIDATION FAILED", err)
        self.assertIn("devices.json id '%s'" % entry["id"], err)
        self.assertIn("lensCluster", err)
        for fragment in expected_fragments:
            self.assertIn(fragment, err)
        self.assertFalse(os.path.exists(os.path.join(self.root, "devices.json")),
                         "nothing may be published when the gate fails")

    def triple(self, **overrides):
        cluster = [lens("ultrawide", 8.1, 8.1), lens("wide", 8.1, 27.34),
                   lens("telephoto", 26.09, 17.72)]
        return multi_camera_device("unittest-triple", ["ultrawide", "wide", "telephoto"],
                                   overrides.get("cluster", cluster))

    def dual(self, cluster):
        return multi_camera_device("unittest-dual", ["ultrawide", "wide"], cluster)

    def test_valid_triple_camera_sample_passes_and_reaches_the_output_unchanged(self):
        entry = self.triple()
        code, err = self.assemble_devices([entry])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.published_devices()["unittest-triple"]["lensCluster"],
                         entry["lensCluster"])

    def test_valid_dual_camera_sample_passes(self):
        cluster = [lens("ultrawide", 8.0, 8.0), lens("wide", 8.0, 25.72)]
        code, err = self.assemble_devices([self.dual(cluster)])
        self.assertEqual(code, 0, err)

    def test_entry_without_the_field_still_validates_and_stays_absent(self):
        code, err = self.assemble_devices(
            [multi_camera_device("unittest-plain", ["ultrawide", "wide"])])
        self.assertEqual(code, 0, err)
        self.assertNotIn("lensCluster", self.published_devices()["unittest-plain"])

    def test_telephoto_lens_is_valid_when_cameras_list_telephoto_twice(self):
        entry = multi_camera_device(
            "unittest-crop", ["ultrawide", "wide", "telephoto", "telephoto"],
            [lens("ultrawide", 8.1, 8.1), lens("wide", 8.1, 27.34),
             lens("telephoto", 26.09, 17.72)])
        code, err = self.assemble_devices([entry])
        self.assertEqual(code, 0, err)

    def test_unknown_camera_type_is_rejected(self):
        entry = self.dual([lens("ultrawide", 8.0, 8.0), lens("macro", 8.0, 25.72)])
        entry["cameras"].append(camera("macro"))
        self.assert_rejected(entry, "macro")

    def test_type_not_among_the_entry_cameras_is_rejected(self):
        cluster = [lens("ultrawide", 8.0, 8.0), lens("telephoto", 8.0, 25.72)]
        self.assert_rejected(self.dual(cluster), "telephoto", "not among")

    def test_missing_coordinate_is_rejected(self):
        for key in ("type", "xMM", "yMM", "diameterMM"):
            with self.subTest(missing=key):
                broken = lens("wide", 8.0, 25.72)
                del broken[key]
                self.assert_rejected(self.dual([lens("ultrawide", 8.0, 8.0), broken]),
                                     key)

    def test_same_type_twice_is_rejected(self):
        cluster = [lens("ultrawide", 8.0, 8.0), lens("ultrawide", 8.0, 25.72)]
        self.assert_rejected(self.dual(cluster), "ultrawide", "twice")

    def test_non_numeric_coordinates_are_rejected(self):
        for key in ("xMM", "yMM", "diameterMM"):
            for bad in ("8.0", True, None, [], {}):
                with self.subTest(key=key, value=bad):
                    broken = lens("wide", 8.0, 25.72)
                    broken[key] = bad
                    self.assert_rejected(
                        self.dual([lens("ultrawide", 8.0, 8.0), broken]), key)

    def test_negative_position_is_rejected(self):
        for key in ("xMM", "yMM"):
            with self.subTest(key=key):
                broken = lens("wide", 8.0, 25.72)
                broken[key] = -0.5
                self.assert_rejected(self.dual([lens("ultrawide", 8.0, 8.0), broken]), key)

    def test_zero_or_negative_diameter_is_rejected(self):
        for bad in (0, 0.0, -16.0):
            with self.subTest(diameter=bad):
                broken = lens("wide", 8.0, 25.72, bad)
                self.assert_rejected(self.dual([lens("ultrawide", 8.0, 8.0), broken]),
                                     "diameterMM")

    def test_non_finite_numbers_are_rejected(self):
        for bad in (float("nan"), float("inf")):
            with self.subTest(value=bad):
                broken = lens("wide", bad, 25.72)
                self.assert_rejected(self.dual([lens("ultrawide", 8.0, 8.0), broken]),
                                     "xMM")

    def test_fewer_than_two_lenses_is_rejected(self):
        for cluster in ([], [lens("wide", 8.0, 8.0)]):
            with self.subTest(count=len(cluster)):
                self.assert_rejected(self.dual(cluster))

    def test_non_array_value_is_rejected(self):
        for bad in ({}, "ultrawide", 3, None, lens("wide", 8.0, 8.0)):
            with self.subTest(value=bad):
                entry = self.dual([])
                entry["lensCluster"] = bad
                self.assert_rejected(entry)

    def test_unknown_key_inside_a_lens_is_rejected(self):
        broken = lens("wide", 8.0, 25.72)
        broken["x"] = 8.0
        self.assert_rejected(self.dual([lens("ultrawide", 8.0, 8.0), broken]), "'x'")

    def test_only_the_bad_entry_is_named(self):
        good = self.dual([lens("ultrawide", 8.0, 8.0), lens("wide", 8.0, 25.72)])
        bad = self.dual([lens("ultrawide", 8.0, 8.0), lens("ultrawide", 8.0, 25.72)])
        bad["id"] = "unittest-dual-bad"
        code, err = self.assemble_devices([good, bad])
        self.assertEqual(code, 1)
        self.assertIn("devices.json id 'unittest-dual-bad'", err)
        self.assertNotIn("id 'unittest-dual'", err)


if __name__ == "__main__":
    unittest.main()

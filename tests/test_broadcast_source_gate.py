#!/usr/bin/env python3
"""Tests for the broadcast source gate in build/broadcast_source_gate.py.

The gate refuses a broadcast spec value that is set or changed without a new
source in the same change, and refuses a new entry with spec values and an empty
source list. It never judges unchanged values, never refuses a move to null or
"unknown", and ignores fields that are not spec values.

Two layers. The first tests the pure judgement (evaluate) on in-memory
snapshots. The second builds throwaway git repositories in a temporary
directory (with a local bare repository as origin) and tests baseline choice,
feature branch versus main, the first run, a stale baseline, and the CLI exit
codes. Every entry id, manufacturer, URL and value here is made up; no test
reads the real source/ shards. The real output_schema.json is read, only to pin
the spec field list.

Run with: python -m unittest discover -s tests -v

No em dashes appear anywhere in this file by project policy.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
BUILD_DIR = os.path.join(REPO_ROOT, "build")

if BUILD_DIR not in sys.path:
    sys.path.insert(0, BUILD_DIR)

import broadcast_source_gate as gate  # noqa: E402  (path set up above)
import field_registry  # noqa: E402

SRC_A = "https://example.test/spec-a"
SRC_B = "https://example.test/spec-b"
SRC_C = "https://example.test/spec-c"

CORE_FILE = "source/broadcast-lenses/broadcast_lens_synth.json"
DETAILS_FILE = "source/broadcast-details/broadcast_details_synth.json"
OTHER_CORE_FILE = "source/broadcast-lenses/broadcast_lens_other.json"
OTHER_DETAILS_FILE = "source/broadcast-details/broadcast_details_other.json"


def core(entry_id, **extra):
    entry = {"id": entry_id, "manufacturer": "Synth", "model": "Model " + entry_id,
             "series": "S", "generation": "HD", "focalLengthMin": 5.0,
             "focalLengthMax": 50.0, "zoomRatio": 10.0, "extenderFactor": 1.0,
             "sensorFormat": "twoThirdsInch", "mount": "B4", "isPTZ": False,
             "isFree": False, "isCustom": False, "addedDate": None}
    entry.update(extra)
    return entry


def detail(entry_id, sources=(SRC_A,), web_sources=None, **extra):
    entry = {"id": entry_id, "lensType": "broadcast", "weightG": 2000, "lengthMm": 200.0,
             "closeFocusM": None, "hasMacro": None, "filterType": None,
             "sources": list(sources),
             "webSources": list(sources if web_sources is None else web_sources),
             "description": "Synthetic description."}
    entry.update(extra)
    return entry


def snap(cores=(), details=(), acks=()):
    return gate.Snapshot(
        {e["id"]: (e, CORE_FILE) for e in cores},
        {e["id"]: (e, DETAILS_FILE) for e in details},
        list(acks))


def verdict(current, baseline):
    """The (id, field) pairs refused for a change from baseline to current."""
    return [(v.entry_id, v.field) for v in gate.evaluate(current, baseline)]


class SpecFieldList(unittest.TestCase):
    """The spec list is derived from the schema and pinned here."""

    CORE_SPEC = {"generation", "focalLengthMin", "focalLengthMax", "zoomRatio",
                 "extenderFactor"}
    DETAILS_SPEC = {
        "weightG", "lengthMm", "frontDiameterMm", "maximumDiameterMm", "closeFocusM",
        "imageCircleMm", "opticalElements", "introductionYear", "maxApertureWide",
        "maxApertureTele", "apertureType", "hasIS", "hasMacro", "hasServoZoom",
        "hasServoFocus", "servoConnector", "formFactor", "filterType", "filterThreadMm",
        "isParfocal", "hasFocusBreathing"}

    def test_list_matches_the_approved_list(self):
        core_spec, details_spec = gate.spec_fields()
        self.assertEqual(set(core_spec), self.CORE_SPEC)
        self.assertEqual(set(details_spec), self.DETAILS_SPEC)

    def test_every_schema_field_is_classified_exactly_once(self):
        # A field added to the schema changes the derived list and fails the test
        # above until it is classified. Stale entries on the non spec lists fail here.
        for def_name, non_spec in ((gate.CORE_DEF, gate.NON_SPEC_CORE),
                                   (gate.DETAILS_DEF, gate.NON_SPEC_DETAILS)):
            allowed = field_registry.allowlist(def_name)
            self.assertTrue(non_spec <= allowed, "stale non spec field in " + def_name)

    def test_sensor_format_and_mount_are_not_spec_fields(self):
        core_spec, _ = gate.spec_fields()
        self.assertNotIn("sensorFormat", core_spec)
        self.assertNotIn("mount", core_spec)
        self.assertIn("generation", core_spec)


class RefusedChanges(unittest.TestCase):
    """Points 1 and 4: a spec value without its source is refused."""

    def test_detail_value_changed_without_new_source(self):
        base = snap(details=[detail("synth-a", weightG=2000)])
        cur = snap(details=[detail("synth-a", weightG=2250)])
        self.assertEqual(verdict(cur, base), [("synth-a", "weightG")])

    def test_detail_value_filled_without_new_source(self):
        # The May 2026 case: the entry has sources, the new value brought none.
        base = snap(details=[detail("synth-a", lengthMm=None)])
        cur = snap(details=[detail("synth-a", lengthMm=210.0)])
        self.assertEqual(verdict(cur, base), [("synth-a", "lengthMm")])

    def test_detail_field_absent_in_baseline_then_set(self):
        base_entry = detail("synth-a")
        del base_entry["weightG"]
        base = snap(details=[base_entry])
        cur = snap(details=[detail("synth-a", weightG=1800)])
        self.assertEqual(verdict(cur, base), [("synth-a", "weightG")])

    def test_value_moved_from_unknown_to_a_value_is_a_set(self):
        base = snap(details=[detail("synth-a", opticalElements="unknown")])
        cur = snap(details=[detail("synth-a", opticalElements=14)])
        self.assertEqual(verdict(cur, base), [("synth-a", "opticalElements")])

    def test_boolean_is_not_equal_to_integer(self):
        base = snap(details=[detail("synth-a", hasIS=True)])
        cur = snap(details=[detail("synth-a", hasIS=1)])
        self.assertEqual(verdict(cur, base), [("synth-a", "hasIS")])

    def test_core_value_changed_without_detail_source(self):
        base = snap(cores=[core("synth-a")], details=[detail("synth-a")])
        cur = snap(cores=[core("synth-a", focalLengthMax=55.0)], details=[detail("synth-a")])
        self.assertEqual(verdict(cur, base), [("synth-a", "focalLengthMax")])

    def test_core_generation_change_is_gated(self):
        base = snap(cores=[core("synth-a")], details=[detail("synth-a")])
        cur = snap(cores=[core("synth-a", generation="4K UHD")], details=[detail("synth-a")])
        self.assertEqual(verdict(cur, base), [("synth-a", "generation")])

    def test_core_change_with_no_paired_detail(self):
        base = snap(cores=[core("synth-a")])
        cur = snap(cores=[core("synth-a", zoomRatio=12.0)])
        violations = gate.evaluate(cur, base)
        self.assertEqual([(v.entry_id, v.field, v.reason) for v in violations],
                         [("synth-a", "zoomRatio", gate.REASON_CORE_NO_DETAIL)])

    def test_new_detail_entry_with_values_and_empty_source_list(self):
        cur = snap(details=[detail("synth-new", sources=())])
        violations = gate.evaluate(cur, snap())
        self.assertTrue(violations)
        self.assertTrue(all(v.reason == gate.REASON_NEW_EMPTY for v in violations))
        self.assertIn(("synth-new", "weightG"), [(v.entry_id, v.field) for v in violations])

    def test_new_entry_with_only_blank_source_strings_is_empty(self):
        cur = snap(details=[detail("synth-new", sources=("  ",), web_sources=("",))])
        self.assertTrue(gate.evaluate(cur, snap()))

    def test_new_core_entry_whose_detail_has_no_source(self):
        cur = snap(cores=[core("synth-new")], details=[detail("synth-new", sources=())])
        pairs = [(v.file, v.entry_id) for v in gate.evaluate(cur, snap())
                 if v.file == CORE_FILE]
        self.assertTrue(pairs)

    def test_a_new_entry_cannot_be_rescued_by_an_ack(self):
        ack = {"id": "synth-new", "field": "weightG", "value": 2000, "source": SRC_A}
        cur = snap(details=[detail("synth-new", sources=())], acks=[ack])
        self.assertIn(("synth-new", "weightG"), verdict(cur, snap()))

    def test_source_added_to_a_different_entry_does_not_count(self):
        base = snap(details=[detail("synth-a"), detail("synth-b")])
        cur = snap(details=[detail("synth-a", weightG=2250),
                            detail("synth-b", sources=(SRC_A, SRC_B))])
        self.assertEqual(verdict(cur, base), [("synth-a", "weightG")])


class AcceptedChanges(unittest.TestCase):
    """Points 2, 3, 5 and 6: what the gate lets through."""

    def test_value_change_with_a_new_source(self):
        base = snap(details=[detail("synth-a", weightG=2000)])
        cur = snap(details=[detail("synth-a", weightG=2250, sources=(SRC_A, SRC_B),
                                   web_sources=(SRC_A,))])
        self.assertEqual(verdict(cur, base), [])

    def test_new_source_only_in_web_sources_counts(self):
        base = snap(details=[detail("synth-a")])
        cur = snap(details=[detail("synth-a", weightG=2250, web_sources=(SRC_A, SRC_B))])
        self.assertEqual(verdict(cur, base), [])

    def test_new_entry_with_a_source(self):
        cur = snap(cores=[core("synth-new")], details=[detail("synth-new")])
        self.assertEqual(verdict(cur, snap()), [])

    def test_new_entry_with_no_spec_values_and_no_source(self):
        bare = {"id": "synth-new", "lensType": "broadcast", "sources": [], "webSources": [],
                "weightG": None, "lengthMm": "unknown"}
        self.assertEqual(verdict(snap(details=[bare]), snap()), [])

    def test_move_to_null_is_never_refused(self):
        base = snap(details=[detail("synth-a", weightG=2000, hasMacro=True)])
        cur = snap(details=[detail("synth-a", weightG=None, hasMacro=None)])
        self.assertEqual(verdict(cur, base), [])

    def test_move_to_unknown_is_never_refused(self):
        base = snap(details=[detail("synth-a", opticalElements=12)])
        cur = snap(details=[detail("synth-a", opticalElements="unknown")])
        self.assertEqual(verdict(cur, base), [])

    def test_removed_field_is_never_refused(self):
        base_entry = detail("synth-a")
        cur_entry = detail("synth-a")
        del cur_entry["weightG"]
        self.assertEqual(verdict(snap(details=[cur_entry]), snap(details=[base_entry])), [])

    def test_removing_a_value_and_a_source_together_is_never_refused(self):
        base = snap(details=[detail("synth-a", sources=(SRC_A, SRC_B))])
        cur = snap(details=[detail("synth-a", weightG=None, sources=(SRC_A,))])
        self.assertEqual(verdict(cur, base), [])

    def test_removed_entry_is_never_judged(self):
        self.assertEqual(verdict(snap(), snap(cores=[core("synth-a")],
                                              details=[detail("synth-a")])), [])

    def test_unchanged_values_are_never_judged_whatever_their_source_state(self):
        # Existing values on an entry whose only source is unrelated, and on an entry
        # with no sources at all, are left alone when nothing changes.
        entries = [detail("synth-a"), detail("synth-b", sources=())]
        same = snap(cores=[core("synth-a"), core("synth-b")], details=entries)
        self.assertEqual(verdict(same, same), [])

    def test_integer_and_float_forms_of_one_number_are_unchanged(self):
        base = snap(details=[detail("synth-a", weightG=2000)])
        cur = snap(details=[detail("synth-a", weightG=2000.0)])
        self.assertEqual(verdict(cur, base), [])

    def test_non_spec_fields_do_not_trigger_the_gate(self):
        base = snap(cores=[core("synth-a")],
                    details=[detail("synth-a", sources=(SRC_A,))])
        cur = snap(
            cores=[core("synth-a", notes="Edited note.", manufacturer="Synth2",
                        model="New model", series="T", sensorFormat="halfInch", mount="PL",
                        isPTZ=True, isFree=True, isCustom=True, addedDate="2026-01-01")],
            details=[detail("synth-a", description="Edited.", productUrl="https://x.test/p",
                            manufacturerUrl="https://x.test/m",
                            fieldNotes={"weightG": "Edited."}, lensType="cine",
                            sources=(SRC_A, SRC_B))])
        self.assertEqual(verdict(cur, base), [])

    def test_changing_the_source_fields_alone_is_fine(self):
        base = snap(details=[detail("synth-a", sources=(SRC_A, SRC_B))])
        cur = snap(details=[detail("synth-a", sources=(SRC_C,))])
        self.assertEqual(verdict(cur, base), [])

    def test_core_change_with_a_new_source_on_the_paired_detail(self):
        base = snap(cores=[core("synth-a")], details=[detail("synth-a")])
        cur = snap(cores=[core("synth-a", focalLengthMin=4.5)],
                   details=[detail("synth-a", sources=(SRC_A, SRC_B))])
        self.assertEqual(verdict(cur, base), [])


class Acknowledgements(unittest.TestCase):
    """Point 2: a correction whose supporting source is already listed."""

    def setUp(self):
        self.base = snap(details=[detail("synth-a", weightG=2000, sources=(SRC_A, SRC_B))])

    def cur(self, acks, weight=2250):
        return snap(details=[detail("synth-a", weightG=weight, sources=(SRC_A, SRC_B))],
                    acks=acks)

    def test_a_new_ack_with_a_listed_source_accepts_the_change(self):
        ack = {"id": "synth-a", "field": "weightG", "value": 2250, "source": SRC_B}
        self.assertEqual(verdict(self.cur([ack]), self.base), [])

    def test_ack_value_must_equal_the_new_value(self):
        ack = {"id": "synth-a", "field": "weightG", "value": 2100, "source": SRC_B}
        self.assertEqual(verdict(self.cur([ack]), self.base), [("synth-a", "weightG")])

    def test_ack_source_must_be_in_the_source_list(self):
        ack = {"id": "synth-a", "field": "weightG", "value": 2250, "source": SRC_C}
        self.assertEqual(verdict(self.cur([ack]), self.base), [("synth-a", "weightG")])

    def test_ack_must_name_the_right_id_and_field(self):
        wrong_id = {"id": "synth-z", "field": "weightG", "value": 2250, "source": SRC_B}
        wrong_field = {"id": "synth-a", "field": "lengthMm", "value": 2250, "source": SRC_B}
        self.assertEqual(verdict(self.cur([wrong_id, wrong_field]), self.base),
                         [("synth-a", "weightG")])

    def test_an_ack_already_in_the_baseline_is_not_a_trace_of_this_change(self):
        ack = {"id": "synth-a", "field": "weightG", "value": 2250, "source": SRC_B}
        base = snap(details=[detail("synth-a", weightG=2000, sources=(SRC_A, SRC_B))],
                    acks=[ack])
        self.assertEqual(verdict(self.cur([ack]), base), [("synth-a", "weightG")])

    def test_ack_covers_only_its_own_field(self):
        base = snap(details=[detail("synth-a", weightG=2000, lengthMm=200.0,
                                    sources=(SRC_A, SRC_B))])
        cur = snap(details=[detail("synth-a", weightG=2250, lengthMm=210.0,
                                   sources=(SRC_A, SRC_B))],
                   acks=[{"id": "synth-a", "field": "weightG", "value": 2250,
                          "source": SRC_B}])
        self.assertEqual(verdict(cur, base), [("synth-a", "lengthMm")])

    def test_core_ack_uses_the_source_list_of_the_paired_detail(self):
        base = snap(cores=[core("synth-a")], details=[detail("synth-a", sources=(SRC_A,))])
        ack = {"id": "synth-a", "field": "focalLengthMax", "value": 55.0, "source": SRC_A}
        cur = snap(cores=[core("synth-a", focalLengthMax=55.0)],
                   details=[detail("synth-a", sources=(SRC_A,))], acks=[ack])
        self.assertEqual(verdict(cur, base), [])

    def test_malformed_acks_are_a_gate_error(self):
        for bad in (["not an object"], [{"id": "a", "field": "b", "value": 1}],
                    [{"id": "a", "field": "b", "value": 1, "source": 5}],
                    [{"id": "a", "field": "b", "value": 1, "source": "s", "extra": 1}]):
            with self.assertRaises(gate.GateError):
                gate.parse_acks({"acks": bad}, "acks")
        with self.assertRaises(gate.GateError):
            gate.parse_acks({"wrong": []}, "acks")
        self.assertEqual(gate.parse_acks(None, "acks"), [])


class UnhappyPaths(unittest.TestCase):
    """Point 8, at the judgement level."""

    def test_value_change_plus_unrelated_source_removal_is_refused(self):
        base = snap(details=[detail("synth-a", weightG=2000, sources=(SRC_A, SRC_B))])
        cur = snap(details=[detail("synth-a", weightG=2250, sources=(SRC_A,))])
        self.assertEqual(verdict(cur, base), [("synth-a", "weightG")])

    def test_value_change_plus_a_replaced_source_is_sourced(self):
        base = snap(details=[detail("synth-a", weightG=2000, sources=(SRC_A, SRC_B))])
        cur = snap(details=[detail("synth-a", weightG=2250, sources=(SRC_A, SRC_C))])
        self.assertEqual(verdict(cur, base), [])

    def test_a_source_moved_between_lists_is_not_a_new_source(self):
        base = snap(details=[detail("synth-a", sources=(SRC_A,), web_sources=())])
        cur = snap(details=[detail("synth-a", weightG=2250, sources=(), web_sources=(SRC_A,))])
        self.assertEqual(verdict(cur, base), [("synth-a", "weightG")])

    def test_core_focal_length_with_source_on_the_paired_detail(self):
        base = snap(cores=[core("synth-a")], details=[detail("synth-a")])
        no_source = snap(cores=[core("synth-a", focalLengthMax=60.0)],
                         details=[detail("synth-a")])
        with_source = snap(cores=[core("synth-a", focalLengthMax=60.0)],
                           details=[detail("synth-a", sources=(SRC_A, SRC_C))])
        self.assertEqual(verdict(no_source, base), [("synth-a", "focalLengthMax")])
        self.assertEqual(verdict(with_source, base), [])

    def test_a_change_touching_many_entries_reports_every_one(self):
        ids = ["synth-%02d" % n for n in range(40)]
        base = snap(cores=[core(i) for i in ids], details=[detail(i) for i in ids])
        cur = snap(cores=[core(i, focalLengthMax=70.0) for i in ids],
                   details=[detail(i, weightG=2500) for i in ids])
        violations = gate.evaluate(cur, base)
        self.assertEqual(len(violations), 80)
        self.assertEqual({v.entry_id for v in violations}, set(ids))

    def test_an_entry_moved_between_shards_is_matched_by_id(self):
        moved = detail("synth-a")
        base = gate.Snapshot({}, {"synth-a": (moved, DETAILS_FILE)}, [])
        cur = gate.Snapshot({}, {"synth-a": (dict(moved), OTHER_DETAILS_FILE)}, [])
        self.assertEqual(gate.evaluate(cur, base), [])

    def test_report_names_file_id_field_and_what_is_missing(self):
        base = snap(cores=[core("synth-a")], details=[detail("synth-a", weightG=2000)])
        cur = snap(cores=[core("synth-a", focalLengthMax=55.0)],
                   details=[detail("synth-a", weightG=2250)])
        report = gate.format_report(gate.evaluate(cur, base), "db-v0 (abc1234)")
        self.assertIn(DETAILS_FILE + " | synth-a | weightG: 2000 -> 2250", report)
        self.assertIn(CORE_FILE + " | synth-a | focalLengthMax: 50.0 -> 55.0", report)
        self.assertIn("gained no new source", report)
        self.assertIn(DETAILS_FILE, report.split("focalLengthMax")[1])
        self.assertIn("broadcast_source_acks.json", report)
        self.assertNotIn(chr(0x2014), report)
        self.assertNotIn(chr(0x2013), report)


# --------------------------------------------------------------------------
# Git level tests.
# --------------------------------------------------------------------------


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


class GitRepo:
    """A throwaway git repository with synthetic shards."""

    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)

    def git(self, *args, check=True):
        proc = subprocess.run(["git"] + list(args), cwd=self.path, capture_output=True,
                              text=True)
        if check and proc.returncode != 0:
            raise AssertionError("git %s failed: %s" % (" ".join(args), proc.stderr))
        return proc.stdout.strip()

    def init(self):
        self.git("init", "-q", "-b", "main")
        for key, value in (("user.name", "Test"), ("user.email", "test@example.test"),
                           ("core.autocrlf", "false"), ("commit.gpgsign", "false"),
                           ("tag.gpgsign", "false")):
            self.git("config", key, value)

    def write_shards(self, cores, details, acks=None):
        write_json(os.path.join(self.path, *CORE_FILE.split("/")), {"lenses": cores})
        write_json(os.path.join(self.path, *DETAILS_FILE.split("/")), {"lenses": details})
        if acks is not None:
            write_json(os.path.join(self.path, *gate.ACKS_PATH.split("/")), {"acks": acks})

    def commit(self, message="change"):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")


class GitCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        self.repo = GitRepo(os.path.join(self.tmp, "work"))
        self.repo.init()
        self.repo.write_shards([core("synth-a")], [detail("synth-a", weightG=2000)])
        self.repo.commit("base")

    def run_gate(self, base=None, remote_check=False, env=None):
        out, err = io.StringIO(), io.StringIO()
        code = gate.run(self.repo.path, base, remote_check, env if env is not None else {},
                        out, err)
        return code, out.getvalue(), err.getvalue()

    def add_origin(self):
        bare = os.path.join(self.tmp, "origin.git")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", bare], check=True,
                       capture_output=True)
        self.repo.git("remote", "add", "origin", bare)
        self.repo.git("push", "-q", "origin", "main")
        self.repo.git("fetch", "-q", "origin")
        return bare

    def bad_change(self):
        self.repo.write_shards([core("synth-a")], [detail("synth-a", weightG=2250)])

    def good_change(self):
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=2250, sources=(SRC_A, SRC_B))])


class FeatureBranchBaseline(GitCase):
    def test_feature_branch_change_without_source_is_refused(self):
        self.add_origin()
        self.repo.git("switch", "-q", "-c", "feature")
        self.bad_change()
        self.repo.commit("unsourced")
        code, _out, err = self.run_gate()
        self.assertEqual(code, 1)
        self.assertIn(DETAILS_FILE + " | synth-a | weightG: 2000 -> 2250", err)
        self.assertIn("merge-base with origin/main", err)

    def test_feature_branch_change_with_source_passes(self):
        self.add_origin()
        self.repo.git("switch", "-q", "-c", "feature")
        self.good_change()
        self.repo.commit("sourced")
        code, out, _err = self.run_gate()
        self.assertEqual(code, 0)
        self.assertIn("passed", out)

    def test_two_commits_judge_the_net_change(self):
        self.add_origin()
        self.repo.git("switch", "-q", "-c", "feature")
        self.bad_change()
        self.repo.commit("value first")
        self.good_change()
        self.repo.commit("source second")
        self.assertEqual(self.run_gate()[0], 0)

    def test_uncommitted_working_tree_change_is_judged(self):
        self.add_origin()
        self.repo.git("switch", "-q", "-c", "feature")
        self.bad_change()
        self.assertEqual(self.run_gate()[0], 1)

    def test_pull_request_event_uses_the_base_branch(self):
        self.add_origin()
        self.repo.git("switch", "-q", "-c", "feature")
        self.bad_change()
        self.repo.commit("unsourced")
        env = {"GITHUB_BASE_REF": "main", "CI": "true"}
        self.assertEqual(self.run_gate(env=env)[0], 1)

    def test_move_to_null_on_a_branch_passes(self):
        self.add_origin()
        self.repo.git("switch", "-q", "-c", "feature")
        self.repo.write_shards([core("synth-a")], [detail("synth-a", weightG=None)])
        self.repo.commit("remove unsourced value")
        self.assertEqual(self.run_gate()[0], 0)

    def test_new_entry_with_empty_source_list_is_refused(self):
        self.add_origin()
        self.repo.git("switch", "-q", "-c", "feature")
        self.repo.write_shards([core("synth-a"), core("synth-b")],
                               [detail("synth-a", weightG=2000), detail("synth-b", sources=())])
        self.repo.commit("new entry")
        code, _out, err = self.run_gate()
        self.assertEqual(code, 1)
        self.assertIn("synth-b", err)
        self.assertIn("source list", err)

    def test_ack_added_in_the_same_change_passes(self):
        self.add_origin()
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=2000, sources=(SRC_A, SRC_B))])
        self.repo.commit("second source on main")
        self.repo.git("push", "-q", "origin", "main")
        self.repo.git("switch", "-q", "-c", "feature")
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=2250, sources=(SRC_A, SRC_B))],
                               acks=[{"id": "synth-a", "field": "weightG", "value": 2250,
                                      "source": SRC_B}])
        self.repo.commit("correction with ack")
        self.assertEqual(self.run_gate()[0], 0)

    def test_many_entries_in_one_change_are_all_reported(self):
        ids = ["synth-%02d" % n for n in range(30)]
        self.repo.write_shards([core(i) for i in ids], [detail(i) for i in ids])
        self.repo.commit("many entries on main")
        self.add_origin()
        self.repo.git("switch", "-q", "-c", "feature")
        self.repo.write_shards([core(i) for i in ids], [detail(i, weightG=2500) for i in ids])
        self.repo.commit("bulk change")
        code, _out, err = self.run_gate()
        self.assertEqual(code, 1)
        for entry_id in ids:
            self.assertIn(" | %s | weightG" % entry_id, err)


class MainBaseline(GitCase):
    """A push to main is judged against the latest release tag."""

    MAIN = {"GITHUB_REF": "refs/heads/main", "GITHUB_REF_NAME": "main"}

    def setUp(self):
        super().setUp()
        self.repo.git("tag", "db-v1")
        self.repo.write_shards([core("synth-a")], [detail("synth-a", weightG=2000, lengthMm=1.0)])
        self.repo.commit("more base")
        self.repo.git("tag", "db-v2")

    def test_unsourced_change_on_main_is_refused_against_the_tag(self):
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=2250, lengthMm=1.0)])
        self.repo.commit("direct push")
        code, _out, err = self.run_gate(env=self.MAIN)
        self.assertEqual(code, 1)
        self.assertIn("baseline: db-v2", err)

    def test_a_bad_commit_stays_judged_until_it_is_fixed(self):
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=2250, lengthMm=1.0)])
        self.repo.commit("bad direct push, release blocked")
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=2250, lengthMm=1.0, description="x")])
        self.repo.commit("unrelated follow up")
        self.assertEqual(self.run_gate(env=self.MAIN)[0], 1)
        self.repo.write_shards(
            [core("synth-a")],
            [detail("synth-a", weightG=2250, lengthMm=1.0, sources=(SRC_A, SRC_B))])
        self.repo.commit("fix: add the source")
        self.assertEqual(self.run_gate(env=self.MAIN)[0], 0)

    def test_a_fix_that_removes_the_value_passes(self):
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=2250, lengthMm=1.0)])
        self.repo.commit("bad")
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=None, lengthMm=1.0)])
        self.repo.commit("revert to unknown")
        self.assertEqual(self.run_gate(env=self.MAIN)[0], 0)

    def test_current_main_with_no_change_passes(self):
        self.assertEqual(self.run_gate(env=self.MAIN)[0], 0)

    def test_the_highest_release_number_wins_not_the_alphabetical_one(self):
        self.repo.git("tag", "db-v10")
        code, out, _err = self.run_gate(env=self.MAIN)
        self.assertEqual(code, 0)
        self.assertIn("db-v10", out)


class NoBaseline(GitCase):
    """Point 8: the very first run with nothing to compare against."""

    def test_first_run_locally_passes_with_a_notice(self):
        code, out, _err = self.run_gate(env={"GITHUB_REF": "refs/heads/main",
                                             "GITHUB_REF_NAME": "main"})
        self.assertEqual(code, 0)
        self.assertIn("no baseline", out)

    def test_first_run_in_ci_fails_closed(self):
        code, _out, err = self.run_gate(env={"CI": "true", "GITHUB_REF": "refs/heads/main",
                                             "GITHUB_REF_NAME": "main"})
        self.assertEqual(code, 2)
        self.assertIn("fails closed", err)

    def test_branch_with_no_main_at_all_is_a_no_baseline_case(self):
        self.repo.git("switch", "-q", "-c", "feature")
        self.repo.git("branch", "-q", "-m", "main", "elsewhere")
        self.assertEqual(self.run_gate()[0], 0)
        self.assertEqual(self.run_gate(env={"CI": "1"})[0], 2)

    def test_unresolvable_explicit_base_is_a_gate_error(self):
        code, _out, err = self.run_gate(base="no-such-ref")
        self.assertEqual(code, 2)
        self.assertIn("no-such-ref", err)

    def test_explicit_base_is_used(self):
        self.bad_change()
        self.assertEqual(self.run_gate(base="HEAD")[0], 1)
        self.repo.commit("bad")
        self.assertEqual(self.run_gate(base="HEAD")[0], 0)

    def test_invalid_shard_json_is_a_gate_error(self):
        path = os.path.join(self.repo.path, *CORE_FILE.split("/"))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{ not json")
        code, _out, err = self.run_gate(base="HEAD")
        self.assertEqual(code, 2)
        self.assertIn("Invalid JSON", err)


class StaleBaseline(GitCase):
    """A local run must not judge changes that are already released."""

    MAIN = MainBaseline.MAIN

    def make_remote_ahead(self):
        """Origin gets db-v2 and a newer main from another clone; this repo stays behind."""
        self.repo.git("tag", "db-v1")
        bare = self.add_origin()
        self.repo.git("push", "-q", "origin", "db-v1")
        other = GitRepo(os.path.join(self.tmp, "other"))
        subprocess.run(["git", "clone", "-q", bare, other.path], check=True,
                       capture_output=True)
        for key, value in (("user.name", "Test"), ("user.email", "test@example.test"),
                           ("commit.gpgsign", "false"), ("tag.gpgsign", "false")):
            other.git("config", key, value)
        other.write_shards([core("synth-a")],
                           [detail("synth-a", weightG=2250, sources=(SRC_A, SRC_B))])
        other.commit("released change")
        other.git("tag", "db-v2")
        other.git("push", "-q", "origin", "main", "db-v2")

    def test_local_tags_behind_the_remote_are_refused_with_a_clear_message(self):
        self.make_remote_ahead()
        # Local main catches up by commits but the tags were never fetched.
        self.repo.git("pull", "-q", "--no-tags", "origin", "main")
        code, _out, err = self.run_gate(remote_check=True, env=self.MAIN)
        self.assertEqual(code, 2)
        self.assertIn("behind the remote", err)
        self.assertIn("db-v1", err)
        self.assertIn("db-v2", err)
        self.assertIn("git fetch --tags", err)

    def test_after_fetching_the_tags_the_released_change_is_not_judged(self):
        self.make_remote_ahead()
        self.repo.git("pull", "-q", "--no-tags", "origin", "main")
        self.repo.git("fetch", "-q", "--tags", "origin")
        code, out, _err = self.run_gate(remote_check=True, env=self.MAIN)
        self.assertEqual(code, 0)
        self.assertIn("db-v2", out)

    def test_stale_tags_refuse_even_when_local_commits_sit_on_top(self):
        self.make_remote_ahead()
        self.repo.git("pull", "-q", "--no-tags", "origin", "main")
        self.repo.write_shards([core("synth-a")],
                               [detail("synth-a", weightG=2250, sources=(SRC_A, SRC_B),
                                       lengthMm=300.0)])
        self.repo.commit("local unsourced length on top of release")
        self.assertEqual(self.run_gate(remote_check=True, env=self.MAIN)[0], 2)

    def test_stale_origin_main_is_refused_on_a_feature_branch(self):
        self.make_remote_ahead()
        self.repo.git("switch", "-q", "-c", "feature")
        code, _out, err = self.run_gate(remote_check=True)
        self.assertEqual(code, 2)
        self.assertIn("behind the remote", err)
        self.repo.git("fetch", "-q", "origin")
        self.assertNotEqual(self.run_gate(remote_check=True)[0], 2)

    def test_no_remote_check_flag_skips_the_check(self):
        self.make_remote_ahead()
        self.repo.git("switch", "-q", "-c", "feature")
        self.assertNotEqual(self.run_gate(remote_check=False)[0], 2)

    def test_ci_does_not_run_the_remote_check(self):
        self.make_remote_ahead()
        self.repo.git("switch", "-q", "-c", "feature")
        env = {"CI": "true"}
        self.assertNotEqual(self.run_gate(remote_check=True, env=env)[0], 2)

    def test_unreachable_remote_is_a_clear_error_not_a_silent_pass(self):
        self.repo.git("tag", "db-v1")
        self.repo.git("remote", "add", "origin", os.path.join(self.tmp, "does-not-exist.git"))
        code, _out, err = self.run_gate(remote_check=True,
                                        env=self.MAIN)
        self.assertEqual(code, 2)
        self.assertIn("--no-remote-check", err)

    def test_explicit_base_skips_the_staleness_check(self):
        self.make_remote_ahead()
        self.assertNotEqual(self.run_gate(base="db-v1", remote_check=True)[0], 2)


class CommandLine(GitCase):
    """The same check runs from the command line, with the documented exit codes."""

    SCRIPT = os.path.join(BUILD_DIR, "broadcast_source_gate.py")

    def cli(self, *args):
        env = {k: v for k, v in os.environ.items()
               if k not in ("CI", "GITHUB_BASE_REF", "GITHUB_REF", "GITHUB_REF_NAME")}
        return subprocess.run([sys.executable, self.SCRIPT, "--root", self.repo.path] + list(args),
                              capture_output=True, text=True, env=env)

    def test_exit_codes(self):
        self.assertEqual(self.cli("--base", "HEAD").returncode, 0)
        self.bad_change()
        refused = self.cli("--base", "HEAD")
        self.assertEqual(refused.returncode, 1)
        self.assertIn("synth-a", refused.stderr)
        self.assertEqual(self.cli("--base", "no-such-ref").returncode, 2)
        # On main with no release tag there is no baseline: a local run passes.
        self.assertEqual(self.cli("--no-remote-check").returncode, 0)
        self.repo.git("tag", "db-v1")
        self.repo.commit("bad change on main")
        self.repo.write_shards([core("synth-a")], [detail("synth-a", weightG=2400)])
        self.assertEqual(self.cli("--no-remote-check").returncode, 1)


if __name__ == "__main__":
    unittest.main()

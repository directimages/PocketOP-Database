#!/usr/bin/env python3
"""Tests for the attribution gate in build/attribution_gate.py.

The gate fails the build when a published string in the source shards, or a
line of CHANGELOG.md, carries an attribution phrase whose subject is not on the
allowlist. It checks the phrase pattern, never a list of names.

Every name used here is a made up placeholder. Every shard, changelog and
allowlist is built synthetically under a temporary directory. No test reads the
real source shards, the real changelog or any production data; the only real
file read is the committed allowlist, to check that it parses and is tidy.

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
import attribution_gate as gate  # noqa: E402

# Placeholder subjects. None of these is a real person, product or company.
NAME = "Zorblax"
OTHER_NAME = "Quennel"
BRAND = "Acmelens"

# Terms the synthetic allowlist carries in most tests.
ALLOWED = {"newsfeed", "staged"}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def lens(entry_id, **fields):
    entry = {"id": entry_id, "manufacturer": BRAND, "model": "Test"}
    entry.update(fields)
    return entry


class TreeCase(unittest.TestCase):
    """A synthetic source tree and changelog per test."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.source = os.path.join(self.root, "source")
        self.changelog = os.path.join(self.root, "CHANGELOG.md")
        os.makedirs(self.source)

    def shard(self, rel, entries, key="lenses"):
        write_json(os.path.join(self.source, *rel.split("/")), {key: entries})

    def write_changelog(self, text):
        with open(self.changelog, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)

    def scan(self, allowed=None):
        return gate.scan(self.source, self.changelog,
                         ALLOWED if allowed is None else allowed,
                         base_dir=self.root)

    def scan_notes(self, text, allowed=None):
        """Scan one lens whose notes field holds text. Returns the violations."""
        self.shard("lenses/lens_acme.json", [lens("unit-1", notes=text)])
        return self.scan(allowed)

    def flagged_terms(self, text, allowed=None):
        return sorted(t for v in self.scan_notes(text, allowed) for t in v.terms)


class PhraseFormTests(TreeCase):
    """Every phrase form in the minimum set, in English and Dutch, is caught."""

    def assert_flags(self, form, texts):
        for text in texts:
            with self.subTest(form=form, text=text):
                found = self.scan_notes(text)
                self.assertEqual([v.form for v in found], [form])
                self.assertEqual(found[0].terms, [NAME])

    def test_by_and_door(self):
        self.assert_flags("by", [
            "hFOV confirmed by %s, applications team." % NAME,
            "Series value approved as series value by %s 2026-06-13" % NAME,
            "Waarde bevestigd door %s." % NAME,
            "goedgekeurd door %s" % NAME,
            "akkoord door %s" % NAME,
        ])

    def test_attribution_verb_then_from(self):
        self.assert_flags("verb_from", [
            "Value supplied from %s." % NAME,
            "Sheet was verified, later, via %s." % NAME,
            "aangeleverd van %s" % NAME,
        ])

    def test_per_and_according_to(self):
        self.assert_flags("per", ["Value used per %s instruction." % NAME,
                                  "Per %s." % NAME])
        self.assert_flags("according", ["according to %s" % NAME,
                                        "volgens %s" % NAME,
                                        "conform %s" % NAME])

    def test_noun_of_subject(self):
        self.assert_flags("noun_of", [
            "Done on instruction from %s." % NAME,
            "op instructie van %s" % NAME,
            "request of %s" % NAME,
            "mail van %s" % NAME,
        ])

    def test_parenthesised_date(self):
        self.assert_flags("date_paren", [
            "no conversion (%s 2026-08-10)." % NAME,
            "no conversion (%s 10-08-2026)." % NAME,
            "no conversion (%s 10/08/2026)." % NAME,
            "no conversion (%s 10 August 2026)." % NAME,
            "geen conversie (%s 10 augustus 2026)." % NAME,
        ])

    def test_bare_date(self):
        self.assert_flags("date_bare", [
            "Done. %s 2026-07-24" % NAME,
            "aangeleverd %s 2026-07-24)" % NAME,
            "Sentence end %s 24-07-2026" % NAME,
        ])

    def test_akkoord(self):
        self.assert_flags("akkoord", ["exact 20x (POS-D02, %s akkoord)." % NAME,
                                      "akkoord van %s" % NAME,
                                      "akkoord met %s" % NAME])

    def test_possessive_and_dutch_sheet(self):
        self.assert_flags("possessive", ["from %s's sheet" % NAME,
                                         "%s's instruction" % NAME,
                                         "%s’s mail" % NAME])
        # Dutch drops the apostrophe: the subject word then carries the s.
        found = self.scan_notes("HFOV uit %ss sheet (catalogus)" % NAME)
        self.assertEqual([v.form for v in found], ["from_noun"])
        self.assertEqual(found[0].terms, [NAME + "s"])

    def test_quarter(self):
        self.assert_flags("quarter", ["F1.5-F3.0 (%s Q2)." % NAME,
                                      "chipset (%s Q3 bevestigd)" % NAME,
                                      "no IR remote (%s Q6: none)" % NAME,
                                      "answer (%s Q12)" % NAME])

    def test_quarter_style_numbers_need_a_boundary(self):
        for text in ("%s Q123 model" % NAME, "%s Q6A body" % NAME):
            with self.subTest(text=text):
                self.assertEqual(self.scan_notes(text), [])

    def test_compound_name_joined_to_an_attribution_participle(self):
        self.assert_flags("compound", [
            "(%s-approved mount datafix)" % NAME,
            "%s-confirmed value" % NAME,
            "%s-verified" % NAME,
            "%s-sourced values" % NAME,
            "%s-supplied" % NAME,
            "%s-provided" % NAME,
            "%s-checked" % NAME,
            "%s-measured" % NAME,
            "%s-signed off" % NAME,
            "%s-goedgekeurd" % NAME,
            "%s-bevestigd" % NAME,
        ])

    def test_compound_with_a_hyphenated_name_reports_every_part(self):
        self.assertEqual(self.flagged_terms("(%s-%s-approved)" % (NAME, OTHER_NAME)),
                         sorted([NAME, OTHER_NAME]))

    def test_compound_with_an_allowed_subject_passes(self):
        for text in ("Newsfeed-verified", "%s-sourced" % BRAND, "%s-supplied" % BRAND.upper(),
                     "%s-approved" % NAME.lower(), "X100-approved", "A-approved"):
            with self.subTest(text=text):
                self.assertEqual(self.scan_notes(text), [])

    def test_attribution_verb_with_a_subject(self):
        self.assert_flags("with_x", ["confirmed with %s" % NAME,
                                     "checked with %s." % NAME,
                                     "confirmed it with %s" % NAME,
                                     "bevestigd met %s" % NAME,
                                     "afgestemd met %s" % NAME])

    def test_subject_before_the_verb(self):
        self.assert_flags("subject_verb", ["%s confirmed the value" % NAME,
                                           "%s said so" % NAME,
                                           "%s wrote back" % NAME,
                                           "%s approved it" % NAME,
                                           "%s (%s) confirmed" % (NAME, BRAND),
                                           "%s bevestigde dit" % NAME,
                                           "%s zei dat" % NAME,
                                           "%s bevestigt dat site en catalogus kloppen" % NAME,
                                           "%s zegt dat" % NAME,
                                           "%s schrijft dat" % NAME,
                                           "%s confirms the value" % NAME,
                                           "%s says so" % NAME,
                                           "%s writes that" % NAME])

    def test_subject_before_the_verb_ignores_model_designations(self):
        for text in ("iPhone 13 Pro Max confirms the value", "0.8 MOD confirmed (primary)",
                     "CN7x17 KAS S confirmed", "Series 7 Zoom Pro approved"):
            with self.subTest(text=text):
                self.assertEqual(self.scan_notes(text), [])

    def test_a_number_or_date_in_front_of_a_name_does_not_hide_it(self):
        for text in ("values gave 72.5, %s confirms that" % NAME,
                     "2026-10-10 %s confirmed" % NAME,
                     "wide 56 (%s confirmed)" % NAME):
            with self.subTest(text=text):
                self.assertEqual(self.flagged_terms(text), [NAME])

    def test_subject_before_the_verb_passes_for_allowed_subjects(self):
        for text in ("%s confirmed" % BRAND, "Newsfeed confirmed", "the lens was confirmed",
                     "%s confirmed" % NAME.lower()):
            with self.subTest(text=text):
                self.assertEqual(self.scan_notes(text), [])

    def test_thanks_to_and_credit(self):
        self.assert_flags("thanks", ["thanks to %s" % NAME, "dank aan %s" % NAME,
                                     "credit to %s." % NAME])

    def test_source_colon_is_not_checked(self):
        # Known limit: "source: X" is too common in ordinary data text.
        self.assertEqual(self.scan_notes("Source: %s" % NAME), [])
        self.assertEqual(self.scan_notes("bron: %s" % NAME), [])

    def test_slash_with_a_brand_from_the_data(self):
        self.assert_flags("slash", ["Sheet-authoritair (%s/%s, Path)" % (NAME, BRAND),
                                    "%s/%s" % (NAME, BRAND.upper())])

    def test_brand_then_slash_is_a_product_line_and_not_checked(self):
        # Brand/product-line pairs are legitimate text. Known limit: a name
        # written after the brand ("BRAND/X") is not seen.
        self.assertEqual(self.scan_notes("%s/%s" % (BRAND, NAME)), [])

    def test_slash_without_any_brand_is_not_checked(self):
        # Known limit: only brand anchored slash forms are checked.
        self.assertEqual(self.scan_notes("%s/Somecorp" % NAME), [])

    def test_numeric_ranges_and_lists_are_not_dates(self):
        for text in ("Focal %s 5.05-91 mm" % NAME, "Zoom %s 18/25/35 set" % NAME,
                     "Series 9.5-18 range", "Sig Zooms 24-75/45", "HFOV 77.2/29"):
            with self.subTest(text=text):
                self.assertEqual(self.scan_notes(text), [])

    def test_two_forms_on_one_site_report_once(self):
        found = self.scan_notes("no conversion (%s 2026-08-10)." % NAME)
        self.assertEqual(len(found), 1)

    def test_every_unlisted_word_of_a_multi_word_subject_is_reported(self):
        self.assertEqual(self.flagged_terms("confirmed by %s %s" % (NAME, OTHER_NAME)),
                         sorted([NAME, OTHER_NAME]))

    def test_one_unlisted_word_in_a_listed_run_is_enough(self):
        self.assertEqual(self.flagged_terms("confirmed by Newsfeed %s" % NAME), [NAME])

    def test_hyphenated_subject_is_checked_per_capitalised_part(self):
        self.assertEqual(self.flagged_terms("supplied by %s-sourced data" % NAME),
                         [NAME])
        self.assertEqual(self.flagged_terms("supplied by %s-sourced data" % BRAND), [])


class AllowedSubjectTests(TreeCase):
    """Subjects that must pass without a violation."""

    def test_allowlisted_word_passes_case_and_possessive_insensitively(self):
        for text in ("confirmed by Newsfeed", "confirmed by NEWSFEED",
                     "confirmed by Newsfeed's team", "uit Newsfeeds sheet"):
            with self.subTest(text=text):
                self.assertEqual(self.scan_notes(text), [])

    def test_brand_from_a_manufacturer_field_passes_without_any_list_edit(self):
        self.shard("lenses/lens_acme.json", [lens("unit-1", notes="per %s spec" % BRAND)])
        self.assertEqual(self.scan(allowed=set()), [])

    def test_brand_from_a_brand_field_passes(self):
        self.shard("cams/cam_x.json",
                   [{"id": "cam-1", "brand": "newbrandx",
                     "notes": "per Newbrandx datasheet"}], key="ptzCameras")
        self.assertEqual(self.scan(allowed=set()), [])

    def test_accents_are_folded_for_brands(self):
        self.shard("lenses/lens_eclair.json",
                   [{"id": "unit-1", "manufacturer": "Éclair",
                     "notes": "by Eclair and by Éclair's team"}])
        self.assertEqual(self.scan(allowed=set()), [])

    def test_a_brand_in_another_shard_is_known_everywhere(self):
        self.shard("lenses/lens_acme.json", [lens("unit-1")])
        self.shard("lenses/lens_other.json",
                   [{"id": "unit-2", "manufacturer": "Otherbrand",
                     "notes": "per %s data" % BRAND}])
        self.assertEqual(self.scan(allowed=set()), [])

    def test_words_with_digits_and_ids_are_skipped(self):
        for text in ("per POS-D28", "powered by PTC500", "confirmed by VC-A71P",
                     "per decision POS-D12"):
            with self.subTest(text=text):
                self.assertEqual(self.scan_notes(text), [])

    def test_single_letter_words_are_skipped(self):
        self.assertEqual(self.scan_notes("noted by A on 2026-01-01"), [])

    def test_roles_and_lowercase_subjects_do_not_match(self):
        for text in ("confirmed by the project owner", "approved by a %s engineer" % BRAND,
                     "confirmed by %s" % NAME.lower()):
            with self.subTest(text=text):
                self.assertEqual(self.scan_notes(text), [])

    def test_a_name_outside_an_attribution_phrase_passes(self):
        # Known limit: the pattern gate cannot see a bare name.
        self.assertEqual(self.scan_notes("%s was at the demo." % NAME), [])

    def test_urls_are_ignored(self):
        text = "see https://example.invalid/page?q=%s/%s" % (NAME, BRAND)
        self.assertEqual(self.scan_notes(text), [])
        # The same slash pair outside a URL is flagged, so the test is not vacuous.
        self.assertEqual(self.flagged_terms("see q=%s/%s" % (NAME, BRAND)), [NAME])

    def test_text_around_a_url_is_still_scanned(self):
        text = "https://example.invalid/x confirmed by %s" % NAME
        self.assertEqual(self.flagged_terms(text), [NAME])


class LocationTests(TreeCase):
    """Violations name the file, entry id, field path or changelog line, offset."""

    def test_shard_violation_names_file_id_field_form_phrase_and_offset(self):
        found = self.scan_notes("abc confirmed by %s." % NAME)
        self.assertEqual(len(found), 1)
        v = found[0]
        self.assertEqual(v.file, "source/lenses/lens_acme.json")
        self.assertEqual(v.entry_id, "unit-1")
        self.assertEqual(v.field, "notes")
        self.assertEqual(v.form, "by")
        self.assertEqual(v.phrase, "by %s" % NAME)
        self.assertEqual(v.offset, 14)
        self.assertIsNone(v.line)

    def test_nested_field_paths_use_dots_and_indexes(self):
        entry = lens("unit-1", sources={"weightG": "per %s" % NAME},
                     cameras=[{"note": "ok"}, {"note": "by %s" % NAME}])
        self.shard("lenses/lens_acme.json", [entry])
        fields = sorted(v.field for v in self.scan())
        self.assertEqual(fields, ["cameras[1].note", "sources.weightG"])

    def test_lists_of_strings_use_indexes(self):
        self.shard("lenses/lens_acme.json", [lens("unit-1", webSources=["x", "by %s" % NAME])])
        self.assertEqual([v.field for v in self.scan()], ["webSources[1]"])

    def test_cine_style_nested_directories_report_forward_slash_paths(self):
        self.shard("cine-lenses/pl/cine_lens_pl_acme.json",
                   [lens("unit-1", notes="by %s" % NAME)])
        self.assertEqual(self.scan()[0].file, "source/cine-lenses/pl/cine_lens_pl_acme.json")

    def test_meta_and_file_level_strings_are_scanned(self):
        write_json(os.path.join(self.source, "meta", "meta_x.json"),
                   {"version": "1.0.0", "notes": ["fine", "per %s" % NAME]})
        found = self.scan()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].file, "source/meta/meta_x.json")
        self.assertEqual(found[0].field, "notes[1]")
        self.assertEqual(found[0].entry_id, gate.FILE_LEVEL)

    def test_changelog_lines_are_scanned_with_line_number_and_offset(self):
        self.write_changelog("# Changelog\n\n- fine line\n- value per %s ok\n" % NAME)
        found = self.scan()
        self.assertEqual(len(found), 1)
        v = found[0]
        self.assertEqual((v.file, v.line, v.offset, v.form),
                         ("CHANGELOG.md", 4, 8, "per"))
        self.assertIsNone(v.entry_id)

    def test_changelog_with_windows_line_endings(self):
        self.write_changelog("# Changelog\r\n\r\n- value per %s ok\r\n" % NAME)
        self.assertEqual([v.line for v in self.scan()], [3])

    def test_missing_changelog_is_skipped(self):
        self.shard("lenses/lens_acme.json", [lens("unit-1")])
        self.assertEqual(self.scan(), [])

    def test_clean_tree_has_no_violations(self):
        self.shard("lenses/lens_acme.json", [lens("unit-1", notes="Measured on the bench.")])
        self.write_changelog("# Changelog\n\n- added entries per %s\n" % BRAND)
        self.assertEqual(self.scan(), [])

    def test_invalid_json_is_a_gate_error(self):
        path = os.path.join(self.source, "lenses", "broken.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        with self.assertRaises(gate.GateError):
            self.scan()


class ReportTests(TreeCase):
    """Local mode prints the phrase, CI mode never prints the subject text."""

    def violations(self):
        self.shard("lenses/lens_acme.json",
                   [lens("unit-1", notes="abc confirmed by %s %s" % (NAME, OTHER_NAME))])
        self.write_changelog("# Changelog\n- value per %s ok\n" % NAME)
        return self.scan()

    def test_local_report_has_location_phrase_and_subject(self):
        report = gate.format_report(self.violations(), ci=False)
        self.assertIn("source/lenses/lens_acme.json id 'unit-1' field 'notes'", report)
        self.assertIn("form by", report)
        self.assertIn("offset 14", report)
        self.assertIn("by %s %s" % (NAME, OTHER_NAME), report)
        self.assertIn(NAME, report)
        self.assertIn("CHANGELOG.md line 2", report)
        self.assertIn("allowlist", report)

    def test_ci_report_masks_every_subject_and_prints_no_phrase(self):
        report = gate.format_report(self.violations(), ci=True)
        self.assertNotIn(NAME, report)
        self.assertNotIn(OTHER_NAME, report)
        self.assertNotIn(NAME.lower(), report.lower())
        self.assertNotIn("phrase", report)
        self.assertIn("Z" + "*" * (len(NAME) - 1), report)
        self.assertIn("Q" + "*" * (len(OTHER_NAME) - 1), report)
        self.assertIn("source/lenses/lens_acme.json id 'unit-1' field 'notes'", report)
        self.assertIn("form by", report)
        self.assertIn("offset 14", report)
        self.assertIn("CHANGELOG.md line 2", report)
        self.assertIn("form per", report)

    def test_mask_keeps_only_the_first_letter(self):
        self.assertEqual(gate.mask("Zorblax"), "Z******")
        self.assertEqual(gate.mask("Ab"), "A*")
        self.assertEqual(gate.mask("Éclair"), "É*****")

    def test_long_reports_are_capped(self):
        entries = [lens("unit-%d" % i, notes="by %s" % NAME) for i in range(gate.MAX_REPORTED + 5)]
        self.shard("lenses/lens_acme.json", entries)
        report = gate.format_report(self.scan(), ci=False)
        self.assertIn("and 5 more", report)

    def test_is_ci_reads_the_ci_variable(self):
        for env, expected in (({"CI": "true"}, True), ({"CI": "1"}, True),
                              ({"CI": "TRUE"}, True), ({}, False), ({"CI": ""}, False),
                              ({"CI": "false"}, False), ({"CI": "0"}, False)):
            with self.subTest(env=env):
                self.assertEqual(gate.is_ci(env), expected)


class AllowlistFileTests(unittest.TestCase):
    """Parsing of the allowlist file, and the committed list itself."""

    def write(self, text):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "allow.txt")
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def test_comments_blank_lines_case_accents_and_crlf(self):
        path = self.write("# section\r\n\r\nNewsfeed\r\n  Éclair  \r\n# more\r\nStaged\r\n")
        self.assertEqual(gate.load_allowlist(path), {"newsfeed", "eclair", "staged"})

    def test_multi_word_entries_are_rejected(self):
        with self.assertRaises(gate.GateError):
            gate.load_allowlist(self.write("Two Words\n"))

    def test_entries_with_digits_are_rejected(self):
        with self.assertRaises(gate.GateError):
            gate.load_allowlist(self.write("Model3\n"))

    def test_duplicate_entries_are_rejected(self):
        with self.assertRaises(gate.GateError):
            gate.load_allowlist(self.write("Newsfeed\nnewsfeed\n"))

    def test_missing_file_is_a_gate_error(self):
        with self.assertRaises(gate.GateError):
            gate.load_allowlist(os.path.join(tempfile.gettempdir(), "no-such-allowlist.txt"))

    def test_committed_allowlist_parses_and_is_not_empty(self):
        terms = gate.load_allowlist(gate.DEFAULT_ALLOWLIST)
        self.assertGreater(len(terms), 10)


class CommittedAllowlistBehaviourTests(TreeCase):
    """What the shipped allowlist lets through and what it still stops."""

    def committed(self, text):
        self.shard("lenses/lens_acme.json", [lens("unit-1", notes=text)])
        return self.scan(gate.load_allowlist(gate.DEFAULT_ALLOWLIST))

    def test_a_dated_record_note_passes(self):
        words = ("Verified", "Confirmed", "Checked", "Updated", "Measured", "Corrected",
                 "Added", "Removed", "Released", "Bevestigd", "Gecontroleerd", "Bijgewerkt")
        for word in words:
            with self.subTest(word=word):
                self.assertEqual(self.committed("%s 2026-11-20" % word), [])
        self.assertEqual(self.committed("Verified 2026-11-20"), [])

    def test_a_record_verb_in_front_of_a_name_still_fails(self):
        found = self.committed("Verified %s 2026-11-20" % NAME)
        self.assertEqual([t for v in found for t in v.terms], [NAME])
        found = self.committed("(Verified %s 2026-11-20)" % NAME)
        self.assertEqual([t for v in found for t in v.terms], [NAME])

    def test_the_first_agent_name_stays_and_the_second_is_not_listed(self):
        self.assertEqual(self.committed("confirmed by Kay"), [])
        self.assertEqual([t for v in self.committed("confirmed by Tim") for t in v.terms],
                         ["Tim"])

    def test_ordinary_negations_before_a_verb_pass(self):
        self.assertEqual(self.committed("Not confirmed by the manufacturer"), [])


class AssembleIntegrationTests(TreeCase):
    """The gate runs inside assemble.py and stops the build before any output."""

    def setUp(self):
        super().setUp()
        meta_dir = os.path.join(self.source, "meta")
        names = sorted({out["meta"] for out in assemble.OUTPUTS})
        for name in names:
            write_json(os.path.join(meta_dir, name),
                       {"version": "0.0.0-test", "updatedAt": "test",
                        "verificationWarning": ["synthetic"], "notes": ["synthetic"]})
        for name, value in (("REPO_ROOT", self.root), ("SOURCE", self.source),
                            ("META_DIR", meta_dir)):
            patcher = mock.patch.object(assemble, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("CI", None)

    def run_assemble(self, argv=()):
        write_json(os.path.join(self.source, "devices", "devices.json"),
                   {"devices": [self.device]})
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = assemble.main(list(argv))
        return code, err.getvalue()

    device = {"id": "unit-device", "marketingName": "Test Device",
              "modelIdentifiers": ["TestPhone1,1"],
              "cameras": [{"label": "1x", "type": "wide", "hFOVDegrees": 70.0,
                           "isDefault": True}]}

    def with_note(self, text):
        entry = dict(self.device)
        entry["notes"] = text
        write_json(os.path.join(self.source, "devices", "devices.json"), {"devices": [entry]})
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = assemble.main([])
        return code, err.getvalue()

    def test_clean_tree_assembles(self):
        code, err = self.run_assemble()
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.exists(os.path.join(self.root, "devices.json")))

    def test_violation_fails_loudly_and_publishes_nothing(self):
        code, err = self.with_note("confirmed by %s" % NAME)
        self.assertEqual(code, 1)
        self.assertIn("VALIDATION FAILED", err)
        self.assertIn("source/devices/devices.json id 'unit-device' field 'notes'", err)
        self.assertIn("by %s" % NAME, err)
        self.assertFalse(os.path.exists(os.path.join(self.root, "devices.json")))

    def test_in_ci_the_failure_hides_the_subject(self):
        os.environ["CI"] = "true"
        code, err = self.with_note("confirmed by %s" % NAME)
        self.assertEqual(code, 1)
        self.assertIn("source/devices/devices.json id 'unit-device' field 'notes'", err)
        self.assertNotIn(NAME, err)
        self.assertIn("Z" + "*" * (len(NAME) - 1), err)

    def test_changelog_violation_fails_the_build(self):
        self.write_changelog("# Changelog\n- done per %s\n" % NAME)
        code, err = self.run_assemble()
        self.assertEqual(code, 1)
        self.assertIn("CHANGELOG.md line 2", err)
        self.assertFalse(os.path.exists(os.path.join(self.root, "devices.json")))

    def test_check_mode_runs_the_gate_too(self):
        write_json(os.path.join(self.source, "devices", "devices.json"),
                   {"devices": [dict(self.device, notes="confirmed by %s" % NAME)]})
        out, err2 = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err2):
            code = assemble.main(["--check"])
        self.assertEqual(code, 1)
        self.assertIn("field 'notes'", err2.getvalue())


class CommandLineTests(TreeCase):
    """python build/attribution_gate.py --root DIR, used by the PR workflow."""

    def run_cli(self, argv, env=None):
        out, err = io.StringIO(), io.StringIO()
        base = {k: v for k, v in os.environ.items() if k != "CI"}
        base.update(env or {})
        with mock.patch.dict(os.environ, base, clear=True), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gate.main(argv)
        return code, out.getvalue(), err.getvalue()

    def allowlist(self):
        path = os.path.join(self.root, "allow.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("Newsfeed\n")
        return path

    def test_clean_root_exits_zero(self):
        self.shard("lenses/lens_acme.json", [lens("unit-1", notes="fine")])
        code, out, _err = self.run_cli(["--root", self.root, "--allowlist", self.allowlist()])
        self.assertEqual(code, 0)
        self.assertIn("passed", out)

    def test_violation_exits_one_with_report_on_stderr(self):
        self.shard("lenses/lens_acme.json", [lens("unit-1", notes="by %s" % NAME)])
        code, _out, err = self.run_cli(["--root", self.root, "--allowlist", self.allowlist()])
        self.assertEqual(code, 1)
        self.assertIn(NAME, err)

    def test_violation_in_ci_hides_the_subject(self):
        self.shard("lenses/lens_acme.json", [lens("unit-1", notes="by %s" % NAME)])
        code, out, err = self.run_cli(["--root", self.root, "--allowlist", self.allowlist()],
                                      env={"CI": "true"})
        self.assertEqual(code, 1)
        self.assertNotIn(NAME, out + err)

    def test_counts_mode_prints_counts_per_form_and_never_a_subject(self):
        self.shard("lenses/lens_acme.json",
                   [lens("unit-1", notes="by %s and per %s" % (NAME, OTHER_NAME)),
                    lens("unit-2", notes="(%s 2026-08-10)" % NAME)])
        self.write_changelog("- per %s\n" % NAME)
        code, out, err = self.run_cli(["--root", self.root, "--allowlist", self.allowlist(),
                                       "--counts"])
        self.assertEqual(code, 1)
        text = out + err
        self.assertNotIn(NAME, text)
        self.assertNotIn(OTHER_NAME, text)
        self.assertIn("shards by: 1", text)
        self.assertIn("shards per: 1", text)
        self.assertIn("shards date_paren: 1", text)
        self.assertIn("changelog per: 1", text)
        self.assertIn("total sites: 4", text)

    def test_bad_allowlist_is_reported_and_fails(self):
        path = os.path.join(self.root, "bad.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("Two Words\n")
        code, _out, err = self.run_cli(["--root", self.root, "--allowlist", path])
        self.assertEqual(code, 1)
        self.assertIn("allowlist", err)


if __name__ == "__main__":
    unittest.main()

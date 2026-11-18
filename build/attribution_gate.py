#!/usr/bin/env python3
"""Attribution gate for the public PocketOP-Database repo (POS-W113).

No real person's name may appear in a public PocketOP repo; people are referred
to by role. Names enter published text through attribution phrasing in free
text: "confirmed by X", "approved as series value by X", "per X instruction",
"(X 2026-08-10)", "X akkoord", "uit Xs sheet", "X Q2", "X/AIDA". A list of known
names would miss every new name and would publish the names it lists, so this
gate checks the PATTERN, never a name.

It scans every string in every source/**/*.json shard and every line of
CHANGELOG.md. Where a string matches an attribution phrase, the subject of the
phrase (a run of capitalised words) must be allowed. A word is allowed when it
is

  - a manufacturer or brand taken from the data itself (the manufacturer and
    brand fields of the shards), so a new brand never needs a manual addition, or
  - a term on the committed list build/attribution_allowlist.txt (public
    sources, retailers, ordinary and document words, agent names).

Otherwise the gate fails, naming file, entry id, field (or CHANGELOG line), the
phrase form, the character offset and, locally, the matched phrase. When the CI
environment variable is set (GitHub Actions sets CI=true) the subject is masked
to its first letter plus asterisks, because CI logs of a public repo are public.

Known limits: a name outside an attribution phrase is not seen; a subject
written in lower case is not seen; a name next to a company that is not a
manufacturer in the data ("X/SomeCorp") is not seen; "source: X" is not
checked. Words with digits and single letters are skipped (model numbers,
decision ids). Kay is an agent name on the allowlist and is also a given name,
so "confirmed by Kay" passes for any real person called Kay. Short capitalised
allowlist terms could equal a person's initials.

Standard library only. Works on macOS and Windows.

Usage:
  python build/attribution_gate.py [--root DIR] [--allowlist FILE] [--counts]

No em dashes appear anywhere in this file by project policy.
"""

import argparse
import collections
import json
import os
import re
import sys
import unicodedata

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BUILD_DIR)
DEFAULT_ALLOWLIST = os.path.join(BUILD_DIR, "attribution_allowlist.txt")

# Entry id reported for strings that are not inside an entry (meta files).
FILE_LEVEL = "(file level)"
# Cap on the violation lines printed in one report.
MAX_REPORTED = 300
# Cap on the length of a printed phrase.
MAX_PHRASE = 120

# Fields of a shard entry that name a manufacturer or brand.
BRAND_FIELDS = ("manufacturer", "brand")


class GateError(Exception):
    """The gate could not run: unreadable allowlist, invalid shard JSON."""


Violation = collections.namedtuple(
    "Violation", ["file", "entry_id", "field", "line", "form", "phrase", "offset", "terms"])


# --------------------------------------------------------------------------
# Words, allowlist and brands.
# --------------------------------------------------------------------------


def fold(text):
    """Lower case and strip accents, so Angenieux matches the accented spelling."""
    norm = unicodedata.normalize("NFKD", text)
    return "".join(c for c in norm if not unicodedata.combining(c)).lower()


def mask(term):
    """First letter plus asterisks: 'Zorblax' becomes 'Z******'."""
    return term[:1] + "*" * (len(term) - 1)


def is_ci(env=None):
    """True when the CI environment variable is set to something truthy."""
    env = os.environ if env is None else env
    return env.get("CI", "").strip().lower() not in ("", "0", "false")


_ALLOWLIST_TERM = re.compile(r"[^\W\d_]+")


def load_allowlist(path):
    """Read the committed allowlist. Returns the set of folded terms.

    One word per line, blank lines and lines starting with # ignored. A line
    that is not a single word of letters, or a repeated term, is an error, so
    a typo is loud instead of silently useless.
    """
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        raise GateError("Cannot read the attribution allowlist '%s': %s" % (path, exc))
    terms = set()
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not _ALLOWLIST_TERM.fullmatch(line):
            raise GateError("Attribution allowlist '%s' line %d: an entry must be one "
                            "word of letters, no spaces or digits." % (path, number))
        key = fold(line)
        if key in terms:
            raise GateError("Attribution allowlist '%s' line %d: duplicate entry."
                            % (path, number))
        terms.add(key)
    return terms


class Vocabulary:
    """The words a subject may consist of: the allowlist plus derived brands."""

    def __init__(self, allowed, brands):
        self.allowed = set(allowed)
        self.brands = set(brands)
        # Multi word brands match as a run of words, never word by word, so a
        # first name inside a brand name does not become allowed on its own.
        self.brand_phrases = collections.defaultdict(list)
        for brand in self.brands:
            words = tuple(brand.split())
            if len(words) > 1:
                self.brand_phrases[words[0]].append(words)

    @staticmethod
    def _in(folded, known):
        return folded in known or (folded.endswith("s") and folded[:-1] in known)

    def is_brand(self, word):
        return self._in(fold(word), self.brands)

    def is_allowed(self, word):
        folded = fold(word)
        return self._in(folded, self.allowed) or self._in(folded, self.brands)

    def unallowed(self, subject):
        """The words of a subject that are not allowed, in order, once each."""
        tokens = [_strip_possessive(t) for t in subject.split()]
        found = []
        index = 0
        while index < len(tokens):
            skip = self._brand_phrase_length(tokens, index)
            if skip:
                index += skip
                continue
            token = tokens[index]
            index += 1
            if any(c.isdigit() for c in token):
                continue
            for part in token.split("-"):
                part = part.strip("'\u2019")
                if len(part) < 2 or not part[0].isupper():
                    continue
                if not self.is_allowed(part) and part not in found:
                    found.append(part)
        return found

    def _brand_phrase_length(self, tokens, index):
        for words in sorted(self.brand_phrases.get(fold(tokens[index]), ()), key=len, reverse=True):
            window = tuple(fold(t) for t in tokens[index:index + len(words)])
            if window == words:
                return len(words)
        return 0


def _strip_possessive(token):
    for suffix in ("'s", "\u2019s", "'", "\u2019"):
        if token.endswith(suffix) and len(token) > len(suffix):
            return token[:-len(suffix)]
    return token


# --------------------------------------------------------------------------
# Attribution phrase forms.
#
# A subject is a run of capitalised words directly after (or before) the
# trigger. Trigger words are case insensitive, the subject is not, which is
# what keeps "confirmed by the project owner" and "approved by a <brand>
# engineer" out of the net: a role is not a name.
# --------------------------------------------------------------------------

_CAP = "A-Z\u00c0-\u00d6\u00d8-\u00de"
_WORD = r"[%s][\w\u2019'\-]*" % _CAP


def _subject(name):
    return r"(?P<%s>%s(?:\s+%s)*)" % (name, _WORD, _WORD)


_SUBJ = _subject("a")

_NOUN = (r"(?:sheet|spreadsheet|lijst|list|bestand|file|mail|e-?mail|notes?|document"
         r"|instruct(?:ion|ie)|request|verzoek|decision|besluit|approval|goedkeuring"
         r"|confirmation|bevestiging)")

_MONTH = (r"(?i:jan|feb|mar|mrt|apr|ma[yi]|mei|jun|jul|aug|sep|oct|okt|nov|dec)[a-zA-Z]*")
# A date with a separator needs a four digit year, so focal ranges ("5.05-91")
# and lists ("18/25/35") are not read as dates.
_DATE = (r"(?:\d{4}-\d{2}-\d{2}"
         r"|\d{1,2}-\d{1,2}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\.\d{1,2}\.\d{4}"
         r"|\d{1,2}\s+" + _MONTH + r"\.?\s+\d{4})")

_VERB = (r"(?:confirm\w*|approv\w*|verif\w*|check\w*|suppl\w*|provid\w*|measur\w*"
         r"|sign\w*\s+off|review\w*|bevestigd|goedgekeurd|aangeleverd|opgegeven|gemeten)")

_PARTICIPLE = (r"(?:approved|confirmed|verified|sourced|supplied|provided|checked|measured"
               r"|signed|reviewed|tested|validated|authori[sz]ed|goedgekeurd|bevestigd"
               r"|gecontroleerd|aangeleverd|opgegeven|gemeten|geleverd|nagekeken)")

_START = r"(?<![\w\-])"

# Order matters: when two forms hit the same subject the first one is reported.
_FORMS = [
    ("by", r"(?i:\b(?:by|door)\s+)" + _SUBJ),
    ("verb_from", r"(?i:\b" + _VERB + r"\b[^.;\n]{0,60}?\b(?:from|via|van)\s+)" + _SUBJ),
    ("per", r"(?i:\bper\s+)" + _SUBJ),
    ("according", r"(?i:\b(?:according\s+to|volgens|conform|aldus)\s+)" + _SUBJ),
    ("noun_of", r"(?i:\b(?:instruct\w*|request|verzoek|decision|besluit|approval|goedkeuring"
                r"|confirmation|bevestiging|e-?mail|mail|note|message|bericht)"
                r"\s+(?:from|of|van|door)\s+)" + _SUBJ),
    ("date_paren", r"\(\s*" + _SUBJ + r"\s+" + _DATE + r"\s*\)"),
    ("date_bare", _START + _SUBJ + r"\s+" + _DATE + r"\b"),
    ("akkoord", _START + _SUBJ + r"\s+(?i:akkoord)\b"),
    ("akkoord", r"(?i:\bakkoord\s+(?:van|door|met)\s+)" + _SUBJ),
    ("possessive", _START + _SUBJ + r"['\u2019]s?\s+(?i:" + _NOUN + r")\b"),
    ("from_noun", r"(?i:\b(?:uit|from|via|volgens)\s+)" + _SUBJ + r"\s+(?i:" + _NOUN + r")\b"),
    ("quarter", _START + _SUBJ + r"\s+Q\d{1,2}\b"),
    # Compound: a capitalised word joined to an attribution participle,
    # "(X-approved mount datafix)", "X-sourced". The subject is the part before
    # the participle, checked like any other subject.
    ("compound", _START + r"(?P<a>[%s][\w\u2019']*(?:-[%s][\w\u2019']*)*)-(?i:%s)\b"
                 % (_CAP, _CAP, _PARTICIPLE)),
    # Attribution verb, then "with X": "confirmed with X", "bevestigd met X".
    ("with_x", r"(?i:\b(?:confirm\w*|check\w*|verif\w*|approv\w*|agreed|clarif\w*|bevestigd"
               r"|gecontroleerd|afgestemd|besproken)\s+(?:(?:it|this|that|them)\s+)?"
               r"(?:with|met|bij)\s+)" + _SUBJ),
    # Subject before the verb: "X confirmed", "X (Brand) said", "X bevestigde".
    # "stated" and "verified" are left out on purpose: in this data they are
    # record words ("Not stated", "HFOV verified"), not attributions.
    ("subject_verb", _START + _SUBJ + r"(?:\s*\([^)]{1,40}\))?\s+"
                     r"(?i:confirmed|said|wrote|approved|agreed|replied|mailed|emailed|told"
                     r"|confirms|says|writes|approves|agrees|replies"
                     r"|bevestigde|zei|schreef|meldde|mailde|antwoordde|keurde"
                     r"|bevestigt|zegt|schrijft|meldt|mailt|antwoordt|keurt)\b"),
    ("thanks", r"(?i:\b(?:thanks\s+to|dank\s+aan|credits?\s+to)\s+)" + _SUBJ),
]
_FORM_RES = [(name, re.compile(pattern)) for name, pattern in _FORMS]

# X/BRAND, where BRAND is a manufacturer or brand from the data. The other
# direction (BRAND/product-line, e.g. a manufacturer and its lens series) is
# ordinary text and is not checked.
_SLASH = re.compile(r"(?<![\w/.\-])(?P<l>%s)/(?P<r>%s)(?![\w/])" % (_WORD, _WORD))

_URL = re.compile(r"https?://\S+")

# Forms that start with the subject cannot tell "iPhone 13 Pro Max confirms" or
# "0.8 MOD confirmed" from "X confirms", so they skip a subject that belongs to
# a model designation. Names carry no digits.
_MODEL_GUARDED = {"subject_verb"}
_DATE_LIKE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4}")


def _is_model_designation(text, match):
    """True when the subject contains a model number or follows a bare number."""
    subject = match.group("a")
    if any(c.isdigit() for c in subject):
        return True
    before = text[:match.start("a")]
    if not before or not before[-1].isspace():
        return False
    token = before.split()[-1]
    return (any(c.isdigit() for c in token) and token[-1] not in ",;:.)!?"
            and not _DATE_LIKE.fullmatch(token))


def scan_text(text, vocab):
    """Yield (form, start, end, subject_start, terms) for each flagged site.

    URLs are blanked first, keeping every offset valid.
    """
    blanked = _URL.sub(lambda m: " " * len(m.group()), text)
    seen = set()
    for form, rx in _FORM_RES:
        for m in rx.finditer(blanked):
            key = m.start("a")
            if key in seen:
                continue
            if form in _MODEL_GUARDED and _is_model_designation(blanked, m):
                continue
            terms = vocab.unallowed(m.group("a"))
            if terms:
                seen.add(key)
                yield form, m.start(), m.end(), key, terms
    for m in _SLASH.finditer(blanked):
        if vocab.is_brand(_strip_possessive(m.group("l"))) or \
                not vocab.is_brand(_strip_possessive(m.group("r"))):
            continue
        key = m.start("l")
        if key in seen:
            continue
        terms = vocab.unallowed(m.group("l"))
        if terms:
            seen.add(key)
            yield "slash", m.start(), m.end(), key, terms


# --------------------------------------------------------------------------
# Walking the shards and the changelog.
# --------------------------------------------------------------------------


def _load_json(path, base_dir):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise GateError("Cannot read shard '%s': %s" % (_rel(path, base_dir), exc))


def _rel(path, base_dir):
    return os.path.relpath(path, base_dir).replace(os.sep, "/")


def _shard_paths(source_dir):
    paths = []
    for dirpath, dirnames, filenames in os.walk(source_dir):
        dirnames.sort()
        for name in sorted(filenames):
            if name.endswith(".json"):
                paths.append(os.path.join(dirpath, name))
    return paths


def _strings(node, path):
    """Yield (field path, string) for every string under node."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(value, path + "." + key if path else key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _strings(value, "%s[%d]" % (path, index))


def _entries(data):
    """Yield (entry id, field prefix, node) units of a shard."""
    if not isinstance(data, dict):
        yield FILE_LEVEL, "", data
        return
    for key, value in data.items():
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    entry_id = item.get("id")
                    yield (entry_id if isinstance(entry_id, str) else "<no id>"), "", item
                else:
                    yield FILE_LEVEL, "%s[%d]" % (key, index), item
        else:
            yield FILE_LEVEL, key, value


def derive_brands(source_dir, base_dir=None):
    """Folded manufacturer and brand values found anywhere in the shards."""
    base_dir = base_dir or os.path.dirname(source_dir)
    brands = set()
    for path in _shard_paths(source_dir):
        data = _load_json(path, base_dir)
        if not isinstance(data, dict):
            continue
        for value in data.values():
            if not isinstance(value, list):
                continue
            for item in value:
                if isinstance(item, dict):
                    for field in BRAND_FIELDS:
                        name = item.get(field)
                        if isinstance(name, str) and name.strip():
                            brands.add(fold(name.strip()))
    return brands


def _phrase(text, start, end):
    shown = re.sub(r"\s+", " ", text[start:end])
    return shown if len(shown) <= MAX_PHRASE else shown[:MAX_PHRASE - 3] + "..."


def scan(source_dir, changelog_path, allowed, base_dir=None):
    """Scan the shards and the changelog. Returns a list of Violation.

    allowed is the set of folded allowlist terms (see load_allowlist). Brands
    are derived from the shards under source_dir. File names in violations are
    relative to base_dir (default: the parent of source_dir), with forward
    slashes on every platform.
    """
    base_dir = base_dir or os.path.dirname(source_dir)
    vocab = Vocabulary(allowed, derive_brands(source_dir, base_dir))
    found = []
    for path in _shard_paths(source_dir):
        name = _rel(path, base_dir)
        data = _load_json(path, base_dir)
        for entry_id, prefix, node in _entries(data):
            for field, text in _strings(node, prefix):
                for form, start, end, _key, terms in scan_text(text, vocab):
                    found.append(Violation(name, entry_id, field, None, form,
                                           _phrase(text, start, end), start, terms))
    if os.path.isfile(changelog_path):
        name = _rel(changelog_path, base_dir)
        try:
            with open(changelog_path, "r", encoding="utf-8") as handle:
                lines = handle.read().splitlines()
        except (OSError, ValueError) as exc:
            raise GateError("Cannot read '%s': %s" % (name, exc))
        for number, text in enumerate(lines, 1):
            for form, start, end, _key, terms in scan_text(text, vocab):
                found.append(Violation(name, None, None, number, form,
                                       _phrase(text, start, end), start, terms))
    return found


# --------------------------------------------------------------------------
# Reporting.
# --------------------------------------------------------------------------


def format_violation(violation, ci):
    if violation.line is not None:
        where = "%s line %d" % (violation.file, violation.line)
    else:
        where = "%s id '%s' field '%s'" % (violation.file, violation.entry_id, violation.field)
    head = "%s: form %s, offset %d" % (where, violation.form, violation.offset)
    if ci:
        return "%s: subject not on allowlist: %s" % (
            head, ", ".join(mask(t) for t in violation.terms))
    return "%s: phrase '%s', not on allowlist: %s" % (
        head, violation.phrase, ", ".join(violation.terms))


def format_report(violations, ci):
    lines = ["ATTRIBUTION GATE: %d attribution site(s) with a subject that is not on the "
             "allowlist." % len(violations)]
    if ci:
        lines.append("CI mode: the subject text is masked because CI logs of a public repo "
                     "are public.")
    for violation in violations[:MAX_REPORTED]:
        lines.append("  " + format_violation(violation, ci))
    if len(violations) > MAX_REPORTED:
        lines.append("  ... and %d more" % (len(violations) - MAX_REPORTED))
    lines.append("If the subject is a public brand, source or ordinary word, add it to "
                 "build/attribution_allowlist.txt in a PR. If it is a person, replace it "
                 "with a role such as 'the project owner' (POS-W113).")
    return "\n".join(lines)


def format_counts(violations):
    """Counts per source and form, and the total. Never prints a subject."""
    counts = collections.Counter(
        ("changelog" if v.line is not None else "shards", v.form) for v in violations)
    lines = ["%s %s: %d" % (source, form, n) for (source, form), n in sorted(counts.items())]
    lines.append("total sites: %d" % len(violations))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Attribution gate (POS-W113).")
    parser.add_argument("--root", default=REPO_ROOT,
                        help="repo root holding source/ and CHANGELOG.md (default: this repo)")
    parser.add_argument("--allowlist", default=DEFAULT_ALLOWLIST)
    parser.add_argument("--counts", action="store_true",
                        help="print counts per phrase form instead of the full report")
    args = parser.parse_args(argv)
    try:
        allowed = load_allowlist(args.allowlist)
        violations = scan(os.path.join(args.root, "source"),
                          os.path.join(args.root, "CHANGELOG.md"), allowed,
                          base_dir=args.root)
    except GateError as exc:
        print("ATTRIBUTION GATE: %s" % exc, file=sys.stderr)
        return 1
    if args.counts:
        print(format_counts(violations))
        return 1 if violations else 0
    if violations:
        print(format_report(violations, is_ci()), file=sys.stderr)
        return 1
    print("Attribution gate passed: no attribution phrase with a subject outside the "
          "allowlist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

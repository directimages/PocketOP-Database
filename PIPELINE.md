# PocketOP-Database publishing pipeline

This repo publishes the JSON files that the iOS app and pocketop.app consume.
The published files at the repo root are generated output. You do not edit them
by hand. You edit small shard files under `source/`, and a GitHub Action
validates them, assembles the published files, and commits the result.

This document covers the full pipeline: sharding and assembly, and the immutable
release tagging with manifest.json and website dispatch.

## Schema and data convention mutations

Before editing any shard to add a field or enum value, change a field's type or
meaning, or remove a field, consult the mutation runbook in the vault:

    HQ/PROJECTS/PocketOP/MUTATION-RUNBOOK.md

The runbook defines the three mutation scenarios (add, change, remove), the live
consumer map, and the gates that govern each scenario. It is the authority for
whether a mutation may happen and how to carry it out safely.

This document remains the authority for shard structure, assembly, validation,
release tags, and manifest.json. The runbook and this document are complementary:
check the runbook first, then follow the pipeline.

## Where the data lives

All editable data lives under `source/`:

```
source/
  broadcast-lenses/    broadcast_lens_<mfr>.json            core broadcast lens fields
  broadcast-details/   broadcast_details_<mfr>.json         detail broadcast lens fields
  cine-lenses/         <mount>/cine_lens_<mount>_<mfr>.json core cine lens fields
  cine-details/        <mount>/cine_details_<mount>_<mfr>.json detail cine lens fields
  ptz-cameras/         ptz_cameras_<brand>.json             core PTZ camera fields
  ptz-details/         ptz_details_<brand>.json             detail PTZ camera fields
  devices/             devices.json                         Apple device list
  meta/                meta_<output>.json                   version and other non entry fields
```

A lens is a **broadcast** lens when its `sensorFormat` is `twoThirdsInch` and its
`mount` is `B4`. Every other lens is a **cine** lens. Cine lenses are grouped
first by mount (`pl`, `lpl`, `ef`, `rf`, `l`, `e`) and then by manufacturer.

The core file and the matching details file always carry the same set of entry
ids. `cine-lenses/pl/cine_lens_pl_arri.json` pairs with
`cine-details/pl/cine_details_pl_arri.json`. The assembler enforces this.

## What gets published

The assembler writes these files to the repo root on every run:

```
broadcast_lenses.json         all broadcast core shards merged
broadcast_lens_details.json   all broadcast detail shards merged
cine_lenses.json              all cine core shards merged across every mount
cine_lens_details.json        all cine detail shards merged across every mount
ptz_cameras.json              all PTZ core shards merged
ptz_details.json              all PTZ detail shards merged
devices.json                  the devices shard, with its meta blocks
```

Legacy files, maintained for older app versions still in the wild. They are
never edited by hand and have no independent meaning. They are always the union
of their split parts:

```
lenses.json                   broadcast_lenses + cine_lenses
lens-details.json             broadcast_lens_details + cine_lens_details
ptz-details.json              identical content to ptz_details.json (hyphen alias)
```

All arrays in every output are sorted by `id`. Consumers join by `id`, not by
array position.

## The naming convention is enforced

Every shard filename is self describing and **globally unique across the whole
source tree**. No two files anywhere under `source/` may share a name. This is
the first thing the assembler checks, before any other validation, so a naming
collision is caught the moment it is introduced rather than after assembly.

The patterns:

| Directory | Filename pattern | Example |
|---|---|---|
| `broadcast-lenses/` | `broadcast_lens_<mfr>.json` | `broadcast_lens_canon.json` |
| `broadcast-details/` | `broadcast_details_<mfr>.json` | `broadcast_details_canon.json` |
| `cine-lenses/<mount>/` | `cine_lens_<mount>_<mfr>.json` | `cine_lens_pl_arri.json` |
| `cine-details/<mount>/` | `cine_details_<mount>_<mfr>.json` | `cine_details_pl_arri.json` |
| `ptz-cameras/` | `ptz_cameras_<brand>.json` | `ptz_cameras_panasonic.json` |
| `ptz-details/` | `ptz_details_<brand>.json` | `ptz_details_panasonic.json` |
| `meta/` | `meta_<output>.json` | `meta_cine_lenses.json` |

`<mfr>` and `<brand>` are slugs: lowercase, accents stripped, non alphanumeric
characters removed. Angenieux, dzofilm, 7artisans, masterbuilt, nisi. The slug
in the filename must match the `manufacturer` or `brand` value inside every
entry in that file, and for cine the mount in the filename must match both the
mount subdirectory and each entry's `mount` value.

## How to add a new lens

1. Decide broadcast or cine, and the mount.
2. Add the core entry to the right core shard, for example
   `source/cine-lenses/pl/cine_lens_pl_arri.json`. Create the file if that
   manufacturer is new in that mount; follow the naming pattern exactly.
3. Add the matching detail entry, with the same `id`, to the paired details
   shard, for example `source/cine-details/pl/cine_details_pl_arri.json`.
4. If you are bumping a version, edit the matching file under `source/meta/`.
5. Commit and push. The Action assembles and commits the published files.

Adding a new manufacturer or brand is just adding new shard files that follow
the naming pattern. There is no list of manufacturers anywhere to update. The
assembler discovers shards by scanning the directories, so a new file is picked
up automatically with zero configuration changes.

## What the Action does

Workflow: `.github/workflows/assemble-database.yml`. It runs on any push that
touches `source/`, and on manual dispatch.

1. Checks out the repo and sets up Python.
2. Runs `python build/broadcast_source_gate.py`, which refuses a broadcast spec
   value set or changed without a new source (see the broadcast source gate below),
   then `python build/assemble.py`, which validates every shard and writes the
   published files.
3. Stages the published files. If nothing changed, it commits nothing. If they
   changed, it commits them back with `chore: assemble database outputs from
   source shards`.

You can run the same validation and assembly locally:

```
python build/assemble.py            # validate and write the published files
python build/assemble.py --check    # validate and field level diff against the
                                     # current root files, write nothing
```

`--check` is the proof that the split is value identical to the originals. It
compares every assembled entry to the current root file it replaces, field by
field, and fails on any difference, naming the entry id, the field, the original
value, and the assembled value.

## What the validator checks

If any of these fail, the Action fails loudly, names the offending shard and
field, and commits nothing:

- a globally duplicated filename anywhere under `source/`
- invalid JSON in any shard
- a missing expected array key in a shard
- an entry with no `id`
- a duplicate `id` within an assembled file
- a `manufacturer` or `brand` value that does not match the shard slug
- a cine lens whose mount does not match its directory, or a broadcast lens in
  a cine directory and the reverse
- a core shard and its paired details shard whose `id` sets differ
- the lenses id set not equal to the lens-details id set, or the ptz_cameras id
  set not equal to the ptz-details id set
- a meta file missing its `version`
- an attribution phrase whose subject is not allowed (see below)

### The attribution gate (POS-W113)

No real person's name goes into a public PocketOP repo; people are referred to
by role ("the project owner"). Names enter published text through attribution
phrasing in free text, so `build/attribution_gate.py` checks the pattern, not a
list of names. It scans every string in every `source/**/*.json` shard and every
line of `CHANGELOG.md`, in English and Dutch, for phrases such as "confirmed by
X", "approved ... by X", "per X", "according to X", "confirmed with X", "X
confirmed" and "X said" (and "X bevestigt", "X zei"), "thanks to X", "(X
2026-08-10)", "X akkoord", "uit Xs sheet", "X Q2", "X/BRAND" and the compound
"X-approved" / "X-sourced". The subject X must be allowed:

- a manufacturer or brand taken from the `manufacturer` and `brand` fields of
  the shards, derived automatically, so a new brand needs no manual addition; or
- a word on `build/attribution_allowlist.txt` (public sources, ordinary words,
  agent names). Adding a word is a visible diff in a PR. Never add a person.

The gate runs inside `build/assemble.py` (also with `--check`), before anything
is written, and as its own read-only workflow, `attribution-gate.yml`, on pull
requests and on pushes to main that touch `source/` or `CHANGELOG.md`. Run it
alone with `python build/attribution_gate.py`. A failure names the file, entry
id, field (or CHANGELOG line), phrase form and character offset. When the `CI`
environment variable is set, the subject text is masked (first letter plus
asterisks), because CI logs of a public repo are public. If the subject is a
person, replace it with a role in the text.

Known limits: a name outside an attribution phrase is not seen; a subject
written in lower case is not seen; "X/COMPANY" is only checked when COMPANY is a
manufacturer in the data and the brand comes second; "source: X" is not checked
(too common in ordinary data text); the subject-before-verb form leaves out
"stated" and "verified" and skips a subject that contains a model number or
follows a bare number ("iPhone 13 Pro Max confirms"); words with digits and
single letters are skipped. Kay is an agent name on the allowlist and also a
given name, so "confirmed by Kay" passes for any real person called Kay; short
capitalised terms on the list could equal a person's initials. The gate cannot
block a direct push to main; it blocks the release (no tag, no website
dispatch) and fails the workflow.

### The broadcast source gate

A broadcast lens spec value cannot enter or change in the published database
unless the same change also brings its source. `build/broadcast_source_gate.py`
checks the broadcast shards (`source/broadcast-lenses/` and
`source/broadcast-details/`) and judges **changes only**: a value that did not
change is never judged, whatever its source state, so the old unsourced values do
not block any release. Cleanup batches pass it: a value that is moved to `null`
or `"unknown"` is never refused, and a filled value that brings its source passes.
Cine and PTZ data are not covered.

**What counts as a spec value.** The fields come from `output_schema.json`: every
property of the broadcast core `$def` (`lens_core`) and the broadcast details
`$def` (`lens_details_broadcast`), minus a short explicit non spec list in the
script. A schema field on neither list is gated by default, and a test fails
until a new schema field is classified.

- Core spec fields (5): `generation`, `focalLengthMin`, `focalLengthMax`,
  `zoomRatio`, `extenderFactor`.
- Detail spec fields (21): `weightG`, `lengthMm`, `frontDiameterMm`,
  `maximumDiameterMm`, `closeFocusM`, `imageCircleMm`, `opticalElements`,
  `introductionYear`, `maxApertureWide`, `maxApertureTele`, `apertureType`,
  `hasIS`, `hasMacro`, `hasServoZoom`, `hasServoFocus`, `servoConnector`,
  `formFactor`, `filterType`, `filterThreadMm`, `isParfocal`,
  `hasFocusBreathing`.
- Not spec fields, they never trigger the gate: `id`, `manufacturer`, `model`,
  `series`, `sensorFormat`, `mount`, `isPTZ`, `isFree`, `isCustom`, `notes`,
  `addedDate`, `lensType`, `description`, `fieldNotes`, `productUrl`,
  `manufacturerUrl`, `sources`, `webSources`. `sensorFormat` and `mount` decide
  whether a lens is a broadcast lens at all, so they classify rather than measure.

**What is refused.**

- A spec value that is set or altered (the new value is not null or `"unknown"`
  and differs from the baseline value) when the entry's source list gained no
  new source in the same change.
- A brand-new entry that sets a spec value and has an empty source list.

The source list of an entry is the union of its `sources` and `webSources`.
"Gained a source" means a string that was not in the baseline union; removing a
source never counts, so a value change plus an unrelated source removal is
refused. A core field change (for example a focal length) is judged against the
paired detail entry with the same `id`, because the source list lives there.
Entries are matched by `id` across all broadcast shards, so moving an entry to
another shard is not a new entry. Values are compared by type: `true` is not `1`,
and `2` equals `2.0`.

**A correction whose source is already listed.** When the supporting source is
already in the entry's list there is nothing new to add. Add an acknowledgement to
`build/broadcast_source_acks.json` in the same change:

```json
{"acks": [
  {"id": "<entry id>", "field": "<field>", "value": <the new value>,
   "source": "<a URL already in the entry's sources>"}
]}
```

An ack counts only when it is new in this change (an ack already in the baseline
file does not), its `value` equals the new value, and its `source` is in the
entry's source list (for a core field, the paired detail entry's list). The diff
then shows which listed source supports which new value. Acks are never pruned
automatically; an old ack that no longer matches does nothing. A new entry cannot
be rescued by an ack.

**Baseline.** The gate compares the shards on disk, uncommitted edits included,
against a baseline that is chosen automatically so a local run matches CI:

- pull request (`GITHUB_BASE_REF` set): the merge-base with `origin/<base>`.
- on `main`: the latest released `db-v` tag, not the previous commit. A change
  that reached main unsourced stays judged until it is fixed, instead of being
  forgiven by the next commit.
- any other branch: the merge-base with `origin/main` (local `main` as a
  fallback). A branch is judged on its net change, not commit by commit.
- `--base REF` overrides the choice.

**No baseline, and a stale baseline.** With no baseline at all (no release tag
on main, or no `main` to take a merge-base with), a local run passes with a
notice, because there is nothing to compare against. In CI (the `CI` variable is
set) the gate fails closed with exit code 2; a shallow checkout also gets this,
which is why the workflows use `fetch-depth: 0`. A local run also refuses when its
baseline is behind the remote: it asks `origin` for the latest `db-v` tag (or the
tip of `main`) and exits 2 with a message when the remote is ahead, because
comparing against old tags would judge changes that are already released. Run
`git fetch --tags origin` and run it again. Offline, `--no-remote-check` skips that
check. An explicit `--base` is trusted as given.

**Where it runs.**

- `broadcast-source-gate.yml`: a read only workflow on pull requests and on pushes
  to main that touch the broadcast shards, the ack file or the gate. This is the
  failing check on a pull request. It only blocks merging if the repository makes
  it a required status check, and a path filtered workflow that does not run for a
  PR cannot report a status, so require it only with that in mind.
- The first step of `assemble-database.yml`, before the shards are validated and
  assembled. A refused change stops the job there, so there is no tag and no
  website dispatch. This also covers the dry run on a feature branch.
- Locally: `python build/broadcast_source_gate.py` (optionally `--base REF`).
  The tests in `tests/test_broadcast_source_gate.py` run on macOS and Windows in
  `build-batches-tests.yml`.

**What Tim sees on a failure.** The report names the file, the entry id and the
field, the old and the new value, and what is missing, then how to fix it:

```
BROADCAST SOURCE GATE: 2 spec value(s) set or changed without a source (baseline: db-v44 (abc1234)).
  source/broadcast-details/broadcast_details_x.json | some-entry | weightG: 2100 -> 2250
    value set or changed, but this entry's sources and webSources gained no new source in this change.
  source/broadcast-lenses/broadcast_lens_x.json | some-entry | focalLengthMax: 52.0 -> 55.0
    core value changed, but the paired detail entry (source/broadcast-details/broadcast_details_x.json) gained no new source in this change.
```

Exit code 1 is a refusal, 2 means the gate could not run (bad, missing or stale
baseline, unreadable shard or ack file). Fix a refusal by adding a new source URL
to the entry, by recording an ack, or by moving the value to `null`.

Known limits: the gate checks that a source was brought, not that it is reachable
or that it supports the value; that is the reviewer's job, and an ack is an
unchecked claim. One new source covers every changed field of that entry and of
its core partner, because the list is per entry, not per field. A new source string
can be any non empty string, not only a URL. A renamed `id` is a new entry. The
first run with no baseline compares nothing. The gate cannot block a direct push to
main; it blocks the release (no tag, no website dispatch) and fails the workflow.
An unreleased bad value on main is judged against the last release, so it keeps
failing until fixed. It needs the `git` command line. Cine and PTZ entries are out
of scope.

## When the Action fails

1. Read the failed step log. The error names the shard path and the field.
2. Fix that shard under `source/`. Common cases: a detail entry added without
   its matching core entry (id set mismatch), a file that does not follow the
   naming pattern, a manufacturer slug that does not match the entry, or a JSON
   syntax error.
3. Run `python build/assemble.py --check` locally until it passes.
4. Commit and push again.

Nothing is published while validation is red, so a bad edit can never reach the
consumers. The previous good output stays in place until a green run replaces it.

## Releases, tags, and manifest.json

jsDelivr serves branch refs from edge caches that can fall behind origin, so a
purge is not reliable. Versioned tags are cached permanently and immutably, so
consumers should fetch a specific release tag, not `@main`.

Every push to `main` that touches `source/` cuts one immutable release:

1. The Action assembles the published files.
2. It reads the existing `db-v*` tags, takes the highest N, and computes the next
   tag `db-v{N+1}`. If that tag somehow already exists it fails and does nothing.
   It never moves, reuses, deletes, or force pushes a tag.
3. It writes `manifest.json`, commits the assembled output and the manifest, and
   pushes the commit to `main`.
4. It creates and pushes the tag `db-v{N+1}` at that commit.
5. It dispatches a `database-updated` event to PocketOP-Website and to
   directimages.nl using the `PAT_DISPATCH_WEBSITE` secret. This call is explicit
   because a push or tag made with the Action's `GITHUB_TOKEN` does not trigger
   any other workflow.

### manifest.json

`manifest.json` at the repo root is the release log. It records the latest tag,
an update timestamp, and one entry per release with the tag, a UTC timestamp, and
every published file's version and entry count:

```json
{
  "latest": "db-v7",
  "updatedAt": "2026-06-12T08:30:00Z",
  "releases": [
    {
      "tag": "db-v7",
      "timestamp": "2026-06-12T08:30:00Z",
      "files": {
        "lenses.json": { "version": "1.30.0", "entries": 727 },
        "devices.json": { "version": "1.6.0", "entries": 19 }
      }
    }
  ]
}
```

### How consumers fetch a release

1. Read the latest tag from the manifest over raw, which always reflects `main`:
   `https://raw.githubusercontent.com/directimages/PocketOP-Database/main/manifest.json`
2. Fetch the data files from that immutable tag over jsDelivr:
   `https://cdn.jsdelivr.net/gh/directimages/PocketOP-Database@db-v7/lenses.json`

Switching the iOS app and the websites over to this tag based fetching is Alex
and Sam's work in separate sessions. This pipeline only produces the tags and the
manifest.

### Dry run on branches and manual dispatch

A push to a feature branch or a manual `workflow_dispatch` never tags or
dispatches. It assembles, commits the output if it changed, prints the tag it
would create, and prints the manifest it would write. Real releases happen only
on a push to `main`.

### Relationship to notify-website.yml

`notify-website.yml` still exists and still dispatches on a direct push of the
root JSON to `main`. In normal operation nobody pushes root JSON by hand any more;
the Action commits it with `GITHUB_TOKEN`, which does not trigger
`notify-website.yml`. The release dispatch in this workflow is what notifies the
sites, so there is no double build. Do not hand edit the root JSON on `main`.

### When a release step fails

- Tag computation fails because the computed tag already exists: stop and inspect
  the tags with `git tag -l 'db-v*'`. Never delete or move a tag to work around
  this. Find why the counter and the tags disagree before doing anything.
- The push of the commit or the tag fails: the release is incomplete. The tag is
  only pushed after the commit, so re run the workflow; the counter advances to a
  fresh tag rather than reusing the failed one.
- The website dispatch fails: the tag and manifest are already published and
  correct. Re run only the dispatch, or check the `PAT_DISPATCH_WEBSITE` secret.
  jsDelivr already serves the new tag regardless of the dispatch.

## Future categories

The directory and naming scheme is built to take a new top level category later,
for example adapters and speedboosters, as its own `source/` subtree with its
own self describing filenames and its own output files. Adding that category is
a deliberate step because it introduces a new published file that consumers must
learn about. Adding manufacturers, brands, mounts, lenses, cameras, or devices
inside the existing categories never requires any configuration change.

## Creating new entries: create_entries.py (POS-W62)

Today a new entry can enter the pipeline by hand appending a full object to a
core brand shard and its matching details brand shard, then running
`assemble.py`, which is the first point that validates it. `build/create_entries.py`
is a create route that validates a batch of brand-new entries entirely before
anything is written, then optionally writes them.

A batch file is a JSON object shaped like:

```json
{
  "core":    {"path": "source/.../<core shard>.json",    "entries": [...]},
  "details": {"path": "source/.../<details shard>.json", "entries": [...]}
}
```

Both sides are required. The tool checks every staged entry against the
exact destination `$def` in `output_schema.json`, the core/details field
partition (`field_registry.py`), an id-must-be-new check (this tool creates,
it never updates an existing id, see `apply_fields.py` for that), and the
core/details id-set pairing check. Every violation across the whole run is
collected and reported together, per entry id and field. Nothing is written
while any violation exists, and nothing is written at all unless `--write`
is given:

```
python build/create_entries.py <batch.json> [more ...]            # dry run
python build/create_entries.py --write <batch.json> [more ...]    # writes
```

Any argument that is a directory is expanded to every `*.json` file directly
inside it, sorted, and each is treated exactly as if it had been passed on
the command line (folder mode). This is a pure input convenience; what gets
validated and how does not change.

## Patching existing entries: apply_fields.py

`build/apply_fields.py` is the validating path for changing fields on existing
detail entries. A staged map is `{ "entry-id": { "field": value } }`, given as a
`.json` file or as ```json blocks inside a staging `.md` file. Every id is
checked first; any orphan id aborts the run and nothing is written. Every field
is set wholesale, except `fieldNotes`, which merges: given keys are added or
overwritten and existing keys stay (POS-D17).

```
python build/apply_fields.py <map.json|pass.md> [more ...]
```

### Removing fieldNotes keys

A merge can never remove a key, so a map states a removal explicitly with the
reserved instruction `removeFieldNotes`, a list of key names, inside the
entry's field map. It works the same in the `.json` and the `.md` format:

```json
{
  "example-entry-id": {
    "removeFieldNotes": ["hasMacro"],
    "fieldNotes": { "filterThreadMm": "merged note" },
    "weightG": 1234
  }
}
```

The same entry can set other fields and merge other `fieldNotes` keys in the
same map. The rules:

- Removal is never implicit. A map without `removeFieldNotes` behaves exactly as
  before.
- The value must be a non empty list of non empty strings with no duplicates.
  Anything else is malformed and aborts the run.
- Every named key must exist in the entry's current `fieldNotes`. A key the
  entry does not have aborts the run, so rerunning an applied removal fails
  loudly instead of passing silently.
- A key that the same entry both sets and removes aborts the run, also when the
  set and the removal sit in different blocks or files.
- When no `fieldNotes` key remains, the `fieldNotes` key itself is deleted, so
  the entry looks like one that never had notes. This holds in every category
  (broadcast, cine, ptz) and applies only to entries a removal ran on.
- Several blocks or files: `removeFieldNotes` combines like `fieldNotes` does,
  as one whole value per (id, field). Two blocks naming the same entry with
  different key sets abort with "Conflicting values"; identical key sets are
  accepted, in any order. There is no union, so list every key to remove from
  one entry in a single block.
- All checks run before any write, the same all or nothing behavior as an
  orphan id.

The run output reports removals in their own section, apart from the applied
fields:

```
Applied 0 field(s) to 0 id(s) across 1 shard(s):
  source/broadcast-details/broadcast_details_example.json
Removed 1 fieldNotes key(s) from 1 id(s):
  example-entry-id: hasMacro
```

The tests are in `tests/test_apply_fields.py` (synthetic fixtures only).

## Markdown-to-batch conversion: build_batches.py

Kay stages new-entry batches as JSON inside fenced code blocks in markdown
staging files in the vault. `build/build_batches.py` is the only place that
converts that markdown into the plain batch JSON `create_entries.py`
understands. It never validates schema, never writes to a shard, and never
runs the real import, that stays `create_entries.py`'s job, invoked here only
in dry run. The two tools are kept as separate layers on purpose: the tool
that catches mapping errors must never itself become a source of them.

### Heading contract

No markers. No hand typed shard paths. `build_batches.py` reads Kay's
existing block headings and derives every shard path from the entry data
itself, reusing `assemble.py`'s own `slugify`, `SHARD_CATEGORIES`, and
`is_broadcast` so naming can never diverge from the assembler:

````
## Core (ptz_cameras_minrray, append 17)
```json
[ ...core entry objects... ]
```
## Detail (ptz_details_minrray, append 17)
```json
[ ...details entry objects... ]
```
````

A block is a markdown heading whose text starts with the word Core, or with
Detail or Details, case-insensitive, trailing text after that word ignored
(the `(ptz_cameras_minrray, append 17)` part above is decoration, not read),
immediately followed (blank lines tolerated, nothing else) by exactly one
fenced json block opening with a line that is exactly ` ```json ` and closing
with a line that is exactly ` ``` `. A heading that matches the word but is
not followed by a fence is not a block, ignored, not an error. This also
means bold paragraph text like `**Core -- correcties...**`, the style
`IMPORT-QUEUE.md` uses for corrections to existing entries, is never picked
up, since it is not a markdown heading; only real `#`/`##`/etc. headings
count.

Path derivation, fully from the entry, no marker to trust or mistype:

- A core entry with a `brand` field is a PTZ core:
  `source/ptz-cameras/ptz_cameras_<brandslug>.json`.
- A core entry with a `manufacturer` field is a lens core. If
  `assemble.is_broadcast(entry)` it is broadcast:
  `source/broadcast-lenses/broadcast_lens_<mfrslug>.json`. Otherwise cine,
  two level by mount: `source/cine-lenses/<mountslug>/cine_lens_<mountslug>_<mfrslug>.json`.
- A core entry with neither field matches no category and fails the file.
- A details entry carries only an `id`, no brand or manufacturer of its own.
  It is paired to the core entry with the same `id` in the same file and
  inherits that core entry's classification and shard.

One Core heading (or several) can hold entries for more than one brand or
manufacturer at once: every core entry pooled from every Core heading in the
file is classified and grouped by its derived shard path automatically, and
the matching Detail entries are grouped by their paired core's shard. One
batch file is written per resulting shard pair, named after the core shard's
filename stem, for example `output/ptz_cameras_minrray.json`, unique by
construction since the stem is derived the same deterministic way every time.

Failure is per file and loud, before anything is written for that file:

- a details entry whose `id` has no matching core entry in the same file
- a core entry that matches no category (no `brand` or `manufacturer` field)
- a core or details entry missing a non empty `id`
- a duplicate core `id` staged twice within the same file's pooled core entries
- a core/details `id` set mismatch within one derived shard group
- unparseable or non array json in a matched block

A file with no Core/Detail blocks is not an import file: skip it, log it,
leave it in `inbox/`. A file with at least one block is an import file, and
every batch derived from it must resolve cleanly or the whole file fails:
nothing from it is written, it stays in `inbox/`, and the reasons are logged.
An output stem that collides with one already written earlier in the same
run is also a failure for the later file, so two files can never silently
overwrite each other's output. Only a file all of whose batches derived and
wrote cleanly gets them written to `output/` and is moved to `done/`.

### The four folders

One base directory holds four subfolders:

```
inbox/  staging markdown to process
output/ the clean batch json files this script produces
done/   staging markdown that processed cleanly, moved here
logs/   one timestamped run log per invocation
```

The base directory is never hardcoded in source. It is read from the
`POCKETOP_IMPORT_BASE` environment variable (set once per machine, the same
pattern as the existing `ANTHROPIC_DEFAULT_OPUS_MODEL`), with an optional
positional CLI argument as an override:

```
python build/build_batches.py                    # uses $POCKETOP_IMPORT_BASE
python build/build_batches.py /path/to/base       # overrides it
python build/build_batches.py --dry-run           # writes output/, moves nothing to done/
```

### What a run does

1. Reads every `*.md` file in `inbox/`, sorted.
2. For each file, parses its Core/Detail blocks and derives every batch's
   shard paths from the entry data. A clean file gets one
   `output/<core shard stem>.json` per derived shard pair, in the exact
   shape `create_entries.py` expects, and moves to `done/` (unless `--dry-run`).
3. If `output/` has any `*.json` files afterward, runs
   `create_entries.py` in dry run over the whole `output/` folder (never
   `--write`) and prints its verdict. This never writes to any shard; the
   real write stays a separate, deliberate, manual step.
4. Writes one timestamped log to `logs/` recording what was read, written,
   skipped, and failed, and exits nonzero if any inbox file failed.

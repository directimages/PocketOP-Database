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
2. Runs `python build/assemble.py`, which validates every shard and writes the
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

## Markdown-to-batch conversion: build_batches.py

Kay stages new-entry batches as JSON inside fenced code blocks in markdown
staging files in the vault. `build/build_batches.py` is the only place that
converts that markdown into the plain batch JSON `create_entries.py`
understands. It never validates schema, never writes to a shard, and never
runs the real import, that stays `create_entries.py`'s job, invoked here only
in dry run. The two tools are kept as separate layers on purpose: the tool
that catches mapping errors must never itself become a source of them.

### Marker contract

A batch is one `batch-core` marker and one `batch-details` marker sharing the
same `name` attribute. Each marker is an HTML comment on its own line,
immediately followed (blank lines tolerated, nothing else) by exactly one
fenced json block:

````
<!-- batch-core shard="source/ptz-cameras/ptz_cameras_minrray.json" name="minrray" -->
```json
[ ...core entry objects... ]
```
<!-- batch-details shard="source/ptz-details/ptz_details_minrray.json" name="minrray" -->
```json
[ ...details entry objects... ]
```
````

Both `shard` and `name` are required attributes; attribute order does not
matter. The fence must open with a line that is exactly ` ```json ` and close
with a line that is exactly ` ``` `. The json block is the raw entries array.
Shard paths are read verbatim from the markers, never inferred from a brand
or filename.

Failure is per file and loud: a file with no markers is not an import file
and is skipped, left in `inbox/`. A file with at least one marker is an
import file, and every batch in it must resolve cleanly (parseable JSON, an
array, a matching name on both sides) or the whole file fails: nothing from
it is written, it stays in `inbox/`, and the reasons are logged. A batch name
that collides with a name already written earlier in the same run is also a
failure for the later file, so two files can never silently overwrite each
other's output. Only a file all of whose batches parsed cleanly gets its
batches written to `output/` and is moved to `done/`.

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
2. For each file, parses and pairs its batches. A clean file gets one
   `output/<name>.json` per batch, in the exact shape `create_entries.py`
   expects, and moves to `done/` (unless `--dry-run`).
3. If `output/` has any `*.json` files afterward, runs
   `create_entries.py` in dry run over the whole `output/` folder (never
   `--write`) and prints its verdict. This never writes to any shard; the
   real write stays a separate, deliberate, manual step.
4. Writes one timestamped log to `logs/` recording what was read, written,
   skipped, and failed, and exits nonzero if any inbox file failed.

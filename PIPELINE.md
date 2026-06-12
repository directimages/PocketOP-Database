# PocketOP-Database publishing pipeline

This repo publishes the JSON files that the iOS app and pocketop.app consume.
The published files at the repo root are generated output. You do not edit them
by hand. You edit small shard files under `source/`, and a GitHub Action
validates them, assembles the published files, and commits the result.

This document is the Milestone 1 version. It covers sharding and assembly.
Release tagging and the manifest are added in Milestone 2.

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

## Future categories

The directory and naming scheme is built to take a new top level category later,
for example adapters and speedboosters, as its own `source/` subtree with its
own self describing filenames and its own output files. Adding that category is
a deliberate step because it introduces a new published file that consumers must
learn about. Adding manufacturers, brands, mounts, lenses, cameras, or devices
inside the existing categories never requires any configuration change.

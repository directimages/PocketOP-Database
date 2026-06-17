# Legacy schema freeze

Frozen field whitelist for the legacy outputs. Mechanically derived from the
current legacy outputs on `@main`; do not hand edit. Regenerate with
`python build/derive_legacy_whitelist.py`.

## Why this exists

The legacy outputs below still serve pre update 2 apps in the field via the
`@main` route. Their schema is frozen: when new detail fields enter the pipeline
at the upcoming data fill, those fields must reach the primary split outputs but
must never leak into the legacy outputs, because an old build can stumble over an
unexpected field. The whitelist captures the exact field set each legacy output
carries today. The strip step in `assemble.py` removes any entry field or top
level key not on the whitelist from these outputs before they are written. The
primary split outputs are never touched.

## How it is derived

For each legacy output the generator reads the current root file and records the
top level keys present and the sorted union of every entry field key present
across all entries. Nothing is researched, inferred, or hand listed. The field
sets below are exactly what is in the files today.

## How it is proven

`python build/assemble.py --check` runs the strip and then diffs every assembled
output, field for field, against the current root file it replaces. Because the
whitelist is exactly the set of keys present today, the strip removes nothing and
the diff stays clean. If the diff is not clean, the derivation is wrong, not the
data: stop and report, do not widen the whitelist to force a pass.

## Lifecycle

The strip is wired into `assemble.py` live, as a proven no op today. It begins
removing fields the moment the first field outside this whitelist appears in the
source. The strip and this whitelist are throwaway: once the `@main` legacy route
is retired (a separate Martijn decision), both are deleted.

## Granularity

The strip operates at the entry top level and the output top level only. It does
not recurse into nested objects (for example `sources` or `fieldNotes`), which is
not where new fields enter the pipeline.

## Teardown (when @main is retired)

The freeze is throwaway. Once Martijn retires the `@main` legacy route (a
separate decision, POS-D31), delete the whole mechanism in one pass:

- Delete the three build files: `build/legacy_whitelist.json`,
  `build/legacy-schema-freeze.md` (this document), and
  `build/derive_legacy_whitelist.py`.
- In `build/assemble.py`, delete the `strip_legacy_outputs` and
  `load_legacy_whitelist` functions and the `LEGACY_WHITELIST_PATH` constant.
- In `build/assemble.py`, remove the two `strip_legacy_outputs(built)` call
  sites, one in `run_check` and one in `run_assemble`.

At that point the legacy outputs can also be dropped from the assembler entirely;
that is part of the same `@main` retirement, not this freeze.


## lenses.json

Legacy union of broadcast plus cine core lenses.

Entry array key: `lenses`. Entries today: see source.

Allowed top level keys (3):

- `version`
- `lenses`
- `updatedAt`

Allowed entry fields (16):

- `addedDate`
- `extenderFactor`
- `focalLengthMax`
- `focalLengthMin`
- `generation`
- `id`
- `isCustom`
- `isFree`
- `isPTZ`
- `manufacturer`
- `model`
- `mount`
- `notes`
- `sensorFormat`
- `series`
- `zoomRatio`


## lens-details.json

Legacy union of broadcast plus cine lens details.

Entry array key: `lenses`. Entries today: see source.

Allowed top level keys (3):

- `version`
- `updatedAt`
- `lenses`

Allowed entry fields (25):

- `closeFocusM`
- `fieldNotes`
- `filterThreadMm`
- `filterType`
- `focusRingRotationDeg`
- `formFactor`
- `frontDiameterMm`
- `gearPitch`
- `hasFocusBreathing`
- `hasFrontRotation`
- `hasMacro`
- `hasServoFocus`
- `hasServoZoom`
- `id`
- `imageCircleMm`
- `introductionYear`
- `isParfocal`
- `lengthMm`
- `lensType`
- `manufacturerUrl`
- `opticalElements`
- `servoConnector`
- `sources`
- `webSources`
- `weightG`


## ptz-details.json

Legacy hyphen alias of ptz_details.json.

Entry array key: `cameras`. Entries today: see source.

Allowed top level keys (3):

- `version`
- `updatedAt`
- `cameras`

Allowed entry fields (23):

- `controlProtocols`
- `depthMm`
- `fieldNotes`
- `hasCeilingMount`
- `hasIR`
- `hasPoE`
- `hasWallMount`
- `heightMm`
- `id`
- `manufacturerUrl`
- `maxPanSpeedDegS`
- `maxTiltSpeedDegS`
- `minLux`
- `mountThreads`
- `panRangeDeg`
- `poeClass`
- `presetCount`
- `sources`
- `tiltRangeDeg`
- `videoOutputs`
- `weightG`
- `whiteBalanceModes`
- `widthMm`

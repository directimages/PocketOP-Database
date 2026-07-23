# Changelog

Most recent changes at the top. One line per file changed per commit.

## lenses.json
### v1.34.0 — 2026-07-23

- Cine datafixes batch 4, pass 4a (value corrections/fills only, no entry-set change): 17 cine core model string corrections (8 Cooke S8/i FF, 2 DZOFilm Vespid Retro, 4 Tokina Vista-P 180mm across PL/E/EF/LPL, 1 Laowa Ultima 25-600mm, 2 Fujinon)
- zeiss-cp2-18mm-t3-6 sensorFormat corrected fullFrame -> superThirtyFive (image circle 30.0mm per POS-D28, versus 43.4mm on every other CP.2; B&H confirms Super 35/Normal 35 coverage, not full frame)
- cine_lenses.json split bumped to v1.31.0 (same 18 core corrections)
- Source: reference/cine-batch4a-apply-2026-07-23.md, Kay-verified against live db-v14 (zero orphans, every current value matched the documented "from" side)

### v1.33.0 — 2026-07-23

- Broadcast core datafixes (6): angenieux-t12x5-3b focalLengthMax 63.6 -> 64.0, zoomRatio 12.0 -> 12.08 (64.0/5.3); angenieux-t26x7-8b model "T26x7.8BESMD AIF HR" -> "T26x7.8BESMD HD"; nikon-s13x9 model "S13x9-EMS" -> "S13x9B1-EMS-20", notes dropped "Approximate model designation."; nikon-s19x8 model "ED S19x8" -> "S19x8B"; nikon-s9x5-5b notes "Focal range estimated. 2x extender likely." -> "2x extender likely." (focal range now barrel-confirmed); zeiss-digizoom-17-112 zoomRatio 6.5 -> 6.59 (112/17)
- Two broadcast entries removed: canon-uj25ex7-6b (confirmed phantom; canon-cj25ex7-6b is the canonical entry), fujinon-la30x7-8brm-xb2 (confirmed duplicate; XB2 semi-servo-kit variant of fujinon-la30x7-8, which stays). Broadcast entry count 126 -> 124
- broadcast_lenses.json split bumped to v1.32.0 (same datafixes and deletions)

### v1.32.1 - 2026-06-20

- canon-hj15ex8-5b: extenderFactor corrected 2.0 -> 1.0. No built-in extender (Kay-verified vs Canon, B&H, Adorama, AbelCine; the 4K twin canon-cj15ex8-5b was already 1.0). Single-field core correction
- broadcast_lenses.json split bumped to v1.31.1 (same correction)

### v1.32.0 — 2026-06-19

- Canon CJ25ex7.6B import: 1 new broadcast entry (`canon-cj25ex7-6b`), CJ series, 7.6–190.0mm, 25×, extender 2.0, B4, twoThirdsInch, 4K UHD. ENG portable
- addedDate: 2026-06-19. Specs supplied and verified by Kay (canon-europe.com Tier-1 + B&H + PRNewswire); pure import, no Tim research
- broadcast_lenses.json split bumped to v1.31.0
- maxApertureWide/maxApertureTele/apertureType/hasIS and description intentionally omitted — gated, land in their own later batches

### v1.31.1 — 2026-06-13

- sony-fe-pz-28-135mm-f4-g-oss: addedDate corrected 2026-06-14 → 2026-06-13 (actual commit date)

### v1.31.0 — 2026-06-13

- Sony FE PZ 28-135mm F4 G OSS import: 1 new entry, E mount, fullFrame, G series, 4K UHD generation
- addedDate: 2026-06-13. Source: Sony Asia spec page (Tier 1)

### v1.30.0 — 2026-06-11

- Zeiss Panoptes 65 import: 8 new entries (35/40/45/55/70/90/110/135mm T2.2), LPL mount, largeFormat, 59.9mm image circle, series "Panoptes 65"
- 95mm filter thread, introductionYear 2026. 25mm and 180mm deferred — close focus / weight specs pending (see incomplete_data.md entries #10 + #22)
- Source: zeiss.com/panoptes65 (Tier 1)

### v1.29.0 — 2026-06-11

- Tokina Vista-C Prime import: 48 new entries (12 focal lengths × PL/EF/E/LPL)
- Focal lengths: 18/21/25/29/35/40/50/65/85/105/135mm T1.5 + 180mm T1.9
- Full frame / VistaVision (46.7mm image circle), series "Vista-C", generation "Cinema"
- New optical formula versus Vista and Vista-P: red/blue flare character, increased spherical aberration, reduced contrast, nearly zero focus breathing
- 18mm: filterType null (no screw-in filter thread); all others: 112mm front thread
- MFT not imported (POS-D15, out of scope)
- All entries stamped addedDate: 2026-06-11
- Source: tokinacinemausa.com (Tier 1)

### v1.28.1 — 2026-06-10

- Dispatch test commit: version-only bump to trigger notify-website GitHub Action. No lens data changed.

### v1.28.0 — 2026-06-09

- Fujinon broadcast import: 2 new entries
  - `fujinon-ua16x4berd` (UA16x4BERD): UA series, 4.0–64.0mm, 16×, extender 2.0, B4, twoThirdsInch, 4K UHD. Ultra-wide portable zoom, BERD drive unit with 16-bit encoders
  - `fujinon-ua30x7-3berd` (UA30x7.3BERD): UA series, 7.3–219.0mm, 30×, extender 2.0, B4, twoThirdsInch, 4K UHD. Portable zoom, BERD drive unit with 16-bit encoders for virtual studio tracking
- Both stamped `addedDate: 2026-06-09`. Specs sourced by Kay from manufacturer documents (videobrokers tier-2 listings, pending verification against official Fujifilm source)
- Both removed from the announcements-watchlist (were logged as Under Development)
- Canon CN30x40 IAS J R1/P1 intentionally NOT imported — already in the DB as `canon-cn30x40-ias-pl` + `canon-cn30x40-ias-rf`; a separate spec conflict (S35/1.5× vs FF/1.0×) is being reconciled by Kay

### v1.27.0 — 2026-06-09

- Fujinon broadcast import: 2 new entries
  - `fujinon-la30x7-8brm-xb2` (LA30x7.8BRM-XB2): LA series, 7.8–234mm, 30×, extender 1.0, B4, twoThirdsInch, 4K UHD. XB2 variant of LA30x7.8BRM with expansion connector for virtual/remote production
  - `fujinon-ua94x8-7besm` (UA94x8.7BESM): UA series, 8.7–818mm, 94×, extender 2.0, B4, twoThirdsInch, 4K UHD. Box lens, under development per 2026 Product Guide
- Both stamped `addedDate: 2026-06-09`. Specs sourced by Kay from official Fujifilm documents

### v1.26.0 — 2026-06-09

- Schema: added `addedDate` field (ISO `YYYY-MM-DD` or `null`) to every entry. Marks when a lens was first committed to main after the App Store launch
- Baseline (pre-launch) entries carry `addedDate: null` — they must never surface as "recently added". 611 of 667 entries
- Non-null dates assigned to the 56 entries added after launch, dated by their first commit to main:
  - `2026-06-01` (8): Zeiss Nano Prime 18/24/35/50/75/100mm T1.5 + Zeiss Supreme Prime Radiance 18mm/135mm T1.5 (commit 7c3ecd8)
  - `2026-06-08` (48): Tokina Vista-P Prime T1.5 — 12 PL (commit c1db1e4) + 36 EF/E/LPL mount variants (commit 7b75848)
- Reclassification/prose commits (412d262, 92ac0a4) added no new lenses — those entries remain `addedDate: null`
- Going forward: every new lens import sets `addedDate` to the import's commit date on insert

### v1.25.0 — 2026-06-08

- Tokina Vista-P Prime T1.5 mount variants: 36 new entries (12 focal lengths × EF/E/LPL), full-frame, 46.7mm image circle, series "Vista-P". Follow-up to v1.24.0 PL import
- id suffix convention: -ef / -e / -lpl (PL entries keep the base id, no suffix). Model string identical across mounts; only mount differs
- MFT not imported — out of scope (POS-D15)
- Source: tokinacinemausa.com spec chart PDF (per-mount columns)

### v1.24.0 — 2026-06-08

- Tokina Vista-P Prime T1.5 import: 12 new entries (18/21/25/29/35/40/50/65/85/105/135/180mm), PL mount, fullFrame, 46.7mm image circle (VistaVision coverage), series "Vista-P"
- Vista-P is a distinct product line from the existing Cinema Vista primes — a modified optical design with increased spherical aberration and reduced contrast for a vintage Petzval-type look. Cinema Vista entries left untouched
- 180mm was absent from the website spec table but confirmed present in the manufacturer All-Focal-Length PDF chart; imported with full specs
- EF, MFT, E, LPL mounts deferred (one entry per mount, POS-D09) pending Kay decision; MFT is out of scope per POS-D15
- Source: tokinacinemausa.com product page + spec chart PDF

### v1.23.2 — 2026-06-03

- notes prose cleanup: removed "large format" wording from 9 entries now classified fullFrame (8× Cooke S8/i FF, 1× MasterBuilt CFZ 27-60mm T2.9)
- masterbuilt-cfz-27-60mm-t2-9: notes spec corrected from "Large Format (54.12mm — Alexa Open Gate/IMAX 65)" to "Full-frame / VistaVision (46.5mm image circle)"; source citation updated to masterbuiltlenses.com (46.5mm verified, HIGH); the prior 54.12mm/Alexa 65 claim is physically impossible at a 46.5mm image circle

### v1.23.1 — 2026-06-03

- sensorFormat reclassification: 16 entries corrected from largeFormat to fullFrame (8× Cooke S8/i FF, 7× Tokina Cinema Vista, 1× MasterBuilt CFZ 27-60mm T2.9)
- Reason: image circles 46.3mm (Cooke), 46.7mm (Tokina), 46.5mm (MasterBuilt) cover full frame / VistaVision only, not 65mm large format (largeFormat requires 54mm+). Verified against cookeoptics.com, tokinacinema.com, masterbuiltlenses.com. Leitz THALIA 65 (60mm) and Viltrox LUNA 42-420mm (60mm) correctly remain largeFormat

### v1.23.0 — 2026-06-01

- Zeiss Nano Prime import: 6 new entries (18/24/35/50/75/100mm T1.5), E-mount, fullFrame, 46.5mm image circle
- Zeiss Supreme Prime Radiance import: 2 new entries (18mm T1.5, 135mm T1.5), PL mount, fullFrame

### v1.19.0 — 2026-05-17

- Cooke SP3 primes import: 18 new entries (6 focal lengths × 3 mounts: E, RF, L)
- Focal lengths: 18mm/25mm/32mm/50mm/75mm/100mm T2.4, Full Frame, SP3 series
- 18mm introductionYear: 2024; 25–100mm introductionYear: 2023

## cine_lens_details.json
### v1.52.0 — 2026-07-23

- Cine datafixes batch 4, pass 4a: 88 detail-id overwrites/fills via build/apply_fields.py across filterThreadMm/filterType/hasMacro/isParfocal/hasFocusBreathing/fieldNotes/frontDiameterMm. 153 fields applied to 88 ids across 15 shards, zero orphans (pre-flight verified against db-v14)
- Field counts: filterThreadMm 66, fieldNotes 58 (all merged in, none previously present — POS-D17 merge-per-key), hasMacro 12, filterType 8, hasFocusBreathing 5, isParfocal 3, frontDiameterMm 1
- Overwrites include: all Cooke Mini S4/i, Panchro/i Classic FF, S4/i, S7/i, S8/i FF and Varotal/i FF filterThreadMm "none" -> published thread size (Varotal/i FF carries the decimal 112.5); dzofilm-arles-14mm/-18mm + dzofilm-vespid-16mm filterType/filterThreadMm -> "none"/"none"; dzofilm-vespid-retro-35mm-t2-1 filterType/filterThreadMm flip -> front_thread/77; sigma-cine-18-35mm-t2-0 + sigma-cine-50-100mm-t2-0 hasFocusBreathing minimal -> moderate; 3 Laowa Ranger S35 hasFocusBreathing none -> minimal; irix-cine-21mm-t1-5-l filterThreadMm 86 -> 95; 4 Thypoch Simera-C filterThreadMm 67 -> 62; 4 Tokina Vista-C 18mm (E/EF/LPL/PL) filterThreadMm null -> 112 + filterType -> front_thread; cooke-panchro-i-classic-ff-18mm-t2-2 frontDiameterMm 125 -> 110
- Fills (previously absent/null): hasMacro true on 12 entries; isParfocal true on 3 entries
- Source: reference/cine-batch4a-apply-2026-07-23.md, Kay-verified against live db-v14 (zero orphans, every current value matched the documented "from" side)

### v1.51.0 — 2026-07-23

- Cine aperture/IS batch (batch 3): maxApertureWide, maxApertureTele, apertureType and hasIS populated for 601 of 603 live cine entries via build/apply_fields.py. First population of these fields for cine; schema-registered and gated, now filled. Values Kay-supplied and verified (cine aperture/IS consolidation, reference/cine-import-map-batch3-aperture-is-2026-07-19.md). 2404 fields applied to 601 ids across 45 shards, zero orphans (pre-flight verified against db-v13)
- Two entries intentionally left without these fields in this pass (fujinon-mk18-55mm-t2-9, fujinon-mk50-135mm-t2-9), the same phantom EF bases already excluded from the batch 2 description backfill; removal is scoped to batch 4

### v1.50.0 — 2026-07-23

- Cine descriptions backfill (batch 2 of 4): description field written on 601 of 603 live cine entries. No other field changed. Two entries intentionally left without a description in this pass (fujinon-mk18-55mm-t2-9, fujinon-mk50-135mm-t2-9), pending a separate batch

### v1.49.0 — 2026-06-18

- fieldNotes-contract compliance pass (no core change; cine detail output only). Stripped internal references, source citations and process notes from user-facing fieldNotes per reference/fieldnotes-contract.md. Rides db-v8.
- canon-cn20x50-ias-h-p1 (cine_details_pl_canon): fieldNotes.hasFocusBreathing reworded — dropped the CineD citation and the optical-design rationale wording.
- sigma-af-cine-28-105mm-t3-ff-e, sigma-af-cine-28-45mm-t2-ff-e (cine_details_e_sigma) + sigma-af-cine-28-105mm-t3-ff-l, sigma-af-cine-28-45mm-t2-ff-l (cine_details_l_sigma): fieldNotes.isParfocal reworded — dropped the "(B&H Photo, WEX)" citation.
- sony-fe-pz-28-135mm-f4-g-oss (cine_details_e_sony): fieldNotes.gearPitch reworded — dropped the "(POS-D33)" internal marker.

### v1.48.0 — 2026-06-17

- Schema-gate reconciliation datafixes (registry-vs-data, dispatched 2026-06-16). No core change; cine detail output only.
- filterType "rear_filter" → "internal": 28 entries — 20 ARRI Signature (16 Primes + 4 Zooms, cine_details_lpl_arri) + 8 Canon EF tele primes (cine_details_ef_canon). Field value only; "rear_filter" text in sources strings left intact.
- filterType "front" → "front_thread": 6 Zeiss Nano Prime T1.5 (18/24/35/50/75/100mm, cine_details_e_zeiss). filterThreadMm already 86, untouched.
- opticalElements descriptive string → element integer: 48 Tokina Vista-C (12 focal lengths × E/EF/LPL/PL). 18→17, 21→19, 25→16, 29→18, 35→14, 40→15, 50→13, 65→14, 85→14, 105→16, 135→16, 180→17. Group count dropped from the value; per-field sources note retained. 8 Angénieux Optimo opticalElements "unknown" untouched.

## broadcast_lens_details.json
### v1.53.0 — 2026-07-23

- Broadcast aperture/IS batch: maxApertureWide, maxApertureTele, apertureType and hasIS populated for all 124 broadcast lenses via build/apply_fields.py. First population of these fields for broadcast; schema-registered and gated, now filled. Values Kay-supplied and verified (broadcast aperture/IS B5 consolidation). 499 fields applied to 124 ids across 5 shards, zero orphans (pre-flight verified against db-v10)
- fieldNotes.hasIS added on three Fujinon entries: fujinon-ha42x9-7, fujinon-ha42x13-5 (OS-TECH optical image stabilization offered on the U48/G48 factory variants; standard S48/F48 have none), fujinon-xa87x9-3 (available with Fujinon's internal image stabilization as a factory option)
- Two entries removed to match the core deletions: canon-uj25ex7-6b, fujinon-la30x7-8brm-xb2

### v1.52.0 - 2026-06-20

- Broadcast description population (Fase 1): 126 user-facing description fields applied across broadcast_details_angenieux / canon / fujinon / nikon / zeiss via build/apply_descriptions.py. Additive field population only; prose imported verbatim from the staged pass blocks, no other field touched. The legacy lens-details union strips description by the freeze, so it stays byte-identical and is not bumped

### v1.51.0 — 2026-06-19

- Canon CJ25ex7.6B sidecar (`canon-cj25ex7-6b`, broadcast_details_canon): weightG 1990, lengthMm 223.6, closeFocusM 0.8, introductionYear 2018, imageCircleMm 11.0, filterType front_thread, filterThreadMm 105, hasMacro true, servo zoom/focus true, servoConnector 20pin, formFactor portable. frontDiameterMm/opticalElements/manufacturerUrl null. Source: canon-europe.com (Tier 1) + B&H + PRNewswire. Pure import, specs Kay-verified

### v1.50.0 — 2026-06-18

- fieldNotes-contract compliance pass (no core change; broadcast detail output only). Rides db-v8.
- fujinon-ua30x7-3berd (broadcast_details_fujinon): fieldNotes key renamed filterThreadNote → filterThreadMm (key must be an existing field name — fieldnotes-contract hard rule, so the note renders inline under that field), and the value reworded to drop the storage/Update-2 migration process notes. Now "Two filter thread options: M95x1 and M107x1."

### v1.49.0 — 2026-06-17

- filterThreadMm cross-field invariant fixes (6 B4 portable broadcast zooms; filterType/filterThreadMm only, no core change). Verified Tier-1 from Canon Operation Manual OMLS-D037A, Sect. 7 Product Specifications, for the three numeric values.
- canon-cj45ex13-6b (broadcast_details_canon): filterThreadMm "none" → 127 (barrel thread 127 mm P0.75; the φ127mm in Canon marketing is the front element, the barrel still carries a 127 P0.75 thread). filterType front_thread unchanged. Manual provenance source added.
- canon-cj45ex9-7b (broadcast_details_canon): filterType "internal" → "front_thread", filterThreadMm "none" → 127 (shares the CJ45 127 mm P0.75 thread). Manual provenance source added.
- canon-cj15ex4-3b (broadcast_details_canon): filterThreadMm null → "unknown" (size not published; the 2026-06-14 "127" was mis-attributed, belongs to the CJ45). filterType front_thread unchanged. No source change.
- canon-j35ex15b (broadcast_details_canon): filterThreadMm 105 → 125 (125 mm P1.0). filterType front_thread unchanged. Manual provenance source added.
- angenieux-t12x5-3b, angenieux-t15x8-3b (broadcast_details_angenieux): filterThreadMm "none" → "unknown" (size not published; prior value rested on a junk Amazon listing). filterType front_thread unchanged. No source change.

### v1.48.0 — 2026-06-17

- Schema-gate reconciliation datafixes (registry-vs-data, dispatched 2026-06-16). No core change; broadcast detail output only.
- fieldNotes bare string → object {"hasMacro": ...}: canon-uj25ex7-6b, canon-xj23x7b (broadcast_details_canon). Value "Macro available via optional MCJ-S02 accessory" preserved inside the object.
- nikon-s19x8 (broadcast_details_nikon): servoConnector "unconfirmed" → null, hasServoZoom "unconfirmed" → null.

## lens-details.json
### v1.54.0 — 2026-07-23

- Legacy union rebuild aggregating the cine_lens_details v1.52.0 pass 4a datafixes above (88 detail ids, 153 fields) and the cine_lenses v1.31.0 core corrections (17 model strings + 1 sensorFormat fix). No entries added or removed

### v1.53.0 — 2026-07-23

- Legacy union rebuild aggregating the cine_lens_details v1.51.0 aperture/IS batch above. maxApertureWide/maxApertureTele/apertureType/hasIS are outside the legacy whitelist and do not surface here. No lens core change

### v1.52.0 — 2026-07-23

- Legacy union rebuild aggregating the cine_lens_details v1.50.0 description backfill above (601 cine entries). No lens core change

### v1.51.0 — 2026-07-23

- Legacy union rebuild aggregating the broadcast_lens_details v1.53.0 aperture/IS batch above. maxApertureWide/maxApertureTele/apertureType/hasIS are outside the legacy whitelist and do not surface here; the three fieldNotes.hasIS additions do (fieldNotes is whitelisted). Two entries removed (canon-uj25ex7-6b, fujinon-la30x7-8brm-xb2)

### v1.50.0 — 2026-06-19

- Legacy union rebuild aggregating the broadcast_lens_details v1.51.0 Canon CJ25ex7.6B sidecar import above. No cine change. One new entry (`canon-cj25ex7-6b`)

### v1.49.0 — 2026-06-18

- Legacy union rebuild aggregating the cine_lens_details v1.49.0 and broadcast_lens_details v1.50.0 fieldNotes-contract compliance fixes above (six fieldNotes cleaned + one key renamed filterThreadNote → filterThreadMm). No lens core change. Rides db-v8.

### v1.48.0 — 2026-06-17

- Legacy union rebuild aggregating the cine_lens_details v1.48.0 and broadcast_lens_details v1.48.0 schema-gate datafixes above (filterType rear_filter→internal ×28, front→front_thread ×6, Tokina Vista-C opticalElements string→integer ×48, Canon fieldNotes string→object ×2, nikon-s19x8 unconfirmed→null). No lens core change.

### v1.47.0 — 2026-06-13

- Sony FE PZ 28-135mm F4 G OSS sidecar: weightG 1215g, lengthMm 162.5, frontDiameterMm 105, closeFocusM 0.4, introductionYear 2014, imageCircleMm 43.3 (unconfirmed — FF standard), opticalElements 18, filterType front_thread/95mm, isParfocal true (SMO design), hasFocusBreathing minimal (SMO design), hasFrontRotation false. focusRingRotationDeg/gearPitch null (FBW power zoom). Source: Sony Asia spec page (Tier 1)

### v1.46.1 — 2026-06-12

- Panoptes 65 LPL details rebuild (8 entries): per-field sources object, filterType → "matte_box", filterThreadMm → "none" (POS-D24), gearPitch 0.8, hasFocusBreathing "minimal"; opticalElements/hasFrontRotation/focusRingRotationDeg null (sources exhausted; ships late summer 2026); webSources per entry
- Vista-C webSources: added webSources array to all 48 Vista-C entries across E/EF/LPL/PL shards; value = per-entry manufacturerUrl

### v1.46.0 — 2026-06-11

- Sidecars for 8 new Zeiss Panoptes 65 entries (v1.30.0 in lenses.json)
- All 8 entries: lensType cine, imageCircleMm 59.9, filterType front_thread, filterThreadMm 95, frontDiameterMm 95, introductionYear 2026, isParfocal null, hasFocusBreathing null, gearPitch null
- Per-entry: closeFocusM, lengthMm (144 or 148), weightG from zeiss.com spec table (Tier 1)
- Source: zeiss.com/panoptes65 (Tier 1)

### v1.45.0 — 2026-06-11

- Sidecars for 48 new Tokina Vista-C Prime entries (v1.29.0 in lenses.json)
- Per-mount specs (weightG, lengthMm) from Tokina Cinema spec sheet per-mount columns (Tier 1)
- 18mm: filterType null, filterThreadMm null (spec sheet: NA); all others: front_thread 112mm
- frontDiameterMm 114 for all 48 entries (Diameter of Front Head from spec sheet)
- introductionYear 2025, imageCircleMm 46.7, focusRingRotationDeg 300, gearPitch 0.8 (convention, unconfirmed)
- hasFocusBreathing "minimal" per POS-D21 (product page: virtually no focus breathing)
- Source: tokinacinemausa.com (Tier 1)

### v1.44.0 — 2026-06-09

- Sidecars for the 2 new Fujinon broadcast lenses (v1.28.0 in lenses.json):
  - `fujinon-ua16x4berd`: weightG 2290, lengthMm 252.6, frontDiameterMm 95, closeFocusM 0.3, intro null, filter `hood_thread` 127mm, hasMacro null, servo zoom+focus true, servoConnector null, portable
  - `fujinon-ua30x7-3berd`: weightG 2260, lengthMm 230.9, frontDiameterMm 95, closeFocusM 0.8, intro null, filter `hood_thread` 95mm, hasMacro null, servo zoom+focus true, servoConnector null, portable
- `fujinon-ua30x7-3berd` carries a `fieldNotes.filterThreadNote`: two thread options (M95x1 + M107x1); M95x1 stored as primary pending the planned Update-2 array migration
- Specs sourced by Kay from manufacturer documents (videobrokers tier-2 listings)

### v1.43.0 — 2026-06-09

- Sidecars for the 2 new Fujinon broadcast lenses (v1.27.0 in lenses.json):
  - `fujinon-la30x7-8brm-xb2`: weightG 1700, lengthMm 190.0, frontDiameterMm 100, closeFocusM 0.8, intro 2025, filter front_thread 95mm, hasMacro true, servo zoom true / focus false, 20pin, portable
  - `fujinon-ua94x8-7besm`: weightG 24300, lengthMm 610, frontDiameterMm null (box lens), closeFocusM 3.05, filter `hood_thread` 127mm, hasMacro null, servo zoom+focus true, 20pin, box
- New `filterType` enum value `"hood_thread"` introduced (UA94 hood-mounted filter); first use in the database
- Specs sourced by Kay from official Fujifilm documents (la30 spec sheet PDF; 2026 general brochure PDF)

### v1.42.0 — 2026-06-08

- Tokina Vista-P Prime T1.5 mount-variant sidecars: 36 new entries (12 focal lengths × EF/E/LPL). All fields identical to the PL entries except weightG and lengthMm, which use the matching mount column from the manufacturer spec chart PDF
- Mount weight/length spread (vs PL): EF ≈ +0.08 kg same length; LPL ≈ +0.15 kg / +8 mm; E ≈ +0.17 kg / +26 mm
- Source: tokinacinemausa.com spec chart PDF (tier-2, per-mount columns)

### v1.41.0 — 2026-06-08

- Tokina Vista-P Prime T1.5 sidecars: 12 new entries (18–180mm); imageCircleMm=46.7, filterType=front_thread, filterThreadMm=112, frontDiameterMm=114, focusRingRotationDeg=300, hasFocusBreathing=none, gearPitch=0.8, opticalElements + lengthMm + weightG + closeFocusM per focal
- weightG and lengthMm use the PL-mount column from the manufacturer All-Focal-Length spec chart PDF (PL is the imported mount). NOTE: the weights in Kay's brief matched the MFT-mount column (~0.13 kg heavier); PL-column values used here for mount accuracy — see Tim completion summary
- frontDiameterMm=114 for all focal lengths (manufacturer "front lead diameter"); the 124mm figure for 135/180mm is the max barrel diameter, not the front diameter
- introductionYear=null (not published); gearPitch=0.8 by reasoning (shared Vista housing, standard 0.8 mod cine gears)
- Source: tokinacinemausa.com product page + spec chart PDF (tier-1/2)

### v1.40.0 — 2026-06-01

- Zeiss Nano Prime sidecars: 6 new entries (18/24/35/50/75/100mm T1.5); imageCircleMm=46.5, filterType=front, filterThreadMm=86, frontDiameterMm=95; source: zeiss.com brochure PDF (tier-1)
- Zeiss Supreme Prime Radiance sidecars: 2 new entries (18mm T1.5, 135mm T1.5); imageCircleMm=46.3, filterType=null; 135mm weight/length flagged as inferred from chassis family
- Angénieux UC 21-56, UC 37-102, EZ-3: no null fills applied — all specified dimension fields already populated from prior import

### v1.39.0 — 2026-05-25

- zeiss-cp3 (×10): filterType front_thread → matte_box, filterThreadMm 86 → "none" (B&H Tier 2: no front filter thread; matte box design; 95mm is barrel diameter not thread; confirmed absent per POS-D24)
- fujinon-hzk24-300mm-t2-9: filterType + filterThreadMm → null (same correction as HZK14-100 v1.38.0; 127mm thread on 114mm barrel physically impossible; FUJIFILM DUVO page publishes no filter info)

### v1.38.0 — 2026-05-25

- fujinon-hzk14-100mm-t2-9: filterType + filterThreadMm corrected null (prior value 'front_thread' / 127mm was physically impossible — 127mm thread exceeds 114mm front diameter; FUJIFILM DUVO page publishes no filter system info)

### v1.37.0 — 2026-05-18

- Broadcast gap fill: 79 entries — filterType, filterThreadMm, closeFocusM, hasMacro, lengthMm, weightG (Kay-verified)
- Brands covered: Canon (CJ/HJ/UJ/XJ/KJ/J/KLL-SC ×57), Fujinon (UA/HA/XA ×16), Angénieux (T-series ×4), Zeiss (DigiZoom ×2), Nikon (TV-Nikkor ×4)
- Cine zoom gap fill: 63 entries — isParfocal, hasFocusBreathing, focusRingRotationDeg, gearPitch, filterType, filterThreadMm, lengthMm, weightG, closeFocusM, imageCircleMm (Kay-verified)
- Brands covered: Canon (CN/EF ×20), Fujinon (ZK/Premista/HZK/HK ×14), Angénieux (Optimo/EZ ×17), ARRI (Signature/Alura/UWZ/Master ×10), Hawk/Vantage ×2, Viltrox ×1, Masterbuilt ×1, Laowa ×1
- Angénieux URL fix: manufacturerUrl + webSources corrected for 8 Optimo entries (style-25-250, 15-40, 28-76, 45-120, 17-80, 19-5-94, 24-290, 28-340)

### v1.36.0 — 2026-05-18

- hasFocusBreathing migration: 69 entries set to "minimal" (Kay-verified source analysis)
- Brands: Angénieux ×1, ARRI ×17, DZOFilm ×29, Laowa ×7, Leitz ×10, plus ARRI Signature Zoom ×4 and Alura ×1
- sources.hasFocusBreathing updated for angenieux-optimo-ultra-12x (Tier 1 product sheet)

### v1.35.0 — 2026-05-17

- POS-D26/D27 schema cleanup: migrate legacy "unconfirmed" string values
- Item 1 (enum/string fields → "unknown"): filterType ×1, hasFocusBreathing ×32, opticalElements ×8
- Item 2 (boolean fields → null): isParfocal ×30, hasMacro ×14, hasFrontRotation ×5
- Item 5 (gearPitch type fix): 168 string "0.8" values migrated to number 0.8
- Item 6 (filterType enum correction): 7 entries "rear" → "internal" (rear net holders / internal filter systems)

### v1.34.1 — 2026-05-17

- POS-D26 schema correction: 7 sources entries with "unconfirmed" in description string split into separate description + `_confidence: "unconfirmed"` keys
- arri-uwz-9-5-18: sources.gearPitch rewritten; sources.gearPitch_confidence added
- canon-cn5x11-ias-t-p1: sources.focusRingRotationDeg rewritten; sources.focusRingRotationDeg_confidence added
- canon-cn30x40-ias-pl: sources.focusRingRotationDeg rewritten; sources.focusRingRotationDeg_confidence added
- canon-cn30x40-ias-rf: sources.focusRingRotationDeg rewritten; sources.focusRingRotationDeg_confidence added
- cooke-sp3-18mm-t2-4-e: sources.lengthMm rewritten; sources.lengthMm_confidence added
- cooke-sp3-18mm-t2-4-rf: sources.lengthMm rewritten; sources.lengthMm_confidence added
- cooke-sp3-18mm-t2-4-l: sources.lengthMm rewritten; sources.lengthMm_confidence added

### v1.34.0 — 2026-05-17

- Part 1 (48 POS-D26 corrections): numeric fields previously stored as "unconfirmed" string now resolved
- imageCircleMm: 17 ARRI Master Primes + Master Zoom 16.5-110 → 31.14 (ARRI brochure PDF, Tier 1)
- imageCircleMm: ARRI Signature Zoom 65-300 → 45.0 (AbelCine Tier 3)
- filterType + filterThreadMm: 10 Leitz Summicron-C lenses → matte_box / none (B&H Tier 2)
- filterThreadMm: canon-hj40ex14b → 127 (B&H Tier 3)
- gearPitch: 9 Fujinon ZK/Premista/HZK lenses → "0.8" (Tier 1/2 per entry); arri-uwz-9-5-18 → "0.8" (unconfirmed, inferred)
- focusRingRotationDeg: 3 Canon IAS Cine Servo lenses → 180 (unconfirmed, inferred from family); Angénieux Optimo Style 25-250 → 339; Optimo 19.5-94 → 320; Optimo 28-340 → 327; Leitz Zoom 25-75 + 55-125 → 270; RED Pro 17-50 → 175
- Part 2 (18 new SP3 sidecars): Cooke SP3 sidecar entries added for all 18 new lenses.json entries
- 18mm lengthMm=109 marked unconfirmed (Gemini source); all other SP3 values from Cooke spec sheet PDF (Tier 1)

## announcements.json
### v1.0.6 — 2026-06-12

- Fix: converted announcement from flat string to required object structure (id, message, type). id: "2026-06-update-1-1-0", type: "info". Flat string was not parsed by the app; popup was not showing.

### v1.0.5 — 2026-06-12

- Update 1.1.0 release announcement: CSV export, bracket thickness controls, custom lens editing/duplication, rebuilt cine lens selector, performance improvements

### v1.0.4 — 2026-05-25

- Cleared beta announcement for App Store release: announcement set to null

### v1.0.3 — 2026-05-15
- Pre-launch announcement: id "2026-05-pre-launch", type info, expires 2026-09-01
- Message: approaching App Store release, thanks beta testers, references pocketop.app lens database

## lenses.json
### v1.18.0 — 2026-05-14

- Gap scan import pass (Kay research, session 06/20): 42 new cine lens entries
- Cooke S8/i FF Primes PL largeFormat (8): 18/25/32/40/50/75/100/135mm T1.6–T2.0
- NiSi Athena Primes E fullFrame (8): 14/18/25/35/40/50/85/135mm T1.9–T2.4
- Meike FF Cine Primes E fullFrame (7): 16/24/35/50/85/105/135mm T2.1–T2.5
- Tokina Cinema Vista Primes E largeFormat (7): 18/21/25/35/50/85/105mm T1.5
- Thypoch Simera-C Primes E fullFrame (5): 21/28/35/50/75mm T1.5
- 7Artisans Spectrum FF Cine Primes E fullFrame (4): 14/35/50/85mm T2.0–T2.9
- Fujinon MK18-55mm T2.9 E-mount (copy from EF, id: fujinon-mk18-55mm-t2-9-e)
- Fujinon MK50-135mm T2.9 E-mount (copy from EF, id: fujinon-mk50-135mm-t2-9-e)
- DZOFilm Tango 18-90mm T2.9 E-mount (copy from EF, id: dzofilm-tango-18-90mm-t2-9-e)

## lens-details.json
### v1.33.1 — 2026-05-14

- Sidecar entries added for all 42 new lenses from gap scan import pass v1.18.0
- Cooke S8/i: matte_box/none/0.8/minimal/270°/46.3mm
- NiSi Athena: 14mm→none/none; others→front_thread/77mm; 0.8/minimal/300°/46.0mm
- Meike FF Cine: front_thread/per-lens filterThread/0.8/minimal/330°/45.0mm
- Tokina Cinema Vista: front_thread/112mm/0.8/none/300°/46.7mm
- Thypoch Simera-C: front_thread/67mm/0.8/minimal/210°/43.3mm
- 7Artisans Spectrum: front_thread/82mm/0.8/minimal/270°/43.3mm
- Fujinon MK18-55/MK50-135/DZO Tango E-mount: all fields copied from EF source entries

## lens-details.json
### v1.33.0 — 2026-05-14

- Full cine null-audit pass (Kay research, all brands, session 06/19):
- Canon: cn7x17-kas-t-p1 filterThreadMm 127→112; cn20x50 filterType front_thread→matte_box; cne20-50mm/cne45-135mm filterType→front_thread filterThreadMm=112 imageCircleMm=46.4; EF photo lenses gearPitch/focusRingRotationDeg→null imageCircleMm=43.2
- Fujinon: Premista series filterType→matte_box filterThreadMm→'none'; HK series hasFocusBreathing→'unconfirmed'
- Angénieux: All Optimo/Optimo Style/Classical filterType→matte_box filterThreadMm→'none'; Optimo Style hasFocusBreathing→'minimal'; Optimo DP hasFocusBreathing→'none'
- ARRI: All filterThreadMm null→'none'; Sig Primes gearPitch→'0.8'; Master Primes focusRingRotationDeg→280; Sig Zooms 24-75/45-135 focusRingRotationDeg→320
- DZOFilm: Catta Ace/Gnosis/Vespid Retro/Cyber hasFocusBreathing→'minimal'; Tango/X-Tract isParfocal→true; X-Tract filterType→'none' filterThreadMm→'none'; Vespid Retro 16mm filterThreadMm→'none'; Vespid Retro 25-125mm filterThreadMm→77
- ZEISS: CP.3 filterType→front_thread filterThreadMm=86; Supreme Prime filterType→'none' filterThreadMm→'none' imageCircleMm=46.3; Supreme Zoom Radiance isParfocal→true; CP.2 filterType→matte_box hasFocusBreathing→'unconfirmed'; CP.2 18mm imageCircleMm=30.0; CZ.2 per-lens filterType/filterThreadMm; LWZ.3 filterType→'none'
- Cooke: All series filterType→matte_box filterThreadMm→'none'; Varotal FF corrected from front_thread/112.5 hasFocusBreathing→'minimal' isParfocal→true
- Leitz: Zoom filterType→matte_box; Thalia 65 filterType→front_thread filterThreadMm=92 focusRingRotationDeg=270 imageCircleMm=60; Summilux-C filterType→front_thread filterThreadMm=95 imageCircleMm=36; Hektor 18mm filterType→'none' filterThreadMm→'none'; Hugo filterType→front_thread filterThreadMm=92 imageCircleMm=43.3
- Sigma: Cine Zooms isParfocal null→true; FF Prime 14mm/20mm filterType→'none'; FF Prime 105mm filterType→front_thread filterThreadMm=105; AF Cine filterThreadMm 82→86 isParfocal→true
- Tokina/Other: Vista isParfocal→true; Hawk SW/Vantage LW specs filled; Viltrox Luna filterType→'none'; RED Pro filterType→'none'; Masterbuilt CFZ filterType→matte_box isParfocal→true; Xeen CF/original filterType→matte_box; Sirui Jupiter hasFocusBreathing→'minimal'; Sirui Nightwalker 16mm/75mm imageCircleMm=28.2; Laowa Ultima imageCircleMm/gearPitch/focusRingRotationDeg isParfocal
- POS-D20 applied: all prime isParfocal set to null (no exceptions)
- POS-D24 applied: 36 corrections — filterThreadMm→'none' where filterType is matte_box or none
- isParfocal→null applied globally to all prime entries

### v1.32.4 — 2026-05-12

- webSources populated for remaining 16 entries that previously had []:
- cooke-cxx-15-40mm-t2-0: cameranordic.com
- cooke-varotal-18-100mm-t3-0: alangordon.com
- cooke-varotal-25-250mm-t3-7: cinelenswiki.com
- zeiss-lwz-2-15-5-45mm-t2-6: photocinerent.com + lensrentals.com
- zeiss-cp2-* (11 entries): zsyst.com + lensrentals.com
- laowa-ultima-25-600mm-t4-s35: newsshooter.com (2026-04-15 launch article)

### v1.32.3 — 2026-05-12

- webSources field added to all 551 lens entries (migration pass):
- Group 4 (121 lenses): webSources copied from existing sources array
- Group 2 (10 lenses): URLs extracted from sources object text values
- Group 1 (404 lenses): webSources set to [manufacturerUrl] (fallback)
- Group 1 (16 lenses): webSources set to [] — no URL available (Cooke CXX/Varotal, ZEISS CP.2, Laowa Ultima)
- 535 lenses have ≥1 URL in webSources; 16 have []

### v1.32.2 — 2026-05-12

- Canon cine null-audit pass 1 (Kay research, session 06/18):
- hasFocusBreathing null→"minimal": cn7x17-kas-s-p1 (Canon tier-1), cn8x15-ias-s-p1, cn10x25-ias-s-p1, cn5x11-ias-t-p1, cne18-80mm-t4-4, cne70-200mm-t4-4, cne15-5-47mm-t2-8, cne30-105mm-t2-8, cne15-5-47mm-t2-8-ef, cne30-105mm-t2-8-ef, cne20-50mm-t2-4-ff, cne45-135mm-t2-4-ff, cne14-35mm-t1-7, cne31-5-95mm-t1-7, cn30x40-ias-pl, cn30x40-ias-rf, cne14mm-t3-1, cne24mm-t1-5, cne35mm-t1-5, cne50mm-t1-3, cne85mm-t1-3, cne135mm-t2-2, cne14mm-t3-1-pl, cne24mm-t1-5-pl, cne35mm-t1-5-pl, cne50mm-t1-3-pl, cne85mm-t1-3-pl, cne135mm-t2-2-pl
- hasFocusBreathing null→"none": cn7x17-kas-t-p1 (Canon: hardware optical focus breathing correction in servo)
- hasFocusBreathing null→"significant": cn20x50-ias-h-p1 (CineD independent review: "quite distinctive at 850mm+")
- hasFocusBreathing null→"significant" (EF photo lenses — editorial classification): ef-16-35-f2-8l-ii, ef-16-35-f4l-is, ef-17-40-f4l, ef-24-70-f2-8l-ii, ef-24-70-f4l-is, ef-24-105-f4l-is-ii, ef-70-200-f2-8l-is-iii, ef-70-200-f2-8l-is-ii, ef-70-200-f4l-is-ii, ef-70-200-f4l, ef-100-400-f4-5-5-6l-is-ii, ef-200-400-f4l-is-ext1-4, ef-70-300-f4-5-6l-is, ef-28-300-f3-5-5-6l-is, ef-100-macro, ef-200-f2l-is, ef-300-f2-8l-is-ii, ef-300-f4l-is, ef-400-f2-8l-is-iii, ef-400-do-is-ii, ef-400-f5-6l, ef-500-f4l-is-ii, ef-600-f4l-is-iii, ef-800-f5-6l-is, ef-135-f2l
- hasFocusBreathing null→"moderate" (EF photo lenses — editorial classification): ef-24mm-f1-4l-ii, ef-35mm-f1-4l-ii, ef-50mm-f1-2l, ef-85mm-f1-2l-ii, ef-85mm-f1-4l-is
- hasFocusBreathing "none"→"minimal" (correction): cne14-35mm-t1-7-ef, cne31-5-95mm-t1-7-ef — same optical design as PL variants; "none" was incorrect
- fieldNotes.hasFocusBreathing added: cn20x50-ias-h-p1 — CineD review context
- isParfocal "unconfirmed"→true: cn7x17-kas-s-p1, cn7x17-kas-t-p1, cn8x15-ias-s-p1, cn10x25-ias-s-p1, cn20x50-ias-h-p1, cn5x11-ias-t-p1, cne15-5-47mm-t2-8, cne30-105mm-t2-8, cne45-135mm-t2-4-ff, cne14-35mm-t1-7
- isParfocal null→"unconfirmed": cn30x40-ias-pl, cn30x40-ias-rf (Tim: zoek Canon CN30x40 specs)
- gearPitch "unconfirmed"→"0.8": cn7x17-kas-s-p1, cn7x17-kas-t-p1, cn8x15-ias-s-p1, cn10x25-ias-s-p1, cn20x50-ias-h-p1, cne14mm-t3-1, cne24mm-t1-5, cne35mm-t1-5, cne50mm-t1-3, cne85mm-t1-3, cne135mm-t2-2
- filterType null→"front_thread": cn7x17-kas-s-p1, cn10x25-ias-s-p1, cn20x50-ias-h-p1, cn5x11-ias-t-p1
- filterType null→"matte_box": cne14-35mm-t1-7, cne31-5-95mm-t1-7, cne14-35mm-t1-7-ef, cne31-5-95mm-t1-7-ef
- filterThreadMm null→112: cn7x17-kas-s-p1 (AbelCine)
- filterThreadMm null→"unconfirmed": cn10x25-ias-s-p1, cn5x11-ias-t-p1
- focusRingRotationDeg 180→200 (correction): cn7x17-kas-t-p1 — cbm-cine + Canon UK spec page
- imageCircleMm null→27.5: cne14-35mm-t1-7, cne31-5-95mm-t1-7, cne14-35mm-t1-7-ef, cne31-5-95mm-t1-7-ef
- imageCircleMm null→43.2: all 30 EF photo lens entries (EF mount standard)
- sources added to all updated entries

### v1.32.1 — 2026-05-12

- filterType "unconfirmed"→"matte_box": premista28-100 (bhphotovideo.com; abelcine.com), premista80-250 (bhphotovideo.com; abelcine.com; ottonemenz.com) — correction to v1.32.0

### v1.32.0 — 2026-05-12

- Fujinon cine null-audit pass 1 (Kay research):
- hasFocusBreathing null→"unconfirmed": zk14-35, zk19-90, zk85-300, zk25-300, premista19-45, premista28-100, premista80-250, hk3-1x14-5, hk4-7x18, hk7-5x24, hk5-3x75 — geen breathing test gevonden
- hasFocusBreathing null→"minimal": xk20-120 (fujifilm.com XK; bhphotovideo.com), hzk14-100 (fujifilm.com; topteks.com BCT), hzk25-1000 (fujifilm.com BCT), mk18-55 (cined.com; newsshooter.com; videomaker.com; provideocoalition.com; fujinon.com), mk50-135 (videomaker.com; newsshooter.com; cined.com; fujinon.com)
- hasFocusBreathing null→"significant": hzk24-300 — newsshooter.com: "exhibits a lot of lens breathing" without BCT
- fieldNotes.hasFocusBreathing added: hzk24-300 — BCT reduces to minimal when enabled; toggleable
- filterType null→"matte_box": premista19-45 — bhphotovideo.com: no filter threads, 114mm matte box
- filterType "unconfirmed"→"front_thread" + filterThreadMm null→111: zk25-300 — bhphotovideo.com; hotrodcameras.com
- filterType null→"front_thread" + filterThreadMm null→111: xk20-120 — tanotis.com; hotrodcameras.com
- focusRingRotationDeg null→200: zk14-35 (fujifilm.com UK; bpm-media.de), zk19-90 (fujifilm.com; fullcompass.com), zk85-300 (fullcompass.com; bhphotovideo.com; hotrodcameras.com)
- focusRingRotationDeg null→280: zk25-300 (bhphotovideo.com; hotrodcameras.com; newsshooter.com), premista19-45 (fdtimes.com; cvp.com), premista28-100 (bhphotovideo.com), premista80-250 (bhphotovideo.com; abelcine.com)
- sources added to all updated entries

### v1.31.0 — 2026-05-12

- Angénieux cine null-audit pass 1 (Kay research):
- hasFocusBreathing null→"minimal": optimo-ultra-compact-21-56, optimo-ultra-compact-37-102 — angenieux.com; bhphotovideo.com; cined.com/fdtimes.com
- hasFocusBreathing null→"unconfirmed": type-ez-1, type-ez-2 (EZ brochure, no statement), type-ez-3 (cbm-cine.com, no statement)
- hasFocusBreathing null→"none": optimo-dp-16-42mm-t2-8, optimo-dp-30-80mm-t2-8 — hhf-old.handheldfilms.com; fjsinternational.com "Zero Breathing and Ramping"
- hasFocusBreathing needs_review→"minimal": optimo-style-48-130 — angenieux.com; fdtimes.com; britishcinematographer.co.uk
- filterThreadMm sources added (null confirmed): optimo-style-16-40, optimo-style-30-76, optimo-style-48-130, optimo-style-25-250
- filterThreadMm sources added (null confirmed): optimo-15-40, optimo-28-76, optimo-45-120, optimo-17-80, optimo-19-5-94, optimo-24-290, optimo-28-340

### v1.30.0 — 2026-05-12

- ARRI cine null-audit pass 1 (Kay research):
- gearPitch null→0.8: all 16 Signature Primes (12/15/18/21/25/29/35/40/47/58/75/95/125/150/200/280mm T1.8) — Panny Hire mechanical spec; ARRI follow-focus gear catalog
- focusRingRotationDeg null→280: all 16 Master Primes (12/14/16/18/21/25/27/32/35/40/50/65/75/100/135/150mm T1.3) — Cinetecnico rental page
- focusRingRotationDeg null→320: Signature Zoom 24-75 T2.8, Signature Zoom 45-135 T2.8 — FJS International rental page
- filterThreadMm: all 55 ARRI cine entries already null — no writes needed

### v1.29.0 — 2026-05-12

- DZOFilm cine null-audit pass 1 (Kay research):
- hasFocusBreathing null→"minimal": Catta Ace 18-35/35-80/70-135, Gnosis 24/32/65/90, Vespid Retro 16/25/35/50/75/100/125, Vespid Cyber 35/50/75 (17 entries)
- isParfocal: Tango 18-90/65-280, X-Tract already true — no change needed
- lengthMm null→87: Vespid 21/35/50/75mm; null→100: Vespid 125mm
- closeFocusM null→0.30: Vespid 25mm, Vespid 40mm
- filterThreadMm (x-tract): source added confirming null (probe lens, no thread)
- filterType "none"→"front_thread" + filterThreadMm null→77: Vespid 90mm Macro (prior read of '/' corrected; dzofilm.com confirms M77)

### v1.28.0 — 2026-05-12
- migrate hasFocusBreathing from boolean to string enum: false→"none" (82), true→"needs_review" (69); null/unconfirmed/absent unchanged

### v1.27.0 — 2026-05-12

- add lensType field (POS-D18): "broadcast" (twoThirdsInch) or "cine" (all other sensorFormats); 121 broadcast, 430 cine; joined from lenses.json on id

### v1.26.0 — 2026-05-10
- null-audit broadcast weightG/lengthMm/closeFocusM pass 3: 24 entries, 64 fields updated
- Canon CJ (2): cj20ex5b all 3 fields; cj45ex13-6b all 3 fields — tier 1 canon.nl/canon-europe.com
- Canon HJ (11): hj11/15/17/18/21/22/40x10/40x14 all 3 fields; hj8x/11x/21x-kll-sc all 3 fields — Canon pocket guide 2009 + spec sheet screenshots
- Canon KJ (3): kj16/kj20/kj21 all 3 fields — Canon pocket guide 2009
- Canon J (2): j35ex15b + j35ex11b all 3 fields — Canon pocket guide 2009
- Canon XJ (2): xj22x7-3b + xj27x6-5b closeFocusM only (weight+length already filled) — Canon pocket guide 2009
- Fujinon (4): ha42x9-7 weightG only; xa87x9-3 lengthMm only; xa20sx8-5bmd + xa20sx8-5bemd all 3 fields — Fujinon brochure PDFs + eXceed catalog
- Skipped (already non-null): canon-hj24ex7-5b, canon-kj10ex4-5b, canon-kj13x6b, xj22x7-3b weight+length, xj27x6-5b weight+length, ha42x9-7 length+closeFocus, xa87x9-3 weight+closeFocus
- Legitimate nulls confirmed: Angénieux T-serie (t12/15/19/26), Nikon S-serie (s9/s13/s15/s19)

### v1.25.0 — 2026-05-10
- null-audit broadcast weightG/lengthMm/closeFocusM: 42 entries updated
- Canon CJ (8): all three fields — tier 1 asia.canon
- Canon HJ (1, hj24ex7-5b): all three fields — tier 1
- Canon KJ (5): all three fields — tier 1-2
- Canon UJ (7): all three fields — tier 1; closeFocusM 3.0m (studio lenses)
- Canon XJ (14): weightG + lengthMm; xj72x9-3b closeFocusM only (2.8m) — tier 1-3
- Fujinon (2): ha27x6-5 weightG+lengthMm, xa101x8-9 lengthMm — tier 1 2012 catalog
- Angénieux (2): t19x7-3b + t26x7-8b all three fields — tier 3
- Zeiss (2): all three fields — tier 1
- Nikon (1): s15x8-5b weightG + lengthMm — tier 3
- Skipped (flagged): canon-uj25ex7-6b (model ID mismatch), canon-xj100x9-3b lengthMm (conflicting sources), canon-kj20x8-5b weight+length (tier-3 unreliable), angenieux-t15x8-3b (weight suspicious)
- Not found: cj12/cj20ex5b/cj45x9/cj45x13, HJ except hj24, kj16/kj21, xj100, fujinon ha42/xa87-length/xa20sx8-5bmd/bemd, angenieux-t12, nikon-s9/s13/s19

### v1.24.0 — 2026-05-10
- correction filterType: set "front_thread" on 8 broadcast entries (Angenieux T-series, Nikon S-series)
- correction hasMacro: 13 entries updated (true/false/unconfirmed); canon-uj25ex7-6b and canon-xj23x7b set false with fieldNotes (MCJ-S02 accessory)
- correction hasServoFocus: 14 entries updated (Fujinon HA-series true→false; Angenieux/Nikon null→false)

### v1.23.0 — 2026-05-10
- correction: imageCircleMm null -> 11.0 on all broadcast entries where null (71 entries)
- correction: formFactor "handheld" -> "portable" on all broadcast entries (58 entries)
- correction: servoConnector "12pin_hirose" -> "12pin" on all broadcast entries (37 entries)


- **1.22.0** (2026-05-10) — hasMacro correction pass (4 changes). cj18ex7-6b: null→false (POS-D11: no macro claim in any source). cj20ex7-8b: false→true (macro confirmed in research). cj14ex4-3b: null→true (Canon pocket guide: macro spec). cj12ex4-3b: null→true (Canon pocket guide: macro spec). Note: hj40ex10b filterThreadMm, hj17ex7-6b filterThreadMm, hj18ex7-6b hasMacro were already correct from earlier HJ pass — no changes needed.
- **1.21.0** (2026-05-10) — Canon CJ pending sources resolved (5 entries). cj18ex7-6b: added B&H source (asia.canon already present). cj20ex5b: newsshooter.com + canon-europe.com press release; hasMacro null→false (no macro claim in any source, POS-D11). cj27ex7-3b: B&H + theasc.com; hasMacro true→false (no macro claim). cj45ex13-6b: B&H; hasMacro true→false (no macro claim, 127mm front confirmed). cj45ex9-7b: sg.canon spec; hasMacro=true confirmed (Singapore spec: "2.8m (10mm with macro)"). canon-cj-http-pending.md removed.
- **1.20.0** (2026-05-10) — Retroactive sources pass: Nikon S (4), Zeiss DigiZoom (2), Angénieux T-series (4) — all 10 entries. Nikon S: primary Nikon broadcast pages offline; dvxuser.com forum (s9x5-5b/s13x9/s19x8) and worthpoint.com (s15x8-5b) as tier-3 sources. Zeiss DigiZoom: B&H product pages + visualproducts.com set listing. Angénieux T-series: amazon.com Eonvic cable listing (confirms B4-mount servo connector spec); adorama.com clearance page for t19x7-3b. No field values changed.
- **1.19.0** (2026-05-10) — Retroactive sources pass Fujinon broadcast series: UA (16), HA (14), XA (15), ZA+LA (5) — all 50 entries. Sources array set to [manufacturerUrl] for each entry. manufacturerUrl was already the primary source for all field values. No entries skipped (all 50 had a non-null manufacturerUrl). No field values changed.
- **1.18.0** (2026-05-10) — Retroactive sources pass Canon KJ + J series (all 10 entries). Primary source: ManualsLib HD XS HJ14ex4.3B manual (2260534) for all entries. Additional: usa.canon.com product page for kj22ex7-6b-ii. No field value corrections — KJ/J portables have built-in macro where applicable (POS-D16 not triggered).
- **1.17.0** (2026-05-10) — Retroactive sources pass Canon UJ series (all 8 entries) + hasMacro corrections per POS-D16. Sources: ManualsLib UJ122x8.2B AF manual (2947870) for all entries; additional B&H/3dbroadcastsales product pages for uj27x6-5b/uj86x9-3b/uj111x8-3b/uj122x8-2b. Value corrections: uj111x8-3b/uj122x8-2b/uj122x8-2b-af hasMacro true→false + fieldNotes.hasMacro added. Note: uj25ex7-6b ID in DB contains "ex" (canon-uj25ex7-6b), not "uj25x7-6b" as listed in task — sources applied to correct ID.
- **1.16.0** (2026-05-10) — Canon XJ hasMacro corrections per POS-D16 (4 entries). xj22x7-3b/xj25x6-8b/xj27x6-5b: hasMacro true→false. xj72x9-3b: hasMacro unconfirmed→false. All 4 entries: fieldNotes.hasMacro added ("Macro available via optional MCJ-S02 accessory"). Canon DIGISUPER field lenses do not have built-in macro; macro is only available via the optional MCJ-S02 accessory (POS-D16).
- **1.15.0** (2026-05-10) — Retroactive sources pass Canon XJ series (all 15 entries). xj22x7-3b/xj23x7b/xj27x6-5b/xj60x9b/xj86x9-3b: ManualsLib XJ100x9.3B AF manual (895784) + B&H/Allied Broadcast product page. xj25x6-8b: ManualsLib High Resolution Lenses manual (538423). Remaining 9 entries (xj72x9-3b/xj75x9-3b/xj76x9b/xj80x8-8b/xj86x9-3b-af/xj86x13-5b/xj95x8-6b/xj95x12-4b/xj100x9-3b): ManualsLib XJ100x9.3B AF manual (895784). No field values changed. Discrepancies flagged for future pass: xj72x9-3b hasMacro=unconfirmed (macro via optional MCJ-S02 accessory, not built-in); xj25x6-8b hasMacro=true (Pocket Manual source not model-specific).
- **1.14.0** (2026-05-10) — Added sources to Canon HJ KLL-SC variants (hj8x5-5b-kll-sc, hj11x4-7b-kll-sc, hj21x7-5b-kll-sc). Sources: theodoropoulos.info Canon lens catalog PDF + B&H product page (Canon HJ8x5.5B KLL-SC). Confirms cine-style HD-EC lenses, no servo zoom/focus, no connector, film-style operation.
- **1.13.0** (2026-05-10) — Retroactive sources pass Canon HJ series (13 of 16 entries; KLL-SC variants excluded per design). Added sources array to: hj40ex14b (B&H + FocusNordic 127mm), hj40ex10b (B&H + FocusNordic 127mm), hj14ex4-3b (ManualsLib 1931526 + B&H), hj11ex4-7b (B&H), hj17ex7-6b (ManualsLib 1931526), hj22ex7-6b, hj40x10b (B&H + FocusNordic 127mm), hj21ex7-5b, hj17ex6-2b, hj18ex28b, hj15ex8-5b, hj18ex7-6b, hj24ex7-5b (last 6: ManualsLib 1931526). Value corrections: hj40ex10b filterThreadMm unconfirmed→127; hj17ex7-6b filterThreadMm null→105; hj18ex7-6b hasMacro unconfirmed→true. Sources: manualmachine.com ManualsLib FieldZoom IF1 manual (1931526), bhphotovideo.com product pages, focusnordic.com 127mm filter compatibility (Kay-verified).
- **1.12.0** (2026-05-10) — Retroactive sources pass Canon CJ series (8 of 12 entries). Added sources array to: cj12ex4-3b (ManualsLib 2517717 p.51), cj14ex4-3b (asia.canon + ManualsLib 2517717 p.53), cj15ex4-3b (asia.canon), cj15ex8-5b (asia.canon), cj18ex28b (asia.canon), cj18ex7-6b (asia.canon), cj20ex7-8b (asia.canon), cj24ex7-5b (asia.canon). No sources for cj20ex5b/cj27ex7-3b/cj45ex13-6b/cj45ex9-7b (all primary pages 404/403 via HTTPS; HTTP-only URLs documented in Private/canon-cj-http-pending.md for manual verification). No field values changed. Discrepancy flagged: cj20ex7-8b hasMacro=false contradicted by research (correction deferred to separate pass).
- **1.11.0** (2026-05-10) — Batch 33: filled 15 sidecars across 7 manufacturers. Tokina Vista 16-28mm T3.0 (FF): weightG=1750, lengthMm=142, frontDiameterMm=114, filterType=front_thread, filterThreadMm=112, isParfocal=false, gearPitch=null, opticalElements=15; tokina-cinema.jp (tier-1). Tokina ATX 11-20mm T2.9 (S35): weightG=1030, lengthMm=99.6, frontDiameterMm=95, filterThreadMm=86, isParfocal=false, focusRingRotationDeg=300, gearPitch=0.8, opticalElements=14; tokina-cinema.jp (tier-1). Tokina ATX 25-75mm T2.9 (S35): weightG=1960, lengthMm=174, frontDiameterMm=95, filterThreadMm=86, isParfocal=true, gearPitch=0.8, opticalElements=18; tokina-cinema.jp (tier-1). Tokina ATX 50-135mm T2.9 MkII (S35): weightG=1450, lengthMm=147.7, frontDiameterMm=95, filterThreadMm=86, isParfocal=true, focusRingRotationDeg=300, gearPitch=0.8, opticalElements=18; tokina-cinema.jp (tier-1). Hawk Super Wide 10-24mm T2.5: all null (manufacturer PDF is image-only, not text-extractable; spec sheet inaccessible via WebFetch); isParfocal=false (no parfocal claim). Hawk Telephoto 100-300mm T2.2 (system lens = 150-450mm + 0.7× reducer): weightG=16300, lengthMm=600, frontDiameterMm=156, closeFocusM=3.05, imageCircleMm=31.0, filterType=rear, isParfocal=false; hawk-v.de (tier-2). Hawk Telephoto 150-450mm T2.8: weightG=15900, lengthMm=660, frontDiameterMm=156, closeFocusM=3.05, imageCircleMm=31.0, filterType=rear, isParfocal=false, opticalElements=18; hawk-v.de (tier-2); note: DB sensorFormat=largeFormat but imageCircleMm=31mm (S35 coverage) — pre-existing lenses.json discrepancy, out of scope. Angénieux Optimo DP 16-42mm T2.8: weightG=1920, lengthMm=190, frontDiameterMm=114, closeFocusM=0.61, imageCircleMm=31.1, isParfocal=false, focusRingRotationDeg=320, gearPitch=0.8; ManualsLib OEM manual (tier-1). Angénieux Optimo DP 30-80mm T2.8: weightG=1900, lengthMm=186, frontDiameterMm=114, closeFocusM=0.61, imageCircleMm=31.4, isParfocal=false, focusRingRotationDeg=320, gearPitch=0.8; ovide.com / VMI rental pages (tier-2). Viltrox Luna 30-300mm T4.0 (FF): weightG=15000, lengthMm=511, frontDiameterMm=165, closeFocusM=1.26, imageCircleMm=46.5, filterType=rear, isParfocal=true, gearPitch=0.8, introductionYear=2024; viltrox.com (tier-1). Viltrox Luna 42-420mm T5.6 (LF): weightG=16000, closeFocusM=1.8, imageCircleMm=60.0, filterType=rear, isParfocal=null, gearPitch=0.8, opticalElements=11, introductionYear=2024; lengthMm/frontDiameterMm null (not published); viltrox.com (tier-1). RED Pro 17-50mm T2.9: weightG=1450, lengthMm=129, frontDiameterMm=114, closeFocusM=0.25, filterType=unconfirmed, isParfocal=false, gearPitch=0.8; RED pages removed post-Nikon acquisition, rental house listings (triode.tv, filmtools.com, hdgear.tv) as tier-2 sources. RED Pro 18-85mm T2.9: weightG=4500, lengthMm=280, frontDiameterMm=142, closeFocusM=0.70, filterType=unconfirmed, isParfocal=false, focusRingRotationDeg=271, gearPitch=0.8; same sources. Vantage LW Zoom 17-35mm T2.8: all null (manufacturer PDF is image-only, not text-extractable); isParfocal=false (no parfocal claim). Masterbuilt CFZ 27-60mm T2.9 (LF): weightG=1910, frontDiameterMm=114, closeFocusM=0.28, filterType=null, isParfocal=true, hasFocusBreathing=false, gearPitch=0.8; masterbuilt.com (tier-1).
- **1.10.0** (2026-05-10) — Batch 32: filled 18 sidecars across 5 manufacturers. Fujinon HK Premier (4, PL, S35): weightG 6500–8900g, lengthMm 310–444mm, frontDiameterMm=136, filterType=rear (rear net holder, no front thread), focusRingRotationDeg=280, isParfocal=false (no claim), gearPitch=null, imageCircleMm=43.2; specs from authorized dealer datasheets (tier-2; fujifilm.com HK pages discontinued April 2022). Fujinon MK (2, EF entry, S35): weightG=980g each, lengthMm=206mm, frontDiameterMm=85, filterType=front_thread, filterThreadMm=82, isParfocal=true, hasFrontRotation=false, focusRingRotationDeg=200, gearPitch=0.8, imageCircleMm=28.5, opticalElements=22; fujifilm.com (tier-1). Sirui Jupiter 28-85mm T3.2 (1, PL, FF): weightG=2520, lengthMm=215, frontDiameterMm=114, filterThreadMm=110, isParfocal=true, hasFocusBreathing=false, focusRingRotationDeg=259, gearPitch=0.8, imageCircleMm=44.0, opticalElements=22; siruishop.de/cf.sirui.com (tier-1). Sirui Night Walker S35 (5, L, S35): weightG 500–587g, lengthMm 84–95mm, frontDiameterMm=79, filterThreadMm=67, focusRingRotationDeg=270, gearPitch=null; imageCircleMm 31–34mm for 24/35/55mm; null for 16mm/75mm (not published); introductionYear 2023 for 24/35/55mm, 2024 for 16mm/75mm; store.sirui.com/cf.sirui.com (tier-1). Irix Cine (6, L, FF): weightG 962–1395g, lengthMm 115–159mm, frontDiameterMm=95, filterThreadMm=86, hasFocusBreathing=false (irixusa.com: 'close to zero'), hasFrontRotation=false, focusRingRotationDeg=180 (270 for 150mm Tele), gearPitch=0.8, imageCircleMm=43.3; irixusa.com (tier-1).
- **1.9.0** (2026-05-10) — Batch 31: filled 12 Canon Cinema sidecar entries. Group A (CN-E EF Zooms, 4): EF-specific lengths used (15.5-47mm: 222mm, 30-105mm: 218mm, 14-35mm: 241.3mm, 31.5-95mm: 246.4mm); isParfocal=true for Flex Zooms (Canon: "excellent parfocal performance"), false for older zooms (POS-D11); hasFocusBreathing=false for Flex Zooms (Canon: "virtually zero"), null for older; gearPitch=0.8, focusRingRotationDeg=300 across all. Group B (CN-E PL Primes, 6): dimensions from EF Canon Museum pages as proxy (Canon does not publish separate PL prime lengths); filterType=front_thread, filterThreadMm=105 (confirmed usa.canon.com CN-E85mm); imageCircleMm=43.3 for all. Group C (CN30x40 / CINE-SERVO 40-1200mm, 2): IAS H PL specs: weightG=6600, lengthMm=405.2, frontDiameterMm=136, filterThreadMm=127, imageCircleMm=29.6; RF: weightG=6700, lengthMm=437.2 (32mm longer, RF housing); both introductionYear=2019 (IAS H, NAB 2019); IAS J 2026 specs not yet published. Sources: global.canon/en/c-museum/ and usa.canon.com/shop (both tier-1).
- **1.8.0** (2026-05-09) — Batch 30: filled 13 XEEN sidecar entries (6 XEEN CF + 7 XEEN original, all PL) + inserted new sigma-cine-24-35mm-t2-2-ff-e sidecar. XEEN CF: weightG 900–1400g, lengthMm 82.3–113.7mm, frontDiameterMm=95, focusRingRotationDeg=200, imageCircleMm=43.3 (43.2 for 135mm), introductionYear=2019 for 16–85mm/null for 135mm. XEEN original: weightG 1160–1382g, lengthMm 80.3–113.7mm, frontDiameterMm=114, focusRingRotationDeg=200, imageCircleMm=43.3 (derived from negative size 24×36mm diagonal), introductionYear=null. All XEEN: filterType/filterThreadMm/gearPitch/opticalElements=null (not published across 6 tiers). isParfocal=null (primes). Sigma E sidecar: weightG=1600, lengthMm=148.7, frontDiameterMm=95, closeFocusM=0.28, filterType=front_thread, filterThreadMm=82, focusRingRotationDeg=180, gearPitch=0.8, isParfocal=false. Sources: xeenglobal.com/en/xeen-cf.php and xeenglobal.com/en/xeen.php (tier-1); newsshooter.com 2019-09-13 for XEEN CF introductionYear (tier-5); sigma-global.com/en/cine-lenses/ff-zoom/24_35_22/ (tier-1).
- **1.7.0** (2026-05-09) — Batch 29: filled sidecar entries for 18 Sigma cine lenses across 4 series. Series A (S35 High Speed Zoom, PL): 18-35mm T2.0 and 50-100mm T2.0. Series B (FF Zoom, EF): 24-35mm T2.2 FF — weightG and lengthMm filled with EF-mount values sourced from sigma-global.com (task 2 correction). Series C (FF High Speed Prime, PL): 14/20/24/28/35/40/50/65/85/105/135mm — 11 primes; filterType=none for 14mm/20mm/105mm (no front element thread), filterThreadMm=86 for 65mm and 85mm, all others 82mm. Series D (AF Cine FF Zoom, L and E): 28-45mm T2 L+E and 28-105mm T3 L+E — focusRingRotationDeg=200, imageCircleMm=null (not published by Sigma). All entries: opticalElements=null (not published), hasFocusBreathing=null, hasFrontRotation=null, isParfocal=null for primes/false for zooms. Sources object added to all 18 entries. Sources: sigma-global.com product pages (tier-1) for all values.
- **1.6.0** (2026-05-09) — Angénieux/Zeiss/Nikon broadcast sidecar fill: formFactor, hasMacro, hasServoZoom, hasServoFocus, servoConnector filled for 10 twoThirdsInch entries (4 Angénieux T-series, 2 Zeiss DigiZoom, 4 Nikon EMS). opticalElements filled for Zeiss DigiZoom 6-24mm (26) and 17-112mm (28) from official Zeiss DigiPrime/DigiZoom spec sheet. imageCircleMm, filterType, filterThreadMm, opticalElements (Angénieux/Nikon) remain null — no primary source found after 6 tiers. T26x7.8B hasServoFocus=false (enhancedviewhd.com: "Manual Focus Control"). Zeiss DigiZoom hasServoZoom/Focus=false (official spec sheet: "Fixed iris and focus gears"). Sources: official Zeiss DigiPrime/DigiZoom PDF, newprovideo.com (T19x7.3 macro), enhancedviewhd.com (T26x7.8 servo), B4-mount Wikipedia (standard), eBay listings (S13x9 Macro, S15x8.5 Macro, S9x5.5), dvxuser.com/worthpoint (Nikon EMS class), search tier 6 (Angénieux 12-pin connector).
- **1.5.0** (2026-05-09) — Canon broadcast sidecar fill: formFactor, filterType, filterThreadMm, hasMacro, hasServoZoom, hasServoFocus, servoConnector filled for all 61 Canon broadcast lenses (CJ/HJ/KJ/UJ/XJ/J series). 3 corrections from 4K UHD brochure: uj86x9-3b, uj90x9b, uj27x6-5b hasMacro null→false. KLL-SC cine-style lenses (HJ8x5.5B/HJ11x4.7B/HJ21x7.5B): hasServoZoom/Focus false, servoConnector "none". Sources: Canon 2009 Pocket Guide, Canon XJ95x brochure, Canon DIGI SUPER 25 XS brochure, Canon 4K UHD broadcast lens brochure 2019, Canon Asia spec pages (CJ/HJ/KJ series).
- **1.4.0** (2026-05-09) — Fujinon broadcast sidecar fill: formFactor, imageCircleMm, hasMacro, hasServoZoom, hasServoFocus, servoConnector, filterType, filterThreadMm filled for all 50 Fujinon broadcast entries (HA/UA/XA/ZA/LA series, incl. 3 new entries added: fujinon-ha27x6-5, fujinon-xa20sx8-5bmd, fujinon-xa20sx8-5bemd). imageCircleMm = 11.0 confirmed for all 50 (universal 2/3" standard). introductionYear and opticalElements remain null (not published in spec sheets). 15 box lens filterType values set to null — gaps documented in TIM/Private/sidecar-research-gaps.md. Sources: Fujifilm spec sheet PDFs (asset.fujifilm.com), Fujinon Pocket Guide 2024, 23premierseriesberd_berm.pdf, UA 4K Premier Series PDF, ManualsLib UA22x8 manual, CVP HA22x7.8 spec, Top-Teks ZA12x4.5 listing.
- **1.3.0** (2026-05-08) — Added formFactor field to broadcast schema for all existing Fujinon broadcast entries (value null, pending fill session).
- **1.2.0** (2026-05-08) — Physical specs extended: weightG, lengthMm, frontDiameterMm, closeFocusM filled for remaining Fujinon broadcast entries from supplemental sources.
- **1.1.0** (2026-05-08) — Fujinon broadcast lens fill: manufacturerUrl set for all 48 Fujinon broadcast entries (UA/HA/XA/ZA/LA series). Physical specs (weightG, lengthMm, frontDiameterMm, closeFocusM) filled for 26 entries confirmed in FUJIFILM FUJINON Broadcast & Cine Catalog 2024. 22 entries receive manufacturerUrl only (older HA/XA/ZA/LA series not in 2024 catalog). All cine entries (ZK/XK/Premista/HZK/HK/MK) remain null — out of scope for this pass. Source: FUJIFILM_FUJINON_Broadcast_Cine_Catalog_2024.pdf.
- **1.0.0** (2026-05-08) — Initial skeleton: 549 entries, all fields null.

## lenses.json

- **1.17.7** (2026-05-10) — Corrected hawk-telephoto-zoom-150-450mm-t2-8 sensorFormat largeFormat→superThirtyFive. imageCircleMm=31.0mm (confirmed in lens-details.json v1.11.0) is Super 35 coverage; largeFormat threshold is ~54mm diagonal. Notes updated to remove incorrect "54.12mm image circle" claim.
- **1.17.6** (2026-05-09) — Added sigma-cine-24-35mm-t2-2-ff-e (Sony E mount variant of Sigma Cine 24-35mm T2.2 FF). Separate entry per POS-D09. Source: sigma-global.com/en/cine-lenses/ff-zoom/24_35_22/.
- **1.17.5** (2026-05-09) — Corrected sigma-cine-24-35mm-t2-2-ff mount PL→EF. This lens was never available in PL mount; available mounts are Canon EF and Sony E only. Notes updated to reflect EF-only status. Source: sigma-global.com/en/cine-lenses/ff-zoom/24_35_22/. Note: Sony E mount variant (sigma-cine-24-35mm-t2-2-ff-e) not yet created; flagged for future session per POS-D09.
- **1.17.4** (2026-05-09) — Corrected T-stop model names for 2 Vespid Retro entries: dzofilm-vespid-retro-35mm-t2-1 (T2.1→T2.8) and dzofilm-vespid-retro-75mm-t2-1 (T2.1→T2.8). IDs unchanged. Source: dzofilm.com Vespid Retro spec table.
- **1.17.3** (2026-05-09) — Corrected model name for leitz-hugo-135mm-t1-5-l (T1.5→T1.9). ID unchanged. Source: leitz-cine.com product page + Duclos Lenses.
- **1.17.2** (2026-05-09) — Removed ghost entry arri-ultra-prime-18mm-t1-9: ARRI Ultra Prime series has no 18mm focal length (series runs 14/16/20/24/28/32/40/50/65/85/100/135/180mm). Entry had no manufacturer source. Confirmed absent across arri.com technical data, CinemaTechnic, and Zeiss product pages.
- **1.17.1** (2026-05-09) — Corrected model names for arri-signature-prime-200mm-t1-8 (T1.8→T2.5) and arri-signature-prime-280mm-t1-8 (T1.8→T2.8). IDs unchanged. Source: arri.com User Manual + product page.
- **1.17.0** (2026-05-08) — Added 3 Fujinon broadcast entries: HA27x6.5BESM (HD studio/field box, 2/3", 27×, 6.5–180mm, 2× extender); XA20sx8.5BMD (HD eXceed remote control ENG, no extender); XA20sx8.5BEMD (HD eXceed remote control ENG, 2× extender). Sources: Fujifilm spec sheet HA27x65BESM.pdf, fujifilm.com remote-control-lenses.
- **1.16.0** (2026-05-08) — L-mount sprint: added 37 new L-mount entries across 5 manufacturers. Leitz HEKTOR (6: 18/25/35/50/73/100mm T2.1, fullFrame, L); Leitz HUGO (14: 18/21/24/28/35/40/50/66/75/90/135mm + 50mm T1.0 + 75mm T2.1 + 90mm T2.1, fullFrame, L); Laowa Ranger FF (3: 16-30/28-75/75-180mm T2.9, fullFrame, L); Laowa Ranger S35 (3: 11-18/17-50/50-130mm T2.9, superThirtyFive, L); Sirui Night Walker (5: 16/24/35/55/75mm T1.2, superThirtyFive, L); Irix Cine (6: 15mm T2.6/21/30/45/65mm T1.5/150mm T3.0 Tele, fullFrame, L). Sigma FF High Speed Prime notes corrected: removed LPL+L claims (sigma-global.com confirms PL/EF/E only). New manufacturer: Irix. Sources: leitz-cine.com, laowacine.com, store.sirui.com, irixlens.com.
- **1.15.0** (2026-05-08) — Added 4 Sigma AF Cine entries across 2 lenses (first L-mount and E-mount entries in database). Sigma AF Cine 28-45mm T2 FF (L + E, fullFrame, available Dec 2025); Sigma AF Cine 28-105mm T3 FF (L + E, fullFrame, available Apr 2026). Schema: "L" and "E" now in active use per broadcast-lenses.md. Sources: sigma-global.com/en/cine-lenses/af-cine/. incomplete_data.md: Sigma 28-105mm T3 scope_decision resolved and removed; Canon CN30x40 IAS stale entry removed (already in DB as 1.13.0); 7 remaining entries updated with 2026-05-08 research findings.
- **1.12.0** (2026-05-06) — Removed 3 test prime entries: test-prime-s35 (superThirtyFive, 32mm), test-prime-ff (fullFrame, 50mm), test-prime-lf (largeFormat, 65mm).
- **1.11.0** (2026-05-06) — Added 27 DZOFilm prime entries across 4 new series. Vespid Prime 2 (6: 18/24/35/50/85/105mm T1.9, fullFrame, PL); Vespid Retro (7: 16mm T2.8 + 25/35/50/75/100/125mm T2.1, fullFrame, PL); Vespid Cyber (3: 35/50/75mm T2.1, fullFrame, PL); Arles Prime (11: 14mm T1.9, 18/21/25/35/40/50/75/100mm T1.4, 135mm T1.8, 180mm T2.4, fullFrame, PL). XEEN Mango not imported — product not found in any manufacturer source (Samyang/XEEN official channels, retailer listings, press releases). All sources: dzofilm.com, bhphotovideo.com, ducloslenses.com, newsshooter.com.
- **1.10.0** (2026-05-06) — Cine prime completeness sprint: added 83 prime entries across 9 series. ZEISS CP.2 (11: 15/18/21/25/28/35/50/50M/85/100/135mm, fullFrame, PL); Cooke S7/i (9: 18/25/32/40/50/75/100/135/180mm, fullFrame, PL); Cooke miniS4/i (9: 18/25/32/40/50/65/75/100/135mm, superThirtyFive, PL); Cooke Panchro/i Classic FF (12: 18/21/25/27/32/40/50/65M/75/100/135/152mm, fullFrame, PL); Leitz Summilux-C (11: 16/18/21/25/29/35/40/50/65/75/100mm, superThirtyFive, PL); Leitz Summicron-C (10: 15/18/21/25/29/35/40/50/75/100mm, superThirtyFive, PL); DZOFilm Vespid Prime (10: 16/21/25/35/40/50/75/90M/100/125mm, fullFrame, PL — 12mm excluded, too wide); DZOFilm Gnosis Macro (4: 24/32/65/90mm, fullFrame, PL); Samyang XEEN (7: 14/16/24/35/50/85/135mm, fullFrame, PL). Also: corrected stale note in arri-signature-prime-12mm (removed incorrect largeFormat reference). Signature Zoom audit: all 4 entries already fullFrame — 0 corrections needed.
- **1.9.0** (2026-05-06) — Cine completeness sprint: added 126 entries across 12 series. Canon CN-E EF zoom variants (4: 15.5-47mm/30-105mm/14-35mm/31.5-95mm, superThirtyFive, EF); Canon CN-E PL primes (6: 14/24/35/50/85/135mm, fullFrame, PL); Fujinon MK (2: 18-55mm/50-135mm, superThirtyFive, EF); ZEISS CP.3 (10: 15/18/21/25/28/35/50/85/100/135mm, fullFrame, PL); ZEISS Supreme Prime (14: 15/18/21/25/29/35/40/50/65/85/100/135/150/200mm, fullFrame, PL); ARRI Signature Prime (16: 12/15/18/21/25/29/35/40/47/58/75/95/125/150/200/280mm, fullFrame, LPL); ARRI Ultra Prime (14: 14/16/20/24/28/32/40/50/65/85/100/135/150/180mm, superThirtyFive, PL); ARRI Master Prime (16: 12/14/16/18/21/25/27/32/35/40/50/65/75/100/135/150mm, superThirtyFive, PL); Cooke S4/i (16: 14/16/18/21/25/27/32/35/40/50/65/75/100/135/150/180mm, superThirtyFive, PL); Sigma FF High Speed Prime (11: 14/20/24/28/35/40/50/85/105/135mm + 65mm, fullFrame, PL); XEEN CF (6: 16/24/35/50/85/135mm, fullFrame, PL); Leitz THALIA 65 (11: 20/24/30/35/45/55/70/90/100/120/180mm, largeFormat, PL).
- **1.8.0** (2026-05-06) — Added 36 Canon EF mount lenses: 14 EF L-series photo zooms (16-35 f/2.8L II, 16-35 f/4L, 17-40 f/4L, 24-70 f/2.8L II, 24-70 f/4L, 24-105 f/4L IS II, 70-200 f/2.8L IS III, 70-200 f/2.8L IS II, 70-200 f/4L IS II, 70-200 f/4L, 100-400 f/4.5-5.6L IS II, 200-400 f/4L IS Ext 1.4x, 70-300 f/4-5.6L IS, 28-300 f/3.5-5.6L IS); 16 EF L-series photo primes (24 f/1.4L II, 35 f/1.4L II, 50 f/1.2L, 85 f/1.2L II, 85 f/1.4L IS, 100 f/2.8L macro, 135 f/2L, 200 f/2L IS, 300 f/2.8L IS II, 300 f/4L IS, 400 f/2.8L IS III, 400 f/4 DO IS II, 400 f/5.6L, 500 f/4L IS II, 600 f/4L IS III, 800 f/5.6L IS); 6 CN-E Cinema EOS primes EF mount (14mm T3.1, 24mm T1.5, 35mm T1.5, 50mm T1.3, 85mm T1.3, 135mm T2.2). All sensorFormat: fullFrame, mount: EF.
- **1.7.6** (2026-04-09) — Added mount field to all 236 entries: B4 (119 broadcast), PL (103 cine), LPL (5 ARRI Signature + Viltrox LUNA 42-420), EF (7 Canon Compact-Servo + DZOFilm Catta Ace/Tango), RF (2 Canon Flex Zoom). DZOFilm Catta Ace and Tango notes updated with DZO EF-style bayonet disclaimer
- **1.7.5** (2026-04-09) — zoomRatio audit: 143 entries recalculated to focalLengthMax/focalLengthMin (2 decimal places), all integers converted to floats; 17 cine Angénieux entries spelling corrected (Angenieux→Angénieux); 2 IDs with periods renamed (canon-hj14ex4.3b→canon-hj14ex4-3b, canon-hj22ex7.6b→canon-hj22ex7-6b)
- **1.7.4** (2026-04-08) — Added 3 test prime entries: test-prime-s35 (superThirtyFive), test-prime-ff (fullFrame), test-prime-lf (largeFormat) — one prime bracket per cine sensor format
- **1.7.3** (2026-04-07) — canon-hj15ex8-5b extenderFactor corrected 1.0→2.0 (confirmed via Canon pocket manual and Canon USA product page)
- **1.7.1** (2026-04-07) — Added 3 Large Format cine zooms: Hawk Telephoto Zoom 150-450mm T2.8, Viltrox LUNA 42-420mm T5.6, MasterBuilt CFZ 27-60mm T2.9 (sensorFormat: largeFormat, schema now live in app)
- **1.7.0** (2026-04-07) — Added 36 cine zoom lenses: ARRI/Fujinon Alura (4), ARRI/Zeiss Master Zoom (1), Fujinon HK Premier (4), Angénieux Optimo DP (2), Zeiss LWZ.2 + Supreme Zoom Radiance (4), Hawk/Vantage spherical zooms (3), Laowa OOOM + Ranger FF/S35 + Lite variants (13), Viltrox LUNA 30-300 (1), Sirui Jupiter (1), RED Pro (2), DZOFilm X-Tract probe zoom (1); removed test-prime-bracket temp entry; 3 Large Format lenses held pending schema support (largeFormat sensorFormat)
- **1.6.2** (2026-04-06) — Cine lens zoomRatio audit: 49 corrections across all cine brands (Canon CN-E, Fujinon ZK/Premista/Duvo, Angenieux Optimo/Style/Legacy/EZ, Cooke, Leitz, Zeiss, Sigma, Tokina, ARRI, DZOFilm) — replaced rounded integers with manufacturer-published or calc-accurate values (1 decimal)
- **1.6.1** (2026-04-06) — Broadcast lens verification audit: 19 corrections on 13 lenses (focalLengthMax from manufacturer specs replacing calculated values), CJ18ex7.6B extender 1.0→2.0, UJ90x9B 9.3-930→9-810mm, HJ40ex14B 14.3-572→14-560mm; removed 2 phantom entries (UA77x9.5, UA80x8); corrected XJ40x10B→HJ40x10B; Zeiss DigiZoom 17-112 zoom 7→6.5; added isCustom field to 119 entries; flagged XA17sx6.3 as unverified
- **1.6.0** (2026-04-05) — Corrected fujinon-zk14-35mm-t2-9 zoomRatio 3 → 2.5 (ZK2.5x14); added test-prime-bracket temp entry (wide=tele bracket test)
- **1.5.0** (2026-04-05) — Added 75 cine zoom lenses: Canon CN/CN-E (14), Fujinon ZK/XK/Premista/Duvo (11), Angenieux Optimo Ultra/EZ/Style/Legacy (17), Cooke Varotal/CXX (6), Leitz Zoom (2), Zeiss CZ.2/LWZ (4), Sigma (3), Tokina Vista/ATX (4), ARRI Signature/UWZ (5), DZOFilm Pictor/Catta/Tango (9)
- **1.4.0** (2026-04-03) — Version bump above high-water mark (1.3.0) for cache safety; full quality checklist passed
- **1.3.0** (2026-04-03) — Version bump above high-water mark (1.2.0) for cache safety; full quality checklist passed
- **1.2.0** (2026-03-28) — Version bump after adding 53 lenses
- **1.1.0** (2026-03-28) — Added 53 missing B4-mount broadcast lenses from research report
- **1.1.0** (2026-03-26) — Added 19 Canon lenses (HJ, KJ, XJ, J series)
- **1.0.4** (2026-03-26) — Version bump for download testing
- **1.0.3** (2026-03-26) — Initial upload

## ptz_cameras.json

### v1.12.0 — 2026-06-17

- Removed panasonic-aw-ue4 from the published core (out of scope per POS-D30; outOfScope flag was true; hFOVTele=111 anomalous for a fixed-lens ePTZ). Full core + detail entry preserved verbatim in TIM/Private/incomplete_data.md, restore only after validation. NOT aw-ue40 (free tier), which is untouched. PTZ core count 137 → 136.

### v1.11.0 — 2026-06-11

- Added Marshall CV625-TBN/TWN (`marshall-cv625-tbn`): NDI HX2/HX3 variant of CV625-TB/TW. Identical sensor (1/1.8-inch Sony IMX678 CMOS, 25×, 7.18mm width). hFOVWide 60.0° published by Marshall; hFOVTele 2.39° calculated. `addedDate: 2026-06-11`. Source: marshall-usa.com/cameras/CV625-TBN-TWN/ (Tier 1)

### v1.10.0 — 2026-06-10

- Added Hollyland Astra P1: new brand `hollyland`. 1/1.8-inch CMOS, 30× optical zoom, HFOV 59.2°–2.5° (published by Hollyland, H values), focal range 7.1–210.0mm. NDI|HX3, 3G-SDI, HDMI, SRT. `addedDate: 2026-06-10`. Source: hollyland.com/product/astra-p1 (Kay-verified)

### v1.9.0 — 2026-06-09

- Schema: added `addedDate` field (ISO `YYYY-MM-DD` or `null`) to every entry. Same basis as lenses.json v1.26.0
- Baseline (pre-launch) entries carry `addedDate: null` — 123 of 135 entries
- Non-null dates assigned to the 12 entries added after launch, dated by their first commit to main:
  - `2026-06-01` (12): JVC KY-PZ510N (commit d5ac4a2) + AVer PTZ310UNV2/PTZ231/PTC310UV2/TR211/TR315/TR315N/TR335/TR335N/TR535/TR535N/TR615 (commit 4c2aa8c)
- Going forward: every new PTZ import sets `addedDate` to the import's commit date on insert

### v1.8.0 — 2026-06-01

- AVer import: 11 new entries (PTZ310UNV2, PTZ231, PTC310UV2, TR211, TR315, TR315N, TR335, TR335N, TR535, TR535N, TR615)
- PTZ310UNV2: NDI-native variant of PTZ310UV2, optics identical (72.1°/6.3°, 12x, 3.9–46.8mm)
- PTZ231: Full HD 30x variant (62.3°/2.5°, 4.5–135mm)
- PTC310UV2: Dual-lens auto-tracking system; main PTZ lens only (70°/6°, 12x, 3.9–46.8mm); panoramic tracking module out of scope
- TR211/TR315/TR315N: 12x 1/2.8" CMOS (70°/6°, 3.9–46.8mm); TR315N is NDI variant
- TR335: 30x 1/2.8" CMOS (62.3°/2.5°); note in entry: published focal range (3.9–46.8mm) is inconsistent with stated 30x zoom; likely AVer data error; HFOV verified
- TR335N: NDI HX3 variant of TR335 (62.3°/2.5°, 4.5–135mm/30x — consistent)
- TR535: 30x dual-camera auto-tracking; main PTZ lens only (62.3°/2.5°, 4.5–135mm); secondary 105° wide-angle module out of scope
- TR535N: NDI HX3 variant of TR535 (62.3°/2.5°, 4.5–135mm, PoE++)
- TR615: 1-inch Sony Exmor RS, 19x, dual 12G-SDI, PoE++ (69.5°/3.5°, 9.79–186.39mm)
- PTZ211: NOT imported — conflicting HFOV values across sources (62.3° from datasheet PDF vs 72.8° from product page); held pending clarification from AVer

### v1.7.0 — 2026-06-01

- Added JVC KY-PZ510N (NDI|HX2 variant of KY-PZ510). Optics identical: 1/2.8-inch CMOS, 12x, hFOVWide 80.0°, hFOVTele 7.8° (calc). Secondary source: omegabroadcast.com distributor spec. Separate entry per NDI precedent (KY-PZ200 / KY-PZ200N).

- **1.7.0** (2026-06-01) — Added jvc-ky-pz510n: NDI|HX2 variant of KY-PZ510; optics identical, sensor values follow KY-PZ510 (1/2.8-inch, sensorWidthMM 5.71, sensorWidthMM 3.84). Note on sensor label discrepancy between JVC main page (1/2.5-inch) and distributor spec (1/2.8-inch) documented in notes.
- **1.6.0** (2026-05-18) — Added 3 BirdDog X1 series entries: birddog-x1 (20x, 55.8°/3.2°), birddog-x1-30x (30x, 58.1°/2.14°), birddog-x1-ultra (12x, 70.28°/6.57°). All HFOV published by BirdDog (Tier 1).
- **1.5.0** (2026-04-29) — Added 33 entries across 4 new brands: Fomako (12: K820/K820N/K30NS/K20/K30/KN20/KN30/KN20A/KN30A/FMK12UH/FMK20UH/K600N), Bolin (11: B2-210/B2-220/B6-420/R9-418F/R9-418N/R9-230H/RANGE/D2-210H/D2-220H/N2-210X/N2-220X), AVer (3: PTZ310UV2/PTZ330UV2/PTZ330UNV2), Minrray (7: UV430E0/E2/E3/UV510E0/E2/UV950E0/E2)
- **1.4.6** (2026-04-09) — Added Sony BRC-AM7(W): 1-inch Exmor RS CMOS, 20x, 8.8–176mm, hFOVWide 75.0° (Sony help guide). Lens module appears shared with Panasonic AW-HE145/UE160/UE150. Panasonic AW-UE4 marked outOfScope (111° HFOV exceeds iPhone ultrawide ~108°)
- **1.4.5** (2026-04-08) — Marshall CV730 FOV correction: marshall-cv730-bk hFOVWide 65.0→63.0 + hFOVTele 2.04→3.7, marshall-cv730-bhn hFOVTele 2.04→3.7 — manufacturer-confirmed by Greg Foster, Applications Engineer, Marshall Electronics
- **1.4.4** (2026-04-06) — datavideo-ptc-150: maxFocalLengthMM corrected 94.6→129.0 (data entry error; correct 30x range is 4.3–129mm per Datavideo)
- **1.4.3** (2026-04-06) — HFOV audit: marshall-cv730-bk hFOVTele 2.0→2.04 (calc), marshall-cv730-bhn hFOVWide 65.0→63.0 + hFOVTele 2.0→2.04, panasonic-aw-ue4 notes corrected (motorized PTZ + digital zoom)
- **1.4.2** (2026-04-05) — panasonic-aw-ue4: hFOVTele null → 111.0 (ePTZ fixed lens, wide=tele)
- **1.4.1** (2026-04-05) — Missing fields filled for 16 cameras: panasonic-aw-he38, marshall-cv630-ndi/bi, marshall-cv625-tb, marshall-cv605-u3, datavideo-ptc-150/150t/280/285/285t/300/305/305t, ptzoptics-pt12x-4k-g3/link-4k, lumens-vc-tr1 (sessions 72–78 research)
- **1.4.0** (2026-04-03) — Version bump above high-water mark (1.3.0) for cache safety; full quality checklist passed
- **1.3.0** (2026-04-03) — Version bump above high-water mark (1.2.1) for cache safety; full quality checklist passed
- **1.2.1** (2026-04-03) — Removed duplicate sony-brc-h800 entry (conflicting specs); merged notes into surviving entry
- **1.2.0** (2026-03-28) — Added Sony PTZ cameras
- **1.1.0** (2026-03-28) — Added Panasonic, Canon, JVC, Lumens, Marshall, BirdDog, Datavideo, PTZOptics entries
- **1.0.1** (2026-03-26) — Version bump for download testing
- **1.0.0** (2026-03-26) — Initial upload

## ptz-details.json

### v1.22.0 — 2026-07-23

- PTZ blok-2 batch 1: aperture, introductionYear, autoTracking plus note, hasIS/hasND/ndDetail op 136 details; connectiviteit-reshape (videoOutputs fysiek-only, controlProtocols zuiver control, streamingProtocols en trackingDataOut nieuw) op 135.

### v1.21.0 — 2026-06-17

- Removed panasonic-aw-ue4 detail entry (paired with the core removal above; out of scope per POS-D30). Full entry preserved verbatim in TIM/Private/incomplete_data.md. PTZ detail count 137 → 136.

### v1.20.1 — 2026-06-12

- Hollyland Astra P1 (`hollyland-astra-p1`): added `hasPoE: true`, set `poeClass: "PoE+"`, added official Quick Guide PDF to sources. Source: Hollyland Astra P1 Quick Guide V1.0 p.8 — "Input Voltage: DC 12V/PoE+"

### v1.20.0 — 2026-06-11

- Sidecar for Marshall CV625-TBN/TWN (`marshall-cv625-tbn`): controlProtocols adds NDI HX2 + NDI HX3 to CV625-TB base set; videoOutputs adds NDI. All other fields identical to marshall-cv625-tb (poeClass PoE+, presetCount 255, panRangeDeg 340, tiltRangeDeg 120, hasIR true, hasCeilingMount true; weight/dims null). Source: marshall-usa.com/cameras/CV625-TBN-TWN/ (Tier 1)

### v1.19.0 — 2026-06-10

- Hollyland Astra P1 sidecar: presetCount=255, panRangeDeg=340, tiltRangeDeg=120, minLux=0.5, weightG=2300, dims 169×188×226mm. controlProtocols: NDI|HX3/VISCA/Pelco-D/RTSP/RTMP/SRT. videoOutputs: 3G-SDI/HDMI/IP. poeClass=null (not specified by source). hasIR/whiteBalanceModes/speed/mountThreads null (not provided). Source: hollyland.com/product/astra-p1

### v1.18.0 — 2026-06-01

- AVer sidecar import: 11 new entries matching ptz_cameras.json v1.8.0 additions
- PTZ310UNV2: controlProtocols add NDI|HX2 + NDI|HX3; PoE+; 180×192×145mm; sources: averusa.com datasheet PDF
- PTZ231: controlProtocols include NDI|HX3; PoE+; 180×192×145mm; sources: averusa.com datasheet PDF
- PTC310UV2: controlProtocols VISCA/Pelco/CGI only (NDI optional license upgrade, not built-in); presetCount=255; PoE+; sources: AVer brochure PDF via presentation.aver.com + charmex.net distributor PDF
- TR211/TR315/TR315N: controlProtocols VISCA/Pelco-D/CGI/NDI|HX3; PoE+; 180×192×145mm
- TR335: controlProtocols VISCA/Pelco-D/CGI/NDI|HX3; PoE+; 180×192×145mm; sources: averusa.com product page + datasheet PDF
- TR335N: controlProtocols add Pelco-P + ONVIF; PoE+; 180×192×145mm; sources: averusa.com datasheet PDF
- TR535: controlProtocols include NDI High Bandwidth + NDI|HX2 + ONVIF; PoE++; 202.5×250.7×218.5mm; sources: AVer brochure PDF (cors-web.aver.com)
- TR535N: controlProtocols include NDI|HX3 + ONVIF; PoE++; 202.5×218.5×250.7mm; sources: averusa.com datasheet PDF
- TR615: controlProtocols include NDI|HX3 + ONVIF + HLS; PoE++; 12G-SDI output; 202.5×304.5×231.5mm; sources: averusa.com datasheet PDF

### v1.17.0 — 2026-06-01

- Added KY-PZ510N sidecar. controlProtocols updated for NDI|HX2 (SRT, RTSP, RTMP, RTMPS added). manufacturerUrl: pro.jvc.com KY-PZ510N page. All optical sidecar fields identical to KY-PZ510.

### v1.16.0 — 2026-05-18

- Added 3 BirdDog X1 detail entries: birddog-x1, birddog-x1-30x, birddog-x1-ultra. Sources: birddog.tv/x1-techspecs/ (Tier 1), birddog.tv/cameras-show/ (Tier 1), videoguys.com (Tier 2).

### v1.15.1 — 2026-05-14
- null-audit pass (Kay research, session 2026-05-14, per POS-D23): 34 field writes across 16 entries
- Canon CR-N700: minLux=2.5, mountThreads="1/4\"-20", hasCeilingMount=true, hasWallMount=true
- Canon CR-N500: minLux=1.5, mountThreads="1/4\"-20", hasCeilingMount=true, hasWallMount=true
- Canon CR-N300: minLux=1.5, mountThreads="1/4\"-20", hasCeilingMount=true, hasWallMount=true
- Canon CR-N100: mountThreads="1/4\"-20", hasCeilingMount=true, hasWallMount=true
- Sony BRC-X1000: mountThreads="1/4\"-20", hasWallMount=true
- Sony BRC-H800: mountThreads="1/4\"-20", hasWallMount=true
- Sony BRC-X400: widthMm=158.4, heightMm=177.5, depthMm=200.2
- Panasonic AW-UE150: minLux=2.0, mountThreads="1/4\"-20"
- Panasonic AW-UE4: presetCount=100, panRangeDeg=0, tiltRangeDeg=0, hasIR=false, minLux=1.0, weightG=500, widthMm=123, heightMm=131, depthMm=136
- Panasonic AW-HE130: mountThreads="1/4\"-20"
- JVC KY-PZ100: weightG=1900, widthMm=148, heightMm=199.5
- JVC KY-PZ200: whiteBalanceModes filled (5 modes)
- JVC KY-PZ510: minLux=0.5
- BirdDog P110: weightG=1000, widthMm=145, heightMm=152, depthMm=171
- BirdDog P240: weightG=2395, widthMm=163, heightMm=199, depthMm=231
- Lumens VC-A50P: whiteBalanceModes filled (5 modes), mountThreads="1/4\"-20"
- Lumens VC-A61P: whiteBalanceModes filled (5 modes)
- Marshall CV620-BK4: maxPanSpeedDegS=300, maxTiltSpeedDegS=300, whiteBalanceModes filled (5 modes), mountThreads="1/4\"-20"
- Marshall CV730-BK: whiteBalanceModes filled (5 modes)
- Bolin Range: presetCount=128, panRangeDeg=340, tiltRangeDeg=120, minLux=0.5, widthMm=201, heightMm=256

### v1.15.0 — 2026-05-12
- schema migration: hasPoE (boolean) replaced with poeClass (string enum) across all 120 entries
- enum values: "none" (no PoE), "PoE" (802.3af), "PoE+" (802.3at), "PoE++" (802.3bt)
- distribution: PoE++ ×18, PoE+ ×70, PoE ×28, none ×4
- datavideo-ptc-140 + datavideo-ptc-150: poeClass "none" + fieldNotes.poeClass "DC 12V only; PoE input via optional AD-POE140 adapter (sold separately)"
- research: Kay (poeClass-research.md, 2026-05-12)

### v1.14.0 — 2026-05-12
- 9 stub entries filled: canon-cr-n400, canon-cr-n350, canon-cr-x300, sony-brc-am7, sony-brc-h900, jvc-ky-pz200, jvc-ky-pz200n, birddog-p110, birddog-p120

### v1.13.0 — 2026-05-10
- correction: minrray-uv510e0/e2 heightMm 168 -> 167.5 (published value; rounding to integer was incorrect)

### v1.12.0 — 2026-05-10
- null-audit pass 3: filled weightG/dims for datavideo-ptc-280, bolin-r9-418n, bolin-r9-230h, minrray-uv510e0, minrray-uv510e2 (5 entries)
- datavideo-ptc-280: weightG 2800 g — distinct from PTC-285 (2600 g); chassis is not identical
- bolin-r9-418n: heightMm 249 is body-only (without feet mats)
- minrray-uv510e0/e2: heightMm 168 rounded from published 167.5 mm

### v1.11.0 — 2026-05-10
- null-audit pass 2: filled weight/dims/presetCount/speed/range for BirdDog P100/P200/P400/P4K, Datavideo PTC-140/150/150T/280/285/285T/300/305/305T, JVC KY-PZ510/PZ540N, Bolin R9-418F, Minrray UV430E0/E2/E3/UV950E0/E2 (21 entries updated)
- birddog-maki-ultra: skipped — ID not present in database
- datavideo-ptc-280: weightG remains null — not confirmed via Tier 1/2 source
- minrray-uv950e2: weightG set to 1540 g (gtrdirect.ca, recent listing); conflicting value 2000 g (manualslib, older edition) discarded in favour of more recent source


- **1.10.0** (2026-05-10) — Null-audit pass 1 Lumens+Marshall: 9 entries. lumens-vc-a53/61p/61pn/tr1/r30: weightG+dims added (data sheets). marshall-cv630-ip/ndi/bi: maxPanSpeedDegS=100, maxTiltSpeedDegS=100 (CV630-IP cut sheet). marshall-cv605-u3: weightG=1290, widthMm=145, heightMm=154 (manua.ls). depthMm for cv605-u3 confirmed legitimately null (not published in any Tier 1/2 source).

- **1.9.0** (2026-05-10) — Fomako/Bolin/AVer/Minrray/PTZOptics fill: 39 entries. Fomako (12): k820/k820n/k30ns/k20/k30/kn20/kn30/kn20a/kn30a/fmk12uh/fmk20uh/k600n. Bolin (11): b2-210/b2-220/b6-420/r9-418f/r9-418n/r9-230h/range/d2-210h/d2-220h/n2-210x/n2-220x. AVer (3): ptz310uv2/ptz330uv2/ptz330unv2. Minrray (7): uv430e0/e2/e3/uv510e0/e2/uv950e0/e2. PTZOptics SE G3 (3): pt12x/pt20x/pt30x-se-g3. PTZOptics SDI G2 (3): pt12x/pt20x/pt30x-sdi-g2. Sources added to all entries. hasIR=false for all 39 (no IR receiver). whiteBalanceModes/minLux/mountThreads/hasWallMount=null for all 39 (not published).

- **1.8.0** (2026-05-10) — Lumens/Marshall fill v2: 6 entries updated. lumens-vc-a51p: weightG=2000, dims 175×185×185mm, Amazon source added. lumens-vc-a71p: weightG=3000, dims 232×189×188mm, sources replaced with manua.ls. lumens-vc-a71pn: weightG=3000, dims 232×189×188mm, manua.ls source added. lumens-vc-a71p-hn: weightG=3000, dims 232×189×188mm, videoOutputs corrected (added 3G-SDI), manua.ls source added. marshall-cv612ht-4k: presetCount 255→128, maxPanSpeed/TiltSpeed=300, minLux=3.0, weightG=2000, dims 174×187×171mm, manua.ls+digibroadcast sources. marshall-cv605-u3: minLux=0.5, spec sheet source added.
- **1.7.0** (2026-05-10) — Lumens/Marshall fill: 21 entries total (11 Lumens + 10 Marshall). Sources added as last field per schema. Lumens: vc-a50p/50s weight/dim from manua.ls (same body); vc-a51p/53/61p/61pn/71p/71pn/71p-hn/tr1/r30 weight/dim null (not published). vc-a51p/tr1 maxPanSpeed inferred (300°/s per press release; 120°/s body-match respectively). vc-a61p minLux 0.1 and speed per AV-IQ datasheet; vc-a71p minLux 0.05 and speed per Amazon. Marshall: cv620-bk4/bi weight/dim from manua.ls; cv630-ip/ndi/bi weight/dim from PDF manuals; cv730-bk/bhn weight/dim+speed from cut sheet PDF. cv730-bk hasCeilingMount+hasWallMount=true; cv730-bhn idem. cv612ht-4k/cv625-tb/cv605-u3 weight/dim null (not published).
- **1.6.0** (2026-05-10) — Added sources field to all 51 filled entries (Canon CR ×4, Sony ×9, Panasonic ×11, JVC ×6, BirdDog ×7, Datavideo ×9, PTZOptics ×5). sources = [manufacturerUrl] for single-source entries; secondary sources added for: sony-brc-x1000 (fullcompass, weightG/dim), sony-brc-am7 (helpguide.sony.net), sony-brc-x400 (manualslib), sony-srg-360she (manua.ls), panasonic-aw-he145 (panasonic EU spec PDF), jvc-ky-pz400n (proflixsales), jvc-ky-pz540n (B&H, speed), birddog-p100 (lensrentals, tiltRange), ptzoptics all 5 (fullcompass, weight/dim). Unfilled entries (manufacturerUrl=null) left unchanged.
- **1.5.0** (2026-05-10) — BirdDog/Datavideo/PTZOptics fill: 21 entries total. BirdDog (7): p100, p110, p120, p200, p240, p400, p4k — source: birddog.tv. p100/p110/p120 tiltRangeDeg=105 (±15° down/+90° up); p400/p4k hasCeilingMount+hasWallMount=true, 6G-SDI output, maxPanSpeed 100°/s. Weight/dim not published for any BirdDog entry. Datavideo (9): ptc-140 through ptc-305t — source: datavideo.com. presetCount/speed/weight/dim all null (not published; spec tables JS-rendered). PTZOptics (5): pt12x-4k-g3, pt20x-4k-g3, pt30x-4k-g3, pt12x-link-4k, pt20x-link-4k — source: ptzoptics.com. Link series adds Dante AV-H protocol. 12x models weightG=1470/168×165×142mm; 20x/30x models weightG=2000/170×228×181mm.
- **1.4.0** (2026-05-10) — JVC fill: filled all fields for 6 JVC entries (ky-pz100, ky-pz200, ky-pz200n, ky-pz400n, ky-pz510, ky-pz540n). Source: jvc.com (primary); ky-pz540n maxPanSpeedDegS/maxTiltSpeedDegS per B&H (JS-rendered spec page). ky-pz100 speeds are AC adapter values (480°/s pan, 300°/s tilt); PoE+ values are lower. ky-pz510 panRangeDeg/tiltRangeDeg/speed null (JS-rendered, not retrievable). ky-pz540n panRangeDeg/tiltRangeDeg null (same). ky-pz200/200n/400n whiteBalanceModes null (not published in spec). ky-pz100 weight/dimensions not published.
- **1.3.0** (2026-05-10) — Panasonic fill: filled all fields for 11 Panasonic entries (aw-ue150, aw-ue150a, aw-ue160, aw-he145, aw-ue100, aw-ue80, aw-ue50, aw-ue40, aw-ue30, aw-ue20, aw-ue4). Source: pro-av.panasonic.net (primary). aw-ue4 is ePTZ (digital pan/tilt): panRangeDeg/tiltRangeDeg/speed/hasIR/whiteBalanceModes/weight/dimensions remain null (not applicable or not published). aw-ue160/aw-ue100 weight/dimensions not published. aw-ue50/aw-ue40/aw-ue30 share spec page (aw-ue50-40); aw-ue30 has no NDI.
- **1.2.0** (2026-05-10) — Sony fill: filled all fields for 9 Sony entries (brc-x1000, brc-h800, brc-am7, brc-x400, srg-x400, srg-x120, srg-300h, srg-360she, brc-h900). Source: pro.sony specification pages (primary). Remaining nulls: brc-am7 weight/dimensions not published; brc-x400/srg-x400/srg-x120 dimensions not published; srg-300h/brc-h900 weight/dimensions not published; maxPanSpeedDegS/maxTiltSpeedDegS null for srg-300h, srg-360she, brc-h900 (not published).
- **1.1.0** (2026-05-10) — Canon CR series fill: filled all fields for canon-cr-n700, canon-cr-n500, canon-cr-n300, canon-cr-n100. Source: canon-europe.com specification pages (primary).
- **1.0.0** (2026-05-08) — Initial skeleton: 120 entries, all fields null.

## devices.json

- **1.6.1** (2026-06-14) - Content-neutral version bump to cut db-v5 and first-publish current_version.json on the CDN; no device data changed (only the version field moved)
- **1.6.0** (2026-04-03) — Added displayMM field to all 50 camera entries across all 19 iPhone/iPad device entries; non-Pro wide=26mm, Pro wide=26mm pre-14-Pro / 24mm from 14-Pro onward
- **1.5.0** (2026-04-03) — Added isSensorCrop and videoZoomFactor fields to sensor-crop telephoto entries (iPhone 15 Pro Max 10x, iPhone 16 Pro 10x, iPhone 17 Pro 8x, iPhone 17 Pro Max 8x); schema addition from session 74.01
- **1.4.0** (2026-04-03) — Version bump above high-water mark (1.3.0) for cache safety; full quality checklist passed
- **1.3.0** (2026-04-03) — Version bump above high-water mark (1.2.0) for cache safety; full quality checklist passed
- **1.2.0** (2026-03-30) — Version bump after audit
- **1.1.0** (2026-03-30) — Audit and clean: removed iPads, fixed hFOVSource strings, removed 2x sensor crop entries, added 10x telephoto entries for iPhone 15 Pro Max and 16 Pro
- **1.1.0** (2026-03-28) — Added hFOV research study corrections: ultrawide 120° → 108.3° (Apple's 120° is diagonal), recalculated all telephoto values, added iPhone 17 Pro 4x/8x entries
- **1.0.1** (2026-03-26) — Version bump for download testing
- **1.0.0** (2026-03-26) — Initial upload

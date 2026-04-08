# Changelog

Most recent changes at the top. One line per file changed per commit.

## lenses.json

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

## devices.json

- **1.6.0** (2026-04-03) — Added displayMM field to all 50 camera entries across all 19 iPhone/iPad device entries; non-Pro wide=26mm, Pro wide=26mm pre-14-Pro / 24mm from 14-Pro onward
- **1.5.0** (2026-04-03) — Added isSensorCrop and videoZoomFactor fields to sensor-crop telephoto entries (iPhone 15 Pro Max 10x, iPhone 16 Pro 10x, iPhone 17 Pro 8x, iPhone 17 Pro Max 8x); schema addition from session 74.01
- **1.4.0** (2026-04-03) — Version bump above high-water mark (1.3.0) for cache safety; full quality checklist passed
- **1.3.0** (2026-04-03) — Version bump above high-water mark (1.2.0) for cache safety; full quality checklist passed
- **1.2.0** (2026-03-30) — Version bump after audit
- **1.1.0** (2026-03-30) — Audit and clean: removed iPads, fixed hFOVSource strings, removed 2x sensor crop entries, added 10x telephoto entries for iPhone 15 Pro Max and 16 Pro
- **1.1.0** (2026-03-28) — Added hFOV research study corrections: ultrawide 120° → 108.3° (Apple's 120° is diagonal), recalculated all telephoto values, added iPhone 17 Pro 4x/8x entries
- **1.0.1** (2026-03-26) — Version bump for download testing
- **1.0.0** (2026-03-26) — Initial upload

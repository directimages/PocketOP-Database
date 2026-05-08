# Changelog

Most recent changes at the top. One line per file changed per commit.

## lens-details.json

- **1.1.0** (2026-05-08) — Fujinon broadcast lens fill: manufacturerUrl set for all 48 Fujinon broadcast entries (UA/HA/XA/ZA/LA series). Physical specs (weightG, lengthMm, frontDiameterMm, closeFocusM) filled for 26 entries confirmed in FUJIFILM FUJINON Broadcast & Cine Catalog 2024. 22 entries receive manufacturerUrl only (older HA/XA/ZA/LA series not in 2024 catalog). All cine entries (ZK/XK/Premista/HZK/HK/MK) remain null — out of scope for this pass. Source: FUJIFILM_FUJINON_Broadcast_Cine_Catalog_2024.pdf.
- **1.0.0** (2026-05-08) — Initial skeleton: 549 entries, all fields null.

## lenses.json

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

# Chicago M3/M4 provisional face production — 27 September 2026

## Status

**A citywide candidate inventory exists; no candidate is an accepted physical block yet.** In response to the production-first decision, this run generated every land face produced by the current Cook ROW + Road Edge rule and kept tiny faces, motorway islands, rail/airport faces and suspected merges for later review. It does not change the Chicago model's M3 or M4 fields. The pipeline is deliberately auditable: raw extracts and receipts, district fragments, stitched whole-city candidates, a review queue and versioned repair proposals remain separate.

## Inputs, rule and storage

The [source acquisition manifest](../../../work/chicago_m3_row_land_2026_09_26/citywide_source_acquisition_2026_09_27.json) covers 154 Cook layer extracts for all 77 Community Areas. It checks each ArcGIS feature-ID retrieval and records source hashes. The 77 cached ROW and Road Edge GeoJSON pairs occupy **353.9 MiB**. The [construction manifest](manifest.json) records the source hash and counts per area, rule, 0.01 m coordinate precision and output hashes.

The candidate barrier is the direct union of Cook ROW `ROWTYPE ∈ {1,4,5}` and ordinary Road Edge `TYPE=1`, minus a 3 m buffer of mapped alley Road Edge `TYPE=5`. This was a development rule from the earlier pilot, not a certified citywide width. Source barrier geometry is snapped to 0.01 m; original Community Area boundaries are preserved to avoid artificial seam overlaps. The source files include overlapping features around Community Area envelopes; construction clips each barrier to the district polygon. The geometry is in EPSG:26916 metres. Water, rail, motorway, airport and other special land are **not** automatically removed from the first candidate pass.

The [district fragments](candidate_inventory.csv) contain **23,694** faces in 77 GeoParquet files, together **31.93 MiB**. The [stitching pass](stitch_summary.json) connects cross-area fragments only when they share at least 0.1 m of boundary, preserving original fragment IDs. It yields **23,204** [citywide provisional faces](global_provisional_faces.parquet) in a **31.27 MiB** compressed geometry file. Source files plus results remain far below the 3 GiB pilot-output budget; the disk has **12.57 GiB free** after the run. The two earlier raw LAS tiles were neither copied nor expanded during this run.

## Construction checks

| Check | Result |
|---|---:|
| Community Areas acquired and processed | 77/77 |
| Source layer pairs | 77 ROW + 77 Road Edge |
| District fragments | 23,694 |
| Cross-area stitch links | 506 |
| Groups joining multiple district fragments | 402 |
| Citywide provisional faces | 23,204 |
| Faces with an unresolved internal Community Area edge | 9 |
| Stitched faces touching the Chicago boundary | 184 |
| Area conservation error in stitching | <0.000001 m² over 464.7 km² of candidate-face area |
| Candidate overlaps over 0.01 m² | 0 |
| Faces under 1,000 m² | 2,793 |
| Faces over 100,000 m² | 354 |

Every district batch passed geometry validity and face-area conservation checks. The [validation report](validation_summary.json) also checks source hashes, global IDs, geometry validity, disk floor and all intersecting candidate pairs. A first build had one 0.097 m² district-seam overlap caused by independently snapping administrative boundaries; preserving their original coordinates removed it. Nine internal district-edge cases remain flagged. Their seam line may be a real corridor boundary or a mismatch; they are **not automatically merged**. These are computational checks, **not** block truth checks. The very large O'Hare airport candidate (about 21.2 km²) and the many tiny faces show why every closed land face cannot simply be scored as an M3/M4 block. A face along a city boundary also needs outside-city context before being declared whole.

The [global candidate inventory](global_candidate_inventory.csv) stores `source_fragment_ids`, contributing Community Areas, outer area, hole area, outer perimeter, raw compactness and edge flags. The [district-fragment queue](review_queue.csv) and [exhaustive stitched-face review queue](global_review_queue.csv) retain every face with diagnostic flags. The [repair ledger](repair_ledger.csv) is a blank, versioned operation schema; it has not been filled with adjudicated decisions. A flag is **not a confirmed error**.

## First repair proposal and next review pass

The [West Veterans Place proposal](west_veterans_split_proposal.json) targets global candidate `M3C_GLOBAL_0c95e935f86f2fa81549` (17,192 m²). A 10 m parcel-gap corridor along municipal street segment `154550` divides it into provisional faces of **10,227** and **5,586 m²**, removing **1,379 m²** of candidate land as proposed road corridor. The six-parcel anchor overlaps one proposed face by 97.45%. The [two proposed geometries](west_veterans_split_proposal.parquet) are separate from the original global table. This is **not an accepted repair**: parcel geometry helped construct the corridor, so overlap with those same parcels does not independently establish its property-side edge or road width. Road status and boundary evidence still require adjudication.

The [citywide street-gap queue](named_street_gap_queue.csv) screened **47,010** named municipal segments and flagged **355** with a run of at least 30 m outside the ROW/Road Edge mask after a 5 m alignment allowance. Every alert links to at least one provisional candidate. The [summary](named_street_gap_queue_summary.json) records thresholds and source hashes. The 11 alerts in the five previously tested areas exactly match the earlier bounded screen. O'Hare (CHI:76) accounts for **189** alerts; **179** of all alerts are municipal class 99, predominantly runway/taxiway and other airport lines. These are special-context leads, not 179 missing ordinary block divisions. An alert elsewhere can be a missing at-grade street, source misalignment, private or lower-level street, or another special case. It triggers review, not an automatic split.

The [global review queue summary](global_review_queue_summary.json) marks **3,756** faces for first review because of small/large area, low raw compactness, city-edge exposure or a named-street alert. The other **19,448** remain in the full census; they are not bulk accepted. Among all faces, 122 intersect a non-class-99 street alert, while one huge airport candidate holds the class-99 alert group. The queue's priority is a work order, not a classifier. After gap and context review, a new repaired candidate version can be evaluated on a complete independent reference. The 23,204-face layer must not enter Chicago M3/M4 before that gate.

The [first linked visual triage](frozen_control_review/README.md) resolves frozen image points to global candidate IDs and records 12 specific follow-ups. It found two probable CHI:49 rail-point misassignments, nine unadjudicated faces that look like ordinary blocks in CHI:57/CHI:63, and one O'Hare candidate containing airport operating land within the image core. This review changes no geometry or acceptance status.

## Reproduce

```bash
.venv/bin/python analysis/scripts/acquire_chicago_m3_citywide_sources_2026_09_27.py --max-new-units 77
.venv/bin/python analysis/scripts/build_chicago_m3_provisional_faces_2026_09_27.py
.venv/bin/python analysis/scripts/stitch_chicago_m3_provisional_faces_2026_09_27.py
.venv/bin/python analysis/scripts/propose_chicago_m3_veterans_repair_2026_09_27.py
.venv/bin/python analysis/scripts/queue_chicago_m3_named_street_gaps_2026_09_27.py
.venv/bin/python analysis/scripts/assemble_chicago_m3_review_queue_2026_09_27.py
.venv/bin/python analysis/scripts/validate_chicago_m3_provisional_faces_2026_09_27.py
```

The first command needs access to the public Cook County GIS service when data are not cached. Each stage preserves its inputs and records hashes; the source and construction scripts enforce an 8 GiB free-space floor. The repair and gap scripts do not alter the original candidate layer.

# Cook 2022 classified LiDAR: Chicago M3/M4 targeted point-cloud test

**Decision:** Classified point returns add useful physical evidence to the polygon-first block method. In this selected pilot they distinguish a built frontage wedge from two tree-covered freeway slivers, show a road-surface trace along West Veterans Place where the current county ROW/Road Edge masks have a gap, and show a bridge deck above local ground. They do **not** by themselves establish legal street boundaries, validate every block, or authorize citywide M3/M4.

## Acquisition and provenance

The [Illinois 2022 Cook LiDAR collection](https://clearinghouse.isgs.illinois.edu/lidar-county) supplies classified LAS 1.4 point clouds. We downloaded the small [tile index/metadata package](https://clearinghouse.isgs.illinois.edu/distribute/district1/cook/2022/cook_TileIndex_metadata.zip) and identified tiles `13259350` (motorway core) and `13759300` (West Veterans Place). Each tile is 2,500 ft square. The publisher distributes the LAS in huge multi-part ZIPs, but its server supports HTTP byte ranges. The scripts requested **only two ZIP members** from [part 3](https://clearinghouse.isgs.illinois.edu/distribute/district1/cook/2022/cook-las3.zip): 633.7 MB and 764.9 MB compressed, rather than an entire ~849 GB archive. The extracted LAS files remain in ignored `analysis/work/chicago_m3_lidar_point_pilot_2026_09_26/`. [Member receipts and LAS headers](summary.json) and [West Veterans receipts](veterans_summary.json) record byte ranges, hashes, point counts and scale/offset values. Raw metadata and the tile-index archive are also retained there.

The tested tiles contain 34,888,939 and 41,757,984 points respectively. We read the LAS 1.4 point-format-6 classification byte and mapped candidate/road geometry to the file's EPSG:6455 coordinate system. Counts below are **fractions of point returns**, not land-area fractions. Multi-return density, occlusion and classification errors can affect them.

## Motorway core: buildings versus vegetation

Nine previously saved ROW + Road Edge + 3 m alley-opening faces fall inside the first tile: two visually built block candidates and seven small motorway slivers. The [full point-class table](candidate_point_classes.csv) preserves all observed codes and counts.

| Saved face | Visual role | Point returns | Class 6 building | Classes 3–5 vegetation | Class 11 road |
|---|---|---:|---:|---:|---:|
| 52 | Residential block | 995,151 | 30.0% | 15.0% | 3.8% |
| 72 | Narrow frontage wedge | 304,059 | 29.0% | 11.5% | 5.1% |
| 56 | High-height freeway sliver | 50,660 | 0% | 44.3% | 1.6% |
| 71 | High-height freeway sliver | 56,239 | 0% | 57.1% | 1.6% |

All seven tested slivers have zero class-6 returns. This resolves the ambiguity in the earlier DSM−DTM raster test for the two height-rich slivers: their height signal is primarily vegetation. The narrow built wedge is protected by strong building-class support despite 0.674 motorway-buffer exposure. **Proposed action:** strong class-6 support rescues a high-motorway-exposure face for block review; zero building returns never automatically rejects a face because parks and vacant true blocks exist. The other six slivers and three visually built faces lie partly or wholly outside this one LAS tile and are not silently counted as point-cloud validations.

## Missing street: West Veterans Place

A frozen named-street screen found a **71.1 m** segment of active municipal **W Veterans Place** outside the Cook ROW plus Road Edge mask after 5 m alignment tolerance. The second tile shows a continuous strip of class-11 road-surface returns aligned with that gap on the [2025 orthophoto overlay](veterans_class11_ortho_overlay.png). Within 3 m of the municipal line, class 11 is **86.7% of 2022 point returns**; at 5 m it is 69.9%. Nearby covered controls W Ainslie Street and W Higgins Avenue are 79.4% and 76.3% at 3 m. Covered N Lipps Avenue has essentially no class-11 returns at the tested centerline position, illustrating that *absence* of this code is not evidence that a street is absent. The [complete buffer-width/control table](veterans_street_point_classes.csv) records 3, 5 and 8 m results.

This is a successful **gap corroboration** test: a named municipal street and 2022 road-surface points align where the current 2D county mask is missing. It does not yet supply the legal ROW edge or the precise landward block boundary. A repair must pair this physical strip with orthophoto, parcels and recorded street/plat evidence, then test the split and M3/M4 area/shape on an independently drawn reference. Cook's [LiDAR acquisition specification](https://opendocs.cookcountyil.gov/procurement/contracts/2103-08021.pdf) says existing edge-of-pavement features supported road-surface classification; the specific delivered point trace should therefore be treated as corroboration rather than independent ground truth for every missing edge.

A [subsequent parcel-gap and topology test](../chicago_m3_veterans_repair_2026_09_27/README.md) produces a reproducible local split and identifies a near-zero-area overlay seam that caused the earlier apparent width instability. The cadastral anchor used in that test does not independently validate M3 area or M4 shape.

## Grade-separated structure check

The first tile includes a class-17 bridge-deck cluster west of the motorway reference core. In a selected local window, 28,882 class-17 returns have median elevation **624.951 ft**, versus **604.016 ft** for 2,975 ground-class returns, a difference of about **6.38 m**. See [bridge_class_profile.csv](bridge_class_profile.csv). This confirms that the point cloud can distinguish at least one elevated surface from local ground. It is a targeted class/profile check; no candidate boundary or network grade assignment was changed from it.

## Metadata caution and next method version

The delivered `cook_2022_metadata.xml` abstract names high vegetation and buildings separately, but its detailed code table omits class 5 and incorrectly labels class 6 “High Veg.” The [ASPRS LAS 1.4 standard](https://www.asprs.org/wp-content/uploads/2021/04/LAS_latest.pdf) defines class 5 as high vegetation and class 6 as building; the spatial returns here follow that standard pattern. The metadata inconsistency must be recorded and the class labels checked against another tile/orthophoto before any citywide classifier is frozen. Other classes and source dependencies also need an audit.

The next candidate version should retain ROW + Road Edge + 3 m alley-opening as the **2D generator**, add municipal named-street gap alerts, and attach LiDAR fields for class-6 building support, class-11 road-surface support and class-17 bridge elevation. Strong 3D evidence can **promote review or trigger a boundary repair**, while conflicts remain unresolved. It must not auto-delete empty parks or set legal block perimeters from a surface raster. Freeze the proposed triage/repair rules before independent complete-zone tests, measuring true-block false removal, corrected merges, precision/recall and M3/M4 geometry error against the unchanged 2D baseline. These nine faces, four street-line controls and one bridge cluster are selected diagnostics, not citywide accuracy estimates.

## Reproduce

```bash
.venv/bin/python analysis/scripts/pilot_chicago_m3_classified_lidar_2026_09_26.py
.venv/bin/python analysis/scripts/pilot_chicago_m3_veterans_lidar_2026_09_26.py
MPLCONFIGDIR=/tmp/mpl-m3-veterans-render .venv/bin/python analysis/scripts/render_chicago_m3_veterans_lidar_2026_09_26.py
```

The scripts reuse downloaded LAS files when present. Initial acquisition requires access to the public archive and transfers only the two recorded ZIP members. The outputs in this directory are small and versioned; the multi-gigabyte raw tiles are ignored by Git.

# Chicago results

One folder per dated release; each has its own README, tables and validation receipts. **Status** means: *release* = constructed for all 77 Community Areas (not a scientific acceptance); *source* = data acquisition or audit checkpoint; *diagnostic* = bounded pilot, not accepted; *superseded* = kept for provenance only. **None is an accepted model matrix.** Current scope and gates: [docs/STATUS.md](../../../docs/STATUS.md). SP releases are separate and unchanged.

## Local attribute releases

| Release | Status | Summary |
|---|---|---|
| [chi_local_2026_09_16_v1](chi_local_2026_09_16_v1/README.md) | release | Original local-source attribute baseline for all 77 Community Areas |
| [chi_functional_2026_09_16_v2](chi_functional_2026_09_16_v2/README.md) | release | Population/jobs densities, six bus-service scenarios and hydrography diagnostics; 163 independent checks passed |
| [chi_employment_sensitivity_2026_09_22_v2](chi_employment_sensitivity_2026_09_22_v2/README.md) | diagnostic | U2 workplace-allocation sensitivity over 14,990 positive-job Census blocks; 138 checks passed |
| chi_employment_sensitivity_2026_09_17_v1 | superseded | Replaced by v2 (no README; scripts in `scripts/_archive/chicago_employment_v1.zip`) |
| [harmonized_candidates_2026_09_22](harmonized_candidates_2026_09_22/README.md) | diagnostic | Chicago companion of the H1–H3 paired SP–Chicago candidates |
| [overture_2026_08_19_review_v1](overture_2026_08_19_review_v1/README.md) | diagnostic | Matched-Overture road measures and footprint pilots |
| [harmonization_checkpoint_2026_09_17](harmonization_checkpoint_2026_09_17/README.md) | source | Independent audit of paired road candidates and footprint pilots; 50 checks passed |

## Sources and acquisition

| Release | Status | Summary |
|---|---|---|
| [data_discovery_2026_09_18](data_discovery_2026_09_18/README.md) | source | Missing-data discovery; details in [data sources](../../../docs/chicago/DATA_SOURCES.md) |
| [chicago_cadastral_2026_09_18](chicago_cadastral_2026_09_18/README.md) | source | Nine Chicago-filtered cadastral datasets; 4,473 audit checks passed |
| [chicago_workbooks_2026_09_19](chicago_workbooks_2026_09_19/README.md) | source | Text extractions of the eight 2024 commercial valuation workbooks (binaries not acquired) |
| [dupage_characteristics_2026_09_21](dupage_characteristics_2026_09_21/README.md) | source | Addison Township target for the 81 Chicago-intersecting DuPage parcels |
| [public_data_alternative_2026_09_21](public_data_alternative_2026_09_21/README.md) | source | Public-data (GHSL) alternative proposal for building height/volume |

## M-family pilots (25 September 2026)

| Release | Status | Summary |
|---|---|---|
| [chicago_m_sample_2026_09_25](chicago_m_sample_2026_09_25/README.md) | diagnostic | Four stratified Community Areas for M1–M4/M6, plus Cook/DuPage entity audit for M7 |
| [chicago_m_physical_cases_2026_09_25](chicago_m_physical_cases_2026_09_25/README.md) | diagnostic | Ten imagery cases and seven Cook source-key cases for M2–M4/M7 |
| [chicago_m_holdout_2026_09_25](chicago_m_holdout_2026_09_25/README.md) | diagnostic | 13 held-out image cases and Cook parent-source check |
| [chicago_m3_external_sources_2026_09_25](chicago_m3_external_sources_2026_09_25/README.md) | diagnostic | OSM and CMAP roadway/rail polygons as block-validation aids |

## M3/M4 physical-block work (26–27 September 2026, active)

Method: [M3/M4 block protocol](../../../docs/chicago/BLOCKS_M3_M4.md). M3/M4 remain unaccepted.

| Release | Status | Summary |
|---|---|---|
| [chicago_m3_row_land_2026_09_26](chicago_m3_row_land_2026_09_26/README.md) | diagnostic | Polygon-first Cook ROW/Road Edge pilot; fixes obvious centerline median errors |
| [chicago_m3_fresh_tiles_2026_09_26](chicago_m3_fresh_tiles_2026_09_26/README.md) | diagnostic | Alley-open ROW matches 11/11 fresh sketches; named-street gap (West Veterans Place) found |
| [chicago_m3_candidate_v1_2026_09_26](chicago_m3_candidate_v1_2026_09_26/README.md) | diagnostic | Candidate inventory: 9 freeway islands among 26 tile-contained candidates |
| [chicago_m3_motorway_holdout_2026_09_26](chicago_m3_motorway_holdout_2026_09_26/README.md) | diagnostic | Motorway-context flag survives a small CHI:49 stress sample |
| [chicago_block_protocol_pilot_v1_2026_09_26](chicago_block_protocol_pilot_v1_2026_09_26/README.md) | diagnostic | First staged assessment under the block protocol |
| [chicago_block_method_comparison_v1_2026_09_26](chicago_block_method_comparison_v1_2026_09_26/README.md) | diagnostic | momepy/Shapely baselines versus the ROW candidate on frozen sketches |
| [chicago_m3_complete_zone_pilot_v1_2026_09_26](chicago_m3_complete_zone_pilot_v1_2026_09_26/README.md) | diagnostic | 3 m alley reopening selected; motorway deletion rule rejected |
| [chicago_m3_lidar_motorway_pilot_2026_09_26](chicago_m3_lidar_motorway_pilot_2026_09_26/README.md) | diagnostic | 2022 LiDAR rasters as supporting evidence for motorway candidates |
| [chicago_m3_lidar_point_pilot_2026_09_26](chicago_m3_lidar_point_pilot_2026_09_26/README.md) | diagnostic | Classified LAS points separate built wedges from tree-covered slivers |
| [chicago_m3_veterans_repair_2026_09_27](chicago_m3_veterans_repair_2026_09_27/README.md) | diagnostic | Centerline-guided nonparcel corridor splits the West Veterans Place face |
| [chicago_m3_named_gap_repair_2026_09_27](chicago_m3_named_gap_repair_2026_09_27/README.md) | diagnostic | That repair does not generalize to the other 11 named-street gap alerts |
| [chicago_m3_reference_zones_v2_2026_09_27](chicago_m3_reference_zones_v2_2026_09_27/README.md) | diagnostic | ROW + Road Edge + 3 m alley beats centerline enclosures in three new zones |
| [chicago_m3_provisional_faces_2026_09_27](chicago_m3_provisional_faces_2026_09_27/README.md) | diagnostic | Citywide provisional face inventory and review queue; no face accepted |

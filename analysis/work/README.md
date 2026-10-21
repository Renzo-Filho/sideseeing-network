# Working data — local intermediates, not published results

Git-ignored except these READMEs. For analysis-ready outputs use [results/](../results/).

| Folder | Meaning |
|---|---|
| [prepared](prepared/README.md) | Validated, standardized SP source tables produced before attribute construction (~3.5 GB). Also reachable as `analysis/processed` |
| [evidence](evidence/README.md) | SP source audits and the experiments behind the accepted M2/M6/U2 choices |
| [runs](runs/README.md) | Execution checkpoints, intermediate calculations, manifests and logs |
| reviews/ | SP model validation working files (15 September 2026) |
| `organization_manifest.json`, `organization_validation.json` | Old/new mapping and SHA-256 checks from the 11 September 2026 reorganization |

## Pilot working folders

Each folder below holds the raw inputs, query receipts and intermediate geometry behind the published release of the same name. Scripts write to these paths directly, so they stay at the top level.

| Folder | Published release |
|---|---|
| `chicago_m_holdout_2026_09_25/` | [results/Chicago/chicago_m_holdout_2026_09_25](../results/Chicago/chicago_m_holdout_2026_09_25/README.md) |
| `chicago_m_physical_cases_2026_09_25/` | [results/Chicago/chicago_m_physical_cases_2026_09_25](../results/Chicago/chicago_m_physical_cases_2026_09_25/README.md) |
| `chicago_m3_external_sources_2026_09_25/` | [results/Chicago/chicago_m3_external_sources_2026_09_25](../results/Chicago/chicago_m3_external_sources_2026_09_25/README.md) |
| `chicago_m3_row_land_2026_09_26/` | [results/Chicago/chicago_m3_row_land_2026_09_26](../results/Chicago/chicago_m3_row_land_2026_09_26/README.md) |
| `chicago_m3_fresh_tiles_2026_09_26/` | [results/Chicago/chicago_m3_fresh_tiles_2026_09_26](../results/Chicago/chicago_m3_fresh_tiles_2026_09_26/README.md) |
| `chicago_m3_motorway_holdout_2026_09_26/` | [results/Chicago/chicago_m3_motorway_holdout_2026_09_26](../results/Chicago/chicago_m3_motorway_holdout_2026_09_26/README.md) |
| `chicago_m3_complete_zone_pilot_v1_2026_09_26/` | [results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26](../results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26/README.md) |
| `chicago_m3_lidar_motorway_pilot_2026_09_26/` | [results/Chicago/chicago_m3_lidar_motorway_pilot_2026_09_26](../results/Chicago/chicago_m3_lidar_motorway_pilot_2026_09_26/README.md) |
| `chicago_m3_lidar_point_pilot_2026_09_26/` | [results/Chicago/chicago_m3_lidar_point_pilot_2026_09_26](../results/Chicago/chicago_m3_lidar_point_pilot_2026_09_26/README.md). The two LAS tiles (2.30 GB) were removed on 20 Oct 2026: `13259350.las` SHA-256 `06dc55c03fa4f0faa09431782c310d0509ff9a73efc9094ab921a88b47e7b14e`, `13759300.las` `8c03b9edbfb38d432f2f30de612d5f685573ac7856044a72d0e27fade6030302`. The pilot scripts fetch them again (the two ZIP members, by byte range) when absent; the URL, ranges and compressed hashes are in the release's `member_receipt.json` and `veterans_member_receipt.json` |
| `chicago_m3_reference_zones_v2_2026_09_27/` | [results/Chicago/chicago_m3_reference_zones_v2_2026_09_27](../results/Chicago/chicago_m3_reference_zones_v2_2026_09_27/README.md) |
| `u1_independent_cases_2026_09_23/` | [results/SP_CHI/u1_independent_cases_2026_09_23](../results/SP_CHI/u1_independent_cases_2026_09_23/README.md) |
| `u1_osm_tiles_2026_09_23/` | [results/SP_CHI/u1_osm_tiles_2026_09_23](../results/SP_CHI/u1_osm_tiles_2026_09_23/README.md) |

**Rule for new work:** write new pilot intermediates to `work/runs/<name>_<date>/`, and publish accepted outputs under `results/`. Do not add new top-level folders here.

These datasets preserve lineage so work can be reproduced or investigated. They are not redundant exports: deleting them loses the ability to rerun the pilots.

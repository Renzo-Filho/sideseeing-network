# GeoSampa buildings checked directly against Overture

Run 5 October 2026 in response to the question: when the old municipal map marks a building, what does Overture actually mark at that location? This is a **map agreement audit**, followed by a bounded 2025 imagery review. It does not treat GeoSampa as present-day ground truth or construct a B1 score.

## Inputs and calculation

- GeoSampa `geoportal:edificacao`: 2,817,745 historical outlines in the [Step 4 acquisition](../b1_step4_2026_10_05/README.md). The City's [Edificações 2D metadata](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/bcf69ef1-2f9e-42c2-b7ec-e808f89e8116) identifies **2004 aerial photographs** as the source and says updates are not planned. The downloaded records have a 2007 creation field and 2014 update fields; those database dates do not establish when the buildings were photographed.
- GeoSampa also publishes [2023/2024 orthophotos](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/5d7ebb7e-9687-491f-b8c6-2e9f79b229cb) and [2020 LiDAR surface data](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/resources/datasets/9214d12b-6439-49b5-9e29-e17271b57c78). These can help check whether old outlines still show buildings, but neither is a newer ready-made building-footprint vector layer. The GeoSampa WFS capabilities checked on 5 October 2026 listed `geoportal:edificacao` as the building polygon layer; its WMS counterpart is titled "Edificações 2D."
- Overture São Paulo building morphology GeoPackage used by the project, extracted from Overture 2026-08-19.
- 96 São Paulo district land polygons used by B1.
- Script: [`audit_sp_geosampa_overture_overlap.py`](../../../scripts/audit_sp_geosampa_overture_overlap.py). It assigns each GeoSampa building to a district by its centroid, then calculates how much of its old polygon area intersects any Overture building. Pairwise intersection areas are summed and capped at the GeoSampa polygon area. Where Overture polygons overlap each other, this **overstates** Overture coverage; the uncovered-area figure is therefore a conservative lower bound for *historical polygon area not represented at the same location*. It is not a lower bound for current missing buildings.
- For polygons with under 5% area overlap, the script checks whether any Overture outline is within 3 m. That separates strict spatial mismatches from near misses; it does not establish whether nearby polygons depict the same building.

## Full-city overlay

2,815,703 GeoSampa polygons have positive area and centroids within district land; 2,042 source records do not enter this assignment. Results: [`by_district.csv`](by_district.csv) and [`method.json`](method.json).

| What Overture says at the old GeoSampa polygons | Count / area | Share |
|---|---:|---:|
| At least 75% of old polygon area overlaps Overture | 2,376,323 buildings | 84.4% of assigned buildings |
| 25% to under 75% overlaps | 234,546 | 8.3% |
| 5% to under 25% overlaps | 67,147 | 2.4% |
| Under 5% overlaps | 137,687 | 4.9% |
| Under 5% overlaps, no Overture geometry within 3 m, old polygon at least 50 m² | 15,879 | 0.56% of assigned buildings |
| Old GeoSampa polygon area covered by Overture, conservative upper estimate | 275.26 of 314.95 km² | 87.4% |
| Old polygon area not covered at that exact location, conservative lower estimate | 39.69 km² | 12.6% |

District examples:

| District | Old GeoSampa buildings | Old area not overlapping Overture | Under 5% overlap | Under 5%, over 3 m away, ≥50 m² |
|---|---:|---:|---:|---:|
| Brás (10) | 8,051 | 4.7% | 68 | 10 |
| Itaim Bibi (35) | 24,637 | 53.0% | 5,907 | 1,318 |
| Parelheiros (55) | 38,232 | 1.5% | 355 | 149 |

The 12.6% is **not** an estimate of missing current buildings: old buildings may have disappeared, footprints can shift, and two maps may split one structure differently. The high agreement in Brás and Parelheiros and low agreement in Itaim Bibi confirm the difference is spatially uneven.

## Dated imagery review of nonmatching polygons

I chose twelve districts before viewing images. In each district, one polygon was randomly drawn from a stored random sample of old GeoSampa outlines with under 5% Overture overlap and no Overture outline within 3 m (`far`), and one from outlines with under 5% overlap but an Overture outline within 3 m (`near`). Each old polygon had at least 50 m² area. This is a **24-case, equal-district diagnostic sample**, not a citywide prevalence estimate. Candidate coordinates are in `imagery_candidates.csv` and `imagery_candidates_near.csv`; final sample, Esri metadata, and tile SHA-256 hashes are in [`imagery_review_v2/imagery_sample.csv`](imagery_review_v2/imagery_sample.csv).

The [Esri World Imagery metadata service](https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/0) gave capture dates between **8 April and 29 June 2025** at the sampled locations. Esri [documents that the per-location metadata includes acquisition date, resolution, and source](https://support.esri.com/en-us/knowledge-base/how-to-view-the-world-imagery-basemap-metadata-in-arcgi-000018129). Three-panel images show imagery, GeoSampa (target polygon yellow), and Overture (red). I visually classified the target in [`visual_review.csv`](imagery_review_v2/visual_review.csv):

| Sample group | Visible roof or roof segment | No visible roof at target | Uncertain |
|---|---:|---:|---:|
| Far: no Overture within 3 m | 5 | 5 | 2 |
| Near: Overture within 3 m | 10 | 1 | 1 |

Examples of **visible roofs without matching Overture coverage**: [large white roof in district 54](imagery_review_v2/near_17_district_54.png), [Itaim Bibi roof segment](imagery_review_v2/near_13_district_35.png), and [Brás roof extension](imagery_review_v2/far_04_district_10.png). Examples where the **old GeoSampa outline no longer marks a visible roof**: [Parelheiros highway](imagery_review_v2/far_18_district_55.png), [Jaguaré cleared lot](imagery_review_v2/far_14_district_41.png), and [Jaguaré pool](imagery_review_v2/near_15_district_41.png). Visual calls are conservative and ambiguous cases are marked uncertain; imagery itself can have position error and is from 2025, not 2026.

## Interpretation for B1

The audit answers the direct overlap question: **most historical GeoSampa footprints substantially overlap Overture, but roughly one in twenty has almost no area overlap, with strong geographic variation.** The imagery shows that both sources make errors relative to 2025 roofs. Some Overture gaps are real, including partial roofs and some entire structures. Some GeoSampa-only polygons now lie on roads, cleared land, pools, or vegetation. Therefore an unconditional `GeoSampa ∪ Overture` is not validated as a current footprint layer; the earlier union recommendation needs reconsideration. Overture alone also cannot be treated as complete in the reviewed locations. No B1 value or source decision was changed by this audit.

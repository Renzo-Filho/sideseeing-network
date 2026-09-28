# Chicago data acquisition checkpoint — 19 September 2026

Nine source datasets were downloaded on September 18 and filtered to the project’s Chicago boundary. On September 19, all nine manifests were confirmed to match the completed independent audit: **4,473 checks passed; zero failed**. No modeling or attribute construction was resumed. This closes the download-and-validation checkpoint within the user’s remaining quota.

## Downloads

Local data: `analysis/data/Chicago/chicago_cadastral_2026_09_18/` (approximately 483 MiB on disk; Git-ignored). Each dataset directory contains Parquet partitions, publisher metadata and a manifest with filters, source URLs, counts and hashes. These local files require separate transfer to another machine.

| Dataset directory | Retained records | Intended use |
|---|---:|---|
| `cook_parcels_2024` | 613,802 | M7 parcel geometry and keys |
| `dupage_parcels_current` | 81 | M7 DuPage portion; U1 fiscal classes |
| `cook_universe_2024` | 883,597 | Assessor join spine, class and coverage |
| `cook_residential_2024` | 439,730 | B2 story categories; B3 area; U1 use |
| `cook_condo_2024` | 287,189 | M7 parent investigation; B3 area |
| `cook_commercial_2024` | 32,930 | B3 area candidates; U1 use; related PINs |
| `cook_buildings_2022` | 779,962 | B1 footprint QA; height diagnostics |
| `benchmarking_2023` | 3,434 | Large-property GFA checks |
| `benchmarking_covered_current` | 3,693 | Benchmarking coverage register |

Counts are source features/records, not mutually exclusive buildings. Full descriptions, publisher links and terms remain in the [discovery report](../../../../docs/chicago/CHICAGO_DATA_DISCOVERY_2026_09_18.md). [download_register.csv](download_register.csv) records exact dataset endpoints and local locations.

## Chicago-only rule and validation

Spatial records were selected with an enclosing query mask, then clipped to the exact union of the supplied 77 Community Areas in EPSG:26916. Only positive-area intersections were retained; boundary-only touches were excluded. Original source area and Chicago intersection area are separate columns, and crossing features are flagged. This operational boundary is the project’s supplied Community Area geography, not a new legal municipal-boundary certification.

Cook assessor rows were retained through normalized PIN10 matches to retained Cook parcels. Commercial PINs required hyphen removal and matching across associated parcels; `chicago_matched_pins` records the qualifying links. A related commercial entity can span the boundary: its reported area is not a Chicago-only area allocation. PIN10 grouping does not establish physical building identity. Benchmarking records were filtered by their reported coordinates inside the exact boundary; this does not clip campus/property areas.

Temporary acquisition caches under `analysis/work/evidence/chicago_cadastral_2026_09_18/` contain broader source-year exports and rejected candidates. They are not final Chicago datasets. The delivered spatial partitions contain only Chicago geometry, and delivered assessor records have Chicago parcel links.

[validation.json](validation.json) checks partition hashes, row counts, unique source IDs, geometry validity, positive area, Chicago containment and complete assessor selection independently from the downloaded exports. All nine manifest hashes were rechecked September 19. Tests also exercised crossing/touching polygons, formatted commercial PINs and leading zeros. Source revision timestamps were not rechecked after download: the attempt was blocked by automatic approval review’s usage-limit failure. Therefore immutable publisher snapshot consistency remains unproven despite reconciled export counts and unique IDs.

A geometry-worker crash was resolved by isolating each worker’s geometry state; saved batches were reused. Slow sorted assessor pagination was replaced by bulk CSV exports. The initial commercial hyphen mismatch was corrected and the complete selection independently revalidated. Retired attempts remain only in the ignored evidence cache.

## Verified remaining gaps

[coverage_audit.json](coverage_audit.json) records Chicago-filtered field coverage:

- Residential area is positive on **439,693 / 439,730** improvement records. Stories include **32,525 “3 Story +”**, **8,950 split-level** and **11 missing** records. These cannot all be interpreted as exact floor counts.
- Condo building area is present on **73,251 / 287,189** unit records; unit area on **41,860 / 287,189**. Building values can repeat across units, so these are populated-record counts, not distinct-building coverage.
- Commercial `stories` and `gross_building_area` have **zero populated records**. `bldgsf` is positive on **29,976 / 32,930** rows; net rentable area on **5,983**. Building and rentable areas are not interchangeable.
- DuPage parcel records lack building floor-area and story fields. Exempt/airport and other unrepresented stock still need building/improvement records.
- Benchmarking only covers a large-property subset and can describe campuses. Footprint area and measured height do not solve missing GFA or exact stories.

DuPage source terms restrict redistribution of real-estate data without county permission; retain source records locally. Official class definitions and SOP text are saved in the packet’s `documentation/` directory. Direct retrieval of the original class-definition PDF returned HTTP 403; the prior Firecrawl text extraction is available, but the PDF binary was not acquired.

## Next bounded data checkpoint

1. **Commercial workbook acquisition:** use Firecrawl to inspect the official valuation reports page linked in the discovery report. Locate the Chicago 2024 township workbooks, download relevant files, and validate sheets, dates, PINs, actual populated stories/area fields and units. Do not assume the workbooks fill the empty API columns. Filter retained records to existing Chicago parcel keys.
2. **DuPage improvement source:** determine intersecting townships spatially from the retained parcel geometry; locate their building-characteristic exports, including exempt/airport stock. Document access, schema, vintage and terms. Do not contact agencies without user authorization.
3. **Condo area and parent gaps:** investigate additional official stock records and reconcile parent/building relationships before treating repeated area values as coverage.
4. Recheck publisher revision timestamps when available. A later check describes later state; it cannot retroactively prove an atomic September 18 snapshot.

Do not rerun completed acquisitions or resume modeling. Existing entry points are `analysis/scripts/acquire_chicago_cadastral.py` (spatial/benchmarking), `acquire_chicago_assessor_bulk.py` (preferred assessor export), and `validate_chicago_cadastral_acquisition.py`. Inspect manifests and saved validation first.

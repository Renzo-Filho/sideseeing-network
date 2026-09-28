# Public-data alternative — proposed September 21, 2026

**September 22 update:** GHSL acquisition is complete for both cities: two 2018 height variants and 2020 built volume. See [acquisition report](../../SP_CHI/ghsl_public_2026_09_21/README.md). The proposal below remains a methodological proposal; no model was changed.


The user supplied seven original commercial workbooks but could not obtain Addison/Cook supplemental characteristics because of access bureaucracy. Restricted assessor records should no longer be a prerequisite for progress. Validation and modeling remain paused; the following is a proposed methodological change, not an implemented or accepted model.

## Received

Seven XLSX files are present in `analysis/data/Chicago/manual_acquisition_2026_09_21/incoming/`: T70, T71, T72, T73, T74, T75 and T77. T76 is absent. See `incoming_inventory.json`. No repeat validation or workbook transformation was performed. Existing extracted commercial records remain useful supplementary evidence; obtaining T76 is lower priority than resolving model scope.

## Recommended route

1. Build a separately versioned candidate **common model that does not depend on M7 cadastral entity counts, B2 fiscal floors or B3 fiscal constructed area**. Exclude an unavailable family from both cities' common comparison, not just Chicago. Preserve the original SP-only model unchanged. This leaves up to ten candidate families, not ten already accepted families: U1 still needs common use definitions/weighting, and topology, denominators and other shared-method choices remain open.
2. Add an optional, separately named **public height/volume extension** computed with the same global products, epoch, resolution and definitions for São Paulo and Chicago. This preserves information about vertical form without requiring privileged cadastral records.
3. Keep municipal/assessor evidence as city-specific diagnostics. Do not mix residential living area, commercial rentable area and repeated condo parent area into a supposedly complete GFA field. Missing DuPage improvements would no longer block the common model.

This follows the existing harmonization plan's permitted exclusions/alternative definitions. It does not authorize skipping future scientific checks when model construction resumes.

## Public acquisition targets

Official source: European Commission Joint Research Centre's [GHSL catalogue](https://human-settlement.emergency.copernicus.eu/datasets.php), inspected via Firecrawl. Catalogue states open/free downloads with attribution.

| Candidate | Publisher route | Possible role | Limitations |
|---|---|---|---|
| GHS-BUILT-H R2023A | [Height download](https://human-settlement.emergency.copernicus.eu/download.php?ds=builtH) / [datasheet](https://human-settlement.emergency.copernicus.eu/ghs_buH2023.php) | District-level height summaries under a new attribute definition | 2018 epoch, 100 m / 3 arcsec cells, gross/net height variants; estimated grid values, not exact building stories or a building-weighted floor distribution |
| GHS-BUILT-V R2023A | [Volume download](https://human-settlement.emergency.copernicus.eu/download.php?ds=builtV) / [datasheet](https://human-settlement.emergency.copernicus.eu/ghs_buV2023.php) | Built-volume intensity, m³ per land m² | Model-derived volume; not legal constructed area or GFA. Multiple epochs include projections; choose an appropriate historical reference and document the 2018 height evidence |

The catalogue was acquired; height/volume raster tiles have **not** been downloaded in this turn. The height datasheet extraction was sparse, so the catalogue provides the confirmed product description. Before acquisition, select an appropriate common epoch/resolution and correct product variant; detailed metadata must establish the height denominator and NoData semantics. Avoid treating the height and derived volume measures as independent evidence or double-weighting correlated building measures.

Public raster coverage is expected from the advertised global products; local tile availability and usable coverage are not yet established. Their coarser scale and older reference date are real tradeoffs. Raster products cannot reproduce the existing SP cadastral B2/B3 values exactly. No arbitrary metres-per-floor conversion is proposed. Recompute the new measures for both cities; do not compare Chicago satellite height to SP tax floors.

## Next acquisition checkpoint

Retrieve official GHSL height/volume metadata and tiles covering both study areas, then store separate city-clipped candidates with their declared vintage, units and provenance. Keep the existing SP model and Chicago releases untouched. Stop chasing restricted Addison/Cook records as a prerequisite. No paid subscription, agency request or replacement model has been initiated.

# Public GHSL height/volume acquisition — completed 22 September 2026

This is a data-acquisition checkpoint for the user-approved public-data alternative. It does not modify the existing São Paulo model, construct replacement attributes, or restart the paused scientific validation work.

## Sources and selected products

Publisher: European Commission Joint Research Centre (JRC), [GHSL catalogue](https://human-settlement.emergency.copernicus.eu/datasets.php). Discovery used Firecrawl; binary files came directly from the publisher's [public directory](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/).

| Product | Selected reference | Units | Potential future role |
|---|---|---|---|
| GHS-BUILT-H ANBH | R2023A, V1-0, 2018, 100 m Mollweide | metres | Net-height candidate, under a new definition rather than fiscal floors |
| GHS-BUILT-H AGBH | R2023A, V1-0, 2018, 100 m Mollweide | metres | Gross-height companion retained to support later denominator/variant selection |
| GHS-BUILT-V total | R2023A, V1-0, 2020, 100 m Mollweide | cubic metres per source cell | Built-volume intensity candidate, not constructed floor area |

Height is available for 2018. The inspected volume directory has five-year editions and no 2018 edition; 2020 is the selected nearest historical edition. Both cities use the same edition of each product, but height and volume are not contemporaneous. No future projection edition or non-residential-only volume variant was selected.

The publisher's `copyright.txt` licenses reuse under CC BY 4.0 with attribution and an indication of changes. Copies are saved beside the source tile archives. The GHSL Data Package 2023 technical PDF is saved under `analysis/work/evidence/ghsl_2026_09_21/`; detailed methodological review is deferred.

## Acquisition scope and storage

The official Mollweide tile index selects **R4_C11 and R5_C11 for Chicago**, and **R12_C14 for São Paulo**. Whole source tiles necessarily contain surrounding areas and are stored separately under `analysis/data/shared/ghsl_public_2026_09_21/` with exact download URLs, retrieval times, source HTTP metadata, byte sizes and SHA-256 receipts.

City extracts are stored under:

- `analysis/data/Chicago/ghsl_public_2026_09_21/`
- `analysis/data/SP/ghsl_public_2026_09_21/`

Each city receives one GeoTIFF per selected product plus metadata JSON. `manifest.json`, `download_register.csv` and `city_extract_register.csv` in this result directory provide the final acquisition inventory. Raw rasters are Git-ignored and must be transferred separately to another machine.

## What “city extract” means

Boundaries are the existing project Chicago Community Areas and corrected SP district geometries. Cells retain the native **ESRI:54009 Mollweide 100 m grid**; no interpolation or raster reprojection is performed. An all-touched city mask retains cells intersecting the boundary and sets outside cells to the publisher's NoData value.

A boundary cell is still a full source cell: its value has **not** been fractionally allocated to the city. Therefore these are acquisition extracts, not final city volume totals. Later aggregation must handle partial cells explicitly, along with water/land denominators and product-specific height weighting. The GeoTIFF/JSON retain the source dtype, NoData, scale and offset; zero is not silently converted into missing data.

## Interpretation and next checkpoint

These public products can support new vertical-form attributes in both cities. They cannot be relabeled as exact story counts, legal GFA or cadastral building records. Do not divide height by an arbitrary metres-per-floor constant. Gross and net height use different definitions; choose the intended denominator from the technical documentation before aggregation. Height and volume are related products and should not automatically receive independent full family weights.

Next, when analysis is requested, specify new attribute names, cell weighting, boundary allocation, source-year qualifications and common-city weighting. M7 physical parcel identity is not solved by these rasters; its exclusion from the proposed strict common comparison remains separate. Other common-model method decisions also remain open. No replacement model or scientific validation result is claimed by this acquisition.

Reproducible acquisition entry point: `analysis/scripts/acquire_ghsl_city_rasters.py`. Existing Chicago releases and the original SP model are preserved.

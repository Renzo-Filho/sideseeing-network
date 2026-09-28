# Chicago DuPage building-source checkpoint — 21 September 2026

**Addison Township is the verified target for the 81 previously acquired Chicago-intersecting DuPage parcels.** This checkpoint adds Chicago-only township geometry and a scoped lookup list. It does not add verified building floors or constructed-area records.

## Data saved and validated

Publisher: DuPage County GIS, [Townships (PLSS) item](https://www.arcgis.com/home/item.html?id=480184791b4b485abff29d6a69378df0). The source service has ten polygon features. After intersection with the project's Community Area union in EPSG:26916, only ADDISON has positive area inside Chicago: **5,957,496.144 m²**. The saved intersection geometry is valid.

All **81 Chicago-filtered DuPage parcels** have positive-area overlap with Addison; all PINs start with `03`, consistent with the [county assessor directory](https://www.dupagecounty.gov/government/departments/supervisor_of_assessments/township_assessor_directory.php). Their combined area outside the township polygon is **0.6074 m²**, at most **0.0811 m²** for any parcel. This small boundary disagreement is retained as a qualification; parcel geometry was not altered to hide it. Ten source features do not imply ten administrative townships: this is the published PLSS feature layer.

Files under `analysis/data/Chicago/dupage_characteristics_2026_09_21/`:

- `chicago_township_intersections.parquet`: Chicago-clipped township geometry, useful to scope M7 joins and B2/B3 acquisition.
- `chicago_parcel_lookup_list.csv`: 81 PINs, property classes and municipality labels copied from the already validated parcel subset. This is a lookup list, not newly acquired characteristics.

Detailed evidence: `township_validation.json`, `source_register.json`, and SHA-256 `manifest.json`. The raw county-wide reference geometry stays in the ignored `.firecrawl/` evidence cache; the saved data geometry is Chicago-only. Apply the existing DuPage source reuse restrictions to parcel-derived records; no redistribution permission was requested.

## Verified lookup route

The [official Addison assessor page](https://www.addisontownship.com/assessors-office/) links to [property search](https://www.addisontownship.com/property-search/), then the [public database](https://search.addisontownship.com/webdb/sd/addison/assessordb/search.aspx). Firecrawl successfully read all three pages. The database offers parcel-number or address search, and supports PINs with or without dashes. The publisher says records can lag office data and assessed values may be uncertified.

No bulk building-characteristic export was identified on these inspected pages. This is not proof that no export exists. A Firecrawl browser pilot for PIN `0312300007` did not produce a saved property result; the session was explicitly stopped. The provider reported 87 seconds and 11 credits for that session. No assertion is made that the parcel is missing from the database, and no stories/area fields have yet been validated.

The existing parcel subset contains 58 exempt (`E`), seven leasehold (`T`), one industrial (`I`) and 15 missing-class records. Tax-exempt/airport coverage is therefore central; a residential-only download would not resolve this subset.

## Next small checkpoint

1. Test the database with **industrial PIN `0301100003`**, then **leasehold `0301200006`**, using explicit browser controls and a bounded timeout. Save the detail URL, visible field labels/values, vintage and data definitions. Do not repeat an unbounded natural-language browser attempt.
2. If real building records are accessible, collect the remaining scoped 81 PINs with a per-PIN outcome register, distinguishing no match, no improvement, missing characteristic and access failure. Preserve raw values; do not infer stories from height or area from assessed value.
3. If the site lacks these records, document the required official export: PIN, improvement/building ID, parent relations, exact floors, constructed area with units/definition, use and effective date, including exempt/airport stock. No agency contact or FOIA submission is authorized by the current data-gathering instruction.
4. Continue condo/physical-parent source work separately. Modeling remains paused.

## Previous commercial checkpoint closed

The [commercial workbook report](../chicago_workbooks_2026_09_19/README.md) is now documented: eight Firecrawl workbook extracts, 32,231 Chicago-linked detail records, all 31,702 prior API key PINs plus 103 additional keys. No stories or explicitly gross-floor-area field was found in the extracted property tables. Original XLSX binaries returned HTTP 403; extraction completeness and formulas remain unverified. Do not claim eight original workbooks were downloaded.

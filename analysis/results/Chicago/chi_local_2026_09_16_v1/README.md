# Chicago local-source attributes v1

**Scope:** descriptive source audit and attribute baseline for all 77 Community Areas. No SP–Chicago ranking or model fit.

- [Wide CSV](tables/attributes_wide.csv): easiest entry point for exploration; each row is a Community Area.
- [GeoPackage](spatial/chicago_community_attributes.gpkg): the same attributes plus geographic support, EPSG:26916.
- [Dictionary](tables/attribute_dictionary.csv): exact fields, methods and status.
- [Long CSV](tables/attributes_long.csv): values with numerator, denominator and coverage counts.
- [Construction checks](validation/checks.json) and [independent validation](validation/independent_checks.json).

CSV is for inspection; Parquet preserves types for code. GeoPackage is for maps. Validation JSON is audit evidence, not another feature table. Prepared per-building/road/block data live only in `analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/`.

M1/M6/B1/B2/U1 are local-source alternatives, U3 is provisional pending ACS provenance, and M3/M4 are experimental enclosures. M2/M7/B3/U2/U4 are null with reasons. All strict cross-city acceptance flags are false. Read [full definitions](../../../../docs/chicago/CHICAGO_ATTRIBUTE_DOCUMENTATION.md) and [requirements](../../../../docs/chicago/CHICAGO_DATA_REQUIREMENTS.md) before selecting features.

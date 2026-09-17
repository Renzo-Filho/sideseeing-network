# Chicago functional extension — September 16, 2026

Population and workplace-job densities for all 77 Community Areas, six bus-service scenarios per area, and hydrographic denominator diagnostics. **163 independent checks pass; no cross-city model acceptance or rankings.**

Start with [methods, sources and remaining work](../../../../docs/chicago/CHICAGO_FUNCTIONAL_EXTENSION.md).

- `tables/attributes_wide.csv` / `.parquet`: 77 units, eight functional features.
- `tables/attributes_long.csv` / `.parquet`: 616 values with numerator, denominator, units, periods and quality flags.
- `tables/attribute_dictionary.csv`: definitions for all eight features.
- `tables/functional_attributes.*`: source totals, gross/water/land areas and densities.
- `tables/bus_service_access.*`: all 462 scenarios, reached population and support counts.
- `tables/border_block_accounting.*`: explicit inside/outside weights and residual mass.
- `tables/population_period_diagnostic.csv`: Census versus supplied ACS, different-period diagnostic only.
- `spatial/functional_attributes.gpkg`: Community Area geometry and measurements, EPSG:26916.
- `reports/functional_qa.png`: six descriptive maps, visually inspected.
- `validation/`: source/code hashes, publisher register, arithmetic checks, independent audit, stage ledger and final checksums.

Reproduce with `analysis/scripts/prepare_chicago_functional.py`, then `analysis/scripts/validate_chicago_functional.py`. Prepared block pieces, 250 m population points, hydro land, schedules and resumable checkpoints are under the ignored `analysis/work/prepared/Chicago/chi_functional_2026_09_16_v2/` directory. The original v1 baseline remains unchanged.

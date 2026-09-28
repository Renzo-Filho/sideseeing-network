# São Paulo documentation

**September 22 harmonized companion:** [H1–H3 execution](../chicago/SP_CHICAGO_HARMONIZATION_EXECUTION.md) adds paired physical candidates and a corrected bus-only U4. Legacy SP U4 included nonbus service; SP v2 is preserved with that qualification. New candidate tables are under `analysis/results/SP/harmonized_candidates_2026_09_22/`; no new fit yet.


Start with [SP_MODEL_FIXES.md](SP_MODEL_FIXES.md) for the current corrected model status and [SP_DATA_RESOLUTION_HANDOFF.md](SP_DATA_RESOLUTION_HANDOFF.md) for preparation lineage, artifact locations and source limitations.

- [SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md](../archive/plans/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md) — v3 definitions and ordered N01–N11 next tasks; integration and attribute stages clearly distinguished.
- [SP_METHOD_DECISIONS.md](SP_METHOD_DECISIONS.md) — issue/cause/action/validation report, approved M6/M2 rules, and results of ten U2 allocation experiments.
- [BUILDING_PIPELINE.md](BUILDING_PIPELINE.md) — retained technical reference for the completed Overture GeoPackage.
- [Research protocol](../../plan.md) — SP-first research scope, later Chicago comparison and separate accessibility study.

The active model has 13 families; M5 and U5 are removed. B2 targets cadastral floor counts, U2 formal employment and U4 service-weighted bus access. M2 uses the approved 5 m structure-exclusion proxy; M6 uses the approved all-unclassified-as-Local overlay. N10 attribute construction is complete for all 96 districts. The corrected SP similarity model v2 is also complete, independently revalidated and supported by 577 robustness scenarios.

Four superseded status reports were removed after consolidation into the current handoff. Historical evidence and prepared data remain unchanged. Use `analysis/scripts/prepare_sp_v3.py`; do not run the old hard-coded v2 pipeline on the expanded raw folder.

Current [attribute construction report](../../analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md) and [primary table](../../analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/attributes_primary.csv). The long table contains the required source/quality metadata.

[Urban model implementation plan](../archive/plans/URBAN_MODEL_IMPLEMENTATION_PLAN.md) — archived N11 design specification retained for implementation history.

## Feature Data Sources

### 1. Base Support & Geometries
- **Files**: `Cadastro e Vias/distrito_municipal_v2.gpkg`, `Meio Ambiente/massa_d_agua.gpkg`
- **Source**: GeoSampa
- **Variables Solved**: Common Support (Denominators)
- **Rationale**: Essential to calculate the gross district area and net land area, ensuring density metrics (M1, M2, M7, U2, U3) are accurate and not diluted by lakes/reservoirs.

### 2. Street Network Morphology (M1, M6)
- **Files**: `Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg`, `Cadastro e Vias/classvias.gpkg`
- **Source**: GeoSampa
- **Variables Solved**: `street_density_km_km2`, `street_class_model_share_*`
- **Rationale**: Provides the physical road lines and functional classifications (arterial, local, collector) to measure total street length per square kilometer and capture the district's traffic morphology.

### 3. Street Connectivity (M2)
- **Files**: `Cadastro e Vias/obra_arte.gpkg`
- **Source**: GeoSampa
- **Variables Solved**: `intersection_density_proxy_5m_km2`
- **Rationale**: Used to explicitly exclude grade-separated road crossings (bridges, viaducts, tunnels) from the street intersection count, providing a true measure of at-grade connectivity.

### 4. Urban Grain & Block Shapes (M3, M4)
- **Files**: `Cadastro e Vias/quadra_viaria_editada.gpkg`
- **Source**: GeoSampa
- **Variables Solved**: `block_log_area_*`, `block_compactness_*`, `block_elongation_*`
- **Rationale**: Physical street blocks are used to compute distributions of block sizes and shapes, characterizing the urban grain.

### 5. Cadastral Density, Built Area & Land Use (M7, B2, B3, U1)
- **Files**: `Cadastro e Vias/Lotes/`, `Cadastro e Vias/IPTU_2026.csv`
- **Source**: GeoSampa
- **Variables Solved**: `cadastral_parcel_density_km2`, `cadastral_floor_count_*`, `cadastral_floor_area_density`, `land_use_entropy_count`
- **Rationale**: Linking physical parcels to fiscal tax accounts reveals the number of lots, building floor counts, built floor area density, and land use diversity. It also provides the spatial foundation for job allocation (U2).

### 6. Building Coverage (B1)
- **Files**: `Edificacoes/sao_paulo_building_morphology.gpkg`
- **Source**: Overture Maps (2026-08-19)
- **Variables Solved**: `building_coverage_land`
- **Rationale**: Provides reliable machine-mapped building footprint shapes to calculate the percentage of total land covered by physical structures.

### 7. Economic Density (U2)
- **Files**: `Socioeconomico/rais_empregos_sp_2022.csv`
- **Source**: RAIS (Ministry of Labor)
- **Variables Solved**: `formal_job_density_area_first_km2`
- **Rationale**: Supplies the number of formal jobs by postal code, probabilistically allocated to buildings and tracts to measure economic density.

### 8. Residential Density (U3)
- **Files**: `Socioeconomico/CNEFE_2022/`, `Socioeconomico/densidade_demografica.gpkg`
- **Source**: IBGE (Census 2022)
- **Variables Solved**: `population_density_km2`
- **Rationale**: Provides demographic counts per census tract, intersected with district boundaries to calculate residential population density and weight transit proximity (U4).

### 9. Public Transit Access (U4)
- **Files**: `Socioeconomico/f-6gy-sptrans-latest/`
- **Source**: SPTrans (GTFS)
- **Variables Solved**: `bus_service_access_weekday_am_400m`
- **Rationale**: Contains scheduled bus departures and stop locations, used to calculate the frequency of bus service within walking distance of populated areas.

### 10. Exploratory Files (Removed from Model)
- **Files**: Various files under `Planejamento e Zoneamento/`, `Meio Ambiente/`, and transit stations (e.g. `estacao_metro_v2.gpkg`)
- **Source**: GeoSampa, Metrô, Seade
- **Variables Solved**: N/A (M5, U5 removed)
- **Rationale**: Collected to investigate green space, zoning, and broader accessibility features, which were later removed from the final 13-family model to focus on the strongest indicators.

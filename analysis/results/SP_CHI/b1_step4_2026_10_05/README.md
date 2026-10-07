# B1 footprint coverage: validation (Step 4)

Run 5 October 2026. Scripts: `analysis/scripts/evaluate_b1_step4.py` (CHI, SP, summary), `analysis/scripts/evaluate_b1_bras.py` (district imagery windows), `analysis/scripts/acquire_geosampa_edificacao.py`. Rules S4-1 to S4-7 were fixed by the user before any test ran ([MODEL_PLAN Step 4](../../../../docs/chicago/MODEL_PLAN.md#step-4--b1-footprint-coverage)). **B1 was accepted with stated limits later on 5 October 2026.** The failed São Paulo reference check remains recorded below.

## New São Paulo sources

- **GeoSampa `geoportal:edificacao`** (Prefeitura de São Paulo WFS): 2,817,745 building outlines from photogrammetric restitution of aerial imagery (1:1,000 in urbanized areas, 1:5,000 elsewhere). The City's [Edificações 2D metadata](https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/bcf69ef1-2f9e-42c2-b7ec-e808f89e8116) says the source was **2004 photographs**, with no planned updates. The downloaded features record creation on 2007-03-11 and last edits from 2014-01-03 to 2014-03-13; these are database dates, not imagery dates. Saved in `analysis/data/SP/geosampa_edificacao_2026_10_05/` (141 pages, `manifest.json` with SHA-256; count equals the server's `numberMatched`).
- **IPTU 2026 `AREA OCUPADA`:** behaves like a footprint (on non-condominium lots at most the lot area; median 0.53 of it); counted once per physical lot (setor + quadra + lote, or setor + quadra + condomínio). 1,674,966 lots, 245.93 km²; 1,774 condominium lots record varying values (lot median used; maximum would add 0.30 km²); 0.44 km² could not be placed in a district.

## Results

| Check | Rule | Result |
|---|---|---|
| S4-1 land = C2; existing Overture values reproduced | — | pass (land within 0.0001 m²; Chicago Overture recomputed within 3 × 10⁻⁹) |
| **S4-2 Chicago: Overture vs Cook 2022 LiDAR footprints** | Spearman ≥ 0.95 and no area beyond 25% | **pass**: Spearman 0.983; Overture a median 8.5% lower; range −17.8% to +3.8% |
| Chicago: Overture vs municipal 2015 (descriptive) | — | Spearman 0.992, median +1.1% (likely shared lineage) |
| **S4-3 São Paulo: Overture vs GeoSampa** | same rule | **fails**: Spearman 0.937; 12 districts beyond 25%. Between the two sources 51 districts move 5 or more ranks (23 move 10 or more) |
| S4-3 São Paulo: Overture vs IPTU occupied area | same rule | fails: Spearman 0.858; Overture a median 22.6% higher. IPTU covers only cadastral lots, so unregistered settlements are missing; a consistency check, not a completeness reference |
| **S4-4 Brás** | must be explained | **explained:** Overture 0.566, GeoSampa 0.568, OpenStreetMap 0.557, Microsoft 0.205, GHSL 0.444. Six imagery windows: Microsoft misses whole blocks and draws others as single blobs; Overture (98.5% OpenStreetMap by area) traces individual buildings. Brás ranks 1st under both Overture and GeoSampa |
| S4-5 lineage (descriptive) | — | Chicago: OpenStreetMap 99.4% of Overture area (median district). São Paulo: OpenStreetMap 91.1%, Google 8.1%, Microsoft 1.3% (median), but **22 districts are more than 50% machine-learning-derived**, all in the North, South and West regions, none in the East or Centre |
| S4-6 Overture ÷ GHSL built fraction (descriptive) | — | Chicago median 0.736; São Paulo 0.948. Outside the city's 5th–95th percentile: Chicago Lake View, Near North Side, Loop, Near South Side, South Deering, Riverdale, Englewood, O'Hare; São Paulo Bom Retiro, **Brás (1.27)**, Campo Belo, Itaim Bibi, Jaguara, Marsilac, Morumbi, Pari, República, Vila Sônia |

## Why São Paulo fails: two mapping regimes in Overture

| Overture regime (share of outline area from Google/Microsoft machine learning) | Districts | Median Overture ÷ GeoSampa − 1 |
|---|---:|---:|
| OpenStreetMap-mapped (< 20%) | 65 | +3.9% |
| Mixed (20–50%) | 8 | +36.6% |
| Machine-learning-dominated (> 50%) | 22 | **−13.4%** |

- In machine-learning-dominated districts Overture is lower than a municipal map based on 2004 photography despite later construction; these districts rank on average 10 places lower under Overture than under GeoSampa. Imagery in Itaim Bibi (Overture −39%; OpenStreetMap coverage 7%) shows missed and partial outlines on dense tile-roof housing and missed towers.
- Where Overture is higher, growth since 2007 is the plausible cause: the share of IPTU occupied area built from 2008 correlates with the gap at Spearman 0.239 (Anhanguera 59%, Iguatemi 46%); Parelheiros windows show Overture equal to or above GeoSampa where buildings exist.
- Machine-learning share alone does not correlate with the gap across all districts (Spearman −0.017) because the mixed, fast-growing periphery offsets it.

## Files

`tables/b1_sources_CHI.csv`, `tables/b1_sources_SP.csv` (coverage per source and Overture lineage shares), `tables/b1_sp_explanations.csv` (post-2007 share, machine-learning share), `tables/b1_step4_by_unit.csv`, `checks.json`, `run_CHI.json`, `run_SP.json`, and window coordinates and tile hashes in `bras/windows.csv`, `district_35/windows.csv`, and `district_55/windows.csv`. The large imagery captures remain local and are excluded from Git.

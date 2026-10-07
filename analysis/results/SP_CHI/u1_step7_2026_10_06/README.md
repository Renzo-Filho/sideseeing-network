# U1 land-use mix (Step 7)

Run 6 October 2026 by `analysis/scripts/evaluate_u1_step7.py` (about 80 s with the São Paulo lot-geometry cache in `analysis/work/u1_step7_2026_10_06/`; 18 min to build it). Post-hoc diagnostics: `audit_u1_chicago_reference.py`, `audit_u1_sp_reference.py`. Decisions S7-1 to S7-6 fixed by the user before the run ([MODEL_PLAN Step 7](../../../../docs/chicago/MODEL_PLAN.md#step-7--u1-land-use-mix)). **The U1 entropy score was not accepted; three land shares were admitted at the final joint review with stated limits.**

## Definition

`u1_entropy4` = normalized Shannon entropy (÷ ln 4) of land area in four occupied uses (residential, commerce/services, industrial, institutional), on classified lot land within each unit's land; missing when that land is below 10% of the unit's land.
- **Chicago:** CMAP LUI 2023 primary `LANDUSE`: 11xx residential; 12xx commerce (incl. 1215/1216 mixed commercial with residential); 13xx institutional except 1360 cemetery (to open space); 14xx industrial; 15xx transport; 2 agriculture, 3 open space, 41xx/42xx vacant, 5 water, 6000 nonparcel, 9999 unclassified.
- **São Paulo:** IPTU 2026 use type per physical lot on GeoSampa fiscal lot polygons (1,677,182 lots; 9,883 lots spanning two partition files merged). Labels mapped with `sp_prep v3/N03/use_mapping.csv`; explicit residential + non-residential labels and condominium lots with both residential and commercial units → commerce (S7-3); "Posto de serviço" → commerce; generic labels ("Não residencial", multiple-use collective/special) → unclassified; a lot's class is the use with most built area (record count breaks ties, so vacant lots stay vacant). Sensitivity `pred_u1_entropy4`: "predominância residencial" labels → residential (Spearman with primary 0.947).

## Results

| | Chicago | São Paulo |
|---|---|---|
| Units with U1 (coverage ≥ 10%) | 76 of 77 (O'Hare missing: 4.9%) | 94 of 96 (Marsilac, Parelheiros missing) |
| Median U1 | 0.649 | 0.664 |
| Highest | Near West Side 0.972, Fuller Park 0.918, South Lawndale 0.911 | Parque do Carmo 0.974, Belém 0.925, Cambuci 0.901 |
| Lowest | Beverly 0.279, Edison Park 0.315, Forest Glen 0.327 | **República 0.316, Sé 0.384**, Alto de Pinheiros 0.410 |
| Median land in the four occupied uses | 54.9% | 59.2% |
| Median land shares, other | nonparcel 27.3%, transport 5.8%, open space 4.1%, vacant 2.4% | no lot polygon 25.2%, vacant 4.9%, lot without IPTU 3.4%, unclassified 2.2% |
| Spearman U1 with U2 / U3 / B1 | 0.363 / 0.043 / 0.081 | 0.349 / −0.405 / 0.013 |
| Spearman four- vs six-class entropy | 0.847 | 0.884 |

**Anchors:** Brás 0.711 vs Loop 0.662 (four classes); six classes 0.642 vs 0.734. The order reversal persists.

**S7-5 validation (rule Spearman ≥ 0.70): fails in both cities.**

| | Pre-registered reference | Result | Post-hoc diagnostic (not a test) |
|---|---|---|---|
| Chicago residential share | Share of Cook 2024 PINs in classes 2xx/3xx | **0.390** | Share of Cook 2024 ground-parcel **land area** in classes 2xx/3xx: 0.825 |
| São Paulo commerce share | Share of CNEFE 2022 addresses that are establishments | **0.422** | Share of CNEFE **buildings** (street + number + block) with an establishment: 0.744 |

Both pre-registered references count units (32% of Cook PINs are condominium units, class 299; CNEFE lists every apartment), while U1 weights land area. Like-for-like references agree well; the failures are a reference-design error.

## Limits

- **Primary use per lot cannot see vertical mixing.** A building with shops below and flats above counts as commerce, so mixed-use centres read as single-use (República and Sé are São Paulo's least mixed districts). U1 measures horizontal mix of lot uses.
- Different sources and meanings: observed use (CMAP) vs declared fiscal use (IPTU); about a quarter of land outside classified lots in both cities (Chicago `6000`, São Paulo no lot polygon).
- São Paulo: 29,971 lot polygons without an IPTU record; 27,756 IPTU lots without a polygon.

## Files

`u1_by_unit.csv` (entropies, class probabilities, land shares, references), `chicago_reference_diagnostic.csv`, `sp_reference_diagnostic.csv`, `checks.json`, `source_register.json`.

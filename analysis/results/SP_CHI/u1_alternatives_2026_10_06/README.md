# What is done in each neighbourhood? Alternatives to U1 (source research)

6 October 2026. Research only; no feature is built. Numbers from `analysis/scripts/audit_u1_alternatives.py` (`audit.json`, `establishments_per_100_dwellings.csv`). Motivation: U1 ([Step 7](../u1_step7_2026_10_06/README.md)) gives each lot one use, so it cannot see vertical mixing (a building with shops below and flats above counts as commerce); São Paulo's centre (República, Sé) reads as least mixed.

**Target (user, 6 October 2026):** the kinds of buildings and places in a neighbourhood (homes, shops, restaurants, offices, workshops, schools, churches…), not jobs.

## Criteria

A usable source must (1) see vertical mixing, (2) exist in both cities, (3) be complete or validated against an official registry, (4) type each unit by activity, (5) be reproducible.

## Sources evaluated

| Source | Evidence | Verdict |
|---|---|---|
| Building-use tags (Overture `subtype`, OpenStreetMap `building=*`) | Chicago: 39.5% of Overture footprint area has a type. São Paulo: no type in the Overture file; in Brás 94.8% of OpenStreetMap building area is tagged only `yes` | **Rejected** (mostly empty, asymmetric) |
| CMAP secondary use (`LANDUSE2`, modifier `M`) | Secondary use on 0.37% of Chicago land; 315 multi-use polygons | **Rejected** (cannot represent vertical mix) |
| Floor-space mix (MXI: floor area for housing, work, amenities) | São Paulo IPTU has floor area per unit and use; Chicago has no whole-stock floor area (B3 refused for this reason) | **São Paulo only**; not a common variable |
| Overture Places (POIs), both cities | Providers differ: Meta 95% of São Paulo places, 57% in Chicago (Microsoft and BrightQuery 16% each, Foursquare 9%). Overture commercial places vs official registries by area: **Chicago Spearman 0.969** (licensed sites; Overture 1.64 × licences); **São Paulo 0.484** (CNEFE establishments; ratio 0.24–1.06 across districts) | **Usable in Chicago, not in São Paulo** (district-uneven completeness) |
| **CNEFE 2022 (São Paulo census address list)** | Every address unit: 4,992,162 private dwellings and 606,716 establishments (education 10,108; health 10,717; religious 15,662; other 570,229). **All establishments carry an enumerator description**, usually an activity word: BAR 35,576; LOJA 25,401; SALÃO 21,561; GARAGEM 16,478; OFICINA 14,563; DEPÓSITO 13,850; ESCRITÓRIO 13,535; VAGO 13,411; … | **Strong**: official, complete, unit-level (vertical mixing seen), typed |
| **Chicago Business Licenses (current active)** | 54,006 licences, 39,688 business sites with community area and detailed activity; licences omit unlicensed activities (many offices, public institutions) | **Official check** for Chicago places |
| Census 2020 housing units (Chicago) | Official block counts | Dwelling side for Chicago |
| Foursquare Open Source Places | Open (Apache 2.0), 100M+ places, now behind a registration portal | Possible independent cross-check; not acquired |

## Face validity of a unit-based view

Establishments per 100 dwellings: São Paulo top five Pari 69.7, Brás 45.3, Bom Retiro 44.8, **Sé 36.5 (4th)**, Belém 24.8; República 22nd (many apartments); Alto de Pinheiros 95th. Chicago licensed sites per 100 housing units: **Loop 9.8 (1st)**, New City 8.8, O'Hare 6.7, Archer Heights 6.1, Lower West Side 6.0. Under U1, Sé ranks 93rd and República 94th of 96 for mix. Levels differ by city because the registries count different universes (CNEFE counts every establishment, including vacant premises; licences only licensed businesses).

## Proposal (for decision)

**"Activity composition" from units:** count each unit by what it is: a dwelling, or an establishment in one of five groups: food & drink; retail; services and offices; making and storing (industry, workshops, repair, warehouses); institutions (education, health, religious, civic). Two candidate coordinates per neighbourhood:
1. **Non-residential intensity**: establishments per 100 dwellings (how much non-housing activity sits among the homes; vertical mixing counted by construction).
2. **Activity diversity**: normalized entropy over the five non-residential groups.

**Sources:** São Paulo CNEFE 2022 (species plus a keyword classification of the descriptions; "VAGO" vacant premises excluded). Chicago: housing units from the Census (same vintage choice as U3 to be decided) and Overture Places typed by its taxonomy (validated against licences), with licences as a check.

**Known limits:** a unit is a unit (a kiosk counts like a department store); the two cities use different instruments (census list vs places), so levels are not comparable and cross-city use falls under C6; the description classification must be audited; vintages differ (CNEFE 2022, places 2026, housing units 2020 or 2020–2024).

**Relation to U1:** complementary. U1 says how land is divided among uses (horizontal); this says what activities units hold (including vertical). Whether to keep both, replace U1, or keep U1's land shares as descriptive is decided after a pilot.

## Sources

[MXI and land-use mix measures (Berkeley ITS)](https://its.berkeley.edu/node/3860); [land-use mix review (arXiv 2105.10383)](https://arxiv.org/pdf/2105.10383); [Chicago Business Licenses – Current Active](https://data.cityofchicago.org/Community-Economic-Development/Business-Licenses-Current-Active/uupf-x98q); [Foursquare OS Places](https://docs.foursquare.com/data-products/docs/fsq-places-open-source); [RAIS microdata (PDET)](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged) (jobs; not used, target is places). Licence site counts saved in `analysis/data/Chicago/business_licenses_2026_10_06/license_sites_by_area.csv` (SHA-256 `f536ff69…3ab4b`).

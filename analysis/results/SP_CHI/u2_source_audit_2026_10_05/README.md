# U2 source audit: who the job registers count, and where

5 October 2026. Decision S3-2 (MODEL_PLAN Step 3). Documents saved in `analysis/data/shared/jobs_docs/` (git-ignored) with SHA-256 below. The comparison table is produced by `analysis/scripts/audit_u2_sources.py`.

## Universe table

| | Chicago: LODES 8 WAC 2022, `S000` `JT00` | São Paulo: RAIS 2022 by CEP (supplied file) |
|---|---|---|
| Who is counted | Jobs covered by state unemployment insurance, plus Federal workers (verified, OnTheMap Data Overview, "Coverage") | Formal employment links declared by establishments (official municipal table "Empregos formais") |
| Job or person | All jobs; a person with two jobs counts twice (`JT00`); primary jobs `JT01` equal workers (verified) | Job links (vínculos) |
| Reference date | "Beginning of quarter" job: positive earnings in Q2 and in Q1, i.e. employed on about 1 April (verified) | 2022 reference year; the 31 December reference was seen only in a search summary (**not verified**) |
| Self-employed, informal | Not unemployment-insurance covered, so not counted (inferred from the coverage statement) | Not counted (formal links only) |
| Public sector | Included: local, state and Federal government employers (verified, "Ownership") | Included: public administration has **693,043 jobs in 178 establishments** (12.9% of the city's formal jobs; verified, official table) |
| Location | Workplace Census block. How multi-establishment employers are assigned to a site was **not verified** in the documents read | Postal code (CEP) of the declaring establishment; CEPs are not polygons |
| Total | 1,458,263 jobs in blocks touching Chicago | File 5,387,474 vs official 5,390,446 (**−0.055%**, verified: file is RAIS 2022 minus about 3,000 records) |
| Data treatment | Partially synthetic dataset with disclosure protection (verified) | 2022 is a series break (eSocial transition; official note cited in the municipal table) |

**Informality in São Paulo:** a state figure (31.3%, third quarter 2023, PNAD Contínua) was seen only in a search summary; IBGE's page refused automated access. **Not verified, not used.** No municipal or district informality figure is in the project.

## São Paulo: register vs survey (`sp_rais_vs_od_work_trips.csv`)

Metrô Origin–Destination survey 2023, "viagens diárias atraídas por motivo no destino": daily trips whose destination purpose is work (industry + commerce + services), by district. It is a household sample survey (79,000 people), counts **trips, not jobs**, includes informal work and records where people actually go. Compared with the RAIS `area_first` allocation (located jobs only):

- OD work trips attracted to the municipality: 5,499,937 per day.
- Spearman between district totals: **0.836**.
- District share ratio RAIS ÷ OD: median 0.83, 10th–90th percentile 0.46–1.31; **18 of 96 districts differ by more than a factor of two.**
- RAIS far above OD: Jaguaré 4.39, Pari 3.03, Sé 2.32 (Jaguaré and Pari contain single CEPs with 66,465 and 80,403 jobs; Sé is the seat of public administration).
- RAIS far below OD: Cachoeirinha 0.27, Cidade Tiradentes 0.33, Marsilac 0.35, Perus 0.36, Lajeado 0.37, Jardim Ângela 0.37, Guaianases 0.39, Parelheiros 0.42.

Neither source is ground truth: OD has sampling error and counts trips; RAIS has address error and excludes informal work. The pattern is consistent with head-office registration (centre too high) and with informal or centrally registered public work in the periphery (periphery too low); the data cannot separate these causes.

## Documents (SHA-256)

| File | Source | SHA-256 |
|---|---|---|
| `OnTheMapDataOverview.pdf` | https://lehd.ces.census.gov/doc/help/onthemap/OnTheMapDataOverview.pdf | `d5f63de3135ebf3c34116e7f12c97362096106d2f03fd4650acefa3516485f18` |
| `LODESTechDoc8.4.pdf` | https://lehd.ces.census.gov/data/lodes/LODES8/LODESTechDoc8.4.pdf | `1189b8aa4cefd6cdf53c3b85e27366054af0cd5418056b04ff70d210b87eddee` |
| `msp_estabelec_empregos_2022.pdf` | Prefeitura de São Paulo, SMUL/Geoinfo (Observatório do Trabalho / RAIS) | `7aa9b81c5eb945a46af3fc30b1955c335f31a4643ba7fd3589e8127459230f5b` |
| `od2023_atracao_viagens_motivo_destino.xlsx` (and `.pdf`) | Prefeitura de São Paulo, SMUL, from Metrô OD 2023 | `5ad70dae4bc1996118694d22ac34557b079d078580a7d3940628e023a8d81abf` |
| `od2023_viagens_motivo_produzidas.pdf` | same, trips by origin | `1efb94dcf006858f460af189a00e49bb73c2ae80afda26092ee15ce01a60785d` |

## Follow-up: OD 2023 jobs by workplace zone, city district series, Chicago checks (5 October 2026)

Script `analysis/scripts/audit_u2_od2023.py` → `sp_od2023_fixed_jobs_by_district.csv`. Inputs saved (git-ignored) with SHA-256: `analysis/data/SP/od2023_metro/Site_190225_PesquisaOD2023.zip` `1844d38ad83c86cbb679f24c04e317aa49704c5009f8e5a0d0246f026f06bd9d` (Metrô OD 2023 tables, microdata, layout, zones); `analysis/data/shared/jobs_docs/msp_empregos_distrito_2011_2024.pdf` `ebaf97910fceea3ca0d17e6f60115b547929048bb02bc368f97a177a9a3380a1`; `analysis/data/Chicago/lodes_2023/il_wac_S000_JT00_2023.csv.gz` `02cd57766b9c1bd4b85367acad26e09fe98850798d5e8ec96a3e8b4af1c01c76`; `analysis/data/Chicago/cmap_mdt_2024_25/TravelSurveys_PublicData_CMAP.zip` `e7e9ec59f778ca673f382ae067e6fd5b56f7000cd0a9362335b41322942bcb8c`.

**OD 2023 Table 14 (jobs, not trips).** Its footnote states that a worker with no fixed workplace is assigned to the **residence zone**. Over the 343 zones of São Paulo municipality: 4,989,267 jobs at a fixed address outside the home, 925,554 at home, 590,577 with no fixed address (total 6,505,398). The microdata (`FE_PESS`, `ZONATRA1/2`, `TRAB1_RE/2_RE`) reproduce all three totals exactly.

**Universe, from the microdata employment relationship (`VINC`).** RAIS-comparable = employee with signed card (1) + public servant (3); informal = employee without card (2), self-employed without CNPJ (6), family business owner (8), family worker (9); other non-RAIS = liberal professional (4), self-employed with CNPJ (5), employer (7).

| Jobs located in São Paulo | RAIS-comparable | Informal | Other non-RAIS |
|---|---:|---:|---:|
| Fixed workplace outside home | 73.7% | 15.6% | 10.7% |
| All locations | 57.7% (3,753,480) | 26.0% | 16.3% |

RAIS 2022 counts 5,390,446 jobs in the municipality, **1.64 million more than OD's RAIS-comparable jobs located there.** Not explained: OD interviews only residents of the metropolitan region; dates differ (31 December 2022 vs August 2023–March 2024); registers can record in the city jobs performed elsewhere; surveys can under-report.

**Like-for-like district comparison** (RAIS `area_first` vs OD RAIS-comparable fixed-workplace jobs): Spearman 0.886. Large gaps remain even with the same universe: Pari 4.04×, Jaguaré 3.21×, Sé 1.85× (RAIS higher); Perus 0.40×, Cidade Tiradentes 0.40×, Parelheiros 0.43×, Lajeado 0.45×, São Miguel 0.47×, Guaianases 0.50× (RAIS lower). **Informality therefore does not explain the district distortions; location of registration does** (or survey error). District informal share correlates with the RAIS/OD-all ratio at Spearman −0.445: it explains part of the all-work gap.

**Sample sizes:** first-job fixed-workplace observations per district minimum 4, median 121, maximum 1,711; 9 districts under 50. RAIS-comparable observations: median 80; **23 districts under 50.** District estimates for small districts are noisy.

**City district RAIS series (Prefeitura, 2011–2024).** Totals 5,390,446 (2022), 5,138,980 (2023), 5,346,517 (2024). Read by column position (the 2018 cell of the "invalid" row is blank): 2022 invalid 10,381 + not located 36,021 = **46,402**. Brás 420,022 (2022), 76,383 (2023), 36,733 (2024); in 2022 Sé fell by 372,760 while Brás rose by 347,070 (cause not established). Spearman with OD RAIS-comparable: 0.859 (2022), 0.837 (2023); with the project's CEP allocation: 0.909 and 0.918.

| District | Project CEP RAIS 2022 | City RAIS 2022 | City 2023 | City 2024 | OD RAIS-comparable | OD all fixed | OD sample (RAIS-comp.) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Brás | 45,960 | 420,022 | 76,383 | 36,733 | 48,486 | 77,307 | 217 |
| Jaguaré | 90,988 | 89,664 | 94,989 | 79,905 | 21,396 | 27,591 | 69 |
| Pari | 106,799 | 21,631 | 94,483 | 121,995 | 19,916 | 31,565 | 103 |
| Sé | 264,809 | 311,402 | 235,595 | 308,893 | 107,660 | 131,590 | 454 |

**Chicago.** LODES 2023 `JT00`: 1,511,189 jobs in blocks touching the city (2022: 1,458,263; +3.6%). CMAP My Daily Travel 2024–25: 7,310 persons; 2,825 report a work tract; 1,871 in Cook County; **1,313 in tracts touching Chicago, median 6 per community area, 51 of 77 areas under 10** — not usable for area-level estimates.

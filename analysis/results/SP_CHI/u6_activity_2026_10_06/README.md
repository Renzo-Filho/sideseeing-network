# U6 activity composition (Step 7b)

Run 6 October 2026 by `analysis/scripts/build_u6_activity.py` (`classify`, `places CHI`, `places SP`, `v2`, `bridge`, `features [overture|cnefe]`, `untyped`, `vertical`, `rais_test`).
- Decisions S7b-1 to S7b-8 were fixed by the user before the run. The São Paulo source was then chosen by the pre-registered D7b-3 test (RT-1 to RT-5, approved before it ran). See [MODEL_PLAN Step 7b](../../../../docs/chicago/MODEL_PLAN.md#step-7b-plan--u6-activity-composition-user-request-6-october-2026).
- Crosswalks were frozen in `analysis/config/u6/` before each check.
- SHA-256 of inputs, crosswalks and scripts: `source_register.sha256`.
- **Accepted with stated limits on 6 October 2026:** the final Overture-based U6 family entered `chicago_model_v1` and `sp_chicago_model_v1`; the earlier CNEFE-based version below was superseded by D7b-3.

## Definition (current)

Units are address units: each dwelling and each establishment counts once. A shop below flats therefore counts as one establishment plus the flats, which is how vertical mixing is counted.

| Column | Meaning |
|---|---|
| `u6_intensity_per_100_dwellings`, `u6_log_intensity` | Classified establishments per 100 dwellings (level 1) |
| `share_<class>` | Share of classified establishments in each of five classes: food_drink, retail, services_offices, making_storing, institutions |
| `clr_<class>` | Centred log-ratio: log(n + 0.5) minus the unit's mean (S7b-6) |
| `u6_clr_city_<class>` | `clr` minus the city mean (C6: each class is read against the unit's own city) |
| `u6_entropy5` | Normalized Shannon entropy of the five shares (÷ ln 5); descriptive only (D7b-4) |
| `dominant_relative_class` | Class with the highest `u6_clr_city`: the class the unit has most **more of than its city usually has** |
| `flag_under_100_establishments` | Composition based on fewer than 100 classified establishments |

**Model coordinates (D7b-4):** `u6_log_intensity` relative to each city, plus the five `u6_clr_city_*`.

**Sources (same establishment instrument in both cities since the D7b-3 test):**
- **Establishments, both cities:** Overture places 2026-08-19.
  - Permanently and temporarily closed places are excluded.
  - Each place gets the most specific taxonomy key in `overture_taxonomy.csv`.
  - Places without a taxonomy are excluded (D7b-2).
- **Dwellings, São Paulo:** CNEFE 2022 species 1–2.
- **Dwellings, Chicago:** ACS 2020–2024 B25001 housing units, allocated from block group → 2020 block (HOUSING20 share) → Community Area (block land share), as for U3.
- **Checks only:** Chicago business licences (`licence_activity.csv`); São Paulo RAIS 2022 establishments (`rais_cnae.csv`).

## D7b-3: which São Paulo instrument? (`rais_test.json`, `rais_test_by_unit.csv`)

**The problem.**
- CNEFE (census list) seems to miss offices in towers; see the CNEFE office section below.
- Overture misses workshops and informal trade.
- Neither can judge the other.

**The reference: RAIS 2022 formal establishments.**
- Source: Base dos Dados, `analysis/scripts/fetch_RAIS_estab.py`.
- The 314,022 records that are not "RAIS negativa" and their 5,390,446 jobs match the city's published 2022 table exactly. This is asserted in the script.
- RT-1:
  - 282,689 establishments with at least one active job on 31 December 2022.
  - Placed by postcode with the U2 `area_first` weights; 98.75% are placed.
  - RAIS's own district field is empty.
- RT-2: sector codes mapped to the five classes by `rais_cnae.csv`, frozen before the run.

**RT-3: Spearman with RAIS over 96 districts, on the model coordinates.**

| Coordinate | CNEFE | Overture |
|---|---|---|
| Log intensity | 0.284 | **0.988** |
| Food & drink | −0.278 | 0.141 |
| Retail | 0.406 | 0.491 |
| Services & offices | 0.853 | 0.850 |
| Making & storing | 0.794 | 0.766 |
| Institutions | 0.754 | 0.882 |
| **Mean** | **0.469** | **0.686** |

**RT-4 decision:** Overture's mean exceeds CNEFE's by **0.217**, far more than the 0.05 margin. **Overture is used in both cities.**

**RT-5 (descriptive).**

Raw counts per district vs RAIS:

| | Total | Food | Retail | Services | Making | Institutions |
|---|---|---|---|---|---|---|
| CNEFE | 0.170 | −0.182 | 0.480 | 0.303 | 0.392 | 0.349 |
| Overture | 0.930 | 0.798 | 0.980 | 0.906 | 0.888 | 0.909 |

Intensity rank (1 = highest of 96):

| District | CNEFE | Overture | RAIS |
|---|---|---|---|
| Consolação | 95 | 14 | 12 |
| Jardim Paulista | 88 | 7 | 9 |
| Bela Vista | 92 | 10 | 16 |
| Itaim Bibi | 56 | 4 | 4 |
| Barra Funda | 65 | 6 | 7 |
| Pinheiros | 16 | 3 | 5 |
| República | 27 | 12 | 10 |
| Sé | 4 | 1 | 2 |
| Brás | 2 | 5 | 3 |
| Pari | 1 | 2 | 1 |

RAIS jobs per RAIS establishment: median 12.2.

**Reading the result.**
- **CNEFE's office gap is confirmed by the referee.** The districts where it was suspected move from the bottom of CNEFE's ranking to RAIS's top 16, and Overture agrees with RAIS there.
- **Overture and RAIS are not the same source.** In São Paulo, 95% of classified Overture places come from Meta (business pages), not from a government registry.
- **Both lean formal, which the 0.05 margin was meant to absorb.** The observed gap is four times the margin.
- **The intensity correlation is partly inflated.** All three instruments share the CNEFE dwellings denominator. CNEFE gets only 0.284 under that same denominator, and raw totals without any denominator show the same gap (0.930 vs 0.170).
- **Food & drink agrees poorly with RAIS for both instruments.** CNEFE −0.28, Overture 0.14. Many bars and snack bars are informal, and RAIS sees only formal ones. The food coordinate is the weakest in São Paulo whichever instrument is used.

## Results (`u6_by_unit.csv`, `phase_e.json`; Overture in both cities)

| | Chicago (77) | São Paulo (96) |
|---|---|---|
| Classified establishments | 111,342 | 416,487 |
| Median intensity (per 100 dwellings) | 6.6 (p10–p90 4.2–11.3) | 6.9 (3.5–22.0) |
| Highest | Loop 42.7, Near West Side 19.8, O'Hare 17.4 | **Sé 47.4**, Pari 39.5, Pinheiros 33.8, Itaim Bibi 29.3, **Brás 25.8** |
| Lowest | Oakland 2.2, Riverdale 2.6, South Shore 2.9 | Marsilac 1.6, Cidade Tiradentes 3.0, Jardim Ângela 3.0, Iguatemi 3.1, Pedreira 3.2 |
| Median entropy | 0.888 (p10–p90 0.80–0.96) | 0.935 (0.86–0.95) |
| Dominant relative class (counts) | making 24, institutions 23, food 14, services 8, retail 8 | making 39, institutions 22, food 17, services 13, retail 5 |
| Flagged (< 100 classified) | Oakland (77), Burnside, Riverdale | Marsilac (99) |

**Anchors (V4):**

| Area | Intensity (rank) | Profile | Dominant relative class |
|---|---|---|---|
| Sé | 47.4 (1st) | services 36%, retail 35% | retail |
| República | 21.9 (12th) | services 45%, retail 27% | services |
| Brás | 25.8 (5th) | retail 64% | retail |
| Pari | 39.5 (2nd) | retail 60% | retail |
| Alto de Pinheiros | 11.8 (26th) | services 45% | services |
| Loop | 42.7 (1st) | services 53%, institutions 24% | — |
| Near West Side | 19.8 | — | food |
| Beverly | 11.1 | — | institutions |
| Archer Heights | 11.1 | — | making |

- Districts dominant in making & storing: the old industrial east and north (Água Rasa, Belém, Cambuci, Casa Verde, …).
- Under U1, Sé ranked 93rd and República 94th of 94 for mix. Under U6 they rank 1st and 12th for intensity.

**Sensitivity check.** Dropping places with Overture confidence < 0.3 keeps 94.6% of classified places in Chicago and 86.5% in São Paulo (São Paulo median confidence 0.67). Rankings barely move (`unclassified_by_unit.json`):
- intensity: Spearman 0.999 in both cities;
- city-centred log-ratios: Chicago 0.995–0.999, São Paulo 0.972–0.997.

**Overlaps (V5, Spearman):**

| Pair | Chicago | São Paulo |
|---|---|---|
| U6 log intensity vs U2 (job density) | **0.71** | **0.91** |
| U6 log intensity vs U1 entropy (dropped) | 0.22 | 0.29 |
| U6 log intensity vs U3 | 0.15 | −0.09 |
| U6 entropy vs U2 | −0.09 | −0.56 |
| U6 entropy vs U3 | 0.04 | 0.04 |

**U6 intensity overlaps strongly with U2 in São Paulo** (0.91). The redundancy is for the final joint review (C5): both are "how much non-residential activity", one per dwelling and one per km² of land.

## Chicago places without a taxonomy are mostly not real establishments

| | Places with a taxonomy | Places without one |
|---|---|---|
| Median Overture confidence | 0.92 | 0.206 |
| Share with confidence < 0.3 | 5.4% | 77.7% |
| Main provider | Meta 54%, BrightQuery 17%, Microsoft 15%, Foursquare 13% | Meta 84%, Microsoft 12% |

- They are 17.5% of Chicago places, concentrated in a few areas:

  | Area | Untyped share |
  |---|---|
  | Kenwood | 72.7% |
  | Hyde Park | 60.1% |
  | Lower West Side | 52.0% |
  | Lincoln Park | 42.2% |
  | Lake View | 30.8% |
  | Logan Square | 29.7% |
  | West Town | 29.1% |
  | Loop | 22.8% |

- A random sample of Kenwood's untyped names was read by hand. Most are non-words or codes ("Jungrenshebe Pludowulthu 16-3", "Rmlhv1", "Tqwh0727 71", "Knuq-0805-60").
- They are excluded as noise. Areas above 30% untyped are flagged (D7b-2).
- Why they cluster there is not known. São Paulo has 3.8% untyped.

## Limits

- **A unit is a unit.** A kiosk counts the same as a department store. Floor-area weighting is impossible in Chicago.
- **Overture leans formal and online.** It under-sees workshops and informal trade:
  - making & storing is 0.41× CNEFE's count in São Paulo;
  - Brás and Pari read as retail rather than retail plus garment workshops;
  - informal commerce in the periphery is undercounted.
- **Provider mix differs by city.** São Paulo is 95% Meta; Chicago mixes Meta, BrightQuery, Microsoft and Foursquare. Levels are compared relative to each city (C6), not absolutely.
- **Food & drink is the weakest coordinate in São Paulo** (RT-3: 0.14 against RAIS).
- **Chicago untyped places are excluded on evidence.** If some are real, Kenwood, Hyde Park and the Lower West Side are undercounted.
- **Years differ.** Overture places are 2026, CNEFE dwellings 2022, ACS 2020–2024, RAIS 2022.

---

## History: the São Paulo CNEFE version (superseded by D7b-3)

Reproduced byte-identical by `features cnefe` → `u6_by_unit_sp_cnefe.csv`, `phase_e_sp_cnefe.json`.

### CNEFE classification

| | São Paulo CNEFE (607,048 establishments) | Chicago Overture (139,388 places on land) | São Paulo Overture (445,872) |
|---|---|---|---|
| Services & offices | 16.3% | 32.7% | 35.5% |
| Retail | 19.0% | 11.1% | 20.8% |
| Food & drink | 13.9% | 11.9% | 12.3% |
| Making & storing | 14.7% | 4.7% | 7.5% |
| Institutions | 10.4% | 19.6% | 17.3% |
| Unclassifiable | 15.6% | 17.5% | 3.8% |
| Excluded (vacant, parking, non-activity) | 10.1% | 2.6% | 2.8% |

**Classification rules:**
- Species 4, 5 and 8 → institutions; species 3 → making_storing.
- Species 6 (other purposes) is classified from the enumerator's description by `cnefe_keywords.csv`: priority-ordered regex rules on accent-free upper-case text.

### Pre-registered checks

| Check | Rule | Result |
|---|---|---|
| V1 São Paulo CNEFE classifier, accuracy | ≥ 90% correct on a 400-record random sample (seed 20261006) | **96.0%** (312 of 325): pass |
| V1 São Paulo CNEFE classifier, coverage | ≤ 15% unclassifiable | **15.6%**: **failed by 0.6 points** (D7b-1: accepted with limit; moot after D7b-3) |
| V2 Chicago, food & drink | Overture vs licensed sites per Community Area, Spearman ≥ 0.80 | **0.980** (16,511 places vs 7,799 sites): pass |
| V2 Chicago, making & storing | same | **0.875** (6,483 vs 3,056): pass |

**V1 notes:**
- Claude did the V1 audit (the record-level `v1_audit_sample.csv` remains local and is excluded from Git); the user has not checked it.
- Of 75 unclassifiable sample records, 49 could be classified by a person (typos, plurals) and 26 could not.
- São Paulo's unclassifiable share by district: median 15.7%, p10–p90 11.7–21.2%; unrelated to intensity (−0.007).

### Bridge study (V3, descriptive)

| Class | CNEFE share | Overture share | Overture ÷ CNEFE | District Spearman |
|---|---|---|---|---|
| Food & drink | 18.7% | 13.2% | 0.71 | 0.67 |
| Retail | 25.5% | 22.3% | 0.87 | 0.40 |
| Services & offices | 22.0% | 38.0% | **1.73** | 0.81 |
| Making & storing | 19.8% | 8.0% | **0.41** | 0.85 |
| Institutions | 14.0% | 18.5% | 1.32 | 0.68 |

In Chicago, food & drink and making & storing appear at the same rate relative to licensed sites (2.12 each). The instrument's class bias therefore differs by city, which is the reason composition is read relative to each city (C6).

### CNEFE appears to miss offices in towers (`vertical`, `cnefe_vertical_listing.csv`/`.json`)

| District | Dwellings per building address | Establishments per building address | Overture ÷ CNEFE | RAIS jobs per CNEFE establishment |
|---|---|---|---|---|
| City median | 2.3 | 1.16 | 0.76 | 7.5 |
| Consolação | 18.5 | 1.16 | 3.98 | 80 |
| Bela Vista | 17.3 | 1.25 | 3.71 | 59 |
| Jardim Paulista | 13.9 | 1.12 | 3.77 | 60 |
| Itaim Bibi | 7.0 | 1.06 | 3.51 | 98 |
| Barra Funda | 15.0 | 1.28 | 3.18 | 91 |
| Pinheiros | 5.6 | 1.09 | 2.99 | 50 |

- CNEFE lists apartments one by one but establishments about once per building.
- The Overture ÷ CNEFE ratio and RAIS jobs per CNEFE establishment agree across districts (Spearman 0.884).
- Mechanism (upper-floor offices not listed one by one) is a hypothesis; IBGE's method text was not read.
- The D7b-3 test then confirmed the consequence (Consolação: CNEFE 95th, RAIS 12th for intensity).

### CNEFE-version results (superseded)

**Intensity:**
- Median 8.7.
- Highest: Pari 53.0, Brás 33.4, Bom Retiro 29.5, Sé 24.6.
- Lowest included Consolação 5.2 and Bela Vista 5.9.

**Entropy:** median 0.981 (p10–p90 0.94–0.99; saturated).

**U6 intensity vs U2:** 0.18.

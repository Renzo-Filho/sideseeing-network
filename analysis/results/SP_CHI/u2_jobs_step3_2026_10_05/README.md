# U2 registered workplace-job density, Chicago and São Paulo

Run 5 October 2026 by `analysis/scripts/evaluate_u2_step3.py` (70 s). Decisions fixed before the run: MODEL_PLAN Step 3 (S3-0 to S3-7) and the user's decisions of 5 October 2026: estimand (a) registered jobs at the employer's establishment; LODES 2023 for Chicago; districts flagged by the OD agreement test accepted with stated limits. Source evidence: [u2_source_audit](../u2_source_audit_2026_10_05/README.md). **Not accepted until the user signs.**

## Definition

`u2_jobs_land_km2` = registered jobs at the declaring establishment ÷ land km² (C2).
- **Chicago:** LODES 8 WAC 2023, `S000` `JT00` (unemployment-insurance-covered and Federal jobs, all jobs per person, about 1 April 2023), block → Community Area by land share (as U3).
- **São Paulo:** RAIS 2022 by CEP, project `area_first` allocation (business constructed area → establishment addresses → residential area); the 508,844 unplaced jobs spread in proportion to the placed ones (district shares unchanged).
- Also reported: `u2_relative_centrality` = area density ÷ city density (for the common stage).

## Results

| Check | Result |
|---|---|
| Chicago mass 2023 | 1,462,492.88 inside + 48,696.12 outside = 1,511,189 block total, pass |
| São Paulo mass | 4,878,630 placed + 508,844 unplaced = 5,387,474, pass; CEP allocation table equals district table |
| No missing values | pass |
| **S3-3 Chicago land share vs CMAP business land** (2022 jobs; rule 5% / 5 ranks) | **2 cases:** Woodlawn −5.4% (5 ranks), Hegewisch −23.6% (2 ranks) |
| **S3-4 São Paulo area_first vs address_first** (same rule) | **26 cases**, Spearman 0.9974. Mostly 5–15%; rank moves of 5 or more: Alto de Pinheiros (10, +35.8%), Vila Jacuí (5), Artur Alvim (5). Largest level changes: Marsilac +157% (251 jobs), Jardim Ângela +40.5% |
| S3-5 São Paulo excluding unplaced jobs | all levels −9.44%, ranks unchanged |
| S3-6 without the 10 largest blocks / CEPs (areas changing > 10%) | Chicago: Loop, Hyde Park, O'Hare. São Paulo: Barra Funda, Consolação, Itaim Bibi, Jaguaré, Pari, Santo Amaro, Sé |
| **OD 2023 agreement** (RAIS share vs OD RAIS-comparable fixed-workplace share; approximate 95% sampling interval) | **45 of 96 flagged** (31 RAIS lower, 14 higher); district totals Spearman 0.886. The interval ignores household clustering: with standard errors ×1.5, 17 flagged; ×2, **6, all RAIS higher: Pari 4.04×, Jaguaré 3.21×, Sé 1.85×, Casa Verde 1.63×, Consolação 1.36×, Itaim Bibi 1.25×.** Brás 0.71× is flagged only at ×1 |

**Values.** Chicago median 944 jobs/km² (Loop 122,514; Riverdale 107). São Paulo median 3,052 (Sé 136,113; Marsilac 1.2). Brás 13,984, 15th in São Paulo. Relative centrality medians: Chicago 0.38, São Paulo 0.86.

## Stated limits (proposed for the acceptance record)

1. Registered jobs at the employer's establishment, not where people physically work; informal and self-employed work excluded (OD 2023: 26.0% informal and 16.3% other non-RAIS of jobs located in São Paulo).
2. São Paulo head-office districts are robustly higher in RAIS than in OD (six districts above); the periphery shortfall is within plausible sampling error.
3. São Paulo CEP allocation: 26 districts change by more than 5% under address-first weights; 508,844 unplaced jobs (351,576 with no address) spread like the placed ones.
4. RAIS 2022 total exceeds OD RAIS-comparable jobs in the city by 1.64 million (unexplained).
5. Chicago: location error unmeasured (no area-level independent source); LODES is partially synthetic; Woodlawn and Hegewisch sensitive to business-land allocation.
6. Vintages: LODES about 1 April 2023; RAIS 2022 reference year.

## Files

`tables/u2_jobs.csv|parquet` (one row per unit, both cities), `checks.json`, `source_register.json`.

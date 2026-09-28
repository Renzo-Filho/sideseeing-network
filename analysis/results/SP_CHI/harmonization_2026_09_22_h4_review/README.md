# H4 bounded readiness checkpoint — September 22, 2026

**Technical readiness passed; scientific scope approval remains pending. No fitting or rankings.** The user reported 14% quota remaining and requested the next close checkpoint. This review reuses the sealed H1–H3 outputs and does not rerun spatial construction.

## Concrete proposal for review

| Family | Proposed primary measurement | Weight |
|---|---|---:|
| M1 | Mapped physical street length / gross area, irrespective of legal access | 1/6 |
| M6 | Ten-part mapped street-class composition, unknown separate | 1/6 |
| B1 | Union footprint coverage / hydrographic land area | 1/6 |
| BV | Land-area-weighted net GHSL grid height, observed zero retained | 1/6 |
| U3 | Census population / gross area | 1/6 |
| U4 | Bus-only weekday morning supply, 400 m, population weighted | 1/6 |

The proposed matrix contains **173 units and 15 raw columns**: five scalar columns and ten composition components belonging to one M6 family. Fifteen columns do not mean fifteen independently weighted families. `proposed_contract.json` sets `fit_authorized=false`.

M2/M3/M4 remain withheld because physical junction/block definitions have not passed. M7/B2/B3 remain excluded under the approved public-data route. U1 remains withheld and U2 remains extended-only. Consequently, the proposal measures mapped street structure, coverage/height, population and bus supply; it does not measure physical block shape, consolidated junction density, land-use diversity or workplace intensity. This materially narrows the earlier model and must be reviewed before H5.

## Readiness evidence

All **13 checks passed**: source hash, exact cohort, unique column set, finite/nonmissing selected values, composition bounds/sums, footprint domain, transform domains and family weights. This is input readiness, not proof of source equivalence or model validity.

All five scalar inputs fall within SP's observed marginal range. Some Chicago hierarchy components exceed SP ranges (motorway: 5 units; secondary: 6; tertiary: 4; residential: 3). These counts can overlap. Save extrapolation flags during H5; do not clip values. Marginal ranges do not establish that joint city distributions are equivalent.

Spearman height–volume correlations are **0.953 in SP and 0.933 in Chicago**. Use height as the proposed primary BV coordinate and volume as an alternative under the same weight; do not add a second independent volume family. Correlation is descriptive and does not validate the satellite estimates.

Remaining qualifications: unequal source completeness; different hydrographic vintages; 2018 height/2020 volume; SP2022 versus Chicago2020 population; bus scenarios one week apart and frequency-based versus scheduled service. Required sensitivities are listed in the proposed contract. No transformations, scales or distances were fitted, and no neighbor rankings were inspected.

## Saved files and next action

- `proposed_matrix.csv` / `.parquet`: complete proposed inputs.
- `proposed_contract.json`: definitions, weights, transforms, exclusions and sensitivities.
- `raw_domain_review.csv`: per-city ranges and potential extrapolation.
- `built_form_correlations.csv`: overlap among built-form measurements.
- `readiness_checks.json`, `progress.json`, `manifest.json`: audit and stopping state.

**Next decision:** accept the reduced six-family scope for a qualified descriptive comparison, or reopen physical junction/block construction before fitting. After scope acceptance, H5 can fit new SP-anchored state and apply it unchanged to Chicago. H6 robustness and final model documentation follow. Existing SP v2 remains untouched.

Reproduce this small review: `.venv/bin/python analysis/scripts/review_harmonization_h4.py`.

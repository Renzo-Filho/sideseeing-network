# Paired harmonization candidates — H1–H3, September 22, 2026

Candidate construction covers **173 reporting units** (96 SP districts and 77 Chicago Community Areas), with **6,209 long-form rows and 37 feature columns**. These include diagnostics and explicitly missing U1; they are not 37 accepted model coordinates. No model was fitted and no cross-city ranking produced.

## Outputs and gates

- `tables/`: paired long/wide candidate attributes and dictionary.
- `roads/`: mapped-street density/hierarchy, diagnostic connector/enclosure measures and eight pilot maps. M2/M3/M4 remain withheld because physical junction/block semantics are unresolved.
- `footprints/`: full paired footprint coverage with gross/land variants; Chicago recomputed, SP frozen numerators reused with three independent shared-method pilot reconstructions.
- `ghsl/`: 1,038 native-grid product/support rows, source-cell recovery receipts and projected-geometry repair log. Final missing candidate values: 0. Recovered source cells: 3. Tiny masked areas below the existing coverage tolerance remain explicit diagnostic residuals.
- `functional/`: 173 population rows and 1,038 bus-only scenarios. U1 withheld; U2 stays extended-only. Completed Chicago employment sensitivity is in `analysis/results/Chicago/chi_employment_sensitivity_2026_09_22_v2/`.
- `family_acceptance_ledger.json`: candidate, withheld, extended-only and excluded status for every family.

Separate SP and Chicago candidate companions are under each city's `harmonized_candidates_2026_09_22/`. Original numeric releases remain unchanged.

## Important correction

Legacy SP transit processing included nine metro and seven rail routes. The new companion filters `route_type=3` and recomputes all 576 SP scenarios. Brás weekday400m supply decreases about16.6%. Original SP v2 is preserved, but its U4 cannot be described as bus-only. Other population, calendar, frequency and operator-scope qualifications remain explicit.

## Verification

| Check group | Passed | Failed |
|---|---:|---:|
| GHSL coverage/partition checks | 1211 | 0 |
| Footprint bounds and SP reconstruction | 176 | 0 |
| Paired functional checks | 2171 | 0 |
| SP bus-only not-greater-than-legacy checks | 576 | 0 |
| Employment independent audit | 138 | 0 |
| Independent candidate-table/source-cell audit | 31 | 0 |
| Targeted unit tests | 28 | 0 |

These numerical checks do not prove source accuracy or scientific measurement equivalence. H1's semantic gates for M2/M3/M4 are still open; their outputs remain diagnostic.

## Next checkpoint

H4 must review the proposed reduced common set (M1/M6/B1/U3/U4, with BV extension), or require improved junction/block methods before accepting M2/M3/M4. That scope choice precedes fitting. Source completeness, land-mask differences and source years remain acceptance qualifications. No zero-filled missing family, pairwise feature deletion or city-specific normalization is permitted.

Full decisions, formulas, code commands, failures/fixes and limitations: [execution documentation](../../../../docs/harmonization/EXECUTION_LOG.md). H5/H6 are not started. No construction jobs remain running after finalization.

# Reopened six-family SP–Chicago plan: scope and evidence review

**Decision status — 22 September 2026:** the user asked to restore the earlier six-family plan and reconsider its pros and cons. It is now an **active proposal for review**, rather than a discarded option. The historical [H4 review](../../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md) and its sealed matrix/contract remain unchanged. A prior decision rejected this scope; the present request reopens it, but does not itself establish scientific acceptance or authorize fitting. Bulk processing remains paused during discussion.

**M2 decision — 25 September 2026:** M2 is deferred from both the planned Chicago model and any future cross-city score. This six-family proposal already excludes it, so its six families and saved matrix do not change. The other exclusions and the scientific acceptance decision remain open. Historical M2 work is retained for diagnostics, not weighted into this proposal.

## Exact restored proposal

Compare **96 São Paulo districts and 77 Chicago Community Areas**, anchored to Brás (SP:10), with six equally weighted families (one sixth each). Fit transformations, scales and family calibration on harmonized SP only, then apply the saved state unchanged to Chicago if the scope and measurements are accepted.

| Family | Primary measurement in the saved H4 proposal | What it contributes |
|---|---|---|
| M1 | Mapped street length per gross area | Street-network intensity, regardless of legal access. |
| M6 | Ten-part mapped street-class length composition, with `unknown` separate | Hierarchy mix; ten shares form **one** family. |
| B1 | Unioned Overture building-footprint coverage per land area | Horizontal building coverage. |
| BV | Land-weighted GHSL net grid height (ANBH, 2018) | Estimated vertical form at 100 m grid support. GHSL volume (2020) is a **same-family sensitivity**, not a seventh independent weight. |
| U3 | Census resident population per gross area | Residential intensity (SP 2022, Chicago 2020). |
| U4 | Population-weighted reachable weekday morning bus supply within 400 m | Accessible bus service; SP expected frequency and CTA scheduled service require review. |

The saved proposal has **173 complete rows and 15 raw columns**: five scalar columns and ten M6 shares. Its [readiness report](../../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/readiness_checks.json) passed **13/13 arithmetic/input checks**, including source hash, completeness, domains and equal weights. No model was fitted and no rankings were inspected. Those checks do not accept source meaning or accuracy.

The [open feature discussion](../OPEN_DISCUSSION.md) explores ways to recover street morphology, workplace intensity and land-use mix. M2 is explicitly deferred from new Chicago and cross-city scoring. M3/M4, M7/B2/B3 and U1/U2 are outside this proposed distance but remain under discussion. Their original definitions, and the historical M2 definition, remain documented in the [13-family ledger](CHICAGO_13_FAMILY_COMPLETION_LEDGER.md). BV is a new vertical-form measure; it does not supply physical cadastral entities, reported floors or fiscal constructed area.

## Advantages and costs

| Advantage | Corresponding limitation |
|---|---|
| A paired numerical matrix already exists for every reporting unit, so a bounded review can proceed without another citywide construction job. | Completeness and finite values do not prove the measurements mean the same thing in both cities. |
| Matched Overture road/building editions and common GHSL grids reduce some source-technology differences. | Coverage can still differ by city and neighborhood. The O'Hare/Marsilac road outliers and uneven Microsoft–Overture footprint pilot demonstrate why local reference review matters. Microsoft is not an independent building-height substitute for GHSL. |
| Avoids forcing Cook/DuPage tax records into SP cadastral definitions before the source/entity question is settled. | Removes parcel subdivision (M7), reported floors (B2) and constructed-area intensity (B3); GHSL height measures none of them. |
| Excludes unvalidated physical junction and block algorithms. | Removes junction density (M2), block size (M3) and shape (M4), including much of the fine-grain urban morphology relevant to Brás. |
| Produces a focused structural, residential and bus-access comparison. | Excludes land-use mix (U1) and workplace intensity (U2), so an apparent analogue may match form and bus access while differing sharply in function. It cannot support a claim of overall urban similarity. |
| One sixth per family is simple and auditable. | M1/M6 share a road source; B1/BV are related built-form measures; U3/U4 both involve population. Equal family weights are a choice, not proof of independent information. Omission/weight sensitivities are essential. |
| SP-fitted scaling gives a consistent reference space. | Chicago class shares can exceed SP marginal ranges; differing source vintages and reporting-unit sizes remain. Extrapolation must be flagged, not clipped away. |

**Interpretation if accepted:** a *qualified six-family structural, population and bus-service analogue model*. It is not the originally specified 13-family urban model. The older SP v2 and Chicago local/functional releases remain separate.

## Conditions before fitting

1. **Decide the release's role and claim.** Is this a separately named, limited comparison while the 13-family work continues, or is the project's primary question intentionally narrowed? Record any changed research question and excluded concepts in the release title and abstract.
2. **Accept each of the six measurements on evidence.** Review M1/M6 source completeness in O'Hare, Marsilac and other outliers; inspect B1 local reference and land-mask sensitivity; review GHSL support, estimate uncertainty and 2018/2020 distinction; document U3 vintage/support; resolve or explicitly qualify U4 frequency/schedule/calendar comparability. The [full-scope ledger](CHICAGO_13_FAMILY_COMPLETION_LEDGER.md) contains the currently open family gates.
3. **Precommit model checks and reporting.** Use the saved H4 required sensitivities: no-BV core; volume instead of height under the same BV budget; gross B1/BV denominators; M6 omission; bus 800 m/weekend; weight and city-balanced alternatives. Report rank stability, family contributions, out-of-SP-range values and local reference limitations. Do not choose variants after inspecting favorable Brás analogues.
4. **Only then authorize H5/H6.** Fit new SP state, apply unchanged to Chicago, validate distance/contribution reconstruction and publish versioned outputs. The sealed H1–H3/H4 artifacts and original city releases remain untouched.

The [current model status](../MODEL_STATUS.md) tracks the scope decision. Until the user settles the release's role and the six scientific gates are reviewed, the existing contracts continue to say `fit_authorized=false`.

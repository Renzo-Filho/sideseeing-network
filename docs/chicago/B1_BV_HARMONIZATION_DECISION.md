# B1 and BV harmonization decision — 25 September 2026

## Decision

**Yes: B1 footprint coverage and BV estimated vertical form can be constructed with common definitions in São Paulo and Chicago. Retain both in the planned Chicago and SP–Chicago model scope.** This resolves the question of whether a paired measurement method exists. It does not claim that mapped footprints or GHSL height are independently verified in every neighborhood, or authorize a model fit. Complete the source-accuracy gates below before accepting their values as model inputs.

| Family | Shared primary measurement | Source and role |
|---|---|---|
| B1 | Area of the exact union of mapped building footprints clipped to district hydrographic land, divided by that land area. Report the gross-area variant. | Matched Overture building release, 2026-08-19.0, in both cities. Microsoft footprints remain a diagnostic source. |
| BV | Area-weighted mean of valid GHSL ANBH 2018 net-height grid values over district hydrographic land, retaining observed zero. This is a mean over 100 m grid support, not an individual-building mean. | Same JRC GHSL R2023A/V1-0 product in both cities. GHSL AGBH is diagnostic; 2020 total volume is a same-family alternative. |

B1 and BV each receive **one family budget** in a future contract if accepted. Height, gross height and volume must not each receive an independent full BV weight. The removed M2 weight is not transferred automatically. BV does not supply B2 reported floors or B3 constructed floor area; those remain separate unresolved source questions.

## Evidence for feasibility

- [H1–H3 paired construction](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md) covers all 96 SP districts and 77 Chicago Community Areas. B1 has one paired value per unit; GHSL has three products on both gross and land support. Both use the same conceptual district land mask, with source geometry transformed to each calculation's CRS. Numeric land areas vary with projection: the observed B1-versus-BV relative area difference is at most 0.1542% in Chicago and 0.4903% in SP. Those area numbers should not be treated as identical across projections; the underlying support and masks, not their projected area values, must be reviewed.
- Full-run receipts report **176/176** footprint bounds/reconstruction checks and **1,211/1,211** GHSL coverage/partition checks. The independent paired-table/source-cell audit was rerun for this decision: **31 passed, 0 failed**. The minimum BV ANBH valid-area fraction is effectively 1 in both cohorts; no candidate value is missing. These are construction checks, not field accuracy tests.
- The [eight-unit Microsoft pilot](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md) used the same B1 union/denominator formula. Microsoft minus Overture land coverage ranges from −2.28 to −0.87 percentage points across five Chicago units, but is −36.12 in Brás, −0.04 in Grajaú and +8.64 in Itaim Bibi. Microsoft is partly in Overture's lineage and cannot independently adjudicate which footprint source is complete.
- In the [H4 built-form review](../../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md), Spearman B1–ANBH correlations are 0.511 in SP and 0.537 in Chicago. Height–volume correlations are 0.953 and 0.933, respectively. The first pair suggests B1 and BV carry distinguishable variation; the latter supports one BV family budget. Correlation alone does not establish satellite accuracy.

## Remaining acceptance gates and next work

1. **B1 independent source check:** in a bounded, preselected set of dense, residential, industrial and peripheral areas in both cities, compare Overture polygons against local imagery/building references. Include Brás, Loop, O'Hare and one SP peripheral area. Record omission/commission cases and whether B1 conclusions change under plausible coverage bounds. Do not use the Microsoft pilot alone as ground truth.
2. **Common land support:** document the SP and Chicago hydrographic masks, vintages and district-edge treatment. Compare land and gross variants. Preserve the distinction between projected area distortion and a genuine support mismatch.
3. **BV plausibility:** inspect selected GHSL cells against independent building-height or local reference evidence in both cities; report observed-zero/NoData area, edge-cell allocation and the 2018 epoch. The 2020 volume product is related to the 2018 height surface, so it is a sensitivity rather than independent validation. The supplied Microsoft SP tiles have no positive heights and cannot serve as the paired height reference.
4. **Precommitted model sensitivity:** once the broader feature scope is settled, compare primary B1+ANBH with no-BV, volume-only BV under the same budget, gross-support variants and no-B1. Report contribution and rank changes without selecting a variant for attractive Brás analogues.

The B1/BV method gate is **passed**: matched definitions and complete paired candidate values exist. The independent source-accuracy and land-support gates remain **open**, so the current `strict_cross_city_accepted=false` flags and `fit_authorized=false` contracts remain correct. No citywide spatial rebuild is needed to answer this feasibility question.

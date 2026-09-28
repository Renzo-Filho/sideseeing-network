# Bounded Chicago M-family source and entity pilot — 25 September 2026

This is a **diagnostic sample**, not a new 77-area construction or an accepted M-family release. It tests whether the current inputs and candidate rules are credible enough to justify broader processing. No similarity model was fitted.

## Design and scope

Four Community Areas were selected reproducibly: divide the existing 77-area municipal M1 street-density values into quartiles, exclude the five already examined in the earlier paired morphology pilot (CHI:24/28/30/32/76), and draw one area from each quartile using seeds `20260925 + quartile`. [The selection file](sample_selection.csv) records **Archer Heights (CHI:57), Gage Park (CHI:63), Roseland (CHI:49) and Jefferson Park (CHI:11)**. This balances one known street-density axis; it is not a probability sample of every morphology, land use or neighborhood type. Loop (CHI:32) is added **only** as a targeted condominium stress case for M7, not a fifth random draw.

The M1/M6 check reads four rows from the previously released local and Overture candidate tables. M2–M4 read the prepared 53,687 selected Overture road records, 28,389 candidate connectors, 39,498 Chicago-intersecting Census blocks, and CMAP rail right-of-way category 1511; geometry construction and matching run only in the four selected areas and a 250 m edge buffer for blocks. M7 reads Cook assessor records for only the four selected areas plus Loop, then joins 62 sampled PIN10 groups to parcel, condo and residential records. The 81-record DuPage local parcel file was read solely to choose 10 class-stratified review rows. No citywide polygonization, parcel/entity count, or attribute rebuild occurred.

Reproduce from the repository root:

```bash
MPLCONFIGDIR=/tmp/chicago-m-sample-mpl .venv/bin/python analysis/scripts/pilot_chicago_m_samples_2026_09_25.py
.venv/bin/python analysis/scripts/pilot_chicago_m7_entities_2026_09_25.py
.venv/bin/python analysis/scripts/validate_chicago_m_sample_2026_09_25.py
```

The final validation reports [five passed scope/arithmetic checks](validation.json). Every candidate junction pair and block polygon queued for physical review is explicitly `unreviewed`.
Coordinates in the M2 queue and WKT geometries in the M3/M4 queue are in **EPSG:26916** (metres).

## Findings

### M1/M6: source scope, not common class equivalence

The Overture-to-municipal mapped-street-density ratios in the four areas are **1.018, 0.999, 1.027 and 1.024** (selection order). Both M6 share vectors sum to one. Municipal code 99 has zero share in this sample; Overture `unknown` ranges from about 0.5% to 1.5%. These totals are close in these four places, but similar length does not establish identical roads or class labels. The airport outlier from the prior pilot was deliberately excluded by the new-sample rule. See [source comparison](m1_m6_source_diagnostic.csv).

### M2: source-linked candidates still need physical-arm labels

The four areas contain **1,468** selected connector candidates and **13** pairs within 10 m. **12/13** near pairs have a short eligible source-road link under the prior 20 m rule. The source-link test produces **51** short links overall and **43** linked components, of which **one** exceeds 35 m diameter. [Counts](m2_sample_summary.csv) and a [13-pair annotation queue](m2_annotation_queue.csv) are saved with coordinates, source arm counts and link IDs.

The 12/13 figure is **not** physical-junction accuracy: linked nearby connectors may still represent separate intersections or grade contexts, and one unlinked near pair may be a true complex. The queued points need map/imagery annotation of junction identity and each physical arm before testing a consolidation rule.

### M3/M4: fewer slivers do not establish true blocks

Three boundary modes were tested per area: all mapped Overture streets, streets excluding `link` subclass, and the latter plus CMAP 1511 rail right-of-way polygon edges with rail-majority polygons withheld. The full [12-row table](m3_m4_sample_summary.csv) reports counts, narrow polygons, Census-reference IoU in both directions, M3 median/IQR log area and M4 median/IQR compactness and elongation. The [85-polygon queue](m3_m4_annotation_queue.csv) contains high/low reference overlap and narrow cases for later physical review.

- Excluding links removes **15, 0, 18 and 14** candidate enclosures in Archer Heights, Gage Park, Roseland and Jefferson Park. Narrow `<6 m` objects change **5→0, 1→1, 3→1 and 1→0**. Yet the share of Census reference blocks with best IoU ≥0.50 is unchanged or lower: **0.166→0.166, 0.110→0.110, 0.253→0.251 and 0.250→0.242**. A cleaner candidate set can therefore lose or merge reference coverage.
- Adding local rail right-of-way edges to the no-link mode creates **7** narrow objects in Archer Heights and **12** in Roseland; it does not consistently improve reference coverage. A rail parcel boundary is useful evidence, not a universal block boundary.
- M3 median log area changes little across the three modes, but M4 compactness IQR is sensitive: in Archer Heights, all-street/no-link/rail modes are **0.092/0.007/0.104**; in Roseland **0.083/0.034/0.088**. Stable medians cannot validate the full M3/M4 family.

The reference is **Census 2020 tabulation blocks**, which can include non-street boundaries. IoU values are diagnostic, not an accuracy estimate against certified physical street blocks. The sample is selected on M1 only and cannot estimate a citywide failure rate.

### M7: tax identifiers and parcel geometries have different cardinalities

The [Cook sample](m7_sample_key_relations.csv) has **62** PIN10 groups selected across four property strata (condominium, commercial, exempt and other) in the four random areas plus Loop. All **17 condominium groups** have unequal assessor-PIN and parcel-feature counts. Targeted Loop examples include **1,286 tax PINs on one parcel feature**, **950 on one**, and **815 on three**. Three of the 62 groups have multiple parcel features. Condo `tieback_key_pin` counts also vary widely, so that field cannot be assumed to be a single physical parent without case review. The [five-unit source-count table](m7_selected_unit_source_counts.csv) gives context; its figures are tax-key diagnostics, not M7 entity counts.

The [DuPage queue](m7_dupage_stratified_queue.csv) contains 10 rows drawn by source class. The locally acquired 81 DuPage records have parcel geometry and classes but no verified improvement/parent identity. None of the Cook or DuPage sample rows has been assigned a physical-entity count.

## Decision and next bounded work

**M1/M6:** retain the existing local Chicago measures with source labels; the four-source comparison gives no reason to change them, but does not close coverage outside the sample.

**M2:** annotate the 13 saved near pairs against source-level road context and independent imagery. Add separated, ordinary T and grade cases deliberately; near-pair sampling alone cannot test false negatives. Record expected physical arms, then compare threshold and grade-aware consolidation rules.

**M3/M4:** annotate a manageable subset of the 85 saved polygons, prioritizing the narrow and low-IoU cases plus large campuses/rail barriers. Confirm whether each is a physical block and identify missing enclosing edges. Do not select a boundary mode by candidate IoU alone; check reference-to-candidate recall and M4 shape tails.

**M7:** review selected condo, elevated parcel, commercial and exempt groups on parcel maps and assessor records. Establish parcel↔PIN↔condo parent↔building cardinality for each. Request new parent/improvement data only for relationships unresolved by these cases. The single PIN10 and `tieback_key_pin` fields are not yet accepted physical-entity identifiers.

No M2/M3/M4/M7 family is promoted by this sample. Source years and observation universes remain as documented in the [Chicago 13-family ledger](../../../../docs/chicago/CHICAGO_13_FAMILY_COMPLETION_LEDGER.md) and [entity decision brief](../../../../docs/chicago/ENTITY_SOURCE_DECISION_BRIEF.md).

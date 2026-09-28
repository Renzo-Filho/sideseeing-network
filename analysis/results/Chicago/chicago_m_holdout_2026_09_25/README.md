# Chicago M2–M4 held-out cases and Cook parent-source check — 25 September 2026

## Design and reproducibility

This follow-up tests the conclusions of the [first physical-case audit](../chicago_m_physical_cases_2026_09_25/README.md) on a second **small, frozen set**. [Selection](case_selection.json) was written before image retrieval. It contains three unused near-pair cases, two isolated source-three-arm controls, seven unused block-queue cases and the previously documented Loop stacked-road **negative control**. Thus 12 cases are new to visual review and one is deliberately reused as a known grade-control fixture. All cases are purposive contrasts from four previously sampled Community Areas plus the Loop; they cannot estimate district or citywide error rates.

Reproduce from repository root:

```bash
.venv/bin/python analysis/scripts/select_chicago_m_holdout_2026_09_25.py
.venv/bin/python analysis/scripts/audit_chicago_m_physical_cases_2026_09_25.py \
  --case-file analysis/results/Chicago/chicago_m_holdout_2026_09_25/case_selection.json \
  --out-dir analysis/results/Chicago/chicago_m_holdout_2026_09_25 \
  --work-dir analysis/work/chicago_m_holdout_2026_09_25
.venv/bin/python analysis/scripts/evaluate_chicago_m_holdout_2026_09_25.py
.venv/bin/python analysis/scripts/audit_cook_parent_publication_2026_09_25.py
```

Thirteen small chips come from the [Cook County 2025 orthophoto service](https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer/info/iteminfo). Marker coordinates use the service's returned image extent; [image receipts](imagery_receipts.json) contain request URLs, extents and hashes. [Junction](H_M2_contact.jpg) and [block](H_M3_contact.jpg) contact sheets permit case review without distributing all raw images. The [single-reviewer labels](visual_case_labels.csv) are provisional; 2025 aerial cover cannot establish legal turning permissions, underground roads or cadastral ownership. Cached raw responses remain under ignored `analysis/work/`.

## M2: plausible arm count, with explicit grade control

| Case | Source topology | Provisional physical reading | Method implication |
|---|---|---|---|
| H_M2_01 | Linked pair, 6.05 m, source arms 3+4 | One broad surface crossing, **five** visible approach corridors tentatively | `3+4−2=5` matches, but wide-lane treatment remains uncertain. |
| H_M2_02 | Linked pair, 5.56 m, source arms 3+3 | One four-arm surface crossing | `3+3−2=4` matches. |
| H_M2_03 | Linked pair, 8.54 m, source arms 4+3 | One branching crossing, **five** visible approaches tentatively | `4+3−2=5` matches, subject to a fixed diagonal-arm convention. |
| H_M2_04/05 | Isolated source-three-arm connectors | Two visible T junctions, three street approaches each | Source arm count agrees in these ordinary controls. |
| H_M2_06 | Previously documented Loop pair, 2.49 m apart | Upper and lower road junctions are distinct | Upper `+1` bridge and lower `−1/−2` covered levels forbid a distance merge. |

The [rule-check table](heldout_rule_checks.csv) and [validation](validation.json) show that the simple `arms(A)+arms(B)−2` hypothesis agrees with all **three provisional** new linked-pair labels. This is **not** a tested general consolidation algorithm: it assumes exactly one joining span, same-level physical continuity and independently recognizable external arms. The Loop control refutes distance-only merging. The prepared road view omits some raw segment `level_rules`; [Overture's level and flag rules](https://docs.overturemaps.org/schema/reference/transportation/types/level_rule/) can be scoped to a portion of a segment. Next implementation should use raw scoped levels and connectors, then be tested on randomly drawn ordinary, divided, ramp and stacked cases with a second reviewer. M2 remains **constructible in principle, not accepted**.

## M3/M4: simple size/width cleanup fails one held-out stress case

Before viewing these seven cases, we froze a provisional rule suggested by the first audit: retain a candidate only if area is at least **1,000 m²** and minimum rectangle width is at least **15 m**. This is a deliberately simple *test hypothesis*, not an approved block definition.

Three candidates appear to be whole street-bounded land units: a commercial site (H_M3_02), a mixed residential/commercial block (H_M3_05) and a ballfield/open-space block (H_M3_07). Three small candidates are an interchange island or rail-related street fragments (H_M3_01/03/06). The rule correctly partitions those six **selected** cases. **H_M3_04 is the counterexample:** at 2,462 m² and 34 m minimum width it passes the size rule, yet the polygon cuts through an industrial yard and parking area without a surrounding public-street boundary. Its rail-ROW-derived mode and low Census IoU were diagnostic flags, but neither supplies a universal rejection rule.

Thus the frozen rule agreed with six of seven purposive labels and had **one false retention**; 6/7 is not an accuracy estimate. M3's block population still needs an explicit ground-street, rail, internal-drive, traffic-island and open-space ontology. M4 must use exactly that accepted population. A size cutoff alone cannot establish the true boundaries or shape distribution. M3/M4 remain **constructible in principle, not accepted**.

## M7: public 2024 parcel service does not publish the needed parent links

The [publication audit](cook_parent_publication.json) queried only public service metadata and the seven earlier PIN10 cases. All **11** public 2024 polygon rows matched the installed 2024 extract by `OBJECTID`; [per-key reconciliation](cook_public_key_reconciliation.csv) confirms this. The source-key ambiguity is therefore not explained by a truncated local extract for these cases. The official [2024 parcel service](https://gis.cookcountyil.gov/traditional/rest/services/parcelHistorical/MapServer) reports **no tables**, its [2024 parcel layer](https://gis.cookcountyil.gov/traditional/rest/services/parcelHistorical/MapServer/2024) reports **no relationships**, and that layer has neither `REF_PIN` nor `POLYTYPE` among its published fields. A separate [hosted 2022 parcel service](https://gis.cookcountyil.gov/hosting/rest/services/Hosted/Parcel_2022/FeatureServer) also reports no tables. This audit does not prove the underlying County Clerk tables do not exist; it shows these tested public endpoints do not expose them.

The [Clerk's parcel metadata](https://gis12.cookcountyil.gov/arcgis/rest/services/CookViewer3Dynamic/MapServer/2024/iteminfo) describes a master PIN table and `REF_PIN` link needed where one map polygon represents multiple parcels, including condos and elevation-specific parcels. The [Assessor's open-data guide](https://datacatalog.cookcountyil.gov/stories/s/Assessor-2025-Open-Data-Refresh/gzdr-q7c4/) describes condominium units sharing the first ten PIN digits as **typically** being in the same building. That is useful for a targeted condo-building sensitivity, but it does not supply a universal legal parcel, improvement or all-stock physical-entity key. In the seven cases, polygon `Name`/PIN14 is duplicated across both overlapping and disjoint features; it does not resolve the parent relation.

For original M7, the smallest source request is a **2024-vintage, PIN14→REF_PIN→parcel-feature crosswalk**, the condo and elevation-specific relationship tables with their field dictionary, parcel/`POLYTYPE` semantics and explicit permission for analytical use. Use the seven recorded PIN10 cases as test fixtures and request a small extract first. If that relation is unavailable, a *distinct ground-parcel-piece count* is a different estimand requiring an explicit user decision and its own paired São Paulo method. We have **not** promoted original M7 or treated PIN10 as a guaranteed physical entity.

## Gate outcome

No 77-area rebuild, São Paulo paired construction or model fit occurred. The new M2 examples support a grade-aware consolidation design but do not validate it; M3/M4 gain a direct counterexample to area-only cleanup; the exact public Cook services tested cannot supply the M7 parent mapping. Next work is a **small method prototype and independent review** for M2/M3/M4, plus a targeted parent-table request or a declared M7 pivot.

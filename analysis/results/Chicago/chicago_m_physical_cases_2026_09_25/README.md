# Chicago M2–M4 and M7 targeted feasibility audit — 25 September 2026

## Question and scope

Can the unresolved Chicago morphology and cadastral families be constructed from the installed sources without mistaking source records for physical entities? This is a **bounded diagnostic**, not a citywide run or acceptance test. It follows the [four-area source sample](../chicago_m_sample_2026_09_25/README.md). The four M2 and six M3/M4 cases were frozen in [case_selection.json](case_selection.json) **before** viewing imagery. They intentionally contrast awkward and ordinary cases; the resulting fractions are not error rates. Seven previously sampled Cook PIN10 groups were selected for source-key and geometry checks. No DuPage entity conclusion follows from these Cook cases.

The scripts are [physical imagery audit](../../../scripts/_archive/chicago_m_pilots_2026_09_25.zip) and [M7 relation audit](../../../scripts/_archive/chicago_m_pilots_2026_09_25.zip). Reproduce with:

```bash
.venv/bin/python analysis/scripts/audit_chicago_m_physical_cases_2026_09_25.py --select-only
.venv/bin/python analysis/scripts/audit_chicago_m_physical_cases_2026_09_25.py
.venv/bin/python analysis/scripts/audit_chicago_m7_case_relations_2026_09_25.py
```

The image script requested ten 800×800 chips from the official [Cook County 2025 orthophoto service](https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer/info/iteminfo), centered on saved EPSG:26916 queue coordinates. The service expands requested WGS84 boxes to square pixels; all marker/polygon overlays use each image's **returned extent**, obtained through its JSON response. Its [receipts](imagery_receipts.json) record query URLs, returned extents and SHA256 values. Raw/overlay chips are cached in `analysis/work/chicago_m_physical_cases_2026_09_25/`; compressed [M2](M2_contact.jpg) and [M3/M4](M3_contact.jpg) contact sheets are preserved here. The [labels](visual_case_labels.csv) are a single reviewer's provisional interpretation of 2025 surface imagery against Overture road data acquired 19 August 2026 and 2020 Census reference blocks. Imagery does not prove grade, turn permissions, legal parcel identity or a surveyed boundary.

## M2: physical junction density

| Preselected case | Source relation | Visual reading | Consequence |
|---|---|---|---|
| M2_01, Archer Heights | Short Overture link; two markers 9.29 m apart | Large road/rail interchange with bridge-flagged ramps; physical arms and levels ambiguous | Do not merge from proximity or link alone. |
| M2_02, Roseland | Short link; 5.18 m apart | Both markers are within one ordinary surface crossing | A merge is plausible. |
| M2_03, Jefferson Park | Short link; 7.18 m apart | Both markers are within one local crossing beside expressway/rail infrastructure | A surface-road merge is plausible; nearby grade-separated lines are not its arms. |
| M2_04, Jefferson Park | **No** short link; 7.75 m apart | Both markers are within one diagonal surface crossing | A link-only rule would miss this likely consolidation. |

The earlier [Loop stacked-road fixture](../../SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md) supplies a complementary negative control: two connectors just 2.49 m apart belong to upper `+1` bridge and lower `-1`/`-2` covered roads. Overture [level rules](https://docs.overturemaps.org/schema/reference/transportation/types/level_rule/) and [road flags](https://docs.overturemaps.org/schema/reference/transportation/types/road_flag_rule/) can apply to part of a line. The current prepared road view retains `road_flags` but not every source `level_rule`, so a grade-aware decision may need the raw segments. **Feasibility:** the installed Overture source can support a prototype that uses connector incidence, local geometry and scoped grade attributes. This review does not establish physical arm counts or a validated consolidation rule. M2 remains **possible, unaccepted**.

## M3/M4: block grain and shape

The [visual labels](visual_case_labels.csv) mark two large candidates as plausible street-bounded land blocks (a school campus in Gage Park and a residential block in Jefferson Park). Four deliberately difficult candidates are unsuitable under a provisional **neighborhood land-block** definition: a 9.8 m² paved interchange fragment, a 15.2 m² rail-edge fragment, a 50.4 m² crossing fragment and a 568.2 m² turn-lane/traffic-island polygon. The last object is real road-bounded land; excluding it is an **ontology decision**, not an imagery error. We must state whether traffic islands and similar non-neighborhood land count.

The prior [four-area quantitative sample](../chicago_m_sample_2026_09_25/README.md) found that removing `link` streets reduces narrow candidates in three areas but does not improve Census-reference recall. Adding local rail right-of-way edges produces new tiny slivers. The two high-IoU cases in this visual sample are plausible blocks, but Census IoU is only a diagnostic and the selected images cannot set a defensible minimum-area cutoff. **Feasibility:** true blocks and their shapes can be measured after the boundary ontology and extraction/filter rules are fixed. Current polygonization does **not** yet produce a validated M3/M4 distribution; both remain **possible, unaccepted**.

## M7: physical cadastral entity

The [seven-case key table](m7_case_key_relations.csv) and [within-PIN10 geometry pairs](m7_case_parcel_pairs.csv) reveal distinct relationships:

| PIN10 | Tax PINs / parcel features | Geometry relation | Why a simple count fails |
|---|---:|---|---|
| `1716238028` | 1,286 / 1 | Condominium parcel; five distinct condo tieback keys | Tax PINs are units/records, not 1,286 land entities. |
| `1710400048` | 950 / 1 | Condo table has 934 rows and 934 distinct tieback keys | Tieback count is not a stable building/parent count. |
| `1710318058` | 815 / 3 | One typed condo feature plus two `PARCELTYPE`-null features; pair IoU 0.51–0.70 | Counting all three double counts much of the mapped land. |
| `1709419111` | 1 / 2 | 40.1 m² elevated feature fully overlaps the base feature | A stacked parcel geometry can add a record without new ground area. |
| `1903201036` | 1 / 2 | Two base features are disjoint, 20.1 m apart | One PIN10 can also span distinct ground pieces. |

Two simpler controls are one ordinary PIN/one base feature (`1308208021`) and 16 condo PINs/one condo feature (`1308311047`). The Assessor's downloaded [condo source metadata](../../../data/Chicago/chicago_cadastral_2026_09_18/cook_condo_2024/source_metadata.json) defines `tieback_key_pin` as the key PIN for **prorated property value**, and `char_building_pins` as a **count** of condominium building parcels. Neither is documented as a physical-building or legal-parent ID. The official [Cook 2024 parcel layer](https://gis.cookcountyil.gov/traditional/rest/services/parcelHistorical/MapServer/2024) exposes `PIN10`, `Name`/PIN14 and `PARCELTYPE`, but its published description also refers to separate PIN, Ref_PIN and condo tables. Its layer metadata declares no exposed relationships (`relationships: []`); those tables are not in our downloaded polygon extract.

**Feasibility:** a transparently named alternative such as *distinct ground parcel pieces* could be piloted from this source with overlap handling and explicit exclusion of elevated layers. It would change M7's original physical cadastral entity meaning and still require disjoint/multipart rules. The original M7 **cannot yet be constructed defensibly** from the installed extract alone. Next inspect the Clerk's 2024 PIN/Ref_PIN/condo relationships for these seven keys and corroborate condo parent and improvement counts with assessor or recorded condominium documents. Then test DuPage separately. Do not use `PIN10`, `tieback_key_pin`, polygon count or Microsoft building footprints as an unqualified parent-entity key.

## Decision and next small validation

| Family | Can a number be computed now? | Can the intended measure be accepted now? | Smallest next evidence |
|---|---|---|---|
| M2 | Yes, as a connector/topology candidate | **No** | Label physical arms in ordinary, divided, ramp and stacked fixtures; preserve scoped grade information; compare rules on held-out cases. |
| M3/M4 | Yes, as polygon/shape candidates | **No** | Lock block ontology, annotate representative and edge cases, then check both precision and reference recall in the same four areas. |
| M7 | Yes, for tax PINs or raw parcel geometry counts | **No** for original physical entity | Retrieve parent/related-PIN records for selected Cook cases; verify disjoint, overlapping and condo groups; test DuPage separately. |

No 77-area rebuild or 13-family model fit was run. The labels are purposive, single-reviewer observations; they do not estimate Chicago-wide error or settle São Paulo comparability. This audit adds local counterexamples and a specific data request, not a pass through the common-model acceptance gate.

The [next frozen case set and public parent-source check](../chicago_m_holdout_2026_09_25/README.md) tests a simple arm formula and block-filter hypothesis and checks the exact Cook parcel REST services for parent-table availability. Its observations remain diagnostic.

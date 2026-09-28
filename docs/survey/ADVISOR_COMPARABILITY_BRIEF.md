# Comparing São Paulo and Chicago: what requires harmonization, and what we have already resolved

**Advisor brief · Revised 24 September 2026 · Evidence through 23 September**

## Answer first: can we build the 13 families?

**Several are already calculated. The unresolved question is whether their numbers represent sufficiently similar things to support the intended comparison.** The project has 13 *feature families*: groups of measurements about one characteristic. For example, block shape includes both compactness and elongation. Thus, 13 families does not mean 13 numerical columns.

| Current position | Original families | What this means |
|---|---|---|
| Paired candidates constructed and retained in the six-family proposal | **M1, M6, B1, U3, U4** | Common calculation rules exist across both cities. Specific source-coverage, date and interpretation checks remain. |
| Physical-object definitions unresolved | **M2, M3, M4** | We can calculate junction and polygon statistics, but have not validated that the objects consistently represent physical junctions and blocks. |
| Common cadastral/floor-area definitions unsupported by current evidence | **M7, B2, B3** | SP measurements and partial CHI inputs exist. Chicago’s available records do not yet establish equivalent counting units and property coverage. |
| Functional comparison unresolved | **U1, U2** | Local use/job values and pilot alternatives exist; their categories, weighting, employment coverage or geographic assignment need reconciliation. |

The **six-family proposal is M1 + M6 + B1 + BV + U3 + U4**: five original families plus a new vertical-form family, BV. It has a complete numerical input table for **96 SP districts and 77 CHI Community Areas**. It addresses several original problems and provides a narrower route forward. It does **not** complete the eight omitted families. Neither proposed common model has been fitted or scientifically accepted. [Current status](../MODEL_STATUS.md) · [Six-family review](../chicago/SIX_FAMILY_PLAN_REASSESSMENT.md)

## The distinction that matters

**Harmonization** means agreeing what is measured and making both datasets implement that definition: which objects count, which categories belong together, how locations are assigned, and which dates are represented. Different sources can be used if these meanings are reconciled.

**Standardization** puts comparable measurements on a common numerical scale. For example, a *z-score* expresses distance from a reference mean in standard-deviation units. It cannot make apartment tax records equivalent to parcels. Our proposed model uses scales learned from SP and applies the same scales to CHI; independently rescaling each city would instead express position relative to different reference populations.

Three recurring terms are useful: **coverage** is how much of the intended population or area the source represents; **spatial support** is the area or object to which a value refers, such as a parcel or Census block; **sensitivity analysis** checks how results change under another reasonable rule. Gross district area includes water; land area subtracts mapped water. Changing that denominator changes a density or coverage measure.

Below, **observed** examples come from project audits; **illustrations** are hypothetical explanations, not measured errors. Each section separates the original problem from progress already made.

## M1 — Street density

**Objective.** Measure how much mapped street length exists per km². More length indicates a denser mapped street fabric, but does not by itself establish walkability or public access.

**Data acquired.** SP: municipal street lines and road classes. CHI: municipal street centerlines. Both: the same Overture road release, a common map dataset.

**Original comparability problem.** A street may be mapped as one centerline or as separate lines for its two carriageways—the roadways carrying traffic in opposite directions. Sources also differ in whether they include access roads, tracks or airfield lines. Equal kilometres need not describe equal sets of streets.

**Observed example.** O’Hare’s municipal network has **141.2 km of class 99**, much inside the airfield; only 20.7% lies within 15 m of eligible Overture streets. Including this entire class as ordinary streets changes what density measures.

**Current position.** **Retained in the six-family proposal.** Matched Overture data and shared inclusion/length rules address the original source-policy mismatch. Local mapping completeness, especially at O’Hare and rural Marsilac, still needs review. [Road audit](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md)

## M2 — Junction density

**Objective.** Count physical junctions with at least three street arms per km². An *arm* is a street approach to a junction: a simple T junction has three.

**Data acquired.** SP: municipal crossings and bridge/tunnel geometry. CHI: municipal nodes and road-level information. Both: Overture segments and connectors, the points used to connect mapped road segments.

**Original comparability problem.** A crossing on a flat map may be a bridge above another road, without a connection. Conversely, several map nodes may describe one divided-road junction. Counting every crossing or every connector measures different objects.

**Observed example.** Two Loop connectors are **2.49 m apart** but belong to different road levels. A distance-only rule would wrongly combine them. Proximity alone cannot establish one physical junction.

**Current position.** **Outside the six-family proposal.** Diagnostic counts exist; a shared physical-junction method remains unresolved. Omitting M2 avoids using those counts but loses direct information about junction structure. [Junction audit](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md)

## M3 — Block size

**Objective.** Describe typical block area and variation. The *median* is the middle value; the *interquartile range* spans the middle 50%. We summarize logarithms of area to reduce the influence of very large blocks.

**Data acquired.** SP: municipal *Quadra* block polygons. CHI: polygons generated from road lines and Census blocks as comparison references. Both: road, rail and water boundary experiments.

**Original comparability problem.** A closed polygon generated by map lines is not necessarily a physical urban block. Individual rail tracks, ramps and divided roads can create artificial narrow polygons; municipal and Census block boundaries also follow different conventions.

**Observed example.** Adding rail centerlines in Near West Side changed candidate enclosures from **765 to 1,404**, with polygons narrower than 6 m increasing from **5 to 359**. The algorithm changed the apparent block population without any urban change.

**Current position.** **Outside the six-family proposal.** Block-size statistics are computable, but a common physical-block population is not validated. [Boundary experiment](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers/README.md)

## M4 — Block shape

**Objective.** Measure *compactness*, how concentrated rather than stretched or irregular a shape is, and *elongation*, the ratio of long to short sides of its enclosing rectangle.

**Data acquired.** The same SP block polygons and CHI generated/reference polygons as M3.

**Original comparability problem.** Correct formulas cannot repair incorrect block boundaries. Splitting one block into several objects or cutting it at a district boundary changes its shape statistics. M4 therefore depends on resolving M3.

**Illustration.** Compactness is `4π × area / perimeter²`. A 100 × 100 m square scores **0.785**. An artificial division into two 50 × 100 m rectangles gives **0.698** each; elongation changes from 1 to 2. Identical land appears less compact and more elongated.

**Current position.** **Outside the six-family proposal.** Shape calculations exist, but their physical interpretation needs common block identities and perimeter rules. [Definitions and acceptance conditions](../chicago/CHICAGO_13_FAMILY_COMPLETION_LEDGER.md)

## M6 — Street hierarchy composition

**Objective.** Describe the share of total mapped street length in each road class, such as major roads and residential streets. These shares sum to one and together form one family.

**Data acquired.** SP and CHI municipal classifications; matched ten-class Overture road data.

**Original comparability problem.** A *taxonomy* is a classification system. Municipal taxonomies do not necessarily assign the same meaning to road classes. *Imputation* means filling a missing value by assumption; different imputation policies also change class shares.

**Observed example.** **23.85% of SP’s legacy street length was assigned to Local by assumption.** Comparing this with a source that keeps unclassified records separate would partly compare missing-data policies rather than street hierarchy.

**Current position.** **Retained in the six-family proposal.** Both cities now use ten common classes without that imputation. Overture’s known lower-order `unclassified` class remains separate from genuinely undetermined `unknown`. This resolves a concrete definition problem; geographic coverage still needs review. [SP rule](../sp/ATTRIBUTE_DOCUMENTATION.md) · [Shared rule](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md)

## M7 — Cadastral entity density

**Objective.** Measure physical property subdivision through accepted cadastral entities per km². A *cadastre* is a property register; its tax identifiers are not automatically physical parcels.

**Data acquired.** SP: IPTU property-tax records and parcel geometry. CHI: Cook County parcels, assessor identifiers and condominium relationships, plus limited DuPage parcel data.

**Original comparability problem.** One physical property may have many apartment tax accounts; one parcel may contain several buildings. A common count needs rules linking these records without treating each account as another physical entity.

**Illustration.** A condominium with 100 separately taxed apartments could count as **one physical entity or 100 tax records**. That difference reflects registration practice, not 100 times more physical subdivision.

**Current position.** **Outside the six-family proposal.** A common entity definition and verified record relationships are still needed. Neither building footprints nor BV grid height identify legal property subdivision. [Entity audit](../chicago/ENTITY_SOURCE_DECISION_BRIEF.md)

## B1 — Building footprint coverage

**Objective.** Measure the fraction of land covered by buildings when viewed from above. A *footprint* is a building’s mapped ground outline; taking the *union* counts overlapping mapped areas only once.

**Data acquired.** Both cities: Overture and supplied Microsoft footprints, plus water maps. CHI also has municipal/Cook footprint sources.

**Original comparability problem.** Different maps detect different buildings and represent different dates. Different water masks also change the land denominator. Matching the formula does not guarantee equal mapping completeness.

**Observed example.** On the same Brás land area, coverage is **20.46% with Microsoft and 56.58% with Overture**. The 36.12-percentage-point difference shows source dependence; it does not establish which map is correct.

**Current position.** **Retained in the six-family proposal.** Paired Overture union calculations already address source selection, overlaps and calculation consistency. Local completeness and water-boundary sensitivity remain. B1 is a constructed mapped-coverage candidate, not an unavailable feature. [Footprint pilot](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md)

## B2 — Reported floors

**Objective.** Describe typical and upper-tail reported floor counts: the median and *90th percentile*, the value at or below which approximately 90% of eligible reports fall. Each accepted entity contributes one observation.

**Data acquired.** SP: IPTU floor reports. CHI: municipal stories and Cook property characteristics. Both have partial Overture floor attributes.

**Original comparability problem.** Reports refer to different entities and subsets of properties. Some Chicago stories are *top-coded*: values above a threshold share one category. Missing commercial/condominium reports can also make the observed sample unrepresentative.

**Observed issue; illustrative consequence.** Cook has **32,525 “3 Story +” records**. Treating that category as exactly 3 makes a hypothetical ten-story property indistinguishable from a three-story one, distorting upper-tail statistics.

**Current position.** **Outside the six-family proposal.** BV supplies estimated height, not reported floors. Converting metres to floors using one assumed floor height would introduce another unvalidated measurement. [Property audit](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md)

## B3 — Constructed floor-area intensity

**Objective.** Sum eligible constructed floor area across unique fiscal units, then divide by district land area. Unlike B1, this includes space on multiple floors; the ratio can exceed one.

**Data acquired.** SP: IPTU constructed area. CHI: residential area, condominium unit/parent-building area, commercial building/rentable area and limited large-property benchmarking data.

**Original comparability problem.** *Gross* building area and *rentable* area include different spaces. Repeated parent-building totals can be counted several times through apartment records. Coverage of property types also differs. Unit conversion cannot fix these definitions.

**Illustration.** A building with **10,000 m² gross area and 7,000 m² rentable area** appears 30% smaller if the second source reports only rentable space, despite identical physical construction.

**Current position.** **Outside the six-family proposal.** No equivalent Chicago quantity covering the intended property stock is established. BV volume measures cubic metres, not square metres of floor space. [Area/entity audit](../chicago/ENTITY_SOURCE_DECISION_BRIEF.md)

## U1 — Land-use diversity

**Objective.** Describe the mix of functions such as housing, commerce and industry. *Entropy* summarizes how evenly a selected set of use categories is represented; its meaning depends on the categories and weights.

**Data acquired.** SP: IPTU entity-use labels. CHI: regional planning agency CMAP’s 2023 land-use polygons. Small tests also use OpenStreetMap (OSM) and Overture points of interest (POIs: mapped destinations).

**Original comparability problem.** SP’s primary measure counts entities; CHI’s weights land area. **Illustration:** nine small residential parcels and one factory covering half the land are 90% residential by count but only 50% by area. Both calculations are correct and answer different questions.

**Observed example.** Even after switching to area weights, Brás/Loop diversity changes from **0.706/0.735** under six classes to **0.774/0.662** under four occupied-use classes, reversing the order. Those four classes cover only **54.6%/34.3%** of district land. Unknown and excluded land cannot silently become classified use.

**Current position.** **Outside the six-family proposal.** Area-based alternatives remain under review. In the 23 September case audit, a broad OSM residential polygon included a Chicago alley: adding coverage did not automatically supply equivalent use information. POI diversity would describe destinations, not replace land-area diversity. [Use pilot](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md) · [Case audit](../../analysis/results/SP_CHI/u1_independent_cases_2026_09_23/README.md)

## U2 — Workplace employment density

**Objective.** Measure workplace job links per km². A *job link* is an employment relationship; a person can hold more than one. This indicates employment concentration, not household income or socioeconomic status generally.

**Data acquired.** SP: RAIS 2022 formal employment, with postal-code, address and fiscal information for locating jobs. CHI: LODES 2022 workplace job totals by Census block, with CMAP land-use allocation support.

**Original comparability problem.** The employment sources do not establish identical worker/job coverage. Many records also lack exact workplace locations. *Allocation* distributes an aggregate total across districts using weights, such as business area or establishment addresses; conserving the total does not prove correct placement.

**Observed example.** Switching SP from area-first to address-first allocation redistributes **275,226.71 job links**; 11 districts change by over 10%. Another **508,844 jobs remain unlocated** under the primary policy. These are uncertainty indicators, not measured allocation errors.

**Current position.** **Outside the six-family proposal.** Job-density candidates exist in both cities; common interpretation remains unresolved. Resident density U3 cannot substitute for workplace concentration. [Allocation experiments](../sp/SP_METHOD_DECISIONS.md)

## U3 — Population density

**Objective.** Measure residents per district km², indicating residential intensity.

**Data acquired.** SP: IBGE Census 2022 population and sector boundaries. CHI: Census 2020 population and block boundaries. These smaller census areas supply the district totals.

**Original comparability problem.** This is one of the closest shared concepts, but the observations are two years apart. Where census areas cross district borders, population must be allocated; area-proportional allocation assumes people are spread uniformly within each source area.

**Illustration.** Two areas both contain 10,000 residents/km² in 2020. If SP grows 10% by 2022, the available figures are **11,000 versus 10,000**. That cannot establish a difference between the areas in 2020.

**Current position.** **Retained in the six-family proposal.** Common aggregation and density calculations are complete. An explicitly dated comparison is feasible subject to documented allocation/year limitations; different census years do not make U3 inherently unusable. [Paired population record](DATA_RESOURCE_SURVEY.md)

## U4 — Accessible bus supply

**Objective.** Estimate bus departures available near residents during a two-hour window. A *400 m catchment* is the straight-line area around a resident location used to identify nearby stops. Population weighting gives places with more residents more influence on the district average.

**Data acquired.** SP: frequency-based GTFS transit files and Census 2022. CHI: CTA scheduled GTFS and Census 2020. GTFS is a standard format for routes, stops and service times.

**Original comparability problem.** A frequency such as “every ten minutes” gives expected departures; a timetable lists scheduled ones. Neither measures actual operation. Transport modes, operators and calendar dates must also be aligned.

**Observed example, already corrected.** Legacy SP processing included metro/rail while CHI used buses. Filtering SP to buses lowered Brás weekday supply by **16.6%**, without any real service change.

**Current position.** **Retained in the six-family proposal.** Bus-only selection and shared nearby-service aggregation fix that mismatch. Frequency/schedule interpretation, operator scope, holiday exceptions and the one-week scenario-date gap still need explicit qualifications. [Paired correction](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md)

## What the six-family proposal actually solves

It makes three distinct kinds of progress:

1. **Repairs retained measurements:** M1/M6 adopt matched road data and common rules; B1 uses matched footprint-union processing; U3 uses an explicit shared aggregation/density definition; U4 removes the mode mismatch and aligns aggregation. These are substantive harmonization steps already implemented.
2. **Adds a different vertical measure:** **BV uses GHSL, the Global Human Settlement Layer**, with estimated height on a 100 m grid. Both cities use the same 2018 height product and aggregation rule. This avoids dependence on incompatible fiscal floor reports while recovering some information about vertical form. The result summarizes grid estimates, not individual buildings’ floors. A 2020 volume product is an alternative within BV, not another independently weighted family.
3. **Leaves unresolved concepts outside the proposed comparison:** it omits M2/M3/M4, M7/B2/B3 and U1/U2. This makes a smaller numerical model feasible, but it loses physical junction/block structure, property subdivision, reported floors, constructed area, land-use mix and workplace intensity. Those problems remain open.

The saved proposal has **173 complete rows, 15 raw columns and six family weights**: ten columns are M6 shares forming one family. Its **13/13 readiness checks** establish properties such as complete inputs, valid numerical ranges and consistent weights. They do not establish mapping accuracy, equivalent coverage or valid urban-similarity conclusions. Remaining review includes source completeness, grid estimates, dates, calendars and sensitivity to weights and definitions. [Six-family scope and conditions](../chicago/SIX_FAMILY_PLAN_REASSESSMENT.md) · [Numerical readiness evidence](../../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md)

**Illustration of the tradeoff:** two districts could match on roads, footprint coverage, height, resident density and bus supply while one is predominantly residential and the other has much more employment and commerce. The six-family model would have limited ability to distinguish that functional difference. Equal family weights also do not make the inputs independent: M1/M6 share roads, and U3/U4 share population information.

## Conclusion for the advisor

**The evidence supports harmonization, not a claim that all 13 families are impossible.** Several shared measurements have already been constructed; others need better definitions, source relationships or data. A numerical standardization step cannot perform those repairs.

The six-family proposal demonstrates a practical, partly harmonized route to a **structural, residential and bus-service comparison**. Its narrower scope must be stated clearly, and its remaining measurement checks must be addressed before fitting. It cannot yet support the original full urban-similarity claim. The next scientific decision is which remaining limitations are acceptable for that narrower question and which omitted characteristics must be recovered.

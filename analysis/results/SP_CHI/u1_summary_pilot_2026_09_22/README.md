# U1 bounded ontology screen — 22 September 2026

**Status: diagnostic, not an accepted U1 measurement.** This screen asks whether six broad source categories can be put into a common **area-weighted** distribution without hiding substantial source mass. It reuses the existing São Paulo area-weighted U1 sensitivity and Chicago CMAP area shares. It does not claim that fiscal primary use and observed CMAP land use are equivalent. No model was fitted or ranked.

## Sampling and computational boundary

`analysis/scripts/pilot_u1_summary_ontology.py` reads only three already-published small attribute tables: 96 SP district rows, 77 Chicago Community Area rows, and SP U1 coverage records. It uses the 173 summary rows **only to select contrasting neighborhoods**; the ontology calculation is saved for **six units per city**. Seed `20260922` fixes the selection. Each city includes Brás/Loop plus one random unit from each predeclared stratum: top quintile residential share, top quintile industrial share, top quintile proposed-excluded share, bottom quintile source coverage, and middle fifth of original entropy. Draws are without replacement. The selected IDs, names and strata are in [sampled_ontology_screen.csv](sampled_ontology_screen.csv).

No raw IPTU records, SP parcel geometries, the 607 MB Chicago LUI GeoPackage, or POI data were opened. The saved pilot is 16 KB. This is a low-cost **screen of existing summaries**, not a source-level map validation.

## Provisional six-category map

| Shared candidate | SP source category | Chicago source category | Main qualification |
|---|---|---|---|
| Residential | residential | residential | SP fiscal use versus CMAP observed parcel use. |
| Commerce/services | commerce/services | commercial | Chicago commercial includes some primary mixed-use codes. |
| Industrial | industry/warehouse | industrial | Warehouse inclusion and primary-use rules need inspection. |
| Institutional | institutional | institutional | Source definitions may differ. |
| Transport/utilities | transport/utilities | transport/utilities | SP includes garage/service labels; CMAP includes broad transportation land. |
| Vacant | vacant | vacant/construction | SP `Terreno` and Chicago vacant/under-construction are not identical. |

SP `mixed/other` and Chicago `open_space`/`agriculture` are **explicit unmatched residuals**, never reassigned to a convenient category. [The crosswalk file](proposed_category_crosswalk.csv) preserves these choices. `candidate_entropy6` renormalizes **only the six mapped shares** and divides Shannon entropy by `ln(6)`; it is a sensitivity indicator, not a validated cross-city U1 value. The original SP and Chicago entropies use seven and eight categories, respectively, so their numerical values are not directly comparable to this candidate.

## Findings from the 12 selected units

| Unit | Mapped six-category share of previously classified source mass | Explicit unmatched share | Candidate six-category entropy |
|---|---:|---:|---:|
| Brás (SP:10) | 79.2% | **20.8%** mixed/other | 0.713 |
| Loop (CHI:32) | 63.2% | **36.8%** open-space/agriculture | 0.735 |

Across the six selected SP units, the unmatched share ranges **8.4–21.2%** (median 15.3%). Across the six Chicago units, it ranges **1.0–36.8%** (median 6.4%). These deliberately stratified samples are **not citywide prevalence estimates**. The similar Brás/Loop entropy values above would conceal very different omitted mass; this simple six-category version must not enter a model unchanged.

Chicago's published `lui_classified_land` is classified CMAP area divided by district land. For the Loop it is 67.0%; combining that with the mapped six-category share yields about **42.3% of district land** in these six candidate classes. SP's published U1 area coverage is classified area divided by **accepted cadastral entity area**, not district land; Brás has 96.2% on that different basis. The SP area sensitivity also sums whole entity areas by assigned district, whereas Chicago intersects observed polygons with each district; the spatial allocation rule itself remains to be harmonized. Those percentages cannot be compared as source completeness. The SP accepted-entity union versus land denominator remains an open spatial-support check.

The small SP use dictionary shows that `mixed/other` includes labels with declared residential or commercial predominance as well as genuinely broad labels. Chicago's current aggregate commercial group includes mixed-use codes. A consistent **dominant-use** rule could recover some mass, but needs raw-code and matched-map checks before recomputation. Open space is a separate conceptual choice: ignoring it narrows U1 to classified developed/vacant use, while treating it as SP `Terreno` would conflate unlike meanings. Local SP zoning files exist, but zoning is not observed use. The local inventory has no verified paired POI dataset.

## Next bounded validation, before any citywide job

1. **Set the target question:** all-land use mix including open space, or developed-land primary-use mix? Specify whether mixed-use is its own class or assigned by documented dominance. Keep unknown/unmapped land outside entropy and report its area.
2. **Inspect source labels and maps in a small subset:** Brás and Loop plus one selected residential and one industrial unit per city (six units total). Draw a fixed-seed mix of area-proportional land points and uniform source polygons, capped at **20 of each per unit**. Record source code, inferred broad use, overlap/unknown status and independently inspected reference evidence. Stop or enlarge the sample only for a stated ambiguity; do not process all 173 units.
3. **Check the SP land denominator on those same units:** union accepted entity polygons, intersect with district land, and report classified/unknown/unmapped land separately. Compare Chicago CMAP classified support on the **same denominator concept**. Use partitioned SP district files and Chicago bounding-box reads; avoid citywide raw scans.
4. **Keep POI diversity as a distinct option.** No paired POI source is currently saved locally. If pursued, select one common release/taxonomy and obtain only tiles around the same sampled units, then inspect duplicates, category coverage and residential/industrial omissions. POI diversity would describe **destinations**, not land-use area.

**Decision:** the coarse area-weighted route remains promising, but this naive crosswalk leaves enough unlike source mass at the Brás/Loop anchors that it cannot be accepted unchanged. No U1 family acceptance or model fit follows from this pilot. See [OPEN_DISCUSSION.md](../../../../docs/DECISIONS.md) for the research choices and [checks.json](checks.json) for arithmetic/source receipts.


**22 September follow-up:** The source-level portion of the next bounded validation was run for the six selected units; see the [three-option sample](../u1_source_samples_2026_09_22/README.md). Its source labels still lack independent truth review, and its land-point sample is too small to replace exact district-clipped coverage. The four steps above remain the original screening plan, with those limitations now specified by the follow-up.

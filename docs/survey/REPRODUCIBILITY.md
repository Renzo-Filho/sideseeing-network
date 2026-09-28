# Reproduction and independent-validation protocol

This page is a practical method for reproducing the existing evidence and extending it without an accidental 173-unit rebuild. Work from the repository root with the project's `.venv`; follow each linked report's frozen config, source manifest and output directory. The commands below are **examples of bounded tests**, not a new global pipeline. Read the [experiment ledger](EXPERIMENT_LEDGER.md) before deciding which checkpoint to repeat.

## 1. Freeze the claim before executing

For every new test, write down: question, estimand, source universe and version, reporting-unit IDs, sampling frame, seed, selection strata, numerator, denominator, geographic projection/assignment, source and output hashes, null codes, exclusion rules, and the exact falsification or acceptance criterion. Keep “unobserved,” “source-unclassified,” “mixed,” “outside geography,” and “not applicable” as different states. Save code and environment versions and an elapsed-time/memory note. Record what is *independently* verified versus checked against the same source.

The current fixed U1 cohort is six units: SP:10 Brás, SP:02 Alto de Pinheiros, SP:95 São Domingos; CHI:32 Loop, CHI:14 Albany Park, CHI:23 Humboldt Park. It was drawn through a seed-20260922 stratified summary screen and then selected for central/residential/industrial contrasts. It is a diagnostic cohort, **not** a representative random sample of all 173 units. The exact-area values refer to all source polygons intersecting each *selected* unit within the stated partition-read strategy; the 20-point counts are samples and must not be turned into precise percentages.

## 2. Input availability and provenance

| Input | Where / how to verify | Reproduction caveat |
|---|---|---|
| Frozen SP preparation, N10 attributes and local v2 model | [SP handoff](../sp/SP_DATA_RESOLUTION_HANDOFF.md), `analysis/processed/SP/`, `analysis/outputs/sp_attributes/`, `analysis/results/SP/models/sp_urban_model_v2/` | Historical results are versioned. Do not overwrite the frozen release to reproduce one bounded test. |
| Chicago local/functional releases and CMAP LUI | [Chicago execution](../chicago/CHICAGO_EXECUTION_REPORT.md), `analysis/data/Chicago/`, `analysis/results/Chicago/` | Large source and prepared files can be Git-ignored. Check their manifests/hashes and source vintages. |
| Cook/DuPage/benchmarking acquisitions | [Chicago acquisition](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md), local `analysis/data/Chicago/chicago_cadastral_2026_09_18/` | Do not redistribute restricted DuPage records. A fresh API response is a new vintage, not a byte-identical reproduction of the saved source. |
| Microsoft footprints | [Pilot and inventory](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md), `analysis/data/{Chicago,SP}/microsoft_buildings_2026_08_13/raw_tiles/`; user's `~/Downloads/dataset-links.csv` | CSV index and six compressed tiles are outside version control; normalized names and SHA-256s are in manifests. The original root copies were deleted only after byte comparison. |
| Overture Places | [Sample checks](../../analysis/results/SP_CHI/u1_source_samples_2026_09_22/poi_checks.json), release 2026-08-19.0 | Remote partition reads need internet, DuckDB `httpfs` and the pinned release. Avoid silently using the newest release or taxonomy. |
| GHSL | [Acquisition register](../../analysis/results/SP_CHI/ghsl_public_2026_09_21/README.md), `analysis/data/shared/ghsl_public_2026_09_21/` | Raw tiles are large, Git-ignored, pinned by URL/hash. Boundary extracts retain native cells. |

## 3. Minimal bounded reruns

Run one step at a time and inspect its manifest and output **before** following a dependency. The source-land tests read selected partitions and bounding boxes; the POI tests require remote Parquet access. They may overwrite same-named diagnostic outputs, so preserve or copy the dated result first when exact historical reproduction matters.

```bash
.venv/bin/python analysis/scripts/pilot_u1_summary_ontology.py
.venv/bin/python analysis/scripts/pilot_u1_source_samples.py
.venv/bin/python analysis/scripts/pilot_u1_clipped_area.py
.venv/bin/python analysis/scripts/pilot_u1_mixed_labels.py
.venv/bin/python analysis/scripts/pilot_u1_dominant_use.py
.venv/bin/python analysis/scripts/pilot_u1_gap_context.py
```

Optional **remote** U1 checks, on the same pinned Overture release:

```bash
.venv/bin/python analysis/scripts/pilot_u1_poi_samples.py
.venv/bin/python analysis/scripts/pilot_u1_poi_quality.py
```

Inspect [summary checks](../../analysis/results/SP_CHI/u1_summary_pilot_2026_09_22/checks.json), [source checks](../../analysis/results/SP_CHI/u1_source_samples_2026_09_22/checks.json), [POI checks](../../analysis/results/SP_CHI/u1_source_samples_2026_09_22/poi_checks.json), and [exact-area validation](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/validation.json). Verify cohort/seed, source filenames/hashes where recorded, area partition conservation, overlap handling and conditional entropy denominator. If local files are absent, record “not reproducible from this clone”; do not substitute current web data and call it the same run.

Other bounded diagnostic entry points: `analysis/scripts/review_junction_complexes_v2.py`, `review_block_reference_fixtures_v2.py`, `review_block_barrier_pilots_v3.py`, `review_rail_corridor_pilots_v3.py`, `review_local_rail_envelopes_v1.py`, `pilot_microsoft_buildings.py`, and `review_harmonization_h4.py`. Their pilot geographies and outputs are linked in the [ledger](EXPERIMENT_LEDGER.md). **Do not run** `prepare_harmonized_roads.py`, `assemble_harmonized_candidates.py`, the original SP/Chicago full construction scripts or an all-173-unit U1 job merely to check a small observation. Treat them as full construction with versioned input/output review.

## 4. Scientific validation that is still missing

### Land use and cadastral coverage

Predeclare strata: SP no raw lot **inside** ordinary Quadra, SP no lot outside mapped blocks, raw lot without accepted use, explicit mixed and unresolved mixed, and Chicago `6000`, `1216` mixed and secondary-use cases. Sample cases from the saved six units, preserving area weights or reporting why purposive cases were chosen. Record coordinates/geometry IDs and source vintage. Two reviewers should assign visible/authoritative evidence categories (ROW, park/plaza, built parcel and broad function, uncertain), source of each label and disagreement. A tax or zoning map derived from the same IPTU universe is *not* independent truth for the no-lot question. Review at least several contrasting cases per stratum before deciding to enlarge the sample; choose any later sample size using observed ambiguity and a declared precision target, not the desired conclusion. Preserve “unjudgeable” cases in the denominator.

Then recompute four- and six-class **district-clipped** category areas in the same units after only predeclared recodes. Publish each class, mixed, source-unclassified, open-space and uncovered land as fractions of *district land*, plus conditional entropy and classified-support fraction. A common raw value requires the same class meanings, land support and exclusion policy in both cities. If the dominant use is not externally credible, keep SP explicit predominance as a separate sensitivity. Compare CMAP primary/secondary examples without adding secondary use as extra area.

### POIs

For the saved 20 listings per unit and a targeted oversample of missing-taxonomy Loop records, record independent existence, location, broad category and duplicate status. Audit by provider and city; retain records with no verifiable truth. Freeze the release and taxonomy. Report classified share, provider mix, record density and an uncertainty/sensitivity range alongside `destination_diversity_12`. Confidence thresholds are scenario definitions, not calibrated truth cutoffs. Test incremental information relative to land use, jobs, population and footprint coverage only after those features have defensible definitions; do not assign POI a new full family weight because an entropy differs.

The first [seven-point/seven-venue audit](../../analysis/results/SP_CHI/u1_independent_cases_2026_09_23/README.md) implements a **purposive, single-reviewer** screen, with fixed SHA-based POI selection, small imagery chips and source receipts. Reproduce its bounded computational portions with `analysis/scripts/audit_u1_land_cases.py`, `audit_u1_poi_cases.py`, `audit_u1_poi_neighbors.py` and `audit_u1_poi_address_ranges.py`; do not mistake the hand-coded case labels for script output. A later accuracy study must add a second reviewer blinded to source labels and probability sampling with known inclusion probabilities. The SP imagery capture date and business-address vintage must be resolved before temporal claims.

### Street topology and footprints

Annotate both cities' divided highways, loop ramps, T junctions, stacked crossings and simple controls with physical arms and grade before choosing an M2 distance rule. Annotate block boundaries with actual roads, water and rights-of-way; classify tiny polygons as real or artifacts without imposing a size filter first. Recompute candidate→reference *and* reference→candidate IoU and count missing support. Inspect O'Hare/Marsilac class-universe cases separately. For B1, use source-independent local imagery/reference on the eight Microsoft/Overture fixtures, reporting each source's missed/extra polygons, observation date, and uncertainty; do not call Overture an independent ground truth for Microsoft because Microsoft contributes to its lineage.

### Cadastral stock, jobs and transit

For M7/B2/B3, draw a parcel↔PIN↔parent↔improvement/building↔fiscal-unit crosswalk for Brás/Loop, condominium, campus/commercial and Addison/exempt examples. Count each parent and area once, show unmatched mass, and retain area definitions and top-coded stories. For U2, compare RAIS and LODES covered-worker universes and exact allocation/residual rules; preserve SP unlocated and Chicago outside-city job mass. For U3/U4, publish vintage and service-calendar scenario sensitivities, with bus-only route scope and a common catchment rule. Arithmetic mass conservation should accompany, not replace, source-semantic review.

## 5. Claim and release gates

An honest future paper needs a frozen sampling frame, case-level independent labels with uncertain outcomes, exact source versions and reusable metadata, denominator/missingness tables, comparisons of alternative ontologies, and sensitivity to city/edge units and source vintages. Name each estimand and support. Report a rejection when a tested proxy fails; do not tune thresholds against appealing analogues. The six-family alternative is a limited research question; it cannot be represented as completion of the original 13-family model. The [current gate ledger](../chicago/CHICAGO_13_FAMILY_COMPLETION_LEDGER.md) and machine-readable contracts control any later model fit.

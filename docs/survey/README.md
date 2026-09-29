# São Paulo–Chicago urban data survey

**Research record, 22 September 2026.** This directory collects the project's evidence about available urban data, failures of coverage or labeling, and the experiments used to detect them. It is intended to support later scientific validation and a possible paper on what public and open data can actually measure in São Paulo and Chicago. It is **not** a claim that a common model has been fitted or that a dataset has been independently ground-truthed.

**For the advisor:** [What requires harmonization, and what we have already resolved](ADVISOR_BRIEF.md) explains each family's objective, acquired data, comparability problem, failure example and current feasibility. The revised brief defines technical terms and distinguishes the six-family proposal's implemented repairs, new vertical measure and omitted concepts, incorporating evidence through 23 September.

For the detailed research and learning record, read in this order:

1. [Research methods field guide](METHODS_FIELD_GUIDE.md): a student-facing explanation of the techniques used, why they were chosen, alternative methods, worked examples and exercises.
2. [Data resource and measurement survey](DATA_RESOURCE_SURVEY.md): source inventory, important discoveries, missingness mechanisms, ontology and entity conflicts, and research implications.
3. [Experiment ledger](EXPERIMENT_LEDGER.md): chronological tests, sample designs, scripts, outputs, checks and limits, including rejected approaches.
4. [Reproduction and validation protocol](#reproduction-and-independent-validation-protocol): inputs, commands, run cost, how to audit a result, and a protocol for independent labels and future claims.
5. [Document index](#reviewed-document-and-artifact-index): the project documentation and result reports reviewed for this survey. Archived plans are marked as historical.

The [current model status](../STATUS.md), [open discussion](../DECISIONS.md), [13-family acceptance ledger](../harmonization/PLAN.md), and [full execution record](../harmonization/EXECUTION_LOG.md) remain the decision authorities. In a conflict, dated output receipts and current status take precedence over old plans. Neither the restored six-family proposal nor the original 13-family route has passed scientific acceptance for a common fit; both contracts retain `fit_authorized=false`.

## How to read claims here

- **Observed locally** means a frozen file, script output, or source record supports the statement. It may still be wrong relative to the world.
- **Publisher-described** means a source definition or limitation comes from its publisher, with the original reference linked.
- **Inferred** means a plausible explanation suggested by observed patterns; it must not be rewritten as a verified cause.
- **Unresolved** means data or a definition is insufficient. The missing value remains visible.
- A validation check can establish arithmetic, geometry, schema, or conservation. It cannot by itself establish completeness, factual accuracy, causal interpretation, or equal meaning in two cities.

The existing local and paired releases are separate research artifacts. The survey records them without rerunning the 173-unit construction. Detailed raw and intermediate geodata under `analysis/data/` and `analysis/work/` are often Git-ignored; a transferred clone alone may reproduce code but not all results. Their manifests, publisher URLs and checksums are identified in the linked reports.

## Reviewed-document and artifact index

**Inventory date: 22 September 2026.** The survey cross-read the documentation below and the dated published result reports. Follow each result report to its scripts, tables, validation JSON, maps, and source manifests. Historical plans are not current acceptance decisions. Git-ignored data and intermediates are indexed by the reports and manifests; this list does not claim to enumerate every raw binary.

The [research methods field guide](METHODS_FIELD_GUIDE.md) explains the techniques behind these files for new researchers.

### Project documentation

| File | Subject | How to read it |
|---|---|---|
| [docs/MODEL_STATUS.md](../STATUS.md) | São Paulo–Chicago model: current status and completion path | Current or cumulative project documentation |
| [docs/OPEN_DISCUSSION.md](../DECISIONS.md) | Open discussion: recovering urban structure and function across São Paulo and Chicago | Current or cumulative project documentation |
| [docs/README.md](../../README.md) | Project documentation | Navigation |
| [docs/archive/audits/SP_MODEL_VALIDATION.md](../archive/audits/SP_MODEL_VALIDATION.md) | São Paulo urban model — independent validation | Historical plan/audit; current status supersedes it |
| [docs/archive/plans/MODEL_IMPLEMENTATION_TASKS_HISTORICAL.md](../archive/plans/MODEL_IMPLEMENTATION_TASKS_HISTORICAL.md) | Historical model implementation checklist | Historical plan/audit; current status supersedes it |
| [docs/archive/plans/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md](../archive/plans/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md) | São Paulo attribute implementation plan | Historical plan/audit; current status supersedes it |
| [docs/archive/plans/URBAN_MODEL_IMPLEMENTATION_PLAN.md](../archive/plans/URBAN_MODEL_IMPLEMENTATION_PLAN.md) | Urban similarity model — detailed implementation plan | Historical plan/audit; current status supersedes it |
| [docs/chicago/CHICAGO_13_FAMILY_COMPLETION_LEDGER.md](../harmonization/PLAN.md) | Full-scope SP–Chicago completion ledger — 22 September 2026 | Current or cumulative project documentation |
| [docs/chicago/CHICAGO_ATTRIBUTE_DOCUMENTATION.md](../chicago/ATTRIBUTES.md) | Chicago local attribute baseline: calculation and processing | Current or cumulative project documentation |
| [docs/chicago/CHICAGO_DATA_DISCOVERY_2026_09_18.md](../chicago/DATA_SOURCES.md) | Chicago missing-data discovery and validation — 18 September 2026 | Current or cumulative project documentation |
| [docs/chicago/CHICAGO_DATA_REQUIREMENTS.md](../chicago/DATA_SOURCES.md) | Chicago data requirements and readiness | Current or cumulative project documentation |
| [docs/chicago/CHICAGO_EXECUTION_REPORT.md](../chicago/EXECUTION_LOG.md) | Chicago construction report and continuation handoff | Current or cumulative project documentation |
| [docs/chicago/CHICAGO_FUNCTIONAL_EXTENSION.md](../chicago/ATTRIBUTES.md) | Chicago functional extension and matched-source acquisition | Current or cumulative project documentation |
| [docs/chicago/CHICAGO_HARMONIZATION_PLAN.md](../harmonization/PLAN.md) | São Paulo–Chicago attribute harmonization plan | Current or cumulative project documentation |
| [docs/chicago/ENTITY_SOURCE_DECISION_BRIEF.md](../DECISIONS.md) | Source and entity decisions before further model construction | Current or cumulative project documentation |
| [docs/chicago/MANUAL_DATA_ACQUISITION.md](../chicago/DATA_SOURCES.md) | Manual acquisition: remaining Chicago building data | Current or cumulative project documentation |
| [docs/chicago/SIX_FAMILY_PLAN_REASSESSMENT.md](../harmonization/PLAN.md) | Reopened six-family SP–Chicago plan: scope and evidence review | Current or cumulative project documentation |
| [docs/chicago/SP_CHICAGO_HARMONIZATION_EXECUTION.md](../harmonization/EXECUTION_LOG.md) | São Paulo–Chicago harmonization: execution documentation | Current or cumulative project documentation |
| [docs/operations/NEXT_AGENT_PROMPT.md](../HANDOFF.md) | Continuation handoff — 22 September 2026 | Current or cumulative project documentation |
| [docs/sp/ATTRIBUTE_DOCUMENTATION.md](../sp/ATTRIBUTES.md) | São Paulo attribute documentation | Current or cumulative project documentation |
| [docs/sp/BUILDING_PIPELINE.md](../sp/PREPARATION.md) | São Paulo building morphology pipeline | Current or cumulative project documentation |
| [docs/sp/README.md](../../README.md) | São Paulo documentation | Current or cumulative project documentation |
| [docs/sp/SP_DATA_RESOLUTION_HANDOFF.md](../sp/PREPARATION.md) | São Paulo preparation: current status and resumption handoff | Current or cumulative project documentation |
| [docs/sp/SP_METHOD_DECISIONS.md](../DECISIONS.md) | SP method decisions: M6 classification, U2 allocation and M2 simplification | Current or cumulative project documentation |
| [docs/sp/SP_MODEL_FIXES.md](../sp/MODEL.md) | SP model corrections and revalidation — 15 September 2026 | Current or cumulative project documentation |

### Dated published result reports

| File | Subject | How to read it |
|---|---|---|
| [analysis/results/Chicago/README.md](../../analysis/results/Chicago/README.md) | Chicago results | Dated result; see receipts and limitations |
| [analysis/results/Chicago/chi_employment_sensitivity_2026_09_22_v2/README.md](../../analysis/results/Chicago/chi_employment_sensitivity_2026_09_22_v2/README.md) | Chicago workplace-allocation sensitivity v2 — September 22, 2026 | Dated result; see receipts and limitations |
| [analysis/results/Chicago/chi_functional_2026_09_16_v2/README.md](../../analysis/results/Chicago/chi_functional_2026_09_16_v2/README.md) | Chicago functional extension — September 16, 2026 | Dated result; see receipts and limitations |
| [analysis/results/Chicago/chi_local_2026_09_16_v1/README.md](../../analysis/results/Chicago/chi_local_2026_09_16_v1/README.md) | Chicago local-source attributes v1 | Dated result; see receipts and limitations |
| [analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md) | Chicago data acquisition checkpoint — 19 September 2026 | Dated result; see receipts and limitations |
| [analysis/results/Chicago/chicago_workbooks_2026_09_19/README.md](../../analysis/results/Chicago/chicago_workbooks_2026_09_19/README.md) | Chicago commercial workbook checkpoint — extracted September 19, documented September 21, 2026 | Dated result; see receipts and limitations |
| [analysis/results/Chicago/data_discovery_2026_09_18/README.md](../../analysis/results/Chicago/data_discovery_2026_09_18/README.md) | Chicago data discovery — 18 September 2026 | Dated result; see receipts and limitations |
| [analysis/results/Chicago/dupage_characteristics_2026_09_21/README.md](../../analysis/results/Chicago/dupage_characteristics_2026_09_21/README.md) | Chicago DuPage building-source checkpoint — 21 September 2026 | Dated result; see receipts and limitations |
| [analysis/results/Chicago/harmonization_checkpoint_2026_09_17/README.md](../../analysis/results/Chicago/harmonization_checkpoint_2026_09_17/README.md) | Harmonization checkpoint — 17 September 2026 | Dated result; see receipts and limitations |
| [analysis/results/Chicago/harmonized_candidates_2026_09_22/README.md](../../analysis/results/Chicago/harmonized_candidates_2026_09_22/README.md) | Chicago harmonized candidate companion | Dated result; see receipts and limitations |
| [analysis/results/Chicago/overture_2026_08_19_review_v1/README.md](../../analysis/results/Chicago/overture_2026_08_19_review_v1/README.md) | Matched Overture review | Dated result; see receipts and limitations |
| [analysis/results/Chicago/public_data_alternative_2026_09_21/README.md](../../analysis/results/Chicago/public_data_alternative_2026_09_21/README.md) | Public-data alternative — proposed September 21, 2026 | Dated result; see receipts and limitations |
| [analysis/results/SP/README.md](../../analysis/results/SP/README.md) | São Paulo — completed district attributes | Dated result; see receipts and limitations |
| [analysis/results/SP/harmonized_candidates_2026_09_22/README.md](../../analysis/results/SP/harmonized_candidates_2026_09_22/README.md) | SP harmonized candidate companion | Dated result; see receipts and limitations |
| [analysis/results/SP/models/sp_urban_model_v2/README.md](../../analysis/results/SP/models/sp_urban_model_v2/README.md) | SP urban similarity — corrected v2 | Dated result; see receipts and limitations |
| [analysis/results/SP/overture_2026_08_19_review_v1/README.md](../../analysis/results/SP/overture_2026_08_19_review_v1/README.md) | Matched Overture review | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/ghsl_public_2026_09_21/README.md](../../analysis/results/SP_CHI/ghsl_public_2026_09_21/README.md) | Public GHSL height/volume acquisition — completed 22 September 2026 | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/README.md) | Full-scope paired morphology pilot flags | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/README.md) | Paired M3/M4 block-boundary sensitivity — diagnostic only | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures/README.md) | Eight paired block fixtures against local references | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers/README.md) | Paired rail and water boundary pilots — 22 September 2026 | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v4_local_rail/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v4_local_rail/README.md) | City-local rail envelope validation | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/README.md) | Paired M2 source-topology review — diagnostic only | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review/README.md) | M1/M6 matched-road scope review | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_h0_h1/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_h0_h1/README.md) | Harmonization build checkpoint — September 22, 2026 | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/README.md) | Paired harmonization candidates — H1–H3, September 22, 2026 | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md](../../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/README.md) | H4 bounded readiness checkpoint — September 22, 2026 | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md) | Microsoft Global ML Building Footprints: bounded paired-source review | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md) | U1 developed-use and POI source diagnosis — bounded six-unit follow-up | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/u1_source_samples_2026_09_22/README.md](../../analysis/results/SP_CHI/u1_source_samples_2026_09_22/README.md) | U1 bounded source and destination samples — 22 September 2026 | Dated result; see receipts and limitations |
| [analysis/results/SP_CHI/u1_summary_pilot_2026_09_22/README.md](../../analysis/results/SP_CHI/u1_summary_pilot_2026_09_22/README.md) | U1 bounded ontology screen — 22 September 2026 | Dated result; see receipts and limitations |

### Other scientific reports and protocol

| File | Subject | How to read it |
|---|---|---|
| [plan.md](../PROTOCOL.md) | São Paulo–Chicago urban-form comparison: research protocol | Current or cumulative project documentation |
| [analysis/results/SP/reports/ATTRIBUTE_REPORT.md](../../analysis/results/SP/reports/ATTRIBUTE_REPORT.md) | São Paulo district attributes — N10 construction report | Dated result; see receipts and limitations |
| [analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md](../../analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md) | São Paulo district attributes — N10 construction report | Current or cumulative project documentation |
| [analysis/results/SP/models/sp_urban_model_v2/reports/MODEL_REPORT.md](../../analysis/results/SP/models/sp_urban_model_v2/reports/MODEL_REPORT.md) | Corrected SP urban similarity model — v2 | Dated result; see receipts and limitations |

### Workspace and handoff documentation outside docs/

- [Repository README](../../README.md) and [analysis workspace guide](../../analysis/README.md): folder roles, environment and symlink/checkout caveats.
- [Working-data guide](../../analysis/work/README.md), [prepared inputs](../../analysis/work/prepared/README.md), [supporting evidence](../../analysis/work/evidence/README.md), and [execution records](../../analysis/work/runs/README.md): distinguish final releases from ignored intermediates, historical v2/v3 data and hash-bound checkpoints.
- [Analysis handoff copy](../HANDOFF.md): operational compatibility copy; maintain identity with the canonical docs/operations version. Its later acquisition notes were used to reconcile the seven locally supplied commercial XLSX files with the earlier eight text-only Firecrawl extracts.

### Machine-readable anchors

- [Full-scope v2 contract](../../analysis/config/sp_chicago_harmonization_v2_full_scope.json) and [H4 proposed contract](../../analysis/results/SP_CHI/harmonization_2026_09_22_h4_review/proposed_contract.json): scope and fit status.
- [H1–H3 publication manifest](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/publication_manifest.json), [family ledger](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/family_acceptance_ledger.json), and [candidate dictionary](../../analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/tables/candidate_dictionary.csv): code/source/output binding.
- [U1 exact-area validation](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/validation.json), [unit coverage](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/unit_coverage.csv), and [category areas](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/category_areas.csv): six-unit evidence.
- [Chicago cadastral validation](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/validation.json), [employment audit](../../analysis/results/Chicago/chi_employment_sensitivity_2026_09_22_v2/validation/independent_checks.json), and [Microsoft B1 validation](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/pilot/validation.json): computational receipts, not independent truth.

## Reproduction and independent-validation protocol

This page is a practical method for reproducing the existing evidence and extending it without an accidental 173-unit rebuild. Work from the repository root with the project's `.venv`; follow each linked report's frozen config, source manifest and output directory. The commands below are **examples of bounded tests**, not a new global pipeline. Read the [experiment ledger](EXPERIMENT_LEDGER.md) before deciding which checkpoint to repeat.

### 1. Freeze the claim before executing

For every new test, write down: question, estimand, source universe and version, reporting-unit IDs, sampling frame, seed, selection strata, numerator, denominator, geographic projection/assignment, source and output hashes, null codes, exclusion rules, and the exact falsification or acceptance criterion. Keep “unobserved,” “source-unclassified,” “mixed,” “outside geography,” and “not applicable” as different states. Save code and environment versions and an elapsed-time/memory note. Record what is *independently* verified versus checked against the same source.

The current fixed U1 cohort is six units: SP:10 Brás, SP:02 Alto de Pinheiros, SP:95 São Domingos; CHI:32 Loop, CHI:14 Albany Park, CHI:23 Humboldt Park. It was drawn through a seed-20260922 stratified summary screen and then selected for central/residential/industrial contrasts. It is a diagnostic cohort, **not** a representative random sample of all 173 units. The exact-area values refer to all source polygons intersecting each *selected* unit within the stated partition-read strategy; the 20-point counts are samples and must not be turned into precise percentages.

### 2. Input availability and provenance

| Input | Where / how to verify | Reproduction caveat |
|---|---|---|
| Frozen SP preparation, N10 attributes and local v2 model | [SP handoff](../sp/PREPARATION.md), `analysis/processed/SP/`, `analysis/outputs/sp_attributes/`, `analysis/results/SP/models/sp_urban_model_v2/` | Historical results are versioned. Do not overwrite the frozen release to reproduce one bounded test. |
| Chicago local/functional releases and CMAP LUI | [Chicago execution](../chicago/EXECUTION_LOG.md), `analysis/data/Chicago/`, `analysis/results/Chicago/` | Large source and prepared files can be Git-ignored. Check their manifests/hashes and source vintages. |
| Cook/DuPage/benchmarking acquisitions | [Chicago acquisition](../../analysis/results/Chicago/chicago_cadastral_2026_09_18/README.md), local `analysis/data/Chicago/chicago_cadastral_2026_09_18/` | Do not redistribute restricted DuPage records. A fresh API response is a new vintage, not a byte-identical reproduction of the saved source. |
| Microsoft footprints | [Pilot and inventory](../../analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/README.md), `analysis/data/{Chicago,SP}/microsoft_buildings_2026_08_13/raw_tiles/`; user's `~/Downloads/dataset-links.csv` | CSV index and six compressed tiles are outside version control; normalized names and SHA-256s are in manifests. The original root copies were deleted only after byte comparison. |
| Overture Places | [Sample checks](../../analysis/results/SP_CHI/u1_source_samples_2026_09_22/poi_checks.json), release 2026-08-19.0 | Remote partition reads need internet, DuckDB `httpfs` and the pinned release. Avoid silently using the newest release or taxonomy. |
| GHSL | [Acquisition register](../../analysis/results/SP_CHI/ghsl_public_2026_09_21/README.md), `analysis/data/shared/ghsl_public_2026_09_21/` | Raw tiles are large, Git-ignored, pinned by URL/hash. Boundary extracts retain native cells. |

### 3. Minimal bounded reruns

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

### 4. Scientific validation that is still missing

#### Land use and cadastral coverage

Predeclare strata: SP no raw lot **inside** ordinary Quadra, SP no lot outside mapped blocks, raw lot without accepted use, explicit mixed and unresolved mixed, and Chicago `6000`, `1216` mixed and secondary-use cases. Sample cases from the saved six units, preserving area weights or reporting why purposive cases were chosen. Record coordinates/geometry IDs and source vintage. Two reviewers should assign visible/authoritative evidence categories (ROW, park/plaza, built parcel and broad function, uncertain), source of each label and disagreement. A tax or zoning map derived from the same IPTU universe is *not* independent truth for the no-lot question. Review at least several contrasting cases per stratum before deciding to enlarge the sample; choose any later sample size using observed ambiguity and a declared precision target, not the desired conclusion. Preserve “unjudgeable” cases in the denominator.

Then recompute four- and six-class **district-clipped** category areas in the same units after only predeclared recodes. Publish each class, mixed, source-unclassified, open-space and uncovered land as fractions of *district land*, plus conditional entropy and classified-support fraction. A common raw value requires the same class meanings, land support and exclusion policy in both cities. If the dominant use is not externally credible, keep SP explicit predominance as a separate sensitivity. Compare CMAP primary/secondary examples without adding secondary use as extra area.

#### POIs

For the saved 20 listings per unit and a targeted oversample of missing-taxonomy Loop records, record independent existence, location, broad category and duplicate status. Audit by provider and city; retain records with no verifiable truth. Freeze the release and taxonomy. Report classified share, provider mix, record density and an uncertainty/sensitivity range alongside `destination_diversity_12`. Confidence thresholds are scenario definitions, not calibrated truth cutoffs. Test incremental information relative to land use, jobs, population and footprint coverage only after those features have defensible definitions; do not assign POI a new full family weight because an entropy differs.

The first [seven-point/seven-venue audit](../../analysis/results/SP_CHI/u1_independent_cases_2026_09_23/README.md) implements a **purposive, single-reviewer** screen, with fixed SHA-based POI selection, small imagery chips and source receipts. Reproduce its bounded computational portions with `analysis/scripts/audit_u1_land_cases.py`, `audit_u1_poi_cases.py`, `audit_u1_poi_neighbors.py` and `audit_u1_poi_address_ranges.py`; do not mistake the hand-coded case labels for script output. A later accuracy study must add a second reviewer blinded to source labels and probability sampling with known inclusion probabilities. The SP imagery capture date and business-address vintage must be resolved before temporal claims.

#### Street topology and footprints

Annotate both cities' divided highways, loop ramps, T junctions, stacked crossings and simple controls with physical arms and grade before choosing an M2 distance rule. Annotate block boundaries with actual roads, water and rights-of-way; classify tiny polygons as real or artifacts without imposing a size filter first. Recompute candidate→reference *and* reference→candidate IoU and count missing support. Inspect O'Hare/Marsilac class-universe cases separately. For B1, use source-independent local imagery/reference on the eight Microsoft/Overture fixtures, reporting each source's missed/extra polygons, observation date, and uncertainty; do not call Overture an independent ground truth for Microsoft because Microsoft contributes to its lineage.

#### Cadastral stock, jobs and transit

For M7/B2/B3, draw a parcel↔PIN↔parent↔improvement/building↔fiscal-unit crosswalk for Brás/Loop, condominium, campus/commercial and Addison/exempt examples. Count each parent and area once, show unmatched mass, and retain area definitions and top-coded stories. For U2, compare RAIS and LODES covered-worker universes and exact allocation/residual rules; preserve SP unlocated and Chicago outside-city job mass. For U3/U4, publish vintage and service-calendar scenario sensitivities, with bus-only route scope and a common catchment rule. Arithmetic mass conservation should accompany, not replace, source-semantic review.

### 5. Claim and release gates

An honest future paper needs a frozen sampling frame, case-level independent labels with uncertain outcomes, exact source versions and reusable metadata, denominator/missingness tables, comparisons of alternative ontologies, and sensitivity to city/edge units and source vintages. Name each estimand and support. Report a rejection when a tested proxy fails; do not tune thresholds against appealing analogues. The six-family alternative is a limited research question; it cannot be represented as completion of the original 13-family model. The [current gate ledger](../harmonization/PLAN.md) and machine-readable contracts control any later model fit.

## Paper framing (external assessment, 22 September 2026)

### My assessment

The strongest potential paper is about **whether urban measurements can be transferred between São Paulo and Chicago**. The project has uncovered cases where similarly named variables measure different populations, land areas, or physical objects. That is a more defensible contribution today than a paper claiming to have found Chicago analogues of Brás. The paired dataset covers 96 São Paulo districts and 77 Chicago Community Areas, but **no cross-city model fit or ranking has been accepted**. [Survey](DATA_RESOURCE_SURVEY.md) · [Current status](../STATUS.md)

#### Findings with the most paper potential

1. **The definition of “land-use diversity” changes the result.** In the six-area pilot, Brás has lower normalized entropy than the Loop when six mapped uses are included (0.706 versus 0.735), but higher entropy when the measure is restricted to four occupied uses (0.774 versus 0.662). This is a substantive change in the question being measured, not a minor parameter adjustment. The catch is serious: only 54.6% of Brás land and 34.3% of Loop land enter the four-use calculation. These are *conditional* diversity measures, not whole-district descriptions. This is the clearest demonstration for a paper, provided it is presented as a bounded case study. [Exact-area pilot](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md)

2. **Missing land-use information has different causes in the two cities.** In the three sampled São Paulo districts, 20–25% of land has no raw fiscal lot polygon; another 1–5% has a lot but no accepted use. In the three Chicago areas, 27–33% is largely mapped as CMAP’s `6000` nonparcel or unclassifiable category. Similar-sized gaps therefore cannot be handled with one “unknown use” rule. Particularly interesting: 7–8.5% of each sampled São Paulo district is outside raw lots *yet inside ordinary mapped blocks*. That warrants investigation, but does not prove those areas contain omitted taxable buildings or any particular use. [Survey](DATA_RESOURCE_SURVEY.md) · [Exact-area pilot](../../analysis/results/SP_CHI/u1_developed_area_2026_09_22/README.md)

3. **A common map source does not give you common physical morphology.** Overture roads can support mapped street length and class shares, but connector lines can split one junction, nearby lines can represent roads at different levels, and polygonized roads can create false blocks. In one Chicago rail test, adding centerlines increased candidate blocks from 765 to 1,404 and narrow polygons from 5 to 359, while candidate-to-reference agreement at IoU ≥0.50 fell from 0.634 to 0.350. That is a useful negative result: an apparently richer boundary network made the physical-block proxy worse. It still needs independently labeled junctions and blocks before becoming a general accuracy claim. [Experiment ledger](EXPERIMENT_LEDGER.md)

4. **Building and employment records expose a deeper entity problem.** São Paulo fiscal accounts, Cook tax PINs, condo units, parcels and buildings cannot safely be counted as the same object. The São Paulo condominium-key correction raised *located fiscal constructed-area mass* from an erroneous intermediate 61.6% to 97.3032%, but that does not establish coverage of all physical buildings. In Chicago, commercial `stories` and `gross_building_area` fields were empty in the tested 2024 slice, while condo area can repeat across units. Likewise, São Paulo’s formal job links and Chicago’s LODES covered jobs have different universes. This could form a strong methods section, though it is currently a collection of source audits rather than a validated cross-city estimate of bias. [Survey](DATA_RESOURCE_SURVEY.md)

### What I would **not** claim yet

The São Paulo-only model is real and tested: Belém, Bom Retiro and Cambuci lead its Brás similarity ranking, and 577 sensitivity scenarios were run. But those are **similarities under the chosen features and distance**, not independently verified urban analogues. Some alternatives materially change the top ten. There is also no accepted Chicago ranking and no pedestrian-accessibility outcome analysis. A paper led by “we found Brás’s Chicago equivalent” would run ahead of the evidence. [SP model report](../../analysis/results/SP/models/sp_urban_model_v2/reports/MODEL_REPORT.md) · [Research protocol](../PROTOCOL.md)

My critical reservation about the proposed measurement paper is **external validity**. The land-use result comes from six deliberately contrasting areas, morphology from small fixtures, and footprint comparison from eight units. The checks establish that calculations reconcile; they do not establish which source is correct on the ground. Without independent case labels, the paper can convincingly show *how conclusions depend on definitions and source support*, but cannot yet estimate citywide error rates or say which ontology is empirically best. [Reproducibility and validation protocol](#reproduction-and-independent-validation-protocol)

**Best next paper question:** *How do source coverage, entity definitions and land-use ontology alter cross-city urban-form comparisons?* I would lead with the land-use reversal, use the street/block and cadastral audits to show that the issue recurs across feature families, and run a small preregistered independent-label study before drafting the main claims. That could make a credible methodological case study. The broader analogue and accessibility paper should wait for accepted common features and outcome data.

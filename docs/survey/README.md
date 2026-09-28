# São Paulo–Chicago urban data survey

**Research record, 22 September 2026.** This directory collects the project's evidence about available urban data, failures of coverage or labeling, and the experiments used to detect them. It is intended to support later scientific validation and a possible paper on what public and open data can actually measure in São Paulo and Chicago. It is **not** a claim that a common model has been fitted or that a dataset has been independently ground-truthed.

**For the advisor:** [What requires harmonization, and what we have already resolved](ADVISOR_COMPARABILITY_BRIEF.md) explains each family's objective, acquired data, comparability problem, failure example and current feasibility. The revised brief defines technical terms and distinguishes the six-family proposal's implemented repairs, new vertical measure and omitted concepts, incorporating evidence through 23 September.

For the detailed research and learning record, read in this order:

1. [Research methods field guide](RESEARCH_METHODS_FIELD_GUIDE.md): a student-facing explanation of the techniques used, why they were chosen, alternative methods, worked examples and exercises.
2. [Data resource and measurement survey](DATA_RESOURCE_SURVEY.md): source inventory, important discoveries, missingness mechanisms, ontology and entity conflicts, and research implications.
3. [Experiment ledger](EXPERIMENT_LEDGER.md): chronological tests, sample designs, scripts, outputs, checks and limits, including rejected approaches.
4. [Reproduction and validation protocol](REPRODUCIBILITY.md): inputs, commands, run cost, how to audit a result, and a protocol for independent labels and future claims.
5. [Document index](DOCUMENT_INDEX.md): the project documentation and result reports reviewed for this survey. Archived plans are marked as historical.

The [current model status](../MODEL_STATUS.md), [open discussion](../OPEN_DISCUSSION.md), [13-family acceptance ledger](../chicago/CHICAGO_13_FAMILY_COMPLETION_LEDGER.md), and [full execution record](../chicago/SP_CHICAGO_HARMONIZATION_EXECUTION.md) remain the decision authorities. In a conflict, dated output receipts and current status take precedence over old plans. Neither the restored six-family proposal nor the original 13-family route has passed scientific acceptance for a common fit; both contracts retain `fit_authorized=false`.

## How to read claims here

- **Observed locally** means a frozen file, script output, or source record supports the statement. It may still be wrong relative to the world.
- **Publisher-described** means a source definition or limitation comes from its publisher, with the original reference linked.
- **Inferred** means a plausible explanation suggested by observed patterns; it must not be rewritten as a verified cause.
- **Unresolved** means data or a definition is insufficient. The missing value remains visible.
- A validation check can establish arithmetic, geometry, schema, or conservation. It cannot by itself establish completeness, factual accuracy, causal interpretation, or equal meaning in two cities.

The existing local and paired releases are separate research artifacts. The survey records them without rerunning the 173-unit construction. Detailed raw and intermediate geodata under `analysis/data/` and `analysis/work/` are often Git-ignored; a transferred clone alone may reproduce code but not all results. Their manifests, publisher URLs and checksums are identified in the linked reports.

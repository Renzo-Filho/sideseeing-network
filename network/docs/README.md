# Sidewalk network documents

Read in this order if you are new: STATUS, then GRAPH_WORK_EXPLAINED, then PAPERS. Dated status goes only in [STATUS.md](STATUS.md). The other pages record plans, decisions and results as of the date they carry.

## Current

| Document | What it is |
|---|---|
| [STATUS.md](STATUS.md) | Where the track stands and what is next |
| [GRAPH_PAPER_PLAN_2026-11-03.md](GRAPH_PAPER_PLAN_2026-11-03.md) | **Draft for the advisors.** The graph paper with Tile2Net as the baseline: the network first, then the enriched graph; methods, reference, gates, contribution and paper. Once agreed, it replaces the October plan's framing and phases |
| [GRAPH_PIPELINE_2026-11-03.md](GRAPH_PIPELINE_2026-11-03.md) | **Draft.** How the graph is produced: inputs and their rates, data management (time, space, storage, splits for data still arriving), the steps S1–S11 with their code, aggregation rules, output tables, the source-ablation matrix, exploratory sensors |
| [GRAPH_WORK_EXPLAINED_2026-10-30.md](GRAPH_WORK_EXPLAINED_2026-10-30.md) | The graph work so far in plain English: the steps, the result map layer by layer, how every source merges into the graph |
| [PAPERS.md](PAPERS.md) | The two papers (dataset, graph): goals, pipeline, phases with gates, open decisions |
| [PLAN.md](PLAN.md) | The original research plan and the numbered decisions agreed with the researcher (later decisions revise earlier ones in place) |
| [GRAPH_GPS_PLAN_2026-10-24.md](GRAPH_GPS_PLAN_2026-10-24.md) | The graph and GPS method: cells and graph, the ladder, phases 0–6 and their gates. Its sections 3–6 stay the method reference for the walk-only inference |
| [GRAPH_PHASE0_RESULTS_2026-10-25.md](GRAPH_PHASE0_RESULTS_2026-10-25.md) | Phase 0: the data contract (clocks, side cue, zones) |
| [GRAPH_PHASE2A_NOTES_2026-10-25.md](GRAPH_PHASE2A_NOTES_2026-10-25.md) | Phase 2a: the walking lines on Morgan and their score against the reference |
| [GRAPH_PHASE2B_NOTES_2026-10-27.md](GRAPH_PHASE2B_NOTES_2026-10-27.md) | Phase 2b: curb distance and road width from the video; camera height |
| [CALIBRATION_DAY_PLAN_2026-11-03.md](CALIBRATION_DAY_PLAN_2026-11-03.md) | **Draft for discussion.** The calibration day on Morgan in modules (height, lens, steps, widths, curb offsets, crossings, slope, barometer, Wi-Fi), the field sheet, what each result feeds, and a 10-minute daily routine |
| [COLLECTION_PROTOCOL.md](COLLECTION_PROTOCOL.md) | General field protocol for Chicago sidewalk collection |
| [WEST_LOOP_COLLECTION.md](WEST_LOOP_COLLECTION.md) | West Loop: boundary, routes and what it adds to the field rules. The field rules it reuses are in the archived [RIVER_NORTH_COLLECTION.md](archive/RIVER_NORTH_COLLECTION.md) |
| [ROUTING_WORKFLOW.md](ROUTING_WORKFLOW.md) | How the route plans are made, step by step, with a worked example |

## Datasets

[datasets/](datasets/README.md) holds the inventory and transfer plans for the field data outside this machine: Brás on Drive and RustFS ([README](datasets/README.md), [preflight](datasets/TRANSFER_PREFLIGHT.md), `bras-captures.csv`), the West Loop transfers ([WEST_LOOP_TRANSFER.md](datasets/WEST_LOOP_TRANSFER.md) and the `west-loop-*-files.txt` manifests), the hospital sites (`hospital-sites.csv`) and the other collections in the shared Drive folder ([OTHER_DATASETS.md](datasets/OTHER_DATASETS.md)).

## Archive

Superseded pages, kept unchanged because current pages still link to them:

| Document | Why it is archived |
|---|---|
| [PILOT_PROTOCOL.md](archive/PILOT_PROTOCOL.md), [PILOT_NEAR_WEST_SIDE.md](archive/PILOT_NEAR_WEST_SIDE.md) | Pilot 1 (14 October 2026), done |
| [PILOT_DATA_PLAN.md](archive/PILOT_DATA_PLAN.md), [PILOT_DATA_TODO.md](archive/PILOT_DATA_TODO.md) | Pilot analysis plan, replaced by the graph plan's phases |
| [PILOT2_PROTOCOL.md](archive/PILOT2_PROTOCOL.md) | Pilot 2 (16 October 2026), done. Still the reference for the voice protocol (PLAN.md decision 14) |
| [RIVER_NORTH_COLLECTION.md](archive/RIVER_NORTH_COLLECTION.md) | River North was dropped as the collection area. Still the source of the field rules West Loop reuses |
| [RESEARCH_CRITIQUE_2026-10-23.md](archive/RESEARCH_CRITIQUE_2026-10-23.md), [HYPOTHESIS_EXPERIMENTS_2026-10-23.md](archive/HYPOTHESIS_EXPERIMENTS_2026-10-23.md) | Proposals folded into the graph plan and PAPERS.md |

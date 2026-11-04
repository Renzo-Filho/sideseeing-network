# Sidewalk network documents

Read in this order if you are new: STATUS, then METHOD §1 (the work in plain words), then RESEARCH_PLAN. Dated status goes only in [STATUS.md](STATUS.md). The other pages record plans, decisions and results as of the date they carry.

On 4 November 2026 the plans, protocols and phase notes were merged into the pages below; the merged originals are in [archive/](#archive), unchanged except for their links.

## Current

| Document | What it is |
|---|---|
| [STATUS.md](STATUS.md) | Where the track stands and what is next |
| [RESEARCH_PLAN.md](RESEARCH_PLAN.md) | The two papers (dataset, graph); the graph paper with Tile2Net as the baseline (**draft for the advisors**): representation, methods, reference, gates, routes, contribution; the work plan (P0–P9, DS0–DS6); **every numbered decision**; open questions, risks, parked ideas |
| [METHOD.md](METHOD.md) | How the graph is built: the work in plain words, inputs, data management and splits, the ladder, steps S0–S11 with their code, width and slope, data structure and output tables, aggregation, the ablation matrix, exploratory sensors, how to read the result map |
| [FIELD_PROTOCOL.md](FIELD_PROTOCOL.md) | How a field day is done: the volunteer briefing, one street per day, spoken words, the researcher's checklist and log, the area, places to check, route files, what changed from the October rules |
| [RESULTS.md](RESULTS.md) | Dated results of the graph phases on Morgan: phase 0 (data contract), 2a (walking lines and the reference), 2b (curb distance, road width, camera height) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | The software (agreed 4 November): one installable package, `walk2net`, anyone can run on their area; requirements, the protocol as data, tables and the few classes (`PedestrianGraph`), the layout, where each piece went, the tests that enforce the research rules, migration steps M1–M5 |
| [CALIBRATION_DAY_PLAN_2026-11-03.md](CALIBRATION_DAY_PLAN_2026-11-03.md) | **Draft for discussion, kept separate from the field protocol.** The calibration day on Morgan in modules, the field sheet, what each result feeds, and a 10-minute daily routine |

## Datasets

[datasets/](datasets/README.md) holds the inventory and transfer plans for the field data outside this machine: Brás on Drive and RustFS ([README](datasets/README.md), [preflight](datasets/TRANSFER_PREFLIGHT.md), `bras-captures.csv`), the West Loop transfers ([WEST_LOOP_TRANSFER.md](datasets/WEST_LOOP_TRANSFER.md) and the `west-loop-*-files.txt` manifests), the hospital sites (`hospital-sites.csv`) and the other collections in the shared Drive folder ([OTHER_DATASETS.md](datasets/OTHER_DATASETS.md)).

## Archive

Superseded pages, kept unchanged (only their links were fixed when they moved):

| Document | Why it is archived |
|---|---|
| [PLAN.md](archive/PLAN.md) | The first research plan (12–16 October). Merged into RESEARCH_PLAN on 4 November; its decisions 1–14 keep their numbers there |
| [PAPERS.md](archive/PAPERS.md) | The two papers (25 October). Merged into RESEARCH_PLAN on 4 November |
| [GRAPH_GPS_PLAN_2026-10-24.md](archive/GRAPH_GPS_PLAN_2026-10-24.md) | The October graph and GPS plan. Its method (sections 3–6) is in METHOD, its decisions and risks in RESEARCH_PLAN (4 November). Still the list of sources consulted in October |
| [GRAPH_PAPER_PLAN_2026-11-03.md](archive/GRAPH_PAPER_PLAN_2026-11-03.md) | The graph paper plan of 3 November. Merged into RESEARCH_PLAN on 4 November; section 14 keeps Renzo's ideas and their full assessment |
| [GRAPH_PIPELINE_2026-11-03.md](archive/GRAPH_PIPELINE_2026-11-03.md) | The pipeline of 3 November. Merged into METHOD on 4 November |
| [GRAPH_WORK_EXPLAINED_2026-10-30.md](archive/GRAPH_WORK_EXPLAINED_2026-10-30.md) | The plain-English explanation of 30 October. Its explanation and map guide are in METHOD; its status is in STATUS and RESULTS (4 November) |
| [GRAPH_PHASE0_RESULTS_2026-10-25.md](archive/GRAPH_PHASE0_RESULTS_2026-10-25.md), [GRAPH_PHASE2A_NOTES_2026-10-25.md](archive/GRAPH_PHASE2A_NOTES_2026-10-25.md), [GRAPH_PHASE2B_NOTES_2026-10-27.md](archive/GRAPH_PHASE2B_NOTES_2026-10-27.md) | The phase notes. Combined, text unchanged, into RESULTS on 4 November |
| [COLLECTION_PROTOCOL.md](archive/COLLECTION_PROTOCOL.md) | The general collection protocol (13 October, before the pilots). Replaced by FIELD_PROTOCOL on 4 November |
| [WEST_LOOP_COLLECTION.md](archive/WEST_LOOP_COLLECTION.md) | The West Loop route plan of 19 October (78 modules, workload, routing comparison). Replaced by FIELD_PROTOCOL's one street per day on 4 November; its boundary and site checks moved there |
| [ROUTING_WORKFLOW.md](archive/ROUTING_WORKFLOW.md) | How `routes.py` (now `walk2net.plan`) and `route_methods.py` made and compared route plans. Background since the street-per-day scheme; `route_methods.py` was dropped on 4 November |
| [RIVER_NORTH_COLLECTION.md](archive/RIVER_NORTH_COLLECTION.md) | River North was dropped as the collection area. Its field rules F1–F8 were used until the briefing replaced them (4 November) |
| [PILOT2_PROTOCOL.md](archive/PILOT2_PROTOCOL.md) | Pilot 2 (16 October 2026), done. Its voice vocabulary is the one used in sessions before the briefing |
| [PILOT_PROTOCOL.md](archive/PILOT_PROTOCOL.md), [PILOT_NEAR_WEST_SIDE.md](archive/PILOT_NEAR_WEST_SIDE.md) | Pilot 1 (14 October 2026), done |
| [PILOT_DATA_PLAN.md](archive/PILOT_DATA_PLAN.md), [PILOT_DATA_TODO.md](archive/PILOT_DATA_TODO.md) | Pilot analysis plan, replaced by the graph phases |
| [RESEARCH_CRITIQUE_2026-10-23.md](archive/RESEARCH_CRITIQUE_2026-10-23.md), [HYPOTHESIS_EXPERIMENTS_2026-10-23.md](archive/HYPOTHESIS_EXPERIMENTS_2026-10-23.md) | Proposals folded into the graph plan and, from there, RESEARCH_PLAN |

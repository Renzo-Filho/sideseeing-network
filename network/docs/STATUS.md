# Sidewalk network: status

This is the **only page with dated status** for the network track. Other pages describe plans, methods and results as of their own date; update this page after each checkpoint instead of adding status banners elsewhere. Newest entry first.

## 3 November 2026: a new plan for the graph paper (draft)

After talking with the advisors: Tile2Net is the baseline. The first result is a network (nodes and edges) at least as accurate as Tile2Net's and better at corners and crossings; the enriched graph (widths, slopes, detections) comes second. The proposed method fuses the walk with Tile2Net's output. Draft: [GRAPH_PAPER_PLAN_2026-11-03.md](GRAPH_PAPER_PLAN_2026-11-03.md). Later the same day Renzo decided most of section 12: the walk's network stands on its own first, the fusion second; Tile2Net runs as released; the test is free-route walks drawn before the walk; the City's curbs are kept for now; reviewers double-label. The margins and the curb source are to review with the advisors. The pipeline is specified in [GRAPH_PIPELINE_2026-11-03.md](GRAPH_PIPELINE_2026-11-03.md), and a calibration day is planned for discussion in [CALIBRATION_DAY_PLAN_2026-11-03.md](CALIBRATION_DAY_PLAN_2026-11-03.md). Collection continues until early or mid December.

## 3 November 2026: the repository was reorganized

No research changed. The network track now has its own folder for everything: `docs/` (with `datasets/` and `archive/`), `graph/`, `scripts/`, `notebooks/` and `data/` (see [README](../README.md)). River North was dropped as the collection area and its documents are archived; West Loop is the collection area.

## Where things stand (from the 25 and 30 October documents)

**Collection, West Loop.**
- 8 sessions, 4.9 h, recorded on 19, 20 and 22 October 2026: Morgan (D1); Aberdeen, Madison and Carpenter (D2); Sangamon and Peoria with two collectors at once (D3) ([PAPERS.md](PAPERS.md) §1).
- More captures were made on 26 and 28 October (transfer manifests in [datasets/](datasets/)) and on 3 November. These documents do not describe them yet.

**Processing.** The desktop-01 run finished on 25 October: 17,499 frames, SAM3 for 37 prompts, redaction, Whisper and motion events. The zone prompts were run on D1–D2.

**Graph paper**, all on Morgan (D1) so far ([GRAPH_WORK_EXPLAINED](GRAPH_WORK_EXPLAINED_2026-10-30.md) §2):

| Phase | Status |
|---|---|
| G0 data contract | Done ([results](GRAPH_PHASE0_RESULTS_2026-10-25.md)) |
| G1 reference | Morgan done: 86 of 109 City curb pieces matched the 2025 orthophoto, 23 redrawn; back of the sidewalk from Cook parcels. It is off by about 0.5 m in places and needs one consistent pass |
| G2a walking lines | Fitted, with crossings tied to the far walking line ([notes](GRAPH_PHASE2A_NOTES_2026-10-25.md)) |
| G2b video measures | Curb distance and road width from the video. Camera height measured on the vest: 1.30 m ([notes](GRAPH_PHASE2B_NOTES_2026-10-27.md)) |
| G3–G6 | Not started |

Results as of 30 October:
- The corrected lines are never on the wrong half of the street. Raw GPS is there 15–29% of the time.
- The lines lie inside the sidewalk 42% of the way on the east side and 67% on the west. Raw GPS manages 18–36%.
- The two lines are 0.6 m closer together than the reference's sidewalk middles. At first they were 3.9 m closer.

The remaining error is mostly a shift that both lines share. Only the aerial photo can fix that.

**Dataset paper** (status of 25 October, [PAPERS.md](PAPERS.md) §3):
- D0 transfer: West Loop done; Brás at 433 of 649 jobs.
- D1 processing: West Loop done; Brás later, with the same prompts.
- D2–D6 (schema, labels, privacy, splits, release): not started.

## Next (priorities set 3 November 2026)

The rule for ordering them: **what can only be done in the field comes first**, because field access ends with collection (early or mid December). Everything computed can wait; a missing measurement cannot be taken afterwards. Detail in the [graph paper plan](GRAPH_PAPER_PLAN_2026-11-03.md).

**1. Before the next collection day**
1. `splits.csv`: every route-plan module marked development or test, and the free test routes drawn ([plan](GRAPH_PAPER_PLAN_2026-11-03.md) §5).
2. Start the daily routine ([calibration plan](CALIBRATION_DAY_PLAN_2026-11-03.md) §7): mount check, height, 10 m taped stretch.

**2. While collecting (November to early December)**
1. The calibration day on Morgan.
2. Walk the free test routes; keep D3 untouched.
3. After each day: transfer, desktop-01 processing, the automatic checks, split by module.
4. Inventory what the 26 and 28 October and 3 November captures cover.

**3. Computing, in parallel**
1. Run Tile2Net as released on West Loop (P1): the earliest risk check.
2. Reference pass on Morgan with the City's curbs (P2), then the scorer that reads Tile2Net's format (P3): Tile2Net's first scores.
3. The walk-only network on Morgan, then D2's corners (P4), scored next to Tile2Net on development data (Gate 1a's measures).
4. The data-review pre-step (S0), once the input-versus-reference rule is agreed.
5. Time-boxed in the gaps: Wi-Fi side cue (two weeks), Project Sidewalk models on a labelled sample (one week).

**4. With the advisors**

The Gate 1 margins, the curb source, the confirmation that the walk's network comes first and the fusion second.

**5. After collection ends**
1. Freeze every setting.
2. The fusion (P5).
3. Gates 1a and 1b, once, on the test routes and D3 (P6).
4. Enrichment and Gate 2 (P7).
5. Routes (P8).
6. The paper (P9).

**Open decisions for the dataset paper** (PAPERS.md): the size of the Brás agreement sample and who relabels it; venues.

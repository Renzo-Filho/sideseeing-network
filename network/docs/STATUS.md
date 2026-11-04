# Sidewalk network: status

This is the **only page with dated status** for the network track. Other pages describe plans, methods and results as of their own date; update this page after each checkpoint instead of adding status banners elsewhere. Newest entry first.

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

## Next

From [GRAPH_WORK_EXPLAINED](GRAPH_WORK_EXPLAINED_2026-10-30.md) §6 and [PAPERS.md](PAPERS.md) §5:
1. A first rough graph on Morgan: nodes at corners, walking lines as edges, crossings (level 0).
2. Sidewalk polygons from the curb and building-side edges, with edges becoming their centrelines (level 1).
3. Lens calibration from the checkerboard video, and the reference clean-up.
4. Corners and alternatives on D2 (G3), then the one-time held-out run on D3 (G4).
5. Comparisons with Tile2Net and OSM (G5), then the paper.

**Open decisions, for Renzo:** the size of the Brás agreement sample and who relabels it; a second labeller for the West Loop corners; venues.

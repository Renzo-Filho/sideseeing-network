# Chicago M3/M4 motorway-context holdout — 26 September 2026

## Decision

The Overture motorway-context flag **survived this small new CHI:49 stress sample**, but M3/M4 remain **unaccepted** for the Chicago-only model. The test supports motorway classification as part of the construction method; it does not establish complete physical blocks, Chicago-wide error rates or an accepted shape distribution.

## Design and frozen rule

`tile_selection.json` freezes four new centers in CHI:49 using seed 20260927 and only district geometry plus locally held Overture motorway distance. Two centers are within 30 m of motorway linework and two are 90–180 m away; they are at least 500 m from the prior fresh tiles, 280 m from old review cases and 550 m from each other. The selection used no ROW candidate or imagery. The 2025 Cook orthophotos were fetched at both 320 and 480 m width, with SHA-256 receipts in `imagery_receipts.json` and `wide_imagery_receipts.json`; the wider view was needed to see complete residential blocks. `visual_reference.json` contains seven rough block sketches and eight non-block landscape points drawn on the wide raw images before the candidate overlay was viewed.

The candidate method and motorway threshold were written to `analysis/config/chicago_m3_motorway_candidate_v1.json` before holdout candidate viewing: Cook active-road ROW plus ordinary Road Edge, mapped alleys reopened by a 1 m buffer, tile-contained land components ≥1,000 m², and a flag where at least 30% of a candidate's area lies within 40 m of Overture `class=motorway` centerlines. This threshold came from the earlier **development** tiles. The source mask does not fill the known West Veterans Place ROW gap.

## Observed result

The four wide tiles contain **35 tile-contained trial candidates**: 22 motorway-flagged and 13 kept. In the two motorway-core views, the flag marks freeway landscape and median fragments while keeping the two residential polygons that were closed within H1. Among the eight negative landscape points, only two fall inside qualifying pre-flag candidates; **both are flagged**, and none falls inside a kept candidate. See `negative_comparison.csv` and the four candidate overlays (cyan kept, red flagged).

Five of seven positive sketches have IoU ≥0.5 with a candidate (median over all seven: **0.751**); none of the seven best matches is motorway-flagged. The two low-overlap cases are explicitly unresolved in `reference_review.json`: H3_R03 has an uncertain curving street/freeway-edge outline, and H4_R01 crosses a curving cul-de-sac or loop that the ROW complement separates into two land components. Their original sketches and measured IoUs remain unchanged. A post-overlay audit also found complete north-row H3 blocks omitted by the initial sketches, so this reference **does not provide complete true-block recall or candidate precision**. It is a useful stress check, not an independent census. The same analyst performed both reviews; road-status and boundary adjudication still need an independent source or reviewer.

The development and holdout evidence together point to a practical construction path: use property-side road polygons for ordinary boundaries, reopen mapped alleys, use motorway classification to flag freeway land, and treat parcels as gap alerts rather than block IDs. It is not ready for citywide release until a street-gap method, airport/rail/private-access rules, and a genuinely complete independent block inventory pass their gates. M4 shape remains downstream of accepted M3 polygons.

## Reproduction

```bash
.venv/bin/python analysis/scripts/select_chicago_m3_motorway_holdout_2026_09_26.py
.venv/bin/python analysis/scripts/evaluate_chicago_m3_motorway_holdout_2026_09_26.py
```

The selector rechecks the frozen centers and verifies cached image hashes; image downloads are needed only if its ignored cache is absent. Source masks come from the preceding Cook ROW/Road Edge bounded cache. No 77-area feature table or model fit changed.

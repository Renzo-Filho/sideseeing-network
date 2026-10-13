# Cross-City Urban Explorer

A static visual-analytics page over the project's three cross-city methods: **Cross-City Urban Index A**, **Cross-City Urban Index B** ([protocol P-AB-1](../docs/SIMPLE_INDEX.md)) and the **harmonized cross-city similarity model**. The model opens on the proposed settings [`sp_chicago_model_v4`](../docs/harmonization/MODEL_REPORT.md#13-version-4-proposed-brás-focused-settings-13-october-2026) (not final): all-relative scaling, full distance, U1 and U6 25% each, B1 20%, U4 10%, M4 and M6 5% each, U2 4%, BV 3%, M1 2%, U3 1%, M3 and M7 off; inside U1 commerce 3, residential 2, industrial 1, institutional 0; inside M4 compactness 2, elongation 1. The earlier candidate [`sp_chicago_model_v3`](../docs/harmonization/MODEL_REPORT.md#12-version-3-final-settings-13-october-2026) is a preset. These are applied to the inputs of [`sp_chicago_model_v2`](../docs/harmonization/MODEL_REPORT.md#11-version-2-u1-commerce-share-8-october-2026), which include the U1 commerce share. Any of the 173 units (96 São Paulo districts, 77 Chicago Community Areas) can be the reference; every view is recomputed in the browser.

## Run it

```bash
# from the repository root
python3 -m http.server 8765 --directory viz
# then open http://127.0.0.1:8765/
```

Opening `index.html` directly from disk also works (classic scripts, no `fetch`). It needs internet for Plotly, MathJax and the IBM Plex fonts (cdnjs and Google Fonts).

## Deployment boundary

This directory is the complete browser application. For a later Vercel project, select `viz/` as the Root Directory and use the static **Other** framework preset with no build command; serve this directory as the output. The research code and result tables in `analysis/` are used to regenerate and verify `data.js` locally, but they are not needed by the deployed page.

## Pages

| Tab | What it shows |
|---|---|
| Overview | Objective, a reference picker with both city maps, each method's three closest units in the other city, data totals per city, the harmonized model's families and sources |
| Docs · Index A / Index B / Harmonized | Methodology with formatted formulas, pipeline, decisions, published test and robustness tables (filled from the result tables, never typed in), limits |
| Explore · Index A / Index B / Harmonized model | Closest 10 per city with what drives each match and rank change against a baseline; distance maps of both cities (or any feature); standardized radar profile with an axis guide; pairwise distance matrix; principal components (scatter, variance, loadings); Ward clusters (scatter, silhouette, maps, profiles, members) |
| Explore · Chicago tracts | The 77 Community Areas broken into 2020 census-tract pieces (801 published), placed against the reference with the Harmonized tab's current settings: a citywide tract map zoomed to the chosen area, the 15 closest tracts in Chicago with the rank each would take among the areas, the chosen area's tracts ranked with each family's share of the squared distance, and a profile table (reference, area, tract; raw and z) |

**Controls (left rail of each explorer).** Reference (shared by all methods); feature on/off and weight (0–3) per factor or family; for the harmonized families with several columns (U1's four land shares, M4's compactness and elongation) an **Inside** panel with a weight per column; Index A/B similarity rule (index gap, the agreed rule; or factor profile, the protocol's diagnostic); harmonized C6 scaling (hybrid, all-absolute, all-relative), full or PCA-truncated distance, and presets: **v4 · proposed** (the starting settings), **v3**, and the v2 runs R1–R3 (equal weights under the current scaling); number of clusters; baseline (the starting settings for the harmonized model, the published settings for Index A/B, or a pinned snapshot of your own). The weight sliders show the contract weights ×10 so they fit the 0–3 range; only their ratios matter. Clicking a unit in any chart, map or table adds it to the profile comparison (up to three).

## Files

| File | Role |
|---|---|
| `index.html` | Page shell, styles, documentation text |
| `app.js` | UI: state, routing, the SVG map component and every view (Plotly 3.5.1) |
| `model.js` | Pure computation, no DOM: block distances, index model, PCoA (Householder + QL), Ward, silhouette, Spearman, comparisons |
| `data.js` | Generated model inputs (`window.VIZ_DATA`); do not edit |
| `../analysis/tests/check_viz_model.js` | Research-side check that `model.js` reproduces the published results |
| `../analysis/scripts/chicago_tract_breakdown.py` | Recomputes the 21 model columns for every census-tract piece of the Chicago areas (read by the export) |

## Rebuild and check

```bash
.venv/bin/python analysis/scripts/export_viz_data.py   # rewrites data.js (~1.2 MB) from the accepted tables
node analysis/tests/check_viz_model.js                        # must print "all checks passed"
```

For the Chicago tracts tab, run `.venv/bin/python analysis/scripts/chicago_tract_breakdown.py` before the export when its inputs change (about 7 minutes; it writes `analysis/results/Chicago/chicago_tract_breakdown_2026_10_13/`).

`export_viz_data.py` exports **inputs**, not results: the min–max scaled factors of `index_A_B.csv`, and for each C6 scaling every distance block as `cm.blocks` builds it for the published fit (scaled columns or log-ratios, share and calibration). It also exports the named settings from `analysis/config/sp_chicago_model_v4.json` and `sp_chicago_model_v3.json` (the first is the starting settings) and each version's tables the documentation quotes. Fit them first with `.venv/bin/python analysis/scripts/sp_chicago_model_settings.py v4` (and `v3`). It adds each tract piece's rows to every block (field `T`), scored with the fit's own constants: a scalar column is standardized with the mean and SD the fit uses (the 77 Chicago areas for a relative column, all 173 units for an absolute one) and capped at ±3, and the U6 log-ratios are taken as the fit reads them. The export asserts that this scoring reproduces the areas' own rows. In the page, `projectedDistance` applies the current column weights, calibration β and family budgets to those rows. Unit polygons are simplified to 20 m in each city's projected CRS, tract pieces to 10 m. The family tables are read through `sp_chicago_model.load_inputs`, so their SHA-256 checks apply.

`analysis/tests/check_viz_model.js` asserts, against `analysis/results/SP_CHI/`: that each preset reproduces its version's distance matrix, inner weights included (v4 1.2e-10, v3 9.9e-11); the v2 R1, R2 and R3 distance matrices under all three scalings (max difference ~2e-10, the 10-decimal export precision); that the commerce share at column weight 0 reproduces the v1 R1 matrices under all three scalings; PCA explained variance; a leave-one-family-out sensitivity; the Ward partition, k and silhouette; Index A and B values and ranks; Brás's Chicago gap ranks and profile distances; and that `projectedDistance`, fed the Chicago areas' own rows, returns exactly their v4 and v3 distances to Brás.

## Notes on the method choices in the page

- **Index A and B have one dimension.** Their principal components and clusters use the weighted factor profile \(\sqrt{w_f}\,f'\); the ranking views follow the selected rule.
- **Weights.** The harmonized distance renormalizes family budgets over the active families (J-7, J-8), so only relative weights matter. Index weights multiply the scaled factors in the sum.
- **Weights inside a family.** A block's dissimilarity is the weighted mean of its columns' squared differences, $\sum_j v_j \Delta_j^2 / \sum_j v_j$ ($v_j = 1$ in the published fit), and its calibration $\beta_b$ is recomputed on the reweighted block. So "Inside U1: commerce 3, residential 1" changes the mix within U1, while U1's own slider still sets how much U1 counts against the other families. A column at 0 leaves the model; that is also how the R3 preset drops a single column (under all-absolute scaling R3 prunes the commerce share). The U6 log-ratios form one composition and are not reweighted.
- **Stable colours.** Principal-component signs and cluster numbers are aligned with the baseline, so colours and axes do not flip while weights change.
- **Tracts are scored, not refitted.** They do not enter the 173-unit model, its calibration or its match strength. The tab uses the full distance even when the Harmonized tab is on the PCA geometry.
- **Not recomputed in the page:** the 500 weight draws and the J-9 alternative definitions (robust and rank scaling, Mahalanobis, substitutes); their published tables are in the Harmonized documentation tab.

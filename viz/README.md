# Cross-City Urban Explorer

A static visual-analytics page over the project's three cross-city methods: **Cross-City Urban Index A**, **Cross-City Urban Index B** ([protocol P-AB-1](../docs/SIMPLE_INDEX.md)) and the **harmonized cross-city similarity model** ([`sp_chicago_model_v2`](../docs/harmonization/MODEL_REPORT.md#11-version-2-u1-commerce-share-8-october-2026), with the U1 commerce share). Any of the 173 units (96 São Paulo districts, 77 Chicago Community Areas) can be the reference; every view is recomputed in the browser.

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

**Controls (left rail of each explorer).** Reference (shared by all methods); feature on/off and weight (0–3) per factor or family; for the harmonized families with several columns (U1's four land shares, M4's compactness and elongation) an **Inside** panel with a weight per column; Index A/B similarity rule (index gap, the agreed rule; or factor profile, the protocol's diagnostic); harmonized C6 scaling (hybrid, all-absolute, all-relative), full or PCA-truncated distance, and presets for the published runs R1–R3; number of clusters; baseline (published settings, or a pinned snapshot of your own). Clicking a unit in any chart, map or table adds it to the profile comparison (up to three).

## Files

| File | Role |
|---|---|
| `index.html` | Page shell, styles, documentation text |
| `app.js` | UI: state, routing, the SVG map component and every view (Plotly 3.5.1) |
| `model.js` | Pure computation, no DOM: block distances, index model, PCoA (Householder + QL), Ward, silhouette, Spearman, comparisons |
| `data.js` | Generated model inputs (`window.VIZ_DATA`); do not edit |
| `../analysis/tests/check_viz_model.js` | Research-side check that `model.js` reproduces the published results |

## Rebuild and check

```bash
.venv/bin/python analysis/scripts/export_viz_data.py   # rewrites data.js (~0.4 MB) from the accepted tables
node analysis/tests/check_viz_model.js                        # must print "all checks passed"
```

`export_viz_data.py` exports **inputs**, not results: the min–max scaled factors of `index_A_B.csv`, and for each C6 scaling every distance block as `cm.blocks` builds it for the published fit (scaled columns or log-ratios, share and calibration). Unit polygons are simplified to 20 m in each city's projected CRS. The family tables are read through `sp_chicago_model.load_inputs`, so their SHA-256 checks apply.

`analysis/tests/check_viz_model.js` asserts, against `analysis/results/SP_CHI/`: the v2 R1, R2 and R3 distance matrices under all three scalings (max difference ~2e-10, the 10-decimal export precision); that the commerce share at column weight 0 reproduces the v1 R1 matrices under all three scalings; PCA explained variance; a leave-one-family-out sensitivity; the Ward partition, k and silhouette; Index A and B values and ranks; Brás's Chicago gap ranks and profile distances.

## Notes on the method choices in the page

- **Index A and B have one dimension.** Their principal components and clusters use the weighted factor profile \(\sqrt{w_f}\,f'\); the ranking views follow the selected rule.
- **Weights.** The harmonized distance renormalizes family budgets over the active families (J-7, J-8), so only relative weights matter. Index weights multiply the scaled factors in the sum.
- **Weights inside a family.** A block's dissimilarity is the weighted mean of its columns' squared differences, $\sum_j v_j \Delta_j^2 / \sum_j v_j$ ($v_j = 1$ in the published fit), and its calibration $\beta_b$ is recomputed on the reweighted block. So "Inside U1: commerce 3, residential 1" changes the mix within U1, while U1's own slider still sets how much U1 counts against the other families. A column at 0 leaves the model; that is also how the R3 preset drops a single column (under all-absolute scaling R3 prunes the commerce share). The U6 log-ratios form one composition and are not reweighted.
- **Stable colours.** Principal-component signs and cluster numbers are aligned with the baseline, so colours and axes do not flip while weights change.
- **Not recomputed in the page:** the 500 weight draws and the J-9 alternative definitions (robust and rank scaling, Mahalanobis, substitutes); their published tables are in the Harmonized documentation tab.

# Chicago block methods: established baselines and current candidate, diagnostic v1

**Date:** 26 September 2026. **Decision:** M3/M4 remain unaccepted. This run compares existing methods and the currently implemented Chicago ROW candidate on the frozen *selected* imagery sketches. It does not test the full future gap-repair and adjudication protocol, and it cannot estimate Chicago-wide precision or recall.

## Methods and reproducibility

All geometries are in EPSG:26916. The input and reference SHA-256 hashes and software versions are in [`summary.json`](summary.json). The rough references were drawn before candidate overlays, but they do not inventory every block; two new-location sketches were later marked ambiguous without editing their rings.

1. **Established enclosure:** [`momepy.enclosures`](https://docs.momepy.org/stable/api/momepy.enclosures.html) on eligible Chicago municipal street centerlines in a 450 m half-width halo around each reference tile.
2. **Source-matched face construction:** noded Shapely polygonization of those *same* municipal lines and halo. This isolates the face-building implementation from the boundary source.
3. **Published artifact heuristic:** circular compactness face-artifact index from [Fleischmann and Vybornova (2024)](https://josis.org/index.php/josis/article/download/319/189/1285), using the [momepy `FaceArtifacts` default KDE/peak procedure](https://docs.momepy.org/stable/api/momepy.FaceArtifacts.html). Because `esda` is absent from this environment, the script reproduces the index and threshold code directly with Shapely and SciPy. The threshold is fitted to all 19,359 existing municipal planar faces **before scoring the local sketches**. It is then applied to local municipal enclosures. The formula is `log(area × area/minimum_bounding_circle_area)`.
4. **Current Chicago candidate:** Cook ROW with mapped alleys reopened in the development tiles; the frozen ROW + ordinary Road Edge candidate with alleys reopened and the 40 m/30% motorway review flag in the four new CHI:49 tiles. Thus the ROW column changes slightly between samples. These are **different boundary inputs** from the municipal centerline runs; the comparison measures practical candidate outcomes, not an isolated algorithm effect.

Run from the repository root, using the locally cached sources:

```bash
MPLCONFIGDIR=/tmp/mplconfig_chicago_blocks .venv/bin/python analysis/scripts/evaluate_chicago_m3_established_methods_2026_09_26.py
```

The [`paired_positive_comparison.csv`](paired_positive_comparison.csv), [`negative_controls.csv`](negative_controls.csv), [`tile_face_counts.csv`](tile_face_counts.csv), and [`published_threshold.json`](published_threshold.json) give case-level results. The prior [candidate protocol pilot](../chicago_block_protocol_pilot_v1_2026_09_26/README.md) records the ROW motorway flag and gap cases.

## Results

| Comparison on clear rough sketches | Municipal centerline enclosure | Current ROW candidate |
|---|---:|---:|
| Development, 11 sketches: median IoU | 0.758 | 0.827 |
| New CHI:49 locations, 5 clear sketches: median IoU | 0.895 | 0.758 |
| Pooled, 16 clear sketches: median IoU | 0.828 | 0.808 |
| Pooled sketches with IoU ≥ 0.5 | 14/16 | 16/16 |
| Pooled median absolute log area error | 0.167 | 0.158 |
| Pooled median absolute compactness error | 0.014 | 0.099 |

The municipal enclosure has higher IoU on **10 of 16** clear cases, and the ROW candidate has higher IoU on six. In particular, ROW resolves the two Loop sketches where centerline IoU is only **0.393 and 0.329**; the ROW IoUs are **0.827 and 0.851**. At the five clear new CHI:49 sketches, municipal centerlines perform better on all five, marginally in one. The pooled medians mix deliberately selected contexts, so they are **not a representative Chicago ranking**. The compactness comparison is also sensitive to the reference’s approximate, often rectangular imagery sketches; it does not certify M4 shape accuracy.

On exactly the same linework and halos, momepy and Shapely returned **identical polygon sets in all 14 tiles** and identical positive-sketch IoUs. This shows there is no polygonization advantage in the custom code on these inputs. It leaves source coverage, grade, boundary position and artifact decisions as the substantive questions.

The published face-artifact rule found two density peaks and a threshold of **7.052**. It flags **1,806/19,359** citywide experimental municipal faces. Excluding the 505 city-edge faces changes the threshold only to **7.058**. On the local selected controls, it flags **0/16 clear positive sketches** and **3/12 non-block points**. Only five of those non-block points lie in a closed face wholly within the halo; **2/5** of those are flagged. The other points include water, airport land and halo-touching landscape, which shape alone is not intended to classify. This is a useful additional review signal, not a validated rejection filter. Its citywide flag count is **not** a count of false blocks.

The current Chicago motorway rule had previously flagged **9/9** reviewed development freeway islands; in the new CHI:49 sample it flagged both non-block controls that lay inside ROW candidates while retaining five clear positive sketches. Its threshold was selected on development cases, and the new reference omits visible blocks. Neither this nor the published shape index supplies independent citywide error rates.

## Evaluation and next gate

The evidence favors a **hybrid investigation**, not automatic replacement of the established method. Retain municipal enclosures as an explicit baseline and possible gap alert; retain ROW geometry where its property-side edge improves a verified block; retain the published face index and motorway exposure as separately reported review flags. A source-matched geometry comparison needs a common face-building operation with municipal and ROW-derived boundary lines plus a complete reference. West Veterans Place still causes a known ROW merge because its corridor is absent from ROW/Road Edge; no general repair has been implemented or validated.

Before M3/M4 approval, freeze a complete independently reviewed reference in large pilot zones; repair and retest named-street gaps; count true and false faces, splits and merges; measure boundary/area/shape errors by context; and test the combined workflow on an untouched holdout. No numerical release threshold can be inferred from these selected sketches. The full staged method is in the [Chicago physical block protocol](../../../../docs/chicago/CHICAGO_PHYSICAL_BLOCK_PROTOCOL_V1.md).

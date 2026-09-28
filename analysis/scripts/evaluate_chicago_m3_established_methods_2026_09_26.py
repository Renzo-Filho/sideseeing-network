"""Diagnostic Chicago comparison of established centerline faces and ROW candidates.

The imagery references are selected rough sketches, not a complete blind census.
The published face-artifact index is fitted on the full existing municipal
centerline-face inventory, then transferred to faces from the same road source
in local reference halos. No threshold is tuned on the reference cases.
"""
from __future__ import annotations

import hashlib
import json
import math
import warnings
from pathlib import Path

import geopandas as gpd
import momepy
import numpy as np
import pandas as pd
import shapely
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde
from shapely.geometry import Polygon, box

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import pixel_point
from evaluate_chicago_m3_motorway_holdout_2026_09_26 import point as holdout_point

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
FRESH = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
HOLD = A / "results/Chicago/chicago_m3_motorway_holdout_2026_09_26"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
CITY_FACES = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/experimental_blocks.parquet"
OUT = A / "results/Chicago/chicago_block_method_comparison_v1_2026_09_26"
HALO_M = 450


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_index(geoms) -> np.ndarray:
    areas = shapely.area(geoms)
    circle_areas = shapely.area(shapely.minimum_bounding_circle(geoms))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(areas * areas / circle_areas)


def fit_published_threshold(values: np.ndarray) -> tuple[float | None, dict]:
    """Replicate momepy.FaceArtifacts circular-compactness KDE defaults.

    Fleischmann and Vybornova (2024): F=log(area*area/minimum-circle-area),
    Silverman KDE on 1000 steps, first valley between peaks bracketing the
    highest peak; momepy defaults height_maxs=.008, prominence=.00075.
    """
    grid = np.linspace(float(values.min()), float(values.max()), 1000)
    density = gaussian_kde(values, bw_method="silverman")(grid)
    peaks, peak_meta = find_peaks(density, height=.008, prominence=.00075, width=1)
    valleys, _ = find_peaks(-density + 1, prominence=.00075, width=1)
    threshold = None
    if len(peaks) > 1 and len(valleys):
        highest = peaks[int(np.argmax(peak_meta["peak_heights"]))]
        bounds = [(lo, hi) for lo, hi in zip(peaks[:-1], peaks[1:]) if lo <= highest <= hi]
        between = [v for v in valleys if any(lo < v < hi for lo, hi in bounds)]
        if between:
            threshold = float(grid[between[0]])
    diagnostic = {
        "peak_positions": [float(grid[i]) for i in peaks],
        "valley_positions": [float(grid[i]) for i in valleys],
        "threshold": threshold,
    }
    return threshold, diagnostic


def iou(a, b) -> float:
    return float(a.intersection(b).area / a.union(b).area)


def compactness(geom) -> float:
    return float(4 * math.pi * geom.area / geom.length**2)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    city = gpd.read_parquet(CITY_FACES)
    fitted = artifact_index(city.geometry.array)
    valid = fitted[np.isfinite(fitted)]
    threshold, fit = fit_published_threshold(valid)
    interior_values = fitted[~city.edge_flag.to_numpy()]
    interior_values = interior_values[np.isfinite(interior_values)]
    interior_threshold, interior_fit = fit_published_threshold(interior_values)
    if threshold is None:
        warnings.warn("Published face-artifact rule found no threshold; no flags assigned")
    fit.update({"city_face_count": len(city), "valid_index_count": len(valid),
                "city_faces_below_threshold": int((valid < threshold).sum()) if threshold is not None else None,
                "city_faces_edge_flag_count": int(city.edge_flag.sum()),
                "non_edge_sensitivity": {"face_count": len(interior_values),
                                         "fit": interior_fit,
                                         "faces_below_threshold": int((interior_values < interior_threshold).sum()) if interior_threshold is not None else None},
                "formula": "log(area_m2 * (area_m2 / minimum_bounding_circle_area_m2))",
                "fit_population": "existing Chicago experimental municipal planar faces, including boundary faces",
                "parameters": {"kde": "Silverman", "grid_points": 1000,
                               "peak_min_height": .008, "peak_min_prominence": .00075}})

    roads = gpd.read_parquet(ROADS)
    fresh_tiles = {t["tile_id"]: t for t in json.loads((FRESH / "tile_selection.json").read_text())["tiles"]}
    hold_tiles = {t["tile_id"]: t for t in json.loads((HOLD / "tile_selection.json").read_text())["tiles"]}
    fresh_refs = json.loads((FRESH / "visual_reference.json").read_text())
    hold_refs = json.loads((HOLD / "visual_reference.json").read_text())
    ambiguous = {c["reference_id"] for c in json.loads((HOLD / "reference_review.json").read_text())["cases"]}
    positive = []
    negative = []
    tile_rows = []
    for sample, tiles, refs in (("development", fresh_tiles, fresh_refs),
                                ("new_location", hold_tiles, hold_refs)):
        for tile_id in sorted({r["tile_id"] for kind in ("positive_polygons", "negative_points")
                               for r in refs[kind]}):
            tile = tiles[tile_id]
            x, y = tile["x"], tile["y"]
            halo = box(x-HALO_M, y-HALO_M, x+HALO_M, y+HALO_M)
            subset = roads.iloc[roads.sindex.query(halo, predicate="intersects")]
            momepy_faces = [g for g in momepy.enclosures(subset.geometry, limit=halo).geometry
                            if g.geom_type == "Polygon" and g.area > 0]
            noded = shapely.union_all([*subset.geometry, halo.boundary])
            shapely_faces = [g for g in shapely.get_parts(shapely.polygonize(shapely.get_parts(noded)))
                             if g.geom_type == "Polygon" and g.area > 0]
            momepy_keys = {shapely.to_wkb(shapely.normalize(g)) for g in momepy_faces}
            shapely_keys = {shapely.to_wkb(shapely.normalize(g)) for g in shapely_faces}
            tile_rows.append({"sample": sample, "tile_id": tile_id,
                              "municipal_segments_in_halo": len(subset),
                              "momepy_face_count": len(momepy_faces),
                              "shapely_face_count": len(shapely_faces),
                              "face_sets_exactly_equal": momepy_keys == shapely_keys})
            for ref in (r for r in refs["positive_polygons"] if r["tile_id"] == tile_id):
                geom = Polygon([pixel_point(tile, p).coords[0] if sample == "development"
                                else holdout_point(tile, p).coords[0] for p in ref["pixel_ring"]])
                row = {"sample": sample, "reference_id": ref["id"], "tile_id": tile_id,
                       "context": ref["context"], "reference_status": "ambiguous" if ref["id"] in ambiguous else "rough_positive",
                       "reference_area_m2": geom.area,
                       "reference_compactness": compactness(geom)}
                for method, faces in (("momepy", momepy_faces), ("shapely", shapely_faces)):
                    best = max(faces, key=lambda g: g.intersection(geom).area)
                    row[f"{method}_iou"] = iou(best, geom)
                    row[f"{method}_area_m2"] = best.area
                    row[f"{method}_compactness"] = compactness(best)
                    row[f"{method}_touches_halo"] = bool(best.boundary.intersects(halo.boundary))
                    if method == "momepy":
                        index = float(artifact_index(np.array([best], dtype=object))[0])
                        row["published_face_index"] = index
                        row["published_artifact_flag"] = bool(index < threshold) if threshold is not None else None
                positive.append(row)
            for ref in (r for r in refs["negative_points"] if r["tile_id"] == tile_id):
                p = pixel_point(tile, ref["pixel_xy"]) if sample == "development" else holdout_point(tile, ref["pixel_xy"])
                row = {"sample": sample, "reference_id": ref["id"], "tile_id": tile_id,
                       "context": ref["context"]}
                for method, faces in (("momepy", momepy_faces), ("shapely", shapely_faces)):
                    match = next((g for g in faces if g.covers(p)), None)
                    row[f"{method}_face_at_point"] = match is not None
                    row[f"{method}_face_touches_halo"] = bool(match.boundary.intersects(halo.boundary)) if match is not None else None
                    if method == "momepy":
                        index = float(artifact_index(np.array([match], dtype=object))[0]) if match is not None else None
                        row["published_face_index"] = index
                        row["published_artifact_flag"] = bool(index < threshold) if index is not None and threshold is not None else None
                negative.append(row)
    pos = pd.DataFrame(positive)
    neg = pd.DataFrame(negative)
    pos.to_csv(OUT / "positive_comparison.csv", index=False)
    neg.to_csv(OUT / "negative_controls.csv", index=False)
    pd.DataFrame(tile_rows).to_csv(OUT / "tile_face_counts.csv", index=False)
    (OUT / "published_threshold.json").write_text(json.dumps(fit, indent=2) + "\n")

    clear = pos.reference_status.eq("rough_positive")
    old_row = pd.read_csv(FRESH / "positive_reference_comparison.csv")
    old_row = old_row.loc[old_row["mode"].eq("cook_row_alley_open"),
                          ["reference_id", "best_component_iou", "best_component_area_m2", "component_compactness"]]
    old_row = old_row.rename(columns={"best_component_iou": "row_candidate_iou",
                                      "best_component_area_m2": "row_candidate_area_m2",
                                      "component_compactness": "row_candidate_compactness"})
    hold_row = pd.read_csv(HOLD / "positive_comparison.csv")[["reference_id", "best_iou", "matched_candidate"]]
    hold_candidates = pd.read_csv(HOLD / "holdout_candidates.csv")[["component_id", "area_m2", "compactness"]]
    hold_row = hold_row.merge(hold_candidates, left_on="matched_candidate", right_on="component_id", validate="many_to_one")
    hold_row = hold_row.rename(columns={"best_iou": "row_candidate_iou", "area_m2": "row_candidate_area_m2",
                                        "compactness": "row_candidate_compactness"})
    row_scores = pd.concat([old_row, hold_row[["reference_id", "row_candidate_iou", "row_candidate_area_m2",
                                               "row_candidate_compactness"]]])
    paired = pos.merge(row_scores, on="reference_id", validate="one_to_one")
    for method in ("momepy", "row_candidate"):
        paired[f"{method}_abs_log_area_error"] = np.abs(np.log(paired[f"{method}_area_m2"] / paired.reference_area_m2))
        paired[f"{method}_abs_compactness_error"] = np.abs(paired[f"{method}_compactness"] - paired.reference_compactness)
    paired.to_csv(OUT / "paired_positive_comparison.csv", index=False)
    clear_paired = paired[paired.reference_status.eq("rough_positive")]
    development = paired[paired["sample"].eq("development")]
    new_clear = clear_paired[clear_paired["sample"].eq("new_location")]
    summary = {
        "scope": "diagnostic selected imagery references; no complete independent census",
        "clear_positive_count": int(clear.sum()),
        "ambiguous_positive_count": int((~clear).sum()),
        "negative_point_count": len(neg),
        "development_median_iou": {k: float(development[k].median()) for k in
                                    ("momepy_iou", "shapely_iou", "row_candidate_iou")},
        "new_location_clear_median_iou": {k: float(new_clear[k].median()) for k in
                                          ("momepy_iou", "shapely_iou", "row_candidate_iou")},
        "pooled_clear_median_iou": {k: float(clear_paired[k].median()) for k in
                                    ("momepy_iou", "shapely_iou", "row_candidate_iou")},
        "pooled_clear_iou_ge_half": {k: int(clear_paired[k].ge(.5).sum()) for k in
                                     ("momepy_iou", "shapely_iou", "row_candidate_iou")},
        "pooled_clear_median_absolute_log_area_error": {k: float(clear_paired[f"{k}_abs_log_area_error"].median())
                                                        for k in ("momepy", "row_candidate")},
        "pooled_clear_median_absolute_compactness_error": {k: float(clear_paired[f"{k}_abs_compactness_error"].median())
                                                           for k in ("momepy", "row_candidate")},
        "momepy_beats_row_clear": int(clear_paired.momepy_iou.gt(clear_paired.row_candidate_iou).sum()),
        "published_flag_clear_positives": int(clear_paired.published_artifact_flag.sum()),
        "published_flag_negative_points": int(neg.published_artifact_flag.sum()),
        "published_threshold": threshold,
        "momepy_shapely_iou_max_absolute_difference": float((pos.momepy_iou - pos.shapely_iou).abs().max()),
        "momepy_shapely_exact_tile_face_sets": int(pd.DataFrame(tile_rows).face_sets_exactly_equal.sum()),
        "tile_count": len(tile_rows),
        "momepy_positive_halo_touch_count": int(pos.momepy_touches_halo.sum()),
        "notes": ["The published filter was fitted to full municipal centerline faces, not to the reference sketches.",
                  "ROW candidate comparison uses different boundary source and processing; it is not algorithm-matched.",
                  "Negative points are targeted controls, not a census of false faces.",
                  "The current ROW candidate has no general source-gap repair and is not the full proposed method."],
        "inputs_sha256": {str(p.relative_to(ROOT)): digest(p) for p in
                           (ROADS, CITY_FACES, FRESH / "tile_selection.json", FRESH / "visual_reference.json",
                            HOLD / "tile_selection.json", HOLD / "visual_reference.json",
                            HOLD / "reference_review.json", FRESH / "positive_reference_comparison.csv",
                            HOLD / "positive_comparison.csv", HOLD / "holdout_candidates.csv",
                            Path(__file__))},
        "versions": {"momepy": momepy.__version__, "shapely": shapely.__version__},
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

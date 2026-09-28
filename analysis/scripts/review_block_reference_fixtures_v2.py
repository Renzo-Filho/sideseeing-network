"""Compare two paired block fixtures with independent local block references.

Reference overlap is diagnostic: Census blocks and municipal Quadra are not one
common physical-block ontology. Do not use this script to accept M3/M4.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely

from harmonization.geometry import largest_overlap
from harmonization.road_intervals import boundary_parts
from harmonization.roads import enclosure_polygons, shape_metrics
from review_block_boundary_pilots_v2 import has_bridge_or_tunnel, source_properties

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures"
PILOTS = [
    ("Chicago", "CHI:32", "32", "Chicago/chi_local_2026_09_16_v1/districts.parquet",
     "Chicago/chi_functional_2026_09_16_v2/blocks.parquet", (448511.6, 4637139.0), "GEOID20"),
    ("SP", "SP:10", "10", "SP/sp_prep_2026_09_10_v3/N02/districts.parquet",
     "SP/sp_prep_2026_09_10_v3/N06/blocks.parquet", (334496.2, 7395335.1),
     "cd_identificador_quadra_viaria_editada"),
    *[("Chicago", f"CHI:{local_id}", local_id,
       "Chicago/chi_local_2026_09_16_v1/districts.parquet",
       "Chicago/chi_functional_2026_09_16_v2/blocks.parquet", None, "GEOID20")
      for local_id in ("24", "28", "30", "76")],
    *[("SP", f"SP:{local_id}", local_id,
       "SP/sp_prep_2026_09_10_v3/N02/districts.parquet",
       "SP/sp_prep_2026_09_10_v3/N06/blocks.parquet", None,
       "cd_identificador_quadra_viaria_editada")
      for local_id in ("30", "35")],
]
MODES = ["all_mapped_streets", "without_links", "without_links_bridges_tunnels",
         "interval_aware_candidate"]


def owned_polygons(lines, district, extraction, districts, local_id):
    poly = enclosure_polygons(lines)
    if len(poly):
        poly = poly[shapely.intersects(poly, district) & shapely.covers(extraction, poly)]
    if not len(poly):
        return gpd.GeoDataFrame(geometry=[], crs=districts.crs)
    frames = gpd.GeoDataFrame(geometry=poly, crs=districts.crs)
    owners = largest_overlap(frames, districts)
    frames = frames.loc[owners.astype(str).eq(local_id)].reset_index(drop=True)
    return frames


def match_best(source, target, id_col):
    """Best whole-object IoU; unmatched objects retain zero score."""
    best_ids, scores = [], []
    for geometry in source.geometry:
        options = target.sindex.query(geometry, predicate="intersects")
        best_id, best_score = None, 0.0
        for pos in options:
            other = target.geometry.iloc[pos]
            intersection = geometry.intersection(other).area
            union = geometry.area + other.area - intersection
            score = intersection / union if union > 0 else 0.0
            if score > best_score:
                best_id, best_score = target.iloc[pos][id_col], score
        best_ids.append(best_id)
        scores.append(best_score)
    return best_ids, np.asarray(scores)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prior = pd.read_csv(A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/paired_boundary_sensitivity.csv")
    summaries = []
    for city, unit, local_id, district_path, reference_path, center, ref_id in PILOTS:
        roads = gpd.read_parquet(A / "work/prepared" / city / "overture_2026_08_19_review_v1/selected_roads.parquet")
        districts = gpd.read_parquet(A / "work/prepared" / district_path)
        if city == "SP":
            districts["unit_id"] = "SP:" + districts.district_id.astype(str).str.zfill(2)
        district = districts.loc[districts.unit_id.eq(unit)].geometry.item()
        extraction = district.buffer(250)
        selected = roads.iloc[roads.sindex.query(extraction, predicate="intersects")].copy()
        props = source_properties(city, set(selected.id))
        reference = gpd.read_parquet(A / "work/prepared" / reference_path)
        reference = reference.iloc[reference.sindex.query(district, predicate="intersects")].copy()
        if city == "SP":
            reference = reference.loc[reference.eligible_type].copy()
        owners = largest_overlap(reference, districts)
        reference = reference.loc[owners.astype(str).eq(local_id).to_numpy()].reset_index(drop=True)
        if not reference.geometry.is_valid.all():
            raise ValueError("Invalid reference geometry")
        if reference.crs != roads.crs:
            raise ValueError("Reference CRS mismatch")
        reference["reference_id"] = reference[ref_id].astype(str)
        reference[["reference_id", "geometry"]].to_parquet(OUT / f"{unit.replace(':','_')}_reference.parquet")
        base = selected.loc[selected.subclass.ne("link")]
        modes = {
            "all_mapped_streets": selected.geometry.values,
            "without_links": base.geometry.values,
            "without_links_bridges_tunnels": base.loc[~base.road_flags.map(has_bridge_or_tunnel)].geometry.values,
        }
        parts = []
        for road in selected.itertuples():
            raw = props[road.id]
            parts.extend(boundary_parts(road.geometry, subclass=raw["subclass"],
                                        subclass_rules=raw["subclass_rules"],
                                        level_rules=raw["level_rules"], road_flags=raw["road_flags"]))
        modes["interval_aware_candidate"] = parts
        candidates_by_mode = {}
        for mode in MODES:
            candidate = owned_polygons(modes[mode], district, extraction, districts, local_id)
            expected = prior.loc[prior.unit_id.eq(unit) & prior.boundary_mode.eq(mode), "whole_enclosures_owned"].item()
            if len(candidate) != expected:
                raise ValueError(f"{unit}/{mode}: {len(candidate)} != prior {expected}")
            candidate["candidate_id"] = [f"{unit}:{mode}:{i:04d}" for i in range(len(candidate))]
            candidate["area_m2"] = candidate.geometry.area
            candidate["min_width_m"] = shape_metrics(candidate.geometry.values).rectangle_min_width_m.values
            match_id, score = match_best(candidate, reference, "reference_id")
            candidate["best_reference_id"] = match_id
            candidate["best_reference_iou"] = score
            candidate.to_parquet(OUT / f"{unit.replace(':','_')}_{mode}.parquet")
            _, reverse = match_best(reference, candidate, "candidate_id")
            summaries.append({
                "unit_id": unit, "boundary_mode": mode,
                "candidate_count": len(candidate), "reference_count": len(reference),
                "candidate_median_best_iou": float(np.median(score)),
                "candidate_share_best_iou_ge_050": float(np.mean(score >= .5)),
                "reference_median_best_iou": float(np.median(reverse)),
                "reference_share_best_iou_ge_050": float(np.mean(reverse >= .5)),
                "reference_role": "city_specific_diagnostic_not_common_input",
            })
            candidates_by_mode[mode] = candidate
            print(unit, mode, len(candidate), "median IoU", round(float(np.median(score)), 3), flush=True)
        if center is None:
            continue
        fig, axes = plt.subplots(2, 2, figsize=(12, 12), sharex=True, sharey=True)
        x, y = center
        for ax, mode in zip(axes.flat, MODES):
            c = candidates_by_mode[mode]
            window = shapely.box(x - 200, y - 200, x + 200, y + 200)
            c = c.iloc[c.sindex.query(window, predicate="intersects")]
            r = reference.iloc[reference.sindex.query(window, predicate="intersects")]
            if len(c):
                c.plot(ax=ax, column="best_reference_iou", cmap="RdYlGn", vmin=0, vmax=1,
                       edgecolor="#333333", linewidth=.5)
            if len(r):
                r.boundary.plot(ax=ax, color="#1261a0", linewidth=1.2)
            ax.set_title(mode + f" (n={len(c)} in view)")
            ax.set_xlim(x - 200, x + 200)
            ax.set_ylim(y - 200, y + 200)
            ax.set_aspect("equal")
        fig.suptitle(unit + " candidate polygons by best reference IoU; blue = local reference")
        fig.savefig(OUT / f"{unit.replace(':','_')}_reference_comparison.png", dpi=170, bbox_inches="tight")
        plt.close(fig)
    pd.DataFrame(summaries).to_csv(OUT / "reference_overlap_summary.csv", index=False)


if __name__ == "__main__":
    main()

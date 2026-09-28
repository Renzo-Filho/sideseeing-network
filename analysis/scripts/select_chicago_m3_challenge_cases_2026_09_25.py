"""Freeze low-Census-overlap M3 challenge cases before OSM/imagery inspection."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyogrio
import shapely

from harmonization.geometry import largest_overlap
from harmonization.roads import shape_metrics
from review_block_reference_fixtures_v2 import owned_polygons

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_external_sources_2026_09_25"
UNITS = ["CHI:11", "CHI:49", "CHI:57", "CHI:63"]


def main():
    out = OUT / "challenge_case_selection.json"
    if out.exists():
        print("Frozen selection already exists:", out)
        return
    roads = gpd.read_parquet(A / "work/prepared/Chicago/overture_2026_08_19_review_v1/selected_roads.parquet")
    districts = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet")
    blocks = gpd.read_parquet(A / "work/prepared/Chicago/chi_functional_2026_09_16_v2/blocks.parquet")
    rail = pyogrio.read_dataframe(A / "data/Chicago/LUI_2023_view_332920193481040239.gpkg",
                                   where="LANDUSE = '1511'", columns=["LANDUSE"]).to_crs(roads.crs)
    earlier = json.loads((A / "results/Chicago/chicago_m_physical_cases_2026_09_25/case_selection.json").read_text())
    hold = json.loads((A / "results/Chicago/chicago_m_holdout_2026_09_25/case_selection.json").read_text())
    new = json.loads((OUT / "new_case_selection.json").read_text())
    known = {c["queue_id"] for c in earlier["cases"] + hold["cases"] + new["cases"] if c["family"] == "M3/M4"}
    cases = []
    for unit in UNITS:
        local_id = unit.split(":")[1]
        district = districts.loc[districts.unit_id.eq(unit)].geometry.item()
        extraction = district.buffer(250)
        local_roads = roads.iloc[roads.sindex.query(extraction, predicate="intersects")]
        local_rail = rail.iloc[rail.sindex.query(extraction, predicate="intersects")]
        rail_union = shapely.union_all(shapely.make_valid(local_rail.geometry.values)) if len(local_rail) else shapely.GeometryCollection()
        base = list(local_roads.loc[local_roads.subclass.ne("link")].geometry.values)
        modes = {"no_links": base,
                 "no_links_rail_row": base + list(shapely.get_parts(rail_union.boundary))}
        reference = blocks.loc[blocks.intersects(district)].copy()
        owned = largest_overlap(reference, districts).astype(str).eq(local_id)
        reference = reference.loc[owned.to_numpy()]
        for mode, lines in modes.items():
            candidates = owned_polygons(lines, district, extraction, districts, local_id)
            if mode == "no_links_rail_row" and len(candidates) and not rail_union.is_empty:
                rail_fraction = [g.intersection(rail_union).area / g.area for g in candidates.geometry]
                candidates = candidates.loc[np.asarray(rail_fraction) <= .5].reset_index(drop=True)
            candidates["candidate_id"] = [f"{unit}:{mode}:{i}" for i in range(len(candidates))]
            metrics = shape_metrics(candidates.geometry.values)
            candidates["area_m2"] = metrics.area_m2.to_numpy()
            candidates["min_width_m"] = metrics.rectangle_min_width_m.to_numpy()
            eligible = candidates.loc[(candidates.area_m2 >= 1000) & (candidates.min_width_m >= 15)
                                      & ~candidates.candidate_id.isin(known)].copy()
            eligible = eligible.loc[eligible.geometry.intersection(district).area / eligible.geometry.area > .99]
            if eligible.empty:
                raise RuntimeError(f"No eligible challenge case for {unit} {mode}")
            scores = []
            for geom in eligible.geometry:
                nearby = reference.loc[reference.intersects(geom)]
                if nearby.empty:
                    scores.append(0.0)
                else:
                    intersection = nearby.geometry.intersection(geom).area
                    union = nearby.geometry.area + geom.area - intersection
                    scores.append(float((intersection / union).max()))
            eligible["reference_iou"] = scores
            chosen = eligible.sort_values(["reference_iou", "area_m2", "candidate_id"]).iloc[0]
            geom = chosen.geometry
            x, y = geom.representative_point().coords[0]
            bounds = geom.bounds
            half = min(200, max(90, .65 * max(bounds[2]-bounds[0], bounds[3]-bounds[1]) + 20))
            cases.append({"case_id": f"C_M3_{len(cases)+1:02d}", "family": "M3/M4",
                          "queue_id": chosen.candidate_id, "unit_id": unit, "category": mode,
                          "x": x, "y": y, "half_width_m": round(half, 2),
                          "area_m2": float(chosen.area_m2), "min_width_m": float(chosen.min_width_m),
                          "reference_iou": float(chosen.reference_iou), "geometry_wkt": geom.wkt})
        print(unit, "two challenges frozen", flush=True)
    out.write_text(json.dumps({"selection_policy": "Lowest Census best IoU among candidates passing area>=1000m2 and width>=15m in each mode and each of four areas, excluding prior reviewed cases; no OSM or imagery examined. Deliberate low-reference-overlap stress test, not a representative sample.",
                               "cases": cases}, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()

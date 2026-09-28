"""Score frozen motorway-core block and nonblock references before adjudication."""
from __future__ import annotations

import hashlib
import json

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import Point

from evaluate_chicago_m3_alley_3m_motorway_stress_2026_09_26 import motorway_corridor
from evaluate_chicago_m3_complete_zones_v1_2026_09_26 import (
    A, OUT, ROADS, core_polygon, digest, match_reference, pixel_polygon,
    plot_zone, prepare_faces,
)
from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries


def pixel_point(zone: dict, xy: list[int]) -> Point:
    x, y, h, n = zone["x"], zone["y"], zone["half_width_m"], zone["image_size_px"]
    return Point(x-h+xy[0]*2*h/n, y+h-xy[1]*2*h/n)


def main() -> None:
    selection = json.loads((OUT / "motorway_zone_selection.json").read_text())
    zone = selection["zone"]
    path = OUT / "motorway_visual_reference_v1.json"
    frozen = json.loads((OUT / "motorway_reference_freeze.json").read_text())
    assert digest(path) == frozen["sha256"][str(path.relative_to(A.parent))]
    reference = json.loads(path.read_text())
    core = core_polygon(zone, reference["core_bounds_px"])
    refs = [{**r, "geometry": pixel_polygon(zone, r["pixel_ring"])}
            for r in reference["positive_polygons"]]
    config = json.loads((A / "config/chicago_m3_alley_repair_v2.json").read_text())
    assert config["chosen_alley_buffer_m"] == 3
    row = source_geometries("CHI:11", "row", lambda p: p.get("ROWTYPE") in (1, 4, 5))
    edge = source_geometries("CHI:11", "road_edge", lambda p: p.get("TYPE") == 1)
    alley = source_geometries("CHI:11", "road_edge", lambda p: p.get("TYPE") == 5)
    masks = {"cook_row_edge_alley_open_1m": shapely.union_all([row, edge]).difference(alley.buffer(1)),
             "cook_row_edge_alley_open_3m": shapely.union_all([row, edge]).difference(alley.buffer(3))}
    roads = gpd.read_parquet(ROADS)
    faces, halo = prepare_faces(zone, roads, masks)
    motorway = motorway_corridor({zone["zone_id"]: zone})
    candidate_rows, positive_rows, negative_rows, summary_rows = [], [], [], []
    for method, geoms in faces.items():
        match, summary = match_reference(refs, geoms, halo, core)
        positive_rows.extend({"method": method, **r} for r in match)
        summary_rows.append({"method": method, **summary})
        for j, g in enumerate(geoms):
            if core.covers(g.representative_point()) and not g.boundary.intersects(halo.boundary):
                exposure = g.intersection(motorway).area/g.area
                candidate_rows.append({"method": method, "candidate_index": j, "area_m2": g.area,
                                       "motorway_exposure": exposure, "motorway_flag": exposure >= .3,
                                       "geometry_wkt": g.wkt})
        for ref in reference["nonblock_points"]:
            p = pixel_point(zone, ref["pixel_xy"])
            match_at_point = next(((j, g) for j, g in enumerate(geoms) if g.covers(p)
                                   and not g.boundary.intersects(halo.boundary)), None)
            if match_at_point:
                j, g = match_at_point
                exposure = g.intersection(motorway).area/g.area
                flag = exposure >= .3
            else:
                j, exposure, flag = None, None, None
            negative_rows.append({"method": method, "reference_id": ref["id"],
                                  "context": ref["context"], "candidate_at_point": j,
                                  "motorway_exposure": exposure, "motorway_flag": flag})
        plot_zone(zone, core, refs, geoms, halo, method)
    pd.DataFrame(candidate_rows).to_csv(OUT / "motorway_complete_candidate_inventory.csv", index=False)
    pd.DataFrame(positive_rows).to_csv(OUT / "motorway_complete_reference_matches.csv", index=False)
    pd.DataFrame(negative_rows).to_csv(OUT / "motorway_complete_negative_points.csv", index=False)
    pd.DataFrame(summary_rows).to_csv(OUT / "motorway_complete_method_summary.csv", index=False)
    result = {"reference_count": len(refs), "negative_point_count": len(reference["nonblock_points"]),
              "method_summary": summary_rows,
              "method_negative_points": pd.DataFrame(negative_rows).groupby("method").apply(
                  lambda q: {"inside_closed_face": int(q.candidate_at_point.notna().sum()),
                             "inside_unflagged_closed_face": int((q.motorway_flag == False).sum())},
                  include_groups=False).to_dict(),
              "reference_sha256": digest(path),
              "status": "new candidate-blind motorway core; visual reference is single-analyst and needs street-status adjudication"}
    (OUT / "motorway_complete_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

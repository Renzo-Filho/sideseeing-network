"""Stitch district-clipped provisional land faces across shared CA boundaries.

Only a shared boundary segment (not a point contact) links faces. No candidate
is accepted, rejected or repaired; source fragment IDs remain in the output.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_provisional_faces_2026_09_27"
DISTRICTS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
SHARED_LINE_MIN_M = 0.1
AREA_TOLERANCE_M2 = 0.1


class DisjointSet:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i):
        while i != self.parent[i]:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        if self.rank[a] < self.rank[b]:
            a, b = b, a
        self.parent[b] = a
        if self.rank[a] == self.rank[b]:
            self.rank[a] += 1


def main():
    manifest = json.loads((OUT / "manifest.json").read_text())
    if len(manifest["units"]) != 77:
        raise RuntimeError(f"Expected all 77 generated units, got {len(manifest['units'])}")
    frames = [gpd.read_parquet(ROOT / item["output_path"])
              for item in manifest["units"]]
    fragments = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True),
                                 geometry="geometry", crs=26916)
    if not fragments.candidate_id.is_unique:
        raise ValueError("Source fragment IDs are not globally unique")
    edge_idx = fragments.index[fragments.requires_stitch].to_numpy()
    edge_geoms = fragments.geometry.iloc[edge_idx].to_numpy()
    tree = shapely.STRtree(edge_geoms)
    dsu = DisjointSet(len(fragments))
    links = []
    for local_i, local_j in tree.query(edge_geoms, predicate="intersects").T:
        if local_j <= local_i:
            continue
        i, j = int(edge_idx[local_i]), int(edge_idx[local_j])
        if fragments.unit_id.iloc[i] == fragments.unit_id.iloc[j]:
            continue
        shared = fragments.geometry.iloc[i].boundary.intersection(
            fragments.geometry.iloc[j].boundary).length
        if shared >= SHARED_LINE_MIN_M:
            dsu.join(i, j)
            links.append({"left_fragment_id": fragments.candidate_id.iloc[i],
                          "right_fragment_id": fragments.candidate_id.iloc[j],
                          "shared_boundary_m": shared})
    groups = {}
    for i in range(len(fragments)):
        groups.setdefault(dsu.find(i), []).append(i)
    districts = gpd.read_parquet(DISTRICTS)
    city = districts.geometry.union_all()
    internal_district_edges = shapely.union_all(districts.geometry.boundary.to_numpy()).difference(
        city.boundary.buffer(0.02))
    results = []
    for members in groups.values():
        geoms = fragments.geometry.iloc[members].to_numpy()
        geom = shapely.normalize(shapely.union_all(geoms))
        if geom.geom_type != "Polygon":
            # A MultiPolygon would imply a point-only connection or a bad seam.
            raise ValueError(f"Non-polygon stitched group: {[fragments.candidate_id.iloc[i] for i in members]}")
        outer_area = Polygon(geom.exterior).area
        outer_length = geom.exterior.length
        source_ids = sorted(fragments.candidate_id.iloc[members])
        source_units = sorted(set(fragments.unit_id.iloc[members]))
        touches_city_edge = geom.boundary.intersects(city.boundary)
        unjoined_edge = (any(bool(fragments.requires_stitch.iloc[i]) for i in members)
                         and geom.boundary.intersection(internal_district_edges).length >=
                         SHARED_LINE_MIN_M)
        geom_id = hashlib.sha256(shapely.to_wkb(geom)).hexdigest()[:20]
        results.append({"candidate_id": f"M3C_GLOBAL_{geom_id}",
                        "stage": "provisional_unreviewed",
                        "source_fragment_ids": ";".join(source_ids),
                        "source_unit_ids": ";".join(source_units),
                        "source_fragment_count": len(members),
                        "touches_city_edge": bool(touches_city_edge),
                        "unjoined_internal_district_edge": bool(unjoined_edge),
                        "area_m2": geom.area,
                        "outer_area_m2": outer_area,
                        "hole_area_m2": outer_area - geom.area,
                        "outer_perimeter_m": outer_length,
                        "raw_compactness": 4 * math.pi * outer_area / outer_length**2,
                        "geometry": geom})
    global_faces = gpd.GeoDataFrame(results, geometry="geometry", crs=26916)
    if not global_faces.candidate_id.is_unique or not global_faces.geometry.is_valid.all():
        raise ValueError("Invalid or repeated stitched candidate")
    area_before = float(fragments.geometry.area.sum())
    area_after = float(global_faces.geometry.area.sum())
    area_error = abs(area_after - area_before)
    if area_error > max(AREA_TOLERANCE_M2, area_before * 1e-8):
        raise ValueError(f"Stitching area conservation failed: {area_error}")
    global_faces = global_faces.sort_values("candidate_id").reset_index(drop=True)
    global_faces.to_parquet(OUT / "global_provisional_faces.parquet", index=False)
    pd.DataFrame(links).to_csv(OUT / "stitch_links.csv", index=False)
    pd.DataFrame(global_faces.drop(columns="geometry")).to_csv(
        OUT / "global_candidate_inventory.csv", index=False)
    report = {"fragment_count": len(fragments), "global_face_count": len(global_faces),
              "stitch_links": len(links),
              "stitched_groups": int((global_faces.source_fragment_count > 1).sum()),
              "unjoined_internal_district_edge_count": int(global_faces.unjoined_internal_district_edge.sum()),
              "touches_city_edge_count": int(global_faces.touches_city_edge.sum()),
              "area_before_m2": area_before, "area_after_m2": area_after,
              "area_error_m2": area_error,
              "global_file_bytes": (OUT / "global_provisional_faces.parquet").stat().st_size,
              "status": "provisional; shared-line stitch only; no source-gap repairs or nonblock filtering"}
    (OUT / "stitch_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

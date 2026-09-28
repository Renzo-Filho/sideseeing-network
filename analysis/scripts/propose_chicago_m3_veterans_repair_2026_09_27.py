"""Version a proposed W Veterans Place split without changing the citywide layer."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

from pilot_chicago_m3_veterans_repair_2026_09_27 import CASE, PIN10, local_parcels

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_provisional_faces_2026_09_27"
INPUT = OUT / "global_provisional_faces.parquet"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
WIDTH_M = 10.0  # Development proposal, not a surveyed road width.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    case = next(c for c in json.loads(CASE.read_text())["cases"] if c["case_id"] == "C_M3_01")
    roi = shapely.from_wkt(case["geometry_wkt"]).buffer(150)
    parcels = local_parcels(roi)
    base = parcels.loc[parcels.PARCELTYPE.eq("BaseParcel")]
    core = base.loc[base.PIN10.isin(PIN10)]
    if set(core.PIN10) != PIN10:
        raise ValueError("Missing one of the six West Veterans anchor parcels")
    core_geom = shapely.union_all(core.geometry.to_numpy())
    nonparcel = roi.difference(shapely.union_all(base.geometry.to_numpy()))
    roads = gpd.read_parquet(ROADS)
    line = roads.loc[roads.trans_id.astype(str).eq("154550")].geometry.item()
    faces = gpd.read_parquet(INPUT)
    hits = faces.iloc[faces.sindex.query(core_geom, predicate="intersects")]
    selected = hits.iloc[hits.geometry.intersection(core_geom).area.argmax()]
    if selected.geometry.intersection(core_geom).area / core_geom.area < 0.95:
        raise ValueError("The expected global candidate no longer covers the parcel anchor")
    corridor = nonparcel.intersection(line.buffer(WIDTH_M)).intersection(selected.geometry)
    parts = [p for p in shapely.get_parts(shapely.make_valid(selected.geometry.difference(corridor)))
             if p.geom_type == "Polygon" and p.area > 1]
    if len(parts) != 2:
        raise ValueError(f"Expected a two-face split; found {len(parts)}")
    proposal = gpd.GeoDataFrame([{"proposal_id": f"WV_{i+1}",
                                  "replaces_candidate_id": selected.candidate_id,
                                  "status": "proposed_unadjudicated",
                                  "area_m2": part.area,
                                  "parcel_core_coverage": part.intersection(core_geom).area/core_geom.area,
                                  "geometry": part}
                                 for i,part in enumerate(parts)], geometry="geometry", crs=26916)
    if proposal.geometry.intersection(core_geom).area.max()/core_geom.area < 0.95:
        raise ValueError("No proposed face contains the six-parcel anchor")
    path = OUT / "west_veterans_split_proposal.parquet"
    proposal.to_parquet(path, index=False)
    report = {"case_id": "C_M3_01", "replaces_candidate_id": selected.candidate_id,
              "municipal_trans_id": "154550", "search_width_m": WIDTH_M,
              "old_face_area_m2": selected.geometry.area,
              "proposed_face_areas_m2": [float(part.area) for part in parts],
              "removed_corridor_area_m2": corridor.area,
              "parcel_core_area_m2": core_geom.area,
              "max_proposal_parcel_coverage": float(proposal.parcel_core_coverage.max()),
              "source_sha256": {"global_provisional_faces": sha(INPUT),
                                "roads": sha(ROADS), "case": sha(CASE)},
              "status": "proposed_unadjudicated; independent public-road and property-side edge review required before applying",
              "output_sha256": sha(path)}
    (OUT / "west_veterans_split_proposal.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

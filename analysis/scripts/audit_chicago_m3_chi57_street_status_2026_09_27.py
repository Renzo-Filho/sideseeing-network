"""Check the candidate-blind CHI57_B1 outline against street source extent."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_reference_zones_v2_2026_09_27"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
OVERTURE = A / "data/Chicago/overture_2026_08_19/segment/part_0000.parquet"


def endpoints(geom):
    return [shapely.Point(part.coords[i]) for part in shapely.get_parts(geom)
            if part.geom_type == "LineString" for i in (0, -1)]


def main():
    roads = gpd.read_parquet(ROADS)
    roads.trans_id = roads.trans_id.astype(str)
    west46 = roads.loc[roads.trans_id.eq("154478")].geometry.item()
    tripp = roads.loc[roads.trans_id.eq("136358")].geometry.item()
    endpoint_gap = min(point.distance(tripp) for point in endpoints(west46))
    table = pq.read_table(OVERTURE, columns=["id", "names", "class", "geometry", "bbox"]).to_pandas()
    project = Transformer.from_crs(4326, 26916, always_xy=True).transform
    nearby = []
    for record in table.itertuples():
        names = record.names
        primary = names.get("primary") if isinstance(names, dict) else None
        if primary != "West 46th Street":
            continue
        geom = transform(project, shapely.from_wkb(record.geometry))
        if geom.distance(west46) > 100:
            continue
        nearby.append({"id": record.id,
                       "length_m": geom.length, "distance_to_municipal_m": geom.distance(west46),
                       "distance_to_tripp_m": geom.distance(tripp)})
    output = {"case": "CHI57_B1", "municipal_w46_trans_id": "154478",
              "municipal_w46_length_m": west46.length,
              "municipal_w46_nearest_endpoint_to_tripp_m": endpoint_gap,
              "municipal_w46_grade_levels": ["0", "0"],
              "nearby_overture_w46": nearby,
              "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in (ROADS, OVERTURE)},
              "interpretation": "Visible pavement west of the mapped W 46th Street stub is not established as a through public street by either mapped street source; image-only block outline must be adjudicated, not scored as truth."}
    (OUT / "CHI_57_B1_street_status.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k:v for k,v in output.items() if k!="source_sha256"},indent=2))


if __name__ == "__main__":
    main()

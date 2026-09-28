"""Run established momepy street-enclosure baseline on frozen Chicago tiles."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import momepy
import pandas as pd
import shapely
from shapely.geometry import Polygon, box

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import pixel_point

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/"analysis"
FRESH=A/"results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
OUT=A/"results/Chicago/chicago_block_protocol_pilot_v1_2026_09_26"
ROADS=A/"work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
HALO_HALF_WIDTH_M=450


def main():
    tiles={t["tile_id"]:t for t in json.loads((FRESH/"tile_selection.json").read_text())["tiles"]}
    refs=json.loads((FRESH/"visual_reference.json").read_text())
    roads=gpd.read_parquet(ROADS)
    rows=[]
    tile_info=[]
    for tile_id in sorted(set(r["tile_id"] for r in refs["positive_polygons"])):
        tile=tiles[tile_id]
        x,y=tile["x"],tile["y"]
        halo=box(x-HALO_HALF_WIDTH_M,y-HALO_HALF_WIDTH_M,
                 x+HALO_HALF_WIDTH_M,y+HALO_HALF_WIDTH_M)
        subset=roads.iloc[roads.sindex.query(halo,predicate="intersects")]
        faces=momepy.enclosures(subset.geometry,limit=halo)
        geoms=[g for g in faces.geometry if g.geom_type=="Polygon" and g.area>0]
        tile_info.append({"tile_id":tile_id,"municipal_road_segments_in_halo":len(subset),
                          "momepy_faces_in_halo":len(geoms)})
        for ref in (r for r in refs["positive_polygons"] if r["tile_id"]==tile_id):
            truth=Polygon([pixel_point(tile,p).coords[0] for p in ref["pixel_ring"]])
            best=max(geoms,key=lambda g:g.intersection(truth).area)
            overlap=best.intersection(truth).area
            rows.append({"reference_id":ref["id"],"tile_id":tile_id,"context":ref["context"],
                         "reference_area_m2":truth.area,"momepy_face_area_m2":best.area,
                         "momepy_iou":overlap/best.union(truth).area,
                         "reference_covered_fraction":overlap/truth.area,
                         "face_touches_halo":best.boundary.intersects(halo.boundary)})
    baseline=pd.DataFrame(rows)
    row=pd.read_csv(FRESH/"positive_reference_comparison.csv")
    row=row.loc[row["mode"].eq("cook_row_alley_open"),["reference_id","best_component_iou"]]
    comparison=baseline.merge(row,on="reference_id",validate="one_to_one")
    comparison=comparison.rename(columns={"best_component_iou":"row_alley_open_iou"})
    OUT.mkdir(parents=True,exist_ok=True)
    comparison.to_csv(OUT/"momepy_baseline_positive_comparison.csv",index=False)
    pd.DataFrame(tile_info).to_csv(OUT/"momepy_baseline_tile_info.csv",index=False)
    summary={"method":"momepy.enclosures on Chicago eligible municipal centerline barriers, 450m half-width halo; same 11 rough sketches; no lake/parcel/ROW filters",
             "momepy_version":momepy.__version__,
             "reference_count":len(comparison),
             "momepy_median_iou":float(comparison.momepy_iou.median()),
             "row_alley_open_median_iou":float(comparison.row_alley_open_iou.median()),
             "momepy_iou_ge_0_5":int(comparison.momepy_iou.ge(.5).sum()),
             "row_alley_open_iou_ge_0_5":int(comparison.row_alley_open_iou.ge(.5).sum()),
             "halo_touched_best_faces":int(comparison.face_touches_halo.sum()),
             "caveat":"Same selected rough sketches used to choose the ROW/alley method; this is a diagnostic direct baseline, not independent superiority evidence or citywide benchmark."}
    (OUT/"momepy_baseline_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()

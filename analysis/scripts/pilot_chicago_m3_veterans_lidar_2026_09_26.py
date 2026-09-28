"""Test whether Cook 2022 classified LiDAR detects a street missing from ROW/EOP."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.ops import substring

from pilot_chicago_m3_classified_lidar_2026_09_26 import fetch_member, parse_header

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "analysis/work/chicago_m3_lidar_point_pilot_2026_09_26"
OUT = ROOT / "analysis/results/Chicago/chicago_m3_lidar_point_pilot_2026_09_26"
MEMBER = "13759300.las"
OFFSET = 723842792273
COMPRESSED = 764851238
UNCOMPRESSED = 1252741169
ROADS = ROOT / "analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
GAPS = ROOT / "analysis/results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26/named_street_gap_screen.csv"


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    path = WORK/MEMBER
    receipt_path = OUT/"veterans_member_receipt.json"
    if not path.exists():
        receipt=fetch_member(path, MEMBER, OFFSET, COMPRESSED, UNCOMPRESSED)
        receipt_path.write_text(json.dumps(receipt,indent=2)+"\n")
    else:
        receipt=json.loads(receipt_path.read_text())
    assert path.stat().st_size == UNCOMPRESSED
    header=parse_header(path)
    raw=gpd.read_parquet(ROADS)
    raw.trans_id=raw.trans_id.astype(str)
    gap=pd.read_csv(GAPS)
    west=gap.loc[gap.trans_id.eq(154550)].iloc[0]
    checks=[("W VETERANS PL uncovered run",shapely.from_wkt(west.uncovered_wkt),"missing_from_county_mask")]
    for name,trans_id in [("N LIPPS AVE", "154551"),("W AINSLIE ST","110450"),("W HIGGINS AVE","112964")]:
        line=raw.loc[raw.trans_id.eq(trans_id)].geometry.item()
        if line.geom_type == "MultiLineString":
            line=max(shapely.get_parts(line),key=lambda part:part.length)
        line=substring(line,.1*line.length,.9*line.length)
        checks.append((name,line,"covered_by_county_mask"))
    regions=[]
    for name,line,status in checks:
        for width in (3,5,8):
            regions.append({"street":name,"status":status,"buffer_m":width,
                            "geometry":line.buffer(width)})
    shapes=gpd.GeoSeries([r["geometry"] for r in regions],crs=26916).to_crs(6455)
    bounds=shapely.union_all(list(shapes)).bounds
    fmt=header["point_format"]
    dtype=np.dtype({"names":["X","Y","classification"],
                    "formats":["<i4","<i4","u1"],
                    "offsets":[0,4,16 if fmt>=6 else 15],
                    "itemsize":header["point_record_length"]})
    points=np.memmap(path,dtype=dtype,mode="r",offset=header["point_offset"],shape=(header["point_count"],))
    scales,offsets=header["xyz_scales"],header["xyz_offsets"]
    counts={i:np.zeros(256,dtype=np.int64) for i in range(len(regions))}
    for start in range(0,len(points),1_000_000):
        part=points[start:start+1_000_000]
        x=part["X"].astype("float64")*scales[0]+offsets[0]
        y=part["Y"].astype("float64")*scales[1]+offsets[1]
        close=(x>=bounds[0])&(x<=bounds[2])&(y>=bounds[1])&(y<=bounds[3])
        if not close.any():continue
        x,y,c=x[close],y[close],part["classification"][close]
        for i,shape in enumerate(shapes):
            inside=shapely.contains_xy(shape,x,y)
            if inside.any():counts[i]+=np.bincount(c[inside],minlength=256)
    rows=[]
    for i,reg in enumerate(regions):
        n=int(counts[i].sum())
        if n==0:continue
        for cls,value in enumerate(counts[i]):
            if value:
                rows.append({"street":reg["street"],"status":reg["status"],"buffer_m":reg["buffer_m"],
                             "class":cls,"count":int(value),"total_points":n,"fraction":value/n})
    table=pd.DataFrame(rows)
    table.to_csv(OUT/"veterans_street_point_classes.csv",index=False)
    wide=table.pivot_table(index=["street","status","buffer_m"],columns="class",values="fraction",fill_value=0)
    print(wide[[c for c in (2,4,5,6,10,11,17,19) if c in wide.columns]].round(3).to_string())
    (OUT/"veterans_summary.json").write_text(json.dumps({"source":receipt,"las_header":header,
       "target_trans_ids":["154550","154551","110450","112964"],
       "interpretation":"Selected named street and nearby controls; class 11 is not independent of county EOP without acquisition-lineage review."},indent=2)+"\n")


if __name__=="__main__":main()

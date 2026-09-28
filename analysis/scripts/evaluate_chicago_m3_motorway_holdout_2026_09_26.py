"""Evaluate the frozen motorway rule on new source-blind centers and imagery refs."""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pyarrow.parquet as pq
import shapely
from PIL import Image
from pyproj import Transformer
from shapely.geometry import Point, Polygon, box
from shapely.ops import transform

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries, components

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/"analysis"
OUT=A/"results/Chicago/chicago_m3_motorway_holdout_2026_09_26"
WORK=A/"work/chicago_m3_motorway_holdout_2026_09_26"
CONF=A/"config/chicago_m3_motorway_candidate_v1.json"
SEGMENTS=A/"data/Chicago/overture_2026_08_19/segment/part_0000.parquet"
TO_METRIC=Transformer.from_crs(4326,26916,always_xy=True).transform


def point(tile,pixel):
    x,y=tile["x"],tile["y"]
    return Point(x-240+pixel[0]*480/1000,y+240-pixel[1]*480/1000)


def main():
    cfg=json.loads(CONF.read_text())
    assert cfg["motorway_corridor_width_m"]==40
    assert cfg["flag_if_candidate_area_in_motorway_corridor_fraction_ge"]==.3
    tiles={t["tile_id"]:t for t in json.loads((OUT/"tile_selection.json").read_text())["tiles"]}
    refs=json.loads((OUT/"visual_reference.json").read_text())
    table=pq.read_table(SEGMENTS,columns=["class","geometry","bbox"])
    to_wgs84=Transformer.from_crs(26916,4326,always_xy=True).transform
    corners=[to_wgs84(t["x"]+dx,t["y"]+dy) for t in tiles.values()
             for dx in (-300,300) for dy in (-300,300)]
    w,s,e,n=(min(p[0] for p in corners),min(p[1] for p in corners),
             max(p[0] for p in corners),max(p[1] for p in corners))
    motorway=shapely.union_all([transform(TO_METRIC,shapely.from_wkb(geom))
                                for cls,geom,bbox in zip(table["class"].to_pylist(),
                                                         table["geometry"].to_pylist(),
                                                         table["bbox"].to_pylist())
                                if cls=="motorway" and geom is not None and bbox is not None
                                and bbox["xmin"]<=e and bbox["xmax"]>=w
                                and bbox["ymin"]<=n and bbox["ymax"]>=s])
    corridor=motorway.buffer(40)
    candidates=[]
    all_parts={}
    for tile_id,tile in tiles.items():
        t={**tile,"half_width_m":240}
        road=source_geometries("CHI:49","row",lambda p:p.get("ROWTYPE") in (1,4,5))
        edge=source_geometries("CHI:49","road_edge",lambda p:p.get("TYPE")==1)
        alley=source_geometries("CHI:49","road_edge",lambda p:p.get("TYPE")==5)
        mask=shapely.union_all([road,edge]).difference(alley.buffer(1))
        area,parts=components(t,mask)
        all_parts[tile_id]=(area,mask,parts)
        fig,ax=plt.subplots(figsize=(8,8),dpi=115)
        ax.imshow(Image.open(WORK/f"{tile_id}_wide.jpg"),
                  extent=[t["x"]-240,t["x"]+240,t["y"]-240,t["y"]+240])
        for ix,part in enumerate(sorted(parts,key=lambda p:p.area,reverse=True),1):
            if part.area<1000 or part.boundary.intersects(area.boundary):
                continue
            frac=part.intersection(corridor).area/part.area
            flag=frac>=.3
            cid=f"{tile_id}_P{ix:02d}"
            candidates.append({"component_id":cid,"tile_id":tile_id,"area_m2":part.area,
                               "compactness":4*math.pi*part.area/part.length**2,
                               "motorway_area_fraction_40m":frac,"motorway_flag":flag,
                               "geometry_wkt":part.wkt})
            xx,yy=part.exterior.xy
            ax.plot(xx,yy,color="red" if flag else "cyan",linewidth=1)
            ax.text(part.representative_point().x,part.representative_point().y,str(ix),
                    color="black",ha="center",va="center",fontsize=8,
                    bbox={"facecolor":"yellow","alpha":.8,"pad":1})
        ax.set(xlim=(t["x"]-240,t["x"]+240),ylim=(t["y"]-240,t["y"]+240),
               title=f"{tile_id}: cyan kept, red motorway flag")
        ax.set_axis_off()
        fig.savefig(OUT/f"{tile_id}_candidate_overlay.png",bbox_inches="tight")
        plt.close(fig)
    cand=pd.DataFrame(candidates)
    cand.to_csv(OUT/"holdout_candidates.csv",index=False)
    shapes={r.component_id:shapely.from_wkt(r.geometry_wkt) for r in cand.itertuples()}
    positives=[]
    for ref in refs["positive_polygons"]:
        geom=Polygon([point(tiles[ref["tile_id"]],p).coords[0] for p in ref["pixel_ring"]])
        matches=[(key,g) for key,g in shapes.items() if key.startswith(ref["tile_id"]+"_")]
        if matches:
            best,g=max(matches,key=lambda item:item[1].intersection(geom).area)
            overlap=g.intersection(geom).area
            iou=overlap/g.union(geom).area
            status=bool(cand.loc[cand.component_id.eq(best),"motorway_flag"].item())
        else:
            best,overlap,iou,status=None,0,0,None
        positives.append({"reference_id":ref["id"],"tile_id":ref["tile_id"],
                          "matched_candidate":best,"best_iou":iou,
                          "reference_covered_fraction":overlap/geom.area,
                          "motorway_flag":status})
    negatives=[]
    for ref in refs["negative_points"]:
        p=point(tiles[ref["tile_id"]],ref["pixel_xy"])
        match=next((key for key,g in shapes.items() if key.startswith(ref["tile_id"]+"_") and g.covers(p)),None)
        flag=bool(cand.loc[cand.component_id.eq(match),"motorway_flag"].item()) if match else None
        negatives.append({"reference_id":ref["id"],"tile_id":ref["tile_id"],
                          "candidate_at_point":match,"motorway_flag":flag})
    pd.DataFrame(positives).to_csv(OUT/"positive_comparison.csv",index=False)
    pd.DataFrame(negatives).to_csv(OUT/"negative_comparison.csv",index=False)
    pos=pd.DataFrame(positives)
    neg=pd.DataFrame(negatives)
    summary={"tiles":len(tiles),"positive_sketches":len(pos),"negative_points":len(neg),
             "tile_contained_candidates":len(cand),"motorway_flagged_candidates":int(cand.motorway_flag.sum()),
             "positive_sketches_with_iou_ge_0_5":int((pos.best_iou>=.5).sum()),
             "positive_sketches_flagged":int((pos.motorway_flag==True).sum()),
             "negative_points_in_candidates_before_motorway_flag":int(neg.candidate_at_point.notna().sum()),
             "negative_points_in_kept_candidates":int(((neg.candidate_at_point.notna())&(neg.motorway_flag==False)).sum()),
             "median_positive_iou":float(pos.best_iou.median()),
             "limits":"One-analyst approximate imagery references; new selected centers in one Community Area, not citywide acceptance."}
    (OUT/"validation_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()

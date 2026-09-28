"""Evaluate frozen candidate-blind Chicago block reference zones."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import geopandas as gpd
import momepy
import numpy as np
import pandas as pd
import shapely
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Polygon, Point, box

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_reference_zones_v2_2026_09_27"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
IOU_CUTOFF = 0.5


def pixel_polygon(zone, ring):
    x, y, h, n = zone["x"], zone["y"], zone["half_width_m"], zone["image_size_px"]
    return Polygon([(x-h+px*2*h/n, y+h-py*2*h/n) for px, py in ring])


def pixel_point(zone, xy):
    x, y, h, n = zone["x"], zone["y"], zone["half_width_m"], zone["image_size_px"]
    return Point(x-h+xy[0]*2*h/n, y+h-xy[1]*2*h/n)


def compactness(geom):
    return 4*math.pi*geom.area/geom.exterior.length**2


def boundary_distances(a, b, step_m=2.0):
    distances=[]
    for first, second in ((a.exterior, b.exterior), (b.exterior, a.exterior)):
        count=max(2, math.ceil(first.length/step_m))
        distances.extend(first.interpolate(i*first.length/count).distance(second)
                         for i in range(count))
    return float(np.median(distances)), float(np.quantile(distances,.95))


def polygon_parts(geom):
    return [p for p in shapely.get_parts(shapely.make_valid(geom)) if p.geom_type=="Polygon" and p.area>1]


def evaluate(zone, refs, controls, roads):
    zid=zone["zone_id"]
    x,y,h=zone["x"],zone["y"],zone["half_width_m"]
    halo=box(x-h,y-h,x+h,y+h)
    c=zone["reference_core_half_width_m"]
    core=box(x-c,y-c,x+c,y+c)
    unit=zone["unit_id"]
    row=source_geometries(unit,"row",lambda p:p.get("ROWTYPE") in (1,4,5))
    edge=source_geometries(unit,"road_edge",lambda p:p.get("TYPE")==1)
    alley=source_geometries(unit,"road_edge",lambda p:p.get("TYPE")==5)
    road_mask=shapely.union_all([row,edge]).difference(alley.buffer(3))
    candidate=polygon_parts(halo.difference(road_mask))
    subset=roads.iloc[roads.sindex.query(halo,predicate="intersects")]
    centerline=[g for g in momepy.enclosures(subset.geometry,limit=halo).geometry
                if g.geom_type=="Polygon" and g.area>1]
    output=[]
    for method,faces in (("row_edge_alley3",candidate),("municipal_momepy",centerline)):
        score=np.zeros((len(refs),len(faces)))
        for i,ref in enumerate(refs):
            for j,face in enumerate(faces):
                if not face.intersects(ref["geometry"]):continue
                score[i,j]=face.intersection(ref["geometry"]).area/face.union(ref["geometry"]).area
        matched={}
        if score.size:
            for i,j in zip(*linear_sum_assignment(-score)):
                if score[i,j]>=IOU_CUTOFF:matched[i]=j
        for i,ref in enumerate(refs):
            best_j=int(score[i].argmax()) if len(faces) else None
            chosen=matched.get(i)
            face=faces[chosen] if chosen is not None else None
            med,p95=boundary_distances(ref["geometry"],face) if face is not None else (None,None)
            simplified={t:face.simplify(t,preserve_topology=True) for t in (2,5,10)} if face is not None else {}
            output.append({"zone_id":zid,"method":method,"record_type":"positive",
                           "reference_id":ref["id"],"reference_context":ref["context"],
                           "matched":chosen is not None,"matched_index":chosen,
                           "best_index":best_j,"best_iou":float(score[i,best_j]) if best_j is not None else 0,
                           "matched_iou":float(score[i,chosen]) if chosen is not None else None,
                           "reference_area_m2":ref["geometry"].area,
                           "candidate_area_m2":face.area if face is not None else None,
                           "relative_area_error":face.area/ref["geometry"].area-1 if face is not None else None,
                           "reference_compactness":compactness(ref["geometry"]),
                           "candidate_compactness":compactness(face) if face is not None else None,
                           "compactness_error":compactness(face)-compactness(ref["geometry"]) if face is not None else None,
                           "reference_hull_compactness":compactness(ref["geometry"].convex_hull),
                           "candidate_hull_compactness":compactness(face.convex_hull) if face is not None else None,
                           "hull_compactness_error":compactness(face.convex_hull)-compactness(ref["geometry"].convex_hull) if face is not None else None,
                           **{f"simplify{t}_compactness":compactness(simplified[t]) if face is not None else None for t in (2,5,10)},
                           **{f"simplify{t}_area_change":simplified[t].area/face.area-1 if face is not None else None for t in (2,5,10)},
                           "boundary_median_m":med,"boundary_p95_m":p95,
                           "candidate_touches_halo":face.boundary.intersects(halo.boundary) if face is not None else None,
                           "candidate_intersects_core":face.intersects(core) if face is not None else None})
        for control in controls:
            point=control["geometry"]
            hit=next(((j,face) for j,face in enumerate(faces) if face.covers(point)),None)
            output.append({"zone_id":zid,"method":method,"record_type":control["type"],
                           "reference_id":control["id"],"reference_context":control["reason"],
                           "matched":False,"point_inside_face":hit is not None,
                           "point_face_index":hit[0] if hit else None,
                           "point_face_area_m2":hit[1].area if hit else None,
                           "point_face_touches_halo":hit[1].boundary.intersects(halo.boundary) if hit else None,
                           "point_inside_street_mask":road_mask.covers(point) if method=="row_edge_alley3" else None})
        matched_face_ids=set(matched.values())
        for j,face in enumerate(faces):
            if not core.covers(face.representative_point()):continue
            hits=[control["id"] for control in controls if face.covers(control["geometry"])]
            output.append({"zone_id":zid,"method":method,"record_type":"candidate_inventory",
                           "candidate_index":j,"candidate_area_m2":face.area,
                           "candidate_compactness":compactness(face),
                           "candidate_touches_halo":face.boundary.intersects(halo.boundary),
                           "matched_positive":j in matched_face_ids,
                           "control_ids":";".join(hits)})
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--version",type=int,choices=[1,2],default=1)
    args=parser.parse_args()
    reference_path=OUT/f"visual_reference_v{args.version}.json"
    freeze_name="reference_freeze.json" if args.version==1 else "reference_v2_freeze.json"
    frozen=json.loads((OUT/freeze_name).read_text())
    assert hashlib.sha256(reference_path.read_bytes()).hexdigest()==frozen["sha256"]
    reference=json.loads(reference_path.read_text())
    zones=json.loads((OUT/"zone_selection.json").read_text())["zones"]
    roads=gpd.read_parquet(ROADS)
    rows=[]
    for zone in zones:
        zid=zone["zone_id"]
        if zid not in reference["complete_zones"]:continue
        refs=[{**r,"geometry":pixel_polygon(zone,r["pixel_ring"])} for r in reference["positive_polygons"]
              if r["zone_id"]==zid]
        controls=[{**r,"geometry":pixel_point(zone,r["pixel_xy"]),"type":kind}
                  for kind in ("special_context_points","negative_points")
                  for r in reference[kind] if r["zone_id"]==zid]
        rows.extend(evaluate(zone,refs,controls,roads))
    table=pd.DataFrame(rows)
    table.to_csv(OUT/f"reference_v{args.version}_comparison.csv",index=False)
    positives=table.loc[table.record_type.eq("positive")]
    excluded=[]
    reference_inventory_complete=False
    if args.version==2 and (OUT/"reference_v2_postfreeze_adjudication.json").exists():
        adjudication=json.loads((OUT/"reference_v2_postfreeze_adjudication.json").read_text())
        excluded=adjudication.get("excluded_positive_ids",[])
        positives=positives.loc[~positives.reference_id.isin(excluded)]
    summary=[]
    for (zone,method),group in positives.groupby(["zone_id","method"]):
        matched=group.loc[group.matched]
        summary.append({"zone_id":zone,"method":method,"references":len(group),
                        "matched_ge_0_5":len(matched),"median_best_iou":float(group.best_iou.median()),
                        "median_matched_area_error":float(matched.relative_area_error.abs().median()) if len(matched) else None,
                        "median_matched_compactness_error":float(matched.compactness_error.abs().median()) if len(matched) else None,
                        "median_matched_hull_compactness_error":float(matched.hull_compactness_error.abs().median()) if len(matched) else None,
                        "median_simplify10_area_change":float(matched.simplify10_area_change.abs().median()) if len(matched) else None,
                        "median_boundary_p95_m":float(matched.boundary_p95_m.median()) if len(matched) else None})
    (OUT/f"evaluation_v{args.version}_summary.json").write_text(json.dumps({"reference_sha256":frozen["sha256"],
       "originally_declared_complete_zones":reference["complete_zones"],
       "reference_inventory_complete":reference_inventory_complete,
       "iou_cutoff":IOU_CUTOFF,
       "postfreeze_excluded_positive_ids":excluded,
       "method_summary":summary,
       "status":"single-analyst approximate references; CHI:57/63 core inventory incomplete; selected-outline diagnostics, not M3/M4 acceptance"},indent=2)+"\n")
    print(pd.DataFrame(summary).to_string(index=False))
    inventory=table.loc[table.record_type.eq("candidate_inventory")]
    print(inventory[["zone_id","method","candidate_index","candidate_area_m2","candidate_touches_halo","matched_positive","control_ids"]].to_string(index=False))
    print(table.loc[~table.record_type.eq("positive"),["zone_id","method","reference_id","point_inside_face","point_face_area_m2","point_face_touches_halo"]].to_string(index=False))


if __name__=="__main__":main()

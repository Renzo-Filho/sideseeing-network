"""H1/H2 paired roads and diagnostic enclosures; no model acceptance or fitting."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd,geopandas as gpd,shapely
from harmonization.roads import CLASSES,connector_arms,enclosure_polygons,shape_metrics
from harmonization.geometry import largest_overlap
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'analysis'
OUT=A/'results/SP_CHI/harmonization_2026_09_22_h1_h3/roads'
WORK=A/'work/runs/sp_chicago_harmonization_2026_09_22/roads'

def clip_lines(lines,geom):
 shapely.prepare(geom)
 inside=shapely.covers(geom,lines)
 result=np.array(lines,copy=True)
 result[~inside]=shapely.intersection(lines[~inside],geom)
 return result

def main():
 OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
 allrows=[];diag=[];inputs=[]
 for city,prefix,base in [('Chicago','CHI','Chicago/chi_local_2026_09_16_v1'),('SP','SP','SP/sp_prep_2026_09_10_v3/N02')]:
  source=A/'data'/city/'overture_2026_08_19'
  dp=A/'work/prepared'/base/'districts.parquet';d=gpd.read_parquet(dp)
  if 'unit_id' not in d:d['unit_id']='SP:'+d.district_id.astype(str).str.zfill(2)
  roads_path=next((source/'segment').glob('*.parquet'));con_path=next((source/'connector').glob('*.parquet'))
  for p in [dp,roads_path,con_path]:inputs.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()})
  r=gpd.read_parquet(roads_path,columns=['id','geometry','subtype','class','connectors','access_restrictions']).to_crs(d.crs)
  r=r.loc[r.subtype.eq('road')&r['class'].isin(CLASSES)].reset_index(drop=True)
  citygeom=d.geometry.union_all();buffer=citygeom.buffer(1500)
  r=r.iloc[r.sindex.query(buffer,predicate='intersects')].reset_index(drop=True)
  if not r.id.is_unique or not r.geometry.is_valid.all():raise ValueError('Invalid roads')
  print(city,'roads',len(r),flush=True)
  arms=connector_arms(r)
  c=gpd.read_parquet(con_path,columns=['id','geometry']).to_crs(d.crs)
  missing=set(arms)-set(c.id)
  missing_inside=[]
  for rr in r.itertuples():
   for link in rr.connectors:
    if link['connector_id'] in missing and citygeom.buffer(100).covers(rr.geometry.interpolate(float(link['at']),normalized=True)):
     missing_inside.append(link['connector_id'])
  if missing_inside:raise ValueError('Missing connector references near reporting city: '+str(missing_inside[:3]))
  c['arms']=c.id.map(arms).fillna(0).astype(int);c=c[c.arms>=3].copy()
  own=np.full(len(c),'',object)
  for z in d.sort_values('unit_id').itertuples():
   ids=c.sindex.query(z.geometry,predicate='intersects');own[ids[own[ids]=='']]=z.unit_id
  c['unit_id']=own;c=c[c.unit_id!=''];counts=c.unit_id.value_counts()
  c.to_parquet(WORK/f'{city}_connector_candidates.parquet',index=False)
  # Whole buffered road objects prevent district clipping from creating artificial blocks.
  polys=enclosure_polygons(r.geometry.values)
  q=gpd.GeoDataFrame(shape_metrics(polys),geometry=polys,crs=d.crs)
  q=q.loc[shapely.intersects(q.geometry.values,citygeom)].reset_index(drop=True)
  q['district_id']=largest_overlap(q,d)
  q['unit_id']=prefix+':'+q.district_id.astype(str).str.zfill(2)
  q['extraction_edge']=~shapely.covers(buffer,q.geometry.values)
  q['narrow_under_6m']=q.rectangle_min_width_m<6
  q['large_over_1km2']=q.area_m2>1e6
  q.to_parquet(WORK/f'{city}_enclosure_candidates.parquet',index=False)
  rows=[];lengthsum=0.
  for z in d.sort_values('unit_id').itertuples():
   ids=r.sindex.query(z.geometry,predicate='intersects');g=clip_lines(r.geometry.values[ids],z.geometry)
   prev=d.loc[d.unit_id.lt(z.unit_id)]
   neighbors=prev.iloc[prev.sindex.query(z.geometry,predicate='intersects')]
   shared=shapely.union_all([z.geometry.boundary.intersection(v.boundary) for v in neighbors.geometry])
   if not shared.is_empty:g=shapely.difference(g,shared)
   lens=shapely.length(g);total=float(lens.sum());lengthsum+=total
   row={'unit_id':z.unit_id,'gross_area_m2':z.geometry.area,'road_length_m':total,'M1_mapped_street_density_km_km2':total/1000/(z.geometry.area/1e6),'M2_connector_candidate_density_km2':counts.get(z.unit_id,0)/(z.geometry.area/1e6),'connector_candidates':int(counts.get(z.unit_id,0)), 'access_rule_length_share':float(lens[r.iloc[ids].access_restrictions.notna()].sum()/total),'strict_cross_city_accepted':False}
   for cl in CLASSES:row['M6_share_'+cl]=float(lens[r['class'].iloc[ids].eq(cl)].sum()/total)
   b=q.loc[q.unit_id.eq(z.unit_id)&~q.extraction_edge]
   row['enclosure_candidates']=len(b);row['narrow_enclosure_count']=int(b.narrow_under_6m.sum());row['large_enclosure_count']=int(b.large_over_1km2.sum())
   for field in ['log_area','compactness','elongation']:
    for name,value in [('median',b[field].median()),('iqr',b[field].quantile(.75)-b[field].quantile(.25))]:row['enclosure_'+field+'_'+name]=value
   rows.append(row)
   print(z.unit_id,'roads complete',flush=True)
  table=pd.DataFrame(rows)
  target=float(shapely.length(clip_lines(r.geometry.values,citygeom)).sum())
  if abs(lengthsum-target)>1:raise ValueError('Road mass not conserved')
  if not np.allclose(table.filter(like='M6_share_').sum(axis=1),1):raise ValueError('Invalid hierarchy shares')
  table.to_csv(OUT/f'{city}_physical_road_candidates.csv',index=False);allrows.extend(rows)
  diag.append({'city':city,'connector_references_outside_acquired_extent':len(missing),'missing_connector_references_within_100m_city':len(missing_inside),'road_length_m':target,'boundary_ownership_delta_m':lengthsum-target,'connector_candidates':len(c),'enclosure_candidates':len(q),'narrow_under_6m':int(q.narrow_under_6m.sum()),'large_over_1km2':int(q.large_over_1km2.sum()),'extraction_edge':int(q.extraction_edge.sum()),'M2_gate':'physical junction consolidation and divided-road arm equivalence not established; diagnostic only','M3_M4_gate':'planar enclosures retain carriageway slivers and barriers unresolved; diagnostic only'})
  # Maps support review; no similarity or geographic analogue claims.
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  pilots=['24','28','30','32','76'] if city=='Chicago' else ['10','30','35']
  for did in pilots:
   z=d.loc[d.district_id.astype(str).str.zfill(2).eq(did)].iloc[0]
   fig,ax=plt.subplots(figsize=(7,7));subset=q.loc[q.unit_id.eq(z.unit_id)]
   subset.plot(ax=ax,color='#d9e7ed',edgecolor='#536878',linewidth=.25)
   subset.loc[subset.narrow_under_6m].plot(ax=ax,color='#d85c41') if subset.narrow_under_6m.any() else None
   c.loc[c.unit_id.eq(z.unit_id)].plot(ax=ax,color='#263a9b',markersize=2)
   gpd.GeoSeries([z.geometry],crs=d.crs).boundary.plot(ax=ax,color='black',linewidth=.8)
   ax.set_title(f'{z.unit_id}: candidate enclosures and connectors\nRed: minimum rectangle width <6 m; no model acceptance');ax.set_axis_off()
   fig.savefig(OUT/f'{city}_{did}_pilot.png',dpi=140,bbox_inches='tight');plt.close(fig)
  print(city,'complete',flush=True)
 pd.DataFrame(allrows).to_csv(OUT/'paired_road_candidates.csv',index=False)
 (OUT/'diagnostics.json').write_text(json.dumps(diag,indent=2));(OUT/'source_receipts.json').write_text(json.dumps(inputs,indent=2))
 (OUT/'policy.json').write_text(json.dumps({'classes':CLASSES,'access':'physical mapped-street universe regardless of legal access; not public-access network; rule presence quantified, absent not presumed public','carriageways':'retained','ramps':'retained','service_alleys_driveways':'excluded','pedestrian':'designated pedestrian class included; footways/paths/steps excluded','unknown':'explicit category; never imputed local','M2_M3_M4':'diagnostic candidates only pending failed semantic gates'},indent=2))
if __name__=='__main__':main()

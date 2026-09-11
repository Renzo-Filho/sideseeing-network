"""Preparation-only geometry review pack and map diagnostics."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/sp-prep-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import duckdb
import geopandas as gpd
import pandas as pd
import pyogrio
import shapely
import json

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/processed/SP/sp_prep_2026_09_09_v2'
REVIEW=OUT/'review';REVIEW.mkdir(exist_ok=True)


def main():
 d=gpd.read_parquet(OUT/'01_districts/districts.parquet')
 s=gpd.read_parquet(OUT/'03_streets/edge_candidates.parquet')
 t=gpd.read_parquet(OUT/'03_streets/cet_source.parquet')
 fig,axes=plt.subplots(1,3,figsize=(16,7),constrained_layout=True)
 colors={'aligned_candidate':'#2b8cbe','alignment_review':'#e08214','unmatched_id':'#bdbdbd','conflicting_or_missing_class':'#c51b7d','no_valid_class_geometry':'#54278f'}
 for ax,code,label in zip(axes,['10','35','30'],['Brás — central reference','Itaim Bibi — contrasting central fabric','Grajaú — peripheral / reservoir district']):
  boundary=d.loc[d.district_id.eq(code)]
  piece=s.iloc[s.sindex.query(boundary.geometry.iloc[0],predicate='intersects')].copy()
  piece.geometry=piece.intersection(boundary.geometry.iloc[0])
  for status,col in colors.items():
   part=piece.loc[piece.class_match_status.eq(status)]
   if len(part):part.plot(ax=ax,color=col,linewidth=.6,label=status.replace('_',' '))
  boundary.boundary.plot(ax=ax,color='#202020',linewidth=.7)
  ax.set_title(label,fontsize=11);ax.set_axis_off()
 handles=[plt.Line2D([0],[0],color=col,lw=2,label=status.replace('_',' ')) for status,col in colors.items()]
 fig.legend(handles=handles,loc='outside lower center',ncol=3,fontsize=9)
 fig.suptitle('Street/CET linkage QA — candidate classes only; no network attributes',fontsize=14)
 fig.savefig(REVIEW/'street_class_alignment.png',dpi=160);plt.close(fig)
 bras=d.loc[d.district_id.eq('10')].geometry.iloc[0]
 p=gpd.read_parquet(OUT/'02_parcels_tax/parcel_records/10.parquet')
 c=duckdb.connect(config={'memory_limit':'512MB','threads':2,'temp_directory':str(REVIEW/'temp')})
 c.read_parquet(str(OUT/'02_parcels_tax/parcel_candidates.parquet')).create_view('candidates')
 coincident=c.execute('select * from candidates where geometry_hash in (select geometry_hash from candidates group by 1 having count(distinct sql_key)>1)').fetchdf()
 coincident.to_parquet(REVIEW/'coincident_geometry_distinct_sql.parquet',index=False)
 identity=pd.read_parquet(OUT/'02_parcels_tax/parcel_identity_status.parquet',columns=['parcel_candidate_id','identity_status'])
 p=p.merge(identity[['parcel_candidate_id','identity_status']],on='parcel_candidate_id',validate='many_to_one')
 fig,ax=plt.subplots(figsize=(9,9),constrained_layout=True)
 p.plot(ax=ax,color='#ededed',edgecolor='#999999',linewidth=.15)
 unresolved=p.loc[p.identity_status.ne('unique_geometry_candidate_semantics_pending')]
 if len(unresolved):unresolved.plot(ax=ax,color='#fdb863',edgecolor='#b35806',linewidth=.3)
 gpd.GeoSeries([bras],crs=d.crs).boundary.plot(ax=ax,color='#222222',linewidth=1)
 ax.set_title('Brás parcel preparation QA\nOrange: unresolved identity / metadata; gray: unique geometry candidates')
 ax.set_axis_off();fig.savefig(REVIEW/'bras_parcel_identity.png',dpi=160);plt.close(fig)
 # Explicit pairwise overlap geometries for boundary review.
 overlaps=[]
 for a,b in zip(*d.sindex.query(d.geometry,predicate='intersects')):
  if a>=b:continue
  g=d.geometry.iloc[a].intersection(d.geometry.iloc[b])
  if g.area>.01:overlaps.append({'district_a':d.district_id.iloc[a],'district_b':d.district_id.iloc[b],'area_m2':g.area,'geometry':g})
 og=gpd.GeoDataFrame(overlaps,crs=d.crs)
 pyogrio.write_dataframe(og,REVIEW/'review_cases.gpkg',layer='district_overlaps_gt_001m2',driver='GPKG')
 pyogrio.write_dataframe(unresolved,REVIEW/'review_cases.gpkg',layer='bras_unresolved_parcel_records',driver='GPKG')
 sg=s.loc[s.intersects(bras)]
 pyogrio.write_dataframe(sg,REVIEW/'review_cases.gpkg',layer='bras_street_candidates',driver='GPKG')
 tg=t.loc[t.geometry_valid].copy()
 tg=tg.loc[tg.intersects(bras)]
 pyogrio.write_dataframe(tg,REVIEW/'review_cases.gpkg',layer='bras_cet_source',driver='GPKG')
 # Quantify spatial relationships of every ambiguous SQL in Brás without dissolving.
 rows=[]
 for sql,group in p.loc[p.identity_status.eq('unresolved_multiple_geometries')].groupby('sql_key'):
  geometries=group.drop_duplicates('geometry_hash').geometry.values
  area_sum=sum(g.area for g in geometries);union=shapely.union_all(geometries)
  rows.append({'sql_key':sql,'geometry_candidates':len(geometries),'sum_area_m2':area_sum,'union_area_m2':union.area,
      'overlap_area_m2':area_sum-union.area,'status':'spatial_evidence_only_no_identity_resolution'})
 pd.DataFrame(rows,columns=['sql_key','geometry_candidates','sum_area_m2','union_area_m2','overlap_area_m2','status']).to_csv(REVIEW/'bras_duplicate_geometry_diagnostics.csv',index=False)
 (REVIEW/'summary.json').write_text(json.dumps({'bras_raw_parcels':len(p),'bras_identity_status':p.identity_status.value_counts().to_dict(),
   'bras_multigeometry_sql_groups':len(rows),'review_overlap_pairs_gt_001m2':len(og),
   'review_status':'source geometry inspection only; no imagery/cadastral field verification'},indent=2))
 print('Review pack written',REVIEW)

if __name__=='__main__':main()

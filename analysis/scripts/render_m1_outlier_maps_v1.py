"""Render local-vs-Overture street maps for the two M1 coverage outliers."""
from pathlib import Path
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from harmonization.roads import CLASSES
from review_m1_geometry_alignment_v1 import DISTRICTS,LOCAL

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
OUT=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review'


def main():
 for city,id in [('Chicago','76'),('SP','52')]:
  district=gpd.read_parquet(A/'work/prepared'/DISTRICTS[city])
  unit=district.loc[district.district_id.astype(str).str.zfill(2).eq(id)].iloc[0]
  area=unit.geometry
  local=gpd.read_parquet(A/'work/prepared'/LOCAL[city])
  if city=='SP':local=local.loc[local.canonical_edge]
  local=local.iloc[local.sindex.query(area,predicate='intersects')]
  raw=gpd.read_parquet(A/'data'/city/'overture_2026_08_19/segment/part_0000.parquet',
                       columns=['geometry','subtype','class']).to_crs(district.crs)
  raw=raw.loc[raw.subtype.eq('road')]
  raw=raw.iloc[raw.sindex.query(area,predicate='intersects')]
  source=raw.loc[raw['class'].isin(CLASSES)]
  excluded=raw.loc[~raw['class'].isin(CLASSES)]
  fig,axes=plt.subplots(1,2,figsize=(13,6))
  local.plot(ax=axes[0],color='#78909c',linewidth=.25)
  if city=='Chicago':
   local.loc[local['class'].eq('99')].plot(ax=axes[0],color='#d43f3a',linewidth=.5)
   title='Local centerlines: red = code 99 O’Hare'
  else:
   local.loc[local.class_model.isna()].plot(ax=axes[0],color='#d43f3a',linewidth=.5)
   title='Municipal lines: red = unresolved class'
  excluded.plot(ax=axes[1],color='#b5bec4',linewidth=.3)
  source.plot(ax=axes[1],color='#245a90',linewidth=.45)
  for ax,name in zip(axes,[title,'Overture: blue eligible; gray excluded']):
   gpd.GeoSeries([area],crs=district.crs).boundary.plot(ax=ax,color='black',linewidth=.8)
   ax.set_xlim(area.bounds[0],area.bounds[2]);ax.set_ylim(area.bounds[1],area.bounds[3])
   ax.set_aspect('equal');ax.set_title(name);ax.set_axis_off()
  fig.suptitle(('CHI' if city=='Chicago' else 'SP')+':'+id+' M1 source-universe outlier')
  fig.savefig(OUT/f'{city}_{id}_m1_outlier.png',dpi=180,bbox_inches='tight')
  plt.close(fig)

if __name__=='__main__':main()

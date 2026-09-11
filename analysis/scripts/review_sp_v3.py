"""Generate pilot input QA maps; no model attributes."""
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import geopandas as gpd
sys.path.insert(0,str(Path(__file__).parent))
from sp_v3 import common as C
C.initialize(C.ROOT/'analysis/config/sp_preparation_v3.json')
out=C.OUT/'review';out.mkdir(exist_ok=True)
d=C.districts();land=gpd.read_parquet(C.OUT/'N02/district_land.parquet');water=gpd.read_parquet(C.OUT/'N02/district_water.parquet');edges=gpd.read_parquet(C.OUT/'N04/edges.parquet')
for code,name in [('10','Brás'),('35','Itaim Bibi'),('30','Grajaú')]:
 boundary=d.loc[d.district_id.eq(code)]
 ix=edges.sindex.query(boundary.geometry.iloc[0],predicate='intersects');e=edges.iloc[ix].copy()
 fig,axes=plt.subplots(1,2,figsize=(12,6),layout='constrained')
 for ax in axes:
  land.loc[land.district_id.eq(code)].plot(ax=ax,color='#eeeee7',edgecolor='#454545',linewidth=.7)
  w=water.loc[water.district_id.eq(code)];w.loc[~w.is_empty].plot(ax=ax,color='#78bdda') if (~w.is_empty).any() else None
  a,b,c,f=boundary.total_bounds;ax.set_xlim(a-150,c+150);ax.set_ylim(b-150,f+150);ax.set_aspect('equal');ax.set_axis_off()
 for mask,color,label in [(e.class_observed.notna(),'#28734b','Observed'),(e.class_observed.isna() & e.class_imputed.eq(True),'#c88719','Imputed'),(e.class_model.isna(),'#c54150','Unresolved')]:
  if mask.any():e.loc[mask].plot(ax=axes[1],color=color,linewidth=.65,label=label)
 axes[0].set_title('Land and supplied surface-water mask');axes[1].set_title('Street classification evidence');axes[1].legend(loc='lower left',fontsize=9)
 fig.suptitle(f'{name} ({code}) — preparation QA, EPSG:31983',fontsize=15)
 fig.savefig(out/f'pilot_{code}.png',dpi=150);plt.close(fig)

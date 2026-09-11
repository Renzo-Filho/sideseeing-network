from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/sp-attribute-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
R=Path(__file__).resolve().parents[2]/'analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1';f=pd.read_parquet(R/'pilot_attributes_long.parquet');names={'10':'Brás','35':'Itaim Bibi','30':'Grajaú'}
features=[('street_density_km_km2','Street density (km/km²)'),('intersection_density_proxy_5m_km2','Intersection proxy (nodes/km²)'),('building_coverage_land','Mapped building / land area'),('cadastral_floor_count_p90','Cadastral floors, P90'),('formal_job_density_area_first_km2','Allocated job links/km²'),('bus_service_access_weekday_am_400m','Expected bus service, weekday 2h')]
fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for ax,(feature,label) in zip(axes.flat,features):
 s=f.loc[f.feature_name.eq(feature)].set_index('district_id').value.reindex(names)
 ax.bar(list(names.values()),s,color=['#16697a','#d39042','#668d3c']);ax.set_title(label,fontsize=11);ax.spines[['top','right']].set_visible(False);ax.tick_params(axis='x',labelsize=9)
fig.suptitle('São Paulo attribute pilots — independent units; proxies retain source limitations',fontsize=13);fig.savefig(R/'pilot_attribute_qa.png',dpi=150);plt.close(fig)

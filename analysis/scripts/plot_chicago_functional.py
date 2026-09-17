"""Descriptive QA maps for the functional extension, not a similarity ranking."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/chicago-functional-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import geopandas as gpd
A=Path(__file__).resolve().parents[1]
OUT=A/'results/Chicago/chi_functional_2026_09_16_v2'
g=gpd.read_file(OUT/'spatial/functional_attributes.gpkg')
g['water_percent']=g.hydro_water_m2/g.gross_area_m2*100
g['water_proxy_difference_km2']=(g.hydro_water_m2-g.cmap_proxy_water_m2)/1e6
fields=[('population_density_2020_gross_km2','Census 2020 residents / gross km²'),('jobs_density_2022_gross_km2','LODES 2022 jobs / gross km²'),('bus_service_access_weekday_am_400m','Weekday bus departures / 2h / resident · 400 m'),('bus_service_access_weekday_am_800m','Weekday bus departures / 2h / resident · 800 m'),('water_percent','Municipal hydro water / gross area · %'),('water_proxy_difference_km2','Hydro water minus CMAP proxy · km²')]
fig,axes=plt.subplots(2,3,figsize=(14,12),facecolor='#f8fafc')
for ax,(field,title) in zip(axes.ravel(),fields):
 g.plot(column=field,ax=ax,cmap='viridis',legend=True,legend_kwds={'shrink':.65},linewidth=.2,edgecolor='white')
 ax.set_title(title,fontsize=10);ax.set_axis_off()
fig.suptitle('Chicago · new functional inputs and water support',fontsize=18,y=.98)
fig.text(.5,.015,'77 Community Areas · EPSG:26916 · gross-area block allocation · CTA bus only\nDescriptive source QA; cross-city measurement acceptance remains pending.',ha='center',fontsize=10)
fig.subplots_adjust(top=.93,bottom=.06,wspace=.05,hspace=.10)
(OUT/'reports').mkdir(exist_ok=True)
fig.savefig(OUT/'reports/functional_qa.png',dpi=140,bbox_inches='tight');plt.close(fig)

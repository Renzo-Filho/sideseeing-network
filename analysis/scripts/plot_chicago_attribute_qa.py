"""Compact descriptive maps; not a similarity-model visualization."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/Chicago/chi_local_2026_09_16_v1'
def main():
    g=gpd.read_file(OUT/'spatial/chicago_community_attributes.gpkg',layer='community_attributes')
    fields=[('street_density_municipal_km_km2','Municipal streets (km / gross km²)'),
            ('building_coverage_municipal_land','Historical mapped footprints / proxy land'),
            ('building_stories_coverage','Positive stories reporting fraction'),
            ('building_stories_p90_municipal','P90 among positive reported stories'),
            ('land_use_entropy_cmap_area8','CMAP primary-area entropy (8 groups)'),
            ('population_density_acs_label2023','Provisional ACS residents / gross km²')]
    fig,axes=plt.subplots(2,3,figsize=(13,11))
    for ax,(field,title) in zip(axes.ravel(),fields):
        g.plot(column=field,ax=ax,legend=True,cmap='viridis',linewidth=.15,edgecolor='white',missing_kwds={'color':'lightgrey'},legend_kwds={'shrink':.65})
        ax.set_title(title,fontsize=10);ax.set_axis_off()
    fig.suptitle('Chicago local-source baseline — 77 Community Areas',fontsize=16)
    fig.text(.5,.02,'Different source vintages and definitions. Descriptive QA only; not accepted for SP–Chicago similarity.',ha='center',fontsize=10)
    fig.subplots_adjust(top=.93,bottom=.06,hspace=.15,wspace=.08)
    fig.savefig(OUT/'reports/attribute_qa.png',dpi=160,bbox_inches='tight');plt.close(fig)
if __name__=='__main__':main()

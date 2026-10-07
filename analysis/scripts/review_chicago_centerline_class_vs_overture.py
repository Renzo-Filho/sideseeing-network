"""Cross-tabulate Chicago centerline CLASS (status N) against the nearest raw Overture road class."""
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
OUT=A/'results/Chicago/chicago_centerline_class_review_2026_09_30'
CLASSES=['1','2','3','4','7','9','99']
TOL_M=15

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    c=gpd.read_file(A/'data/Chicago/steet_center_lines_20260915.geojson').to_crs(26916)
    c=c[c.status.eq('N')&c['class'].isin(CLASSES)].copy()
    c['len_km']=c.geometry.length/1000
    p=gpd.GeoDataFrame(c[['class','street_typ','len_km']],geometry=c.geometry.interpolate(.5,normalized=True),crs=26916).reset_index(names='i')
    s=gpd.read_parquet(A/'data/Chicago/overture_2026_08_19/segment/part_0000.parquet')
    s=s.loc[s.subtype.eq('road'),['class','geometry']].to_crs(26916).rename(columns={'class':'overture_class'})
    j=gpd.sjoin_nearest(p,s,max_distance=TOL_M,distance_col='d').sort_values('d').drop_duplicates('i')
    p=p.merge(j[['i','overture_class']],on='i',how='left')
    p['overture_class']=p.overture_class.fillna(f'no_road_within_{TOL_M}m')
    t=p.groupby(['class','overture_class']).len_km.sum().rename('km').reset_index()
    t['share_of_class']=t.km/t.groupby('class').km.transform('sum')
    t.sort_values(['class','km'],ascending=[True,False]).to_csv(OUT/'centerline_class_vs_overture_class.csv',index=False)
    ty=p[p['class'].eq('4')].groupby('street_typ',dropna=False).len_km.sum().rename('km').reset_index()
    ty['share']=ty.km/ty.km.sum()
    ty.sort_values('km',ascending=False).to_csv(OUT/'class4_street_type.csv',index=False)

if __name__=='__main__':main()

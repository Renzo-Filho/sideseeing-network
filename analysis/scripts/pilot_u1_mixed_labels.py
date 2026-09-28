"""Inspect mixed-use coding in three selected districts per city."""
from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd
import pyogrio
import shapely

from pilot_u1_source_samples import LAND, SP_RECORDS, CHI_LUI, UNITS

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/SP_CHI/u1_developed_area_2026_09_22'
PROFILE=ROOT/'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N03/parcel_fiscal_profiles.parquet'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lands={city:gpd.read_parquet(path).set_index('district_id') for city,path in LAND.items()}
    con=duckdb.connect();con.execute('SET threads=1');con.execute("SET memory_limit='512MB'")
    profiles=con.execute(f"SELECT parcel_candidate_id,district_id,distinct_uses,parcel_use_candidate FROM read_parquet('{PROFILE}') WHERE district_id IN ('10','02','95')").df();con.close()
    rows=[]
    for district in UNITS['SP']:
        land=lands['SP'].loc[district,'geometry']
        raw=gpd.read_parquet(SP_RECORDS/f'{district}.parquet',columns=['parcel_candidate_id','geometry']).drop_duplicates('parcel_candidate_id')
        p=raw.merge(profiles.loc[profiles.district_id.eq(district),['parcel_candidate_id','distinct_uses','parcel_use_candidate']],on='parcel_candidate_id',how='inner')
        for n, group in p.loc[p.parcel_use_candidate.eq('mixed/other')].groupby('distinct_uses'):
            union=shapely.intersection(shapely.union_all(group.geometry.to_numpy()),land)
            rows.append({'city':'SP','unit_id':f'SP:{district}','label':f'mixed/other; distinct fiscal uses={n}','source_objects':len(group),'clipped_area_m2':union.area,'land_fraction':union.area/land.area})
    for district in UNITS['CHI']:
        land=lands['CHI'].loc[district,'geometry']
        bbox=tuple(gpd.GeoSeries([land],crs=26916).to_crs(3857).total_bounds)
        p=pyogrio.read_dataframe(CHI_LUI,bbox=bbox,columns=['GlobalID','LANDUSE','LANDUSE2'],use_arrow=True).to_crs(26916)
        p=p.loc[p.geometry.intersects(land)]
        flags={'primary_1216_mixed_commercial_residential':p.LANDUSE.astype(str).str.startswith('1216'),
               'any_secondary_LANDUSE2':p.LANDUSE2.fillna('').astype(str).str.strip().ne('')}
        for label,mask in flags.items():
            selected=p.loc[mask]
            union=shapely.intersection(shapely.union_all(selected.geometry.to_numpy()),land) if len(selected) else shapely.GeometryCollection()
            rows.append({'city':'CHI','unit_id':f'CHI:{district}','label':label,'source_objects':len(selected),'clipped_area_m2':union.area,'land_fraction':union.area/land.area})
    pd.DataFrame(rows).to_csv(OUT/'mixed_label_screen.csv',index=False)
    print(pd.DataFrame(rows)[['unit_id','label','source_objects','land_fraction']].to_string(index=False))


if __name__=='__main__':main()

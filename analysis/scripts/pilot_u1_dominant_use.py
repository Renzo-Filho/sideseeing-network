"""Six-unit SP explicit-dominance sensitivity for mixed/other fiscal use."""
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from pilot_u1_source_samples import LAND, SP_RECORDS, UNITS

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/SP_CHI/u1_developed_area_2026_09_22'
FISCAL=ROOT/'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N03/fiscal_records.parquet'
PROFILE=ROOT/'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N03/parcel_fiscal_profiles.parquet'


def dominance(labels: object) -> str:
    if not isinstance(labels, (list, tuple, np.ndarray)) or len(labels) == 0:
        return 'unresolved'
    decisions=[]
    for label in labels:
        text=str(label).casefold()
        if 'predominância comercial' in text:
            decisions.append('commerce_services')
        elif 'predominância residencial' in text:
            decisions.append('residential')
        else:
            return 'unresolved'
    return decisions[0] if len(set(decisions)) == 1 else 'unresolved'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect();con.execute('SET threads=1');con.execute("SET memory_limit='512MB'")
    paths=(str(FISCAL),str(PROFILE))
    query='''WITH labels AS (
        SELECT parcel_candidate_id, district_id, list_sort(list_distinct(list(use_raw))) AS raw_labels
        FROM read_parquet(?) WHERE district_id IN ('10','02','95') AND location_candidate
        GROUP BY parcel_candidate_id,district_id
    ) SELECT p.parcel_candidate_id,p.district_id,p.distinct_uses,p.parcel_use_candidate,l.raw_labels
        FROM read_parquet(?) p JOIN labels l USING(parcel_candidate_id,district_id)
        WHERE p.district_id IN ('10','02','95') AND p.parcel_use_candidate='mixed/other' '''
    mixed=con.execute(query,list(paths)).fetchdf();con.close()
    mixed['dominance']=mixed.raw_labels.map(dominance)
    lands=gpd.read_parquet(LAND['SP']).set_index('district_id')
    rows=[]
    for district in UNITS['SP']:
        land=lands.loc[district,'geometry']
        raw=gpd.read_parquet(SP_RECORDS/f'{district}.parquet',columns=['parcel_candidate_id','geometry']).drop_duplicates('parcel_candidate_id')
        joined=raw.merge(mixed.loc[mixed.district_id.eq(district),['parcel_candidate_id','distinct_uses','dominance']],on='parcel_candidate_id',how='inner')
        for category in ['residential','commerce_services','unresolved']:
            chosen=joined.loc[joined.dominance.eq(category)]
            union=shapely.intersection(shapely.union_all(chosen.geometry.to_numpy()),land) if len(chosen) else shapely.GeometryCollection()
            rows.append({'unit_id':f'SP:{district}','dominance':category,'mixed_source_parcels':len(chosen),
                'explicit_single_category_parcels':int(chosen.distinct_uses.eq(1).sum()),
                'clipped_area_m2':union.area,'land_fraction':union.area/land.area})
    pd.DataFrame(rows).to_csv(OUT/'sp_dominant_use_sensitivity.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__=='__main__':main()

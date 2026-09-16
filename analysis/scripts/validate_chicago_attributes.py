#!/usr/bin/env python3
"""Independent release checks and pilot reconstruction for Chicago's local baseline."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
import shapely
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/Chicago/chi_local_2026_09_16_v1'
WORK=ROOT/'analysis/work/prepared/Chicago/chi_local_2026_09_16_v1'
checks=[]
def check(name,condition,detail=''):
    checks.append({'check':name,'passed':bool(condition),'detail':detail})
    if not condition:raise AssertionError(f'{name}: {detail}')
def main():
    w=pd.read_parquet(OUT/'tables/attributes_wide.parquet')
    l=pd.read_parquet(OUT/'tables/attributes_long.parquet')
    d=gpd.read_parquet(WORK/'districts.parquet')
    land=gpd.read_parquet(WORK/'district_land.parquet')
    b=gpd.read_parquet(WORK/'buildings.parquet')
    check('exact 77 qualified IDs',set(w.unit_id)=={f'CHI:{x:02}' for x in range(1,78)} and len(w)==77)
    check('unique unit-feature keys',not l.duplicated(['unit_id','feature']).any())
    check('no infinite values',np.isfinite(l.value.dropna()).all())
    check('missing families explicitly null',l.loc[l.status.eq('blocked'),'value'].isna().all() and set(l.loc[l.status.eq('blocked'),'family'])=={'M2','M7','B3','U2','U4'})
    check('no cross-city acceptance implied',not l.strict_cross_city_accepted.any())
    check('district area accounting',np.allclose(w.gross_area_m2,w.land_area_m2+w.water_area_m2,atol=.01,rtol=1e-9))
    ratio=l[l.numerator.notna() & l.denominator.gt(0)]
    check('all reported ratio numerators reconstruct values',np.allclose(ratio.value,ratio.numerator/ratio.denominator))
    for prefix in ['road_share_code_','land_use_share_']:
        check(prefix+' sums to one',np.allclose(w.filter(regex='^'+prefix).sum(axis=1),1))
    fractions=l[l.unit.eq('fraction')].value.dropna()
    check('all fractions bounded',fractions.ge(-1e-9).all() and fractions.le(1+1e-7).all())
    check('entropy bounded',w.land_use_entropy_cmap_area8.between(0,1).all())
    check('building IDs resolved',b.bldg_id.is_unique and b.bldg_id.notna().all())
    check('metric valid prepared geometries',all(g.crs.to_epsg()==26916 and g.is_valid.all() for g in [d,land,b]))
    check('area IDs have positive land',w.land_area_m2.gt(0).all())
    gpkg=pyogrio.read_dataframe(OUT/'spatial/chicago_community_attributes.gpkg',layer='community_attributes').set_index('unit_id')
    check('GeoPackage CRS and IDs',gpkg.crs.to_epsg()==26916 and set(gpkg.index)==set(w.unit_id))
    for col in w.select_dtypes(include='number').columns:
        check('gpkg '+col,np.allclose(w[col],gpkg.loc[w.unit_id,col],equal_nan=True))
    longwide=l.pivot(index='unit_id',columns='feature',values='value')
    check('long-wide equivalence',np.allclose(w.set_index('unit_id').loc[longwide.index,longwide.columns],longwide,equal_nan=True))
    csv=pd.read_csv(OUT/'tables/attributes_wide.csv',dtype={'district_id':str})
    check('csv-parquet equivalence',np.allclose(csv.select_dtypes(include='number'),w.select_dtypes(include='number'),equal_nan=True))
    # An untiled full union independently reconstructs production B1 for five contrasting units.
    pilots=['LOOP','NEAR WEST SIDE','WEST TOWN','SOUTH LAWNDALE','OHARE']
    pilot_rows=[]
    for name in pilots:
        q=d[d.district_name.eq(name)]
        check('pilot identity '+name,len(q)==1)
        row=q.iloc[0];g=row.geometry;idx=b.sindex.query(g,predicate='intersects')
        union=shapely.union_all(shapely.intersection(b.geometry.values[idx],g))
        area=union.intersection(land.loc[land.district_id.eq(row.district_id),'geometry'].iloc[0]).area
        reported=w[w.unit_id.eq(row.unit_id)].iloc[0]
        check('untiled B1 '+name,np.isclose(area/row.land_area_m2,reported.building_coverage_municipal_land,rtol=1e-9,atol=1e-10))
        floors=b.loc[b.district_id.eq(row.district_id)&b.stories.gt(0),'stories'].to_numpy()
        check('B2 percentile '+name,np.isclose(np.quantile(floors,.9),reported.building_stories_p90_municipal))
        pilot_rows.append({'unit_id':row.unit_id,'name':name,'land_union_m2':area,'positive_floor_reports':len(floors)})
        print('pilot',name,flush=True)
    m=json.loads((OUT/'validation/run_manifest.json').read_text())
    for path,expected in m['outputs'].items():
        p=OUT/path
        with p.open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
        check('published checksum '+path,actual==expected)
    result={'passed':len(checks),'failed':0,'checks':checks,'pilot_reconstruction':pilot_rows,'limits':'Arithmetic and local-source integrity checks do not establish common SP-Chicago measurement equivalence.'}
    (OUT/'validation/independent_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':len(checks),'failed':0}),flush=True)
if __name__=='__main__':main()

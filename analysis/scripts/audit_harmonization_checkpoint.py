"""Read-only audit of existing candidate releases; write a separate dated checkpoint."""
from pathlib import Path
import hashlib
import json
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'analysis'
RUN = 'overture_2026_08_19_review_v1'
OUT = A / 'results/Chicago/harmonization_checkpoint_2026_09_17'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(2**20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    checks, inputs, summaries = [], {}, []
    def read(path):
        inputs[str(path.relative_to(ROOT))] = sha(path)
        return pd.read_csv(path)
    def check(name, passed, detail=None):
        checks.append(dict(name=name, passed=bool(passed), detail=detail))
    for city, prefix, count in [('Chicago','CHI',77), ('SP','SP',96)]:
        folder = A/'results'/city/RUN
        frame = read(folder/'paired_road_candidates.csv')
        meta = json.loads((folder/'review.json').read_text())
        inputs[str((folder/'review.json').relative_to(ROOT))] = sha(folder/'review.json')
        shares = frame.filter(like='share_')
        check(city+' qualified IDs',frame.unit_id.is_unique and set(frame.unit_id)=={f'{prefix}:{i:02}' for i in range(1,count+1)})
        check(city+' finite/nonnegative',np.isfinite(frame.select_dtypes('number')).all().all() and frame.select_dtypes('number').ge(0).all().all())
        check(city+' density reconstruction',np.allclose(frame.road_density_km_km2,frame.road_length_km/frame.gross_area_km2,rtol=1e-12))
        check(city+' nine unit-sum shares',shares.shape[1]==9 and np.allclose(shares.sum(axis=1),1,rtol=0,atol=1e-12))
        check(city+' total length',np.isclose(frame.road_length_km.sum(),meta['city_length_km'],rtol=1e-12))
        check(city+' connector accounting',int(frame.connector_3arm_candidates.sum())==meta['connector_candidates'])
        check(city+' not accepted',not frame.strict_cross_city_accepted.any())
        inventory=read(folder/'source_class_inventory.csv')
        chosen=inventory.loc[inventory.subtype.eq('road') & inventory['class'].isin(meta['selected_classes'])]
        check(city+' separate class inventory',np.isclose(chosen.length_inside_m.sum()/1000,frame.road_length_km.sum(),rtol=1e-12))
        summaries.append({'city':city,'unknown_length_fraction':float(np.average(frame.share_unknown,weights=frame.road_length_km)),
                          'unclassified_length_fraction':float(np.average(frame.share_unclassified,weights=frame.road_length_km)),
                          'records_with_access_restrictions':meta['access_restriction_records'],
                          'selected_records':meta['selected_segments'], 'city_length_km':meta['city_length_km']})
    print('paired road accounting checked',flush=True)
    pilots=read(A/'results/Chicago'/RUN/'footprint_source_pilots.csv')
    check('ten unique footprint pilot/source rows',len(pilots)==10 and not pilots.duplicated(['unit_id','source']).any())
    check('footprint fractions bounded',pilots[['coverage_gross','coverage_hydro_land']].ge(0).all().all() and pilots[['coverage_gross','coverage_hydro_land']].le(1+1e-12).all().all())
    check('union bounded by individual areas',(pilots.union_gross_m2<=pilots.summed_individual_m2+.01).all())
    dpath=A/'work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet'
    lpath=A/'work/prepared/Chicago/chi_functional_2026_09_16_v2/district_hydro_land.parquet'
    districts=gpd.read_parquet(dpath).set_index('unit_id')
    land=gpd.read_parquet(lpath).set_index('unit_id')
    for path in [dpath,lpath]:inputs[str(path.relative_to(ROOT))]=sha(path)
    reconstruction=[]
    sources={'overture':next((A/'data/Chicago/overture_2026_08_19/building').glob('*.parquet')),
             'municipal_2015':A/'work/prepared/Chicago/chi_local_2026_09_16_v1/buildings.parquet'}
    for source,path in sources.items():
        inputs[str(path.relative_to(ROOT))]=sha(path)
        buildings=gpd.read_parquet(path,columns=['geometry']).to_crs(26916)
        for row in pilots.loc[pilots.source.eq(source)].itertuples():
            geom=districts.loc[row.unit_id].geometry
            ids=buildings.sindex.query(geom,predicate='intersects')
            polygons=shapely.make_valid(buildings.geometry.values[ids])
            # Full union of whole intersecting objects, then clip: no tile helper reused.
            union=shapely.union_all(polygons)
            gross=union.intersection(geom).area
            onland=union.intersection(land.loc[row.unit_id].geometry).area
            check(f'{source} {row.unit_id} untiled gross',np.isclose(gross,row.union_gross_m2,rtol=1e-9,atol=.01))
            check(f'{source} {row.unit_id} untiled land',np.isclose(onland,row.union_hydro_land_m2,rtol=1e-9,atol=.01))
            check(f'{source} {row.unit_id} denominators',np.isclose(gross/geom.area,row.coverage_gross,rtol=1e-9) and np.isclose(onland/land.loc[row.unit_id].geometry.area,row.coverage_hydro_land,rtol=1e-9))
            reconstruction.append({'unit_id':row.unit_id,'source':source,'untiled_gross_m2':gross,'untiled_land_m2':onland,
                                   'gross_difference_m2':gross-row.union_gross_m2,'land_difference_m2':onland-row.union_hydro_land_m2})
            print('independent footprint',source,row.unit_id,flush=True)
        del buildings
    pd.DataFrame(reconstruction).to_csv(OUT/'independent_footprint_unions.csv',index=False)
    pd.DataFrame(summaries).to_csv(OUT/'road_policy_diagnostics.csv',index=False)
    cmp=pilots.pivot(index='unit_id',columns='source',values='coverage_hydro_land')
    cmp['overture_minus_municipal_percentage_points']=(cmp.overture-cmp.municipal_2015)*100
    cmp.to_csv(OUT/'footprint_source_differences.csv')
    # Preserve original checksum evidence; report post-release documentation drift separately.
    functional=A/'results/Chicago/chi_functional_2026_09_16_v2'
    registered=json.loads((functional/'validation/release_checksums.json').read_text())
    drift=[]
    for rel,expected in registered.items():
        path=functional/rel
        actual=sha(path) if path.exists() else None
        if actual!=expected:drift.append({'path':rel,'expected':expected,'actual':actual})
    check('functional numeric artifact integrity',not any(not r['path'].endswith('.md') for r in drift),drift)
    result={'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),
            'checks':checks,'functional_checksum_drift':drift,'strict_cross_city_accepted':False,
            'limits':'Accounting and untiled unions do not validate mapping completeness, access policy, topology, or common entities.'}
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    inputs[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    (OUT/'input_code_checksums.json').write_text(json.dumps(inputs,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'failed':result['failed'],'checksum_drift':len(drift)}),flush=True)
    if result['failed']:raise RuntimeError('Audit failed; inspect checkpoint checks.json')

if __name__=='__main__':main()

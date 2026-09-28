"""Independent accounting, sampled geometry and artifact checks for U2 sensitivity."""
from pathlib import Path
import hashlib,json
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'analysis';RUN='chi_employment_sensitivity_2026_09_17_v1'
W=A/'work/prepared/Chicago'/RUN;O=A/'results/Chicago'/RUN;B=A/'work/prepared/Chicago/chi_functional_2026_09_16_v2'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    q=pd.read_parquet(W/'block_allocations.parquet');d=pd.read_parquet(W/'block_support_diagnostics.parquet');tab=pd.read_parquet(O/'tables/district_job_sensitivity.parquet')
    cfg=json.loads((A/'config/chicago_employment_sensitivity_v1.json').read_text());checks=[]
    def check(name,passed,detail=None):checks.append({'name':name,'passed':bool(passed),'detail':detail})
    check('unique block/scenario/unit',not q.duplicated(['GEOID20','scenario','unit_id']).any())
    check('154 unique district/scenario rows',len(tab)==154 and not tab.duplicated(['unit_id','scenario']).any())
    check('finite allocation outputs',np.isfinite(q.select_dtypes('number')).all().all())
    check('nonnegative jobs',q.jobs_allocated.ge(0).all())
    check('no strict acceptance',not tab.strict_cross_city_accepted.any())
    conserved=q.groupby(['scenario','GEOID20']).agg(total=('jobs_allocated','sum'),expected=('block_jobs','first'))
    check('every block conserves jobs',np.allclose(conserved.total,conserved.expected,rtol=1e-8,atol=1e-7))
    check('allocation numerator denominator',np.allclose(q.jobs_allocated,q.block_jobs*q.allocation_mass_m2/q.allocation_denominator_m2,rtol=1e-10,atol=1e-7))
    check('fallback reproduces gross area',np.allclose(q.loc[q.gross_fallback].jobs_allocated,q.loc[q.gross_fallback].gross_baseline_jobs,rtol=1e-10,atol=1e-7))
    check('fallback iff support negligible',np.array_equal(q.gross_fallback,q.support_area_m2.le(cfg['support_epsilon_m2'])))
    check('density and differences',np.allclose(tab.jobs_density_km2,tab.jobs_allocated/tab.gross_area_km2) and np.allclose(tab.difference_jobs,tab.jobs_allocated-tab.baseline_jobs))
    check('fallback fraction bounded',tab.fallback_fraction.between(0,1+1e-12).all())
    raw=pd.read_csv(O/'tables/district_job_sensitivity.csv');check('CSV Parquet agreement',np.allclose(raw.select_dtypes('number'),tab.select_dtypes('number')))
    for scenario,t in tab.groupby('scenario'):
        part=q.loc[q.scenario.eq(scenario)];inside=part.loc[part.unit_id.ne('OUTSIDE_CHICAGO')].groupby('unit_id').jobs_allocated.sum()
        check(scenario+' complete district universe',set(t.unit_id)=={f'CHI:{i:02}' for i in range(1,78)})
        check(scenario+' aggregate reconstruction',np.allclose(t.set_index('unit_id').jobs_allocated.sort_index(),inside.reindex(sorted(t.unit_id),fill_value=0)))
        check(scenario+' inside outside balance',np.isclose(t.jobs_allocated.sum()+part.loc[part.unit_id.eq('OUTSIDE_CHICAGO')].jobs_allocated.sum(),part.drop_duplicates('GEOID20').block_jobs.sum(),rtol=1e-10))
    # A deterministic stratified sample, selected without inspecting allocation differences.
    outside=q.loc[q.unit_id.eq('OUTSIDE_CHICAGO') & q.piece_area_m2.gt(.01)].drop_duplicates('GEOID20').nlargest(8,'block_jobs').GEOID20
    sample=set(outside)|set(d.loc[d.gross_fallback].nlargest(4,'block_jobs').GEOID20)|set(d.nlargest(4,'ambiguous_area_m2').GEOID20)|set(d.drop_duplicates('GEOID20').sample(4,random_state=20260917).GEOID20)
    blocks=gpd.read_parquet(B/'blocks.parquet').set_index('GEOID20');pieces=gpd.read_parquet(B/'block_district_pieces.parquet');land=gpd.read_parquet(W/'land_use_full_block_extent.parquet')
    samples=[]
    for geoid in sorted(sample):
        block=blocks.loc[geoid];ids=land.sindex.query(block.geometry,predicate='intersects');sub=land.iloc[ids]
        # Alternative construction: for each eligible code, subtract union of ALL OTHER codes.
        unions={code:grp.geometry.union_all().intersection(block.geometry) for code,grp in sub.groupby('code')}
        p=pieces.loc[pieces.GEOID20.eq(geoid)];outside_geom=block.geometry.difference(p.geometry.union_all())
        for scenario,prefixes in cfg['scenarios'].items():
            exclusive=[]
            for code,geom in unions.items():
                if not code.startswith(tuple(prefixes)):continue
                if geom.area<=0:continue
                other=shapely.union_all([g for k,g in unions.items() if k!=code])
                # Zero-area line contacts do not affect polygon support.
                geom=shapely.union_all([g for g in shapely.get_parts(geom) if g.geom_type in ('Polygon','MultiPolygon')])
                other=shapely.union_all([g for g in shapely.get_parts(other) if g.geom_type in ('Polygon','MultiPolygon')])
                exclusive.append(geom.difference(other))
            support=shapely.union_all(exclusive);fallback=support.area<=cfg['support_epsilon_m2'];den=block.geometry.area if fallback else support.area
            actual=q.loc[q.GEOID20.eq(geoid)&q.scenario.eq(scenario)].set_index('unit_id')
            check(f'{geoid} {scenario} independent support',np.isclose(support.area,actual.support_area_m2.iloc[0],rtol=1e-8,atol=.01))
            for unit,geom in list(zip(p.unit_id,p.geometry))+[('OUTSIDE_CHICAGO',outside_geom)]:
                expected=block.jobs*(geom.area if fallback else geom.intersection(support).area)/den
                value=actual.loc[unit,'jobs_allocated'] if unit in actual.index else 0.
                check(f'{geoid} {scenario} {unit} independent allocation',np.isclose(expected,value,rtol=1e-7,atol=1e-5))
                samples.append({'GEOID20':geoid,'scenario':scenario,'unit_id':unit,'independent_jobs':expected,'stored_jobs':value})
        print('independent block',geoid,flush=True)
    manifest=json.loads((O/'validation/source_code_manifest.json').read_text())
    for path,meta in manifest.items():check('input/code unchanged '+path,sha(ROOT/path)==meta['sha256'])
    progress=json.loads((W/'progress.json').read_text())
    for path,h in progress['artifacts'].items():check('artifact '+path,sha(ROOT/path)==h)
    pd.DataFrame(samples).to_csv(O/'validation/independent_block_reconstruction.csv',index=False)
    result={'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'sample_blocks':len(sample),'checks':checks,'strict_cross_city_accepted':False,'audit_code_sha256':sha(Path(__file__))}
    (O/'validation/independent_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','failed','sample_blocks']}))
    if result['failed']:raise RuntimeError('Independent checks failed')

if __name__=='__main__':main()

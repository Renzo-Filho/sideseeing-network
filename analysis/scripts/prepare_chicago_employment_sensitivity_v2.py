"""Checkpointed employment sensitivity; preserves functional v2 and source files."""
from pathlib import Path
import hashlib,json
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from harmonization.geometry import polygonal
from harmonization.employment_v2 import exclusive_support,partition_block,allocate_jobs
ROOT=Path(__file__).resolve().parents[2]; A=ROOT/'analysis'
CONFIG=A/'config/chicago_employment_sensitivity_v2.json';CFG=json.loads(CONFIG.read_text());RUN=CFG['run_id']
WORK=A/'work/prepared/Chicago'/RUN;OUT=A/'results/Chicago'/RUN
BASE=A/'work/prepared/Chicago/chi_functional_2026_09_16_v2'
LUI=A/'data/Chicago/LUI_2023_view_332920193481040239.gpkg'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()


def dump(path,value):
    part=path.with_suffix(path.suffix+'.part');part.write_text(json.dumps(value,indent=2,default=str)+'\n');part.replace(path)


def main():
    for p in [WORK,WORK/'chunks',OUT,OUT/'tables',OUT/'validation']:p.mkdir(parents=True,exist_ok=True)
    paths=[CONFIG,Path(__file__),A/'scripts/harmonization/employment_v2.py',A/'scripts/harmonization/geometry.py',LUI,BASE/'blocks.parquet',BASE/'block_district_pieces.parquet',A/'results/Chicago/chi_functional_2026_09_16_v2/tables/functional_attributes.parquet']
    manifest={str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths}
    signature=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    progress_path=WORK/'progress.json'
    progress=json.loads(progress_path.read_text()) if progress_path.exists() else {'signature':signature,'chunks':{}}
    if progress['signature']!=signature:raise ValueError('Changed inputs/code: use a new versioned run')
    dump(OUT/'validation/source_code_manifest.json',manifest)
    blocks=gpd.read_parquet(BASE/'blocks.parquet');positive=blocks.loc[blocks.jobs.gt(0)].sort_values('GEOID20').reset_index(drop=True)
    pieces=gpd.read_parquet(BASE/'block_district_pieces.parquet');groups={key:list(zip(p.unit_id,p.geometry)) for key,p in pieces.groupby('GEOID20')}
    cache=WORK/'land_use_full_block_extent.parquet';meta_path=WORK/'land_use_metadata.json'
    if cache.exists() and meta_path.exists():
        meta=json.loads(meta_path.read_text());assert meta['signature']==signature and meta['cache_sha256']==sha(cache)
        land=gpd.read_parquet(cache)
    else:
        bounds=positive.to_crs(3857).total_bounds
        land=pyogrio.read_dataframe(LUI,columns=['LANDUSE','LANDUSE2','GlobalID'],bbox=tuple(bounds)).to_crs(26916)
        invalid=int((~land.is_valid).sum());land.geometry=land.geometry.map(polygonal)
        land['code']=land.LANDUSE.fillna('UNKNOWN').astype(str).str.strip()
        land.to_parquet(cache,index=False)
        meta={'signature':signature,'raw_features':pyogrio.read_info(LUI)['features'],'bbox_records':len(land),'bbox_source_crs_3857':bounds.tolist(),'invalid_repaired':invalid,'codes':land.code.value_counts().to_dict(),'cache_sha256':sha(cache),'scope':'Raw regional source bbox covers whole positive-job blocks; no city-only filter','schema':list(land.columns)}
        dump(meta_path,meta)
    print('land-use prepared',len(land),'positive-job blocks',len(positive),flush=True)
    for start in range(0,len(positive),CFG['chunk_size']):
        key=f'{start:05}';path=WORK/'chunks'/f'{key}.parquet';old=progress['chunks'].get(key)
        if old and path.exists() and sha(path)==old['sha256']:
            print('verified chunk',key,flush=True);continue
        rows=[]
        for row in positive.iloc[start:start+CFG['chunk_size']].itertuples():
            partitions=partition_block(row.geometry,groups[row.GEOID20])
            ids=land.sindex.query(row.geometry,predicate='intersects')
            geoms=land.geometry.values[ids];codes=land.code.values[ids]
            for scenario,prefixes in CFG['scenarios'].items():
                support,covered,ambiguous=exclusive_support(geoms,codes,row.geometry,prefixes)
                allocations,masses,den,fallback=allocate_jobs(row.jobs,row.geometry,partitions,support,CFG['support_epsilon_m2'])
                for (unit,geom),jobs,mass in zip(partitions,allocations,masses):
                    rows.append({'GEOID20':row.GEOID20,'unit_id':unit,'scenario':scenario,'block_jobs':row.jobs,'jobs_allocated':jobs,
                        'piece_area_m2':geom.area,'block_area_m2':row.geometry.area,'allocation_mass_m2':mass,'allocation_denominator_m2':den,
                        'overlay_residual_m2':den-(row.geometry.area if fallback else support.area),'support_area_m2':support.area,'cmap_covered_m2':covered,'ambiguous_area_m2':ambiguous,'gross_fallback':fallback,
                        'gross_baseline_jobs':row.jobs*geom.area/row.geometry.area})
        frame=pd.DataFrame(rows);partial=path.with_suffix('.parquet.part');frame.to_parquet(partial,index=False);partial.replace(path)
        progress['chunks'][key]={'sha256':sha(path),'positive_job_blocks':min(CFG['chunk_size'],len(positive)-start)}
        progress['status']='allocating';dump(progress_path,progress)
        print('completed chunk',key,flush=True)
    frame=pd.concat([pd.read_parquet(p) for p in sorted((WORK/'chunks').glob('*.parquet'))],ignore_index=True)
    mass=frame.groupby(['scenario','GEOID20']).agg(allocated=('jobs_allocated','sum'),expected=('block_jobs','first'))
    assert np.allclose(mass.allocated,mass.expected,rtol=1e-8,atol=1e-7)
    assert not frame.duplicated(['scenario','GEOID20','unit_id']).any()
    frame.to_parquet(WORK/'block_allocations.parquet',index=False)
    diagnostic=frame.drop_duplicates(['scenario','GEOID20']).drop(columns=['unit_id','jobs_allocated','piece_area_m2','allocation_mass_m2','gross_baseline_jobs'])
    diagnostic.to_parquet(WORK/'block_support_diagnostics.parquet',index=False)
    baseline=pd.read_parquet(A/'results/Chicago/chi_functional_2026_09_16_v2/tables/functional_attributes.parquet').set_index('unit_id')
    district=[];summary=[]
    for scenario,part in frame.groupby('scenario'):
        totals=part.loc[part.unit_id.ne('OUTSIDE_CHICAGO')].groupby('unit_id').jobs_allocated.sum().reindex(baseline.index,fill_value=0)
        fallback=part.loc[part.gross_fallback & part.unit_id.ne('OUTSIDE_CHICAGO')].groupby('unit_id').jobs_allocated.sum().reindex(baseline.index,fill_value=0)
        gross=part.loc[part.unit_id.ne('OUTSIDE_CHICAGO')].groupby('unit_id').gross_baseline_jobs.sum().reindex(baseline.index,fill_value=0)
        assert np.allclose(gross,baseline.jobs_allocated,rtol=1e-8,atol=1e-5)
        for unit in baseline.index:
            district.append({'unit_id':unit,'scenario':scenario,'jobs_allocated':totals[unit],'gross_area_km2':baseline.loc[unit,'gross_area_m2']/1e6,
                'jobs_density_km2':totals[unit]/(baseline.loc[unit,'gross_area_m2']/1e6),'baseline_jobs':baseline.loc[unit,'jobs_allocated'],
                'difference_jobs':totals[unit]-baseline.loc[unit,'jobs_allocated'],'fallback_jobs':fallback[unit],
                'fallback_fraction':fallback[unit]/totals[unit] if totals[unit]>0 else 0.,'strict_cross_city_accepted':False})
        d=diagnostic.loc[diagnostic.scenario.eq(scenario)]
        summary.append({'scenario':scenario,'whole_intersecting_block_jobs':float(positive.jobs.sum()),'inside_jobs':float(totals.sum()),
            'outside_jobs':float(part.loc[part.unit_id.eq('OUTSIDE_CHICAGO'),'jobs_allocated'].sum()),'positive_job_blocks':len(d),
            'fallback_blocks':int(d.gross_fallback.sum()),'whole_block_fallback_jobs':float(d.loc[d.gross_fallback,'block_jobs'].sum()),
            'inside_fallback_jobs':float(fallback.sum()),'ambiguous_area_m2':float(d.ambiguous_area_m2.sum()),
            'min_cmap_coverage_fraction':float((d.cmap_covered_m2/d.block_area_m2).min()),
            'blocks_with_under_99pct_cmap_coverage':int((d.cmap_covered_m2/d.block_area_m2<.99).sum()),
            'low_support_positive_blocks_under_1m2':int(((d.support_area_m2>CFG['support_epsilon_m2'])&(d.support_area_m2<1)).sum())})
    table=pd.DataFrame(district);table.to_csv(OUT/'tables/district_job_sensitivity.csv',index=False);table.to_parquet(OUT/'tables/district_job_sensitivity.parquet',index=False)
    pd.DataFrame(summary).to_csv(OUT/'tables/mass_and_fallback_summary.csv',index=False)
    dump(OUT/'validation/construction_checks.json',{'per_block_conservation':True,'baseline_reproduced':True,'district_rows':len(table),'positive_job_blocks':len(positive),'zero_job_blocks_skipped':int(blocks.jobs.eq(0).sum()),'strict_cross_city_accepted':False,'summary':summary})
    progress['status']='complete_construction_pending_independent_audit'
    progress['artifacts']={str(p.relative_to(ROOT)):sha(p) for p in [WORK/'block_allocations.parquet',WORK/'block_support_diagnostics.parquet',OUT/'tables/district_job_sensitivity.csv',OUT/'tables/district_job_sensitivity.parquet',OUT/'tables/mass_and_fallback_summary.csv',OUT/'validation/construction_checks.json']}
    dump(progress_path,progress);dump(OUT/'validation/progress.json',progress)
    print('construction complete',flush=True)

if __name__=='__main__':main()

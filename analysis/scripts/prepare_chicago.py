#!/usr/bin/env python3
"""Build a transparent local Chicago baseline. Does not fit cross-city similarity.
Run from any directory: <repo>/.venv/bin/python <repo>/analysis/scripts/prepare_chicago.py
"""
from pathlib import Path
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
import shapely
from harmonization.geometry import polygonal, largest_overlap, union_coverage, normalized_entropy, exclusive_category_areas

ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT/'analysis/config/chicago_attributes_v1.json').read_text())
RAW = ROOT/'analysis/data/Chicago'
WORK = ROOT/'analysis/work/prepared/Chicago'/CFG['release_id']
OUT = ROOT/'analysis/results/Chicago'/CFG['release_id']
AUDIT = {}
ROWS = []


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str, allow_nan=False)+'\n')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def source(pattern):
    files = list(RAW.glob(pattern))
    if len(files) != 1:
        raise ValueError(f'Expected exactly one {pattern}: {files}')
    return files[0]


def add(did, family, feature, value, unit, method, numerator=None, denominator=None,
        status='local_source_exploratory', n=None):
    ROWS.append(dict(city_id='CHI', district_id=did, unit_id=f'CHI:{did}', family=family,
        feature=feature, value=value, unit=unit, numerator=numerator, denominator=denominator,
        source_entities=n, status=status, strict_cross_city_accepted=False, method=method))


def metric_polygons(g, label):
    if g.crs is None:
        raise ValueError(f'{label}: CRS missing')
    before = len(g)
    invalid = int((~g.geometry.is_valid).sum())
    null = int(g.geometry.isna().sum())
    g = g.to_crs(CFG['metric_crs']).copy()
    original_area = float(g.geometry.area.sum())
    g.geometry = g.geometry.map(polygonal)
    g = g[g.geometry.area > 0].reset_index(drop=True)
    AUDIT[label] = {'rows_read': before, 'invalid_before': invalid, 'null_before': null,
                    'positive_polygon_rows': len(g), 'area_change_repair_m2': float(g.area.sum()-original_area)}
    assert g.is_valid.all()
    return g


def main():
    for sub in ['tables','spatial','reports','validation']:
        (OUT/sub).mkdir(parents=True,exist_ok=True)
    WORK.mkdir(parents=True,exist_ok=True)
    print('Hashing raw sources', flush=True)
    manifest = [{'path':str(p.relative_to(ROOT)), 'bytes':p.stat().st_size, 'sha256':sha(p)}
                for p in sorted(RAW.rglob('*')) if p.is_file()]
    dump(OUT/'validation/source_manifest.json', manifest)
    d = metric_polygons(pyogrio.read_dataframe(source('Boundaries_-_Community*')), 'districts')
    d['district_id'] = d.area_numbe.astype(int).map(lambda n:f'{n:02d}')
    assert (d.area_numbe.astype(int)==d.area_num_1.astype(int)).all()
    assert set(d.district_id)=={f'{n:02d}' for n in range(1,78)} and len(d)==77
    d=d.sort_values('district_id').reset_index(drop=True)
    d=d[['district_id','community','geometry']].rename(columns={'community':'district_name'})
    d['unit_id']='CHI:'+d.district_id
    d['gross_area_m2']=d.area
    city=shapely.union_all(d.geometry)
    AUDIT['district_overlap_m2']=float(d.area.sum()-city.area)
    assert AUDIT['district_overlap_m2'] < 1
    print('Land use and water',flush=True)
    bounds=gpd.GeoSeries([city],crs=d.crs).to_crs(3857).total_bounds
    lui=metric_polygons(pyogrio.read_dataframe(source('LUI_2023*'),bbox=tuple(bounds),
        columns=['LANDUSE','LANDUSE2','GlobalID'],use_arrow=True),'lui')
    lui=lui.iloc[lui.sindex.query(city,predicate='intersects')].reset_index(drop=True)
    assert lui.GlobalID.notna().all() and lui.GlobalID.is_unique
    water=shapely.union_all(lui.loc[lui.LANDUSE.eq(CFG['water_code']),'geometry'])
    lands=[]
    def category(code):
        return next((v for k,v in CFG['land_use_prefixes'].items() if str(code).startswith(k)), 'unclassified_excluded')
    lui['category']=lui.LANDUSE.map(category)
    lui.to_parquet(WORK/'land_use.parquet',index=False)
    for i,row in d.iterrows():
        land=row.geometry.difference(water);lands.append(land)
        d.loc[i,'water_area_m2']=row.geometry.intersection(water).area
        d.loc[i,'land_area_m2']=land.area
        q=lui.iloc[lui.sindex.query(row.geometry,predicate='intersects')].copy()
        pieces=shapely.intersection(q.geometry.values,row.geometry)
        q['clipped_area_m2']=shapely.area(pieces)
        covered=shapely.union_all(pieces).area
        overlap=float(q.clipped_area_m2.sum()-covered)
        exclusive, ambiguous_area=exclusive_category_areas(pieces,q.category.values,land)
        masses=pd.Series(exclusive).reindex(CFG['land_use_groups'],fill_value=0)
        method='CMAP 2023 primary LANDUSE; eight broad groups; within-category union on land, conflicting-category overlap excluded; excludes water,6000,9999; secondary uses not split'
        add(row.district_id,'U1','land_use_entropy_cmap_area8', normalized_entropy(masses,8),'index',method,n=len(q))
        for name,value in masses.items():
            add(row.district_id,'U1','land_use_share_'+name,value/masses.sum() if masses.sum() else np.nan,'fraction',method,value,masses.sum())
        for name,value in [('lui_ambiguous_gross',ambiguous_area/row.gross_area_m2),('lui_coverage_gross',covered/row.gross_area_m2),('lui_overlap_gross',overlap/row.gross_area_m2),('lui_classified_land',masses.sum()/land.area),('lui_secondary_use_area_fraction',q.loc[q.LANDUSE2.fillna('').str.strip().ne(''),'clipped_area_m2'].sum()/q.clipped_area_m2.sum())]:
            add(row.district_id,'U1',name,value,'fraction','Source coverage diagnostic',status='diagnostic')
        assert masses.sum() <= land.area+.01
        assert covered <= row.gross_area_m2+.01
    land_gdf=gpd.GeoDataFrame(d.drop(columns='geometry'),geometry=lands,crs=d.crs)
    assert np.allclose(d.gross_area_m2,d.water_area_m2+d.land_area_m2,atol=.01,rtol=1e-9)
    d.to_parquet(WORK/'districts.parquet',index=False)
    land_gdf.to_parquet(WORK/'district_land.parquet',index=False)
    print('Road lengths and source-code composition',flush=True)
    roads=pyogrio.read_dataframe(source('steet*'),columns=['trans_id','class','status','fnode_id','tnode_id','f_zlev','t_zlev'],use_arrow=True).to_crs(d.crs)
    AUDIT['road_source']={'rows':len(roads),'class_counts':roads['class'].fillna('NULL').value_counts().to_dict(),'status_counts':roads.status.fillna('NULL').value_counts().to_dict()}
    roads=roads[roads['class'].isin(CFG['road_classes']) & roads.status.isin(CFG['road_status']) & roads.geometry.notna()].copy().reset_index(drop=True)
    roads['_wkb']=shapely.to_wkb(shapely.normalize(roads.geometry.values))
    AUDIT['road_exact_duplicates_removed']=int(roads._wkb.duplicated().sum())
    roads=roads.drop_duplicates('_wkb').drop(columns='_wkb').reset_index(drop=True)
    roads.to_parquet(WORK/'eligible_roads.parquet',index=False)
    # Each district gets only unassigned pieces; sorted IDs own exactly coincident boundaries.
    previous=shapely.Polygon();assigned_total=0.
    for row in d.itertuples():
        q=roads.iloc[roads.sindex.query(row.geometry,predicate='intersects')].copy()
        pieces=shapely.difference(shapely.intersection(q.geometry.values,row.geometry),previous)
        lengths=shapely.length(pieces);total=float(lengths.sum());assigned_total+=total
        add(row.district_id,'M1','street_density_municipal_km_km2',total/1000/(row.gross_area_m2/1e6),'km/km2',CFG['road_rule_note'],total/1000,row.gross_area_m2/1e6,n=len(q))
        for c in CFG['road_classes']:
            length=float(lengths[q['class'].eq(c).values].sum())
            add(row.district_id,'M6','road_share_code_'+c,length/total if total else np.nan,'fraction','Length shares of the same M1 universe; source codes, not SP categories',length,total)
        previous=shapely.union_all([previous,row.geometry])
    expected=float(shapely.length(shapely.intersection(roads.geometry.values,city)).sum())
    AUDIT['road_length_conservation']={'assigned_m':assigned_total,'city_clipped_m':expected,'difference_m':assigned_total-expected}
    assert np.isclose(assigned_total,expected,rtol=1e-8,atol=.01)
    print('Exploratory planar road blocks',flush=True)
    network=shapely.union_all(roads.geometry.values)
    blocks=gpd.GeoDataFrame(geometry=list(shapely.get_parts(shapely.polygonize(shapely.get_parts(network)))),crs=d.crs)
    blocks=blocks[blocks.area>0].reset_index(drop=True)
    blocks['district_id']=largest_overlap(blocks,d).values
    blocks=blocks[blocks.district_id.notna()].copy()
    # Retain whole objects only when completely within supplied city domain; edge objects excluded.
    blocks['within_city_fraction']=shapely.area(shapely.intersection(blocks.geometry.values,city))/blocks.area
    blocks['edge_flag']=blocks.within_city_fraction.lt(1-1e-8) | shapely.intersects(blocks.geometry.values,city.boundary)
    blocks['area_m2']=blocks.area;blocks['compactness']=4*np.pi*blocks.area/blocks.length**2
    def elongation(g):
        c=np.asarray(g.minimum_rotated_rectangle.exterior.coords);side=np.linalg.norm(np.diff(c,axis=0),axis=1)
        return side.max()/side.min() if side.min()>0 else np.nan
    blocks['elongation']=blocks.geometry.map(elongation)
    blocks.to_parquet(WORK/'experimental_blocks.parquet',index=False)
    for row in d.itertuples():
        q=blocks[blocks.district_id.eq(row.district_id)&~blocks.edge_flag]
        for family,col,values in [('M3','block_log_area',np.log(q.area_m2)),('M4','block_compactness',q.compactness),('M4','block_elongation',q.elongation)]:
            for stat,value in [('median',values.median()),('iqr',values.quantile(.75)-values.quantile(.25))]:
                add(row.district_id,family,col+'_'+stat+'_experimental',value,'log(m2)' if family=='M3' else 'ratio','Whole planar road-enclosed polygons; boundary-touching excluded; no carriageway or barrier correction; NOT accepted physical blocks',status='experimental_not_model_ready',n=len(q))
    AUDIT['blocks']={'total':len(blocks),'edge_excluded':int(blocks.edge_flag.sum())}
    print('Buildings',flush=True)
    cache=WORK/'buildings_source.parquet'
    # Always bind cache to source content; an unmanifested cache is not silently trusted.
    raw=source('Building_Footprints*');cache_meta=WORK/'buildings_cache.json';rawhash=next(x['sha256'] for x in manifest if x['path']==str(raw.relative_to(ROOT)))
    if cache.exists() and cache_meta.exists() and json.loads(cache_meta.read_text()).get('source_sha256')==rawhash:
        b=gpd.read_parquet(cache)
    else:
        b=pyogrio.read_dataframe(raw,columns=['bldg_id','bldg_statu','stories','no_stories','bldg_sq_fo','footprint_','year_built'],use_arrow=True)
        b.to_parquet(cache,index=False);dump(cache_meta,{'source_sha256':rawhash})
    AUDIT['building_status_counts']=b.bldg_statu.fillna('NULL').value_counts().to_dict()
    b=metric_polygons(b[b.bldg_statu.eq(CFG['building_status'])], 'buildings')
    duplicate=b.bldg_id.duplicated(False)
    AUDIT['duplicate_active_building_ids']=b.loc[duplicate,'bldg_id'].value_counts().to_dict()
    repaired=[]
    for bid,q in b[duplicate].groupby('bldg_id'):
        item=q.iloc[0].copy();item['geometry']=shapely.union_all(q.geometry)
        for col in ['stories','no_stories','bldg_sq_fo']:
            if q[col].nunique(dropna=False)>1: item[col]=None
        repaired.append(item)
    if repaired:
        b=gpd.GeoDataFrame(pd.concat([b[~duplicate],gpd.GeoDataFrame(repaired,crs=b.crs)],ignore_index=True),crs=b.crs)
    assert b.bldg_id.notna().all() and b.bldg_id.is_unique
    assert not b.bldg_id.eq('0').any()
    b['district_id']=largest_overlap(b,d).values
    for col in ['stories','no_stories','bldg_sq_fo']:
        b[col]=pd.to_numeric(b[col],errors='coerce')
    AUDIT['building_story_fields']={'positive_stories':int(b.stories.gt(0).sum()),'positive_below_ground_stories':int(b.no_stories.gt(0).sum()),'no_stories_definition':'NO_STORIES_BELOW: below-ground stories, not competing total floor count','max_stories':float(b.stories.max()),'source_vintage_counts':b.footprint_.fillna('NULL').value_counts().to_dict()}
    b.to_parquet(WORK/'buildings.parquet',index=False)
    for row,land in zip(d.itertuples(),lands):
        gross,onland,summed=union_coverage(b,row.geometry,land,CFG['tile_m'])
        assert 0<=onland<=row.land_area_m2+.01 and gross<=summed+.01
        add(row.district_id,'B1','building_coverage_municipal_land',onland/row.land_area_m2,'fraction','ACTIVE municipal footprint exact tiled union; CMAP 5000 water mask proxy; source metadata August 2015',onland,row.land_area_m2)
        add(row.district_id,'B1','building_coverage_municipal_gross',gross/row.gross_area_m2,'fraction','Same footprint union / gross area',gross,row.gross_area_m2,status='diagnostic')
        add(row.district_id,'B1','footprint_overlap_excess_fraction',(summed-gross)/summed if summed else 0,'fraction','Summed clipped area minus union, divided by sum',summed-gross,summed,status='diagnostic')
        q=b[b.district_id.eq(row.district_id)];floors=q.loc[q.stories.gt(0),'stories']
        for name,value in [('median',floors.median()),('p90',floors.quantile(.9))]:
            add(row.district_id,'B2','building_stories_'+name+'_municipal',value,'stories','One positive stories field per ACTIVE building; whole geometry largest-overlap assignment; no missing-floor imputation; distinct from SP fiscal entities',n=len(floors))
        add(row.district_id,'B2','building_stories_coverage',len(floors)/len(q) if len(q) else np.nan,'fraction','Positive stories / assigned ACTIVE building records',len(floors),len(q),status='diagnostic')
        print('  buildings',row.district_id,flush=True)
    print('Population and explicit missing families',flush=True)
    acs=pd.read_csv(RAW/'chicago_acs_community_areas.csv')
    assert len(acs)==77 and acs.community_area.is_unique
    acs['name']=acs.community_area.str.strip().str.upper()
    joined=d.merge(acs,left_on='district_name',right_on='name',validate='one_to_one',how='left')
    assert joined.total_population.notna().all() and joined.total_population.ge(0).all()
    assert joined.total_population.sum()==acs.total_population.sum()
    joined[['district_id','district_name','community_area','acs_year','total_population']].to_csv(OUT/'tables/population_crosswalk.csv',index=False)
    for row in joined.itertuples():
        add(row.district_id,'U3','population_density_acs_label2023',row.total_population/(row.gross_area_m2/1e6),'residents/km2','Provided ACS aggregate; exact validated name crosswalk; period/MOE provenance unresolved',row.total_population,row.gross_area_m2/1e6,status='provisional_population_provenance')
        for family,reason in {**CFG['blocked_families'],'M2':'Road topology/level consistency and common SP method not yet validated; no planar proxy promoted'}.items():
            add(row.district_id,family,family.lower()+'_unavailable',np.nan,'unavailable',reason,status='blocked')
    AUDIT['population_mass']=float(acs.total_population.sum())
    long=pd.DataFrame(ROWS)
    assert not long.duplicated(['unit_id','feature']).any()
    finite=long.value.dropna();assert np.isfinite(finite).all()
    wide=long.pivot(index='unit_id',columns='feature',values='value').reset_index()
    wide=d[['unit_id','district_id','district_name','gross_area_m2','water_area_m2','land_area_m2']].merge(wide,on='unit_id',validate='one_to_one')
    long.to_csv(OUT/'tables/attributes_long.csv',index=False)
    long.to_parquet(OUT/'tables/attributes_long.parquet',index=False)
    wide.to_csv(OUT/'tables/attributes_wide.csv',index=False)
    wide.to_parquet(OUT/'tables/attributes_wide.parquet',index=False)
    dictionary=long[['family','feature','unit','method','status','strict_cross_city_accepted']].drop_duplicates()
    dictionary.to_csv(OUT/'tables/attribute_dictionary.csv',index=False)
    spatial=d[['unit_id','geometry']].merge(wide,on='unit_id',validate='one_to_one')
    gpkg=OUT/'spatial/chicago_community_attributes.gpkg'
    spatial.to_file(gpkg,layer='community_attributes',driver='GPKG')
    land_gdf.to_file(gpkg,layer='community_land_proxy',driver='GPKG')
    reread=pyogrio.read_dataframe(gpkg,layer='community_attributes')
    assert len(reread)==77 and reread.crs.to_epsg()==26916 and reread.is_valid.all()
    for col in wide.select_dtypes(include='number').columns:
        assert np.allclose(reread[col],spatial[col],equal_nan=True)
    AUDIT['release']={'units':len(wide),'features':len(dictionary),'long_rows':len(long),'all_strict_cross_city_accepted':False,'gpkg_roundtrip':True,'complete_local_baseline':True}
    dump(OUT/'validation/checks.json',AUDIT)
    dump(OUT/'validation/run_manifest.json',{'completed_utc':datetime.now(timezone.utc).isoformat(),'config':CFG,'python':platform.python_version(),'versions':{m.__name__:m.__version__ for m in [np,pd,gpd,pyogrio,shapely]},'code':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'analysis/config/chicago_attributes_v1.json',ROOT/'analysis/scripts/harmonization/geometry.py']},'outputs':{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='run_manifest.json'}})
    print('COMPLETE',OUT,flush=True)

if __name__=='__main__':
    main()

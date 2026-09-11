"""Prepare SP inputs for plan Sections 1–3. Deliberately does not build attributes.

Run from the project environment. Raw inputs are read-only. Stage checkpoints are
bound to the complete input, configuration and script fingerprints. Ambiguous
identity, cadastral semantics and network topology are never silently resolved.
"""
from pathlib import Path
import csv
import hashlib
import importlib.metadata
import inspect
import json
import platform
import re
import sqlite3
import time
import traceback

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'analysis/data/SP'
CONFIG_PATH = ROOT / 'analysis/config/sp_preparation_v2.json'
CFG = json.loads(CONFIG_PATH.read_text())
OUT = ROOT / 'analysis/processed/SP' / CFG['run_id']
OUT.mkdir(parents=True, exist_ok=True)
CAD = RAW / 'Cadastro e Vias'


def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str, allow_nan=False))
    tmp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def log(message):
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), message, flush=True)


def write_geo(g, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    g.to_parquet(path, index=False)


def read_geo(path):
    g = pyogrio.read_dataframe(path, fid_as_index=True).reset_index().rename(columns={'fid':'source_fid'})
    if g.crs is None:
        raise ValueError(f'Unknown CRS: {path}')
    return g.to_crs(CFG['metric_crs'])


def con():
    return duckdb.connect(config={'threads':2, 'memory_limit':'768MB', 'preserve_insertion_order':False, 'temp_directory':str(OUT/'temp')})


def records(c, query):
    return json.loads(c.execute(query).fetchdf().to_json(orient='records'))


def copy(c, query, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # All paths are program-controlled, never interpolated user SQL.
    escaped = str(path).replace("'", "''")
    c.execute(f"COPY ({query}) TO '{escaped}' (FORMAT PARQUET, COMPRESSION ZSTD)")


def inventory():
    rows = []
    for p in sorted(RAW.rglob('*')):
        if not p.is_file():
            continue
        st = p.stat()
        row = {'path':str(p.relative_to(ROOT)), 'bytes':st.st_size, 'mtime_ns':st.st_mtime_ns,
               'sha256':sha(p), 'observation_date':None, 'download_date':None,
               'source_url':None, 'license':None, 'provenance_status':'unverified_not_inferred_from_mtime'}
        if p.suffix.lower() in ['.gpkg','.shp']:
            row['layers'] = []
            for layer, _ in pyogrio.list_layers(p):
                info = pyogrio.read_info(p, layer=layer)
                row['layers'].append({'crs':info['crs'], 'layer':info['layer_name'], 'features':int(info['features']),
                    'geometry_type':info['geometry_type'], 'schema':dict(zip(info['fields'].tolist(),info['dtypes'].tolist()))})
        elif p.suffix.lower() == '.csv':
            with p.open(encoding='utf-8-sig') as f:
                row['schema'] = next(csv.reader(f,delimiter=';'))
        if p.name == 'IPTU_2026.csv': row['observation_date'] = 'tax year 2026'
        if p.name == '3550308_SAO_PAULO.csv': row['observation_date'] = '2022 census'
        if p.name.startswith('sao_paulo_building_morphology'):
            row['provenance_sidecar'] = str((p.parent/'sao_paulo_building_morphology.metadata.json').relative_to(ROOT))
        rows.append(row)
    dump(OUT/'source_manifest.json',rows)
    return rows


def polygon_only(g):
    if g.geom_type in ('Polygon','MultiPolygon'): return g
    parts = [polygon_only(x) for x in shapely.get_parts(g) if x.geom_type in ('Polygon','MultiPolygon','GeometryCollection')]
    return shapely.union_all(parts) if parts else shapely.Polygon()


def districts():
    d = read_geo(CAD/'distrito_municipal_v2.gpkg')
    d['district_id'] = d.cd_distrito_municipal.astype(str).str.zfill(2)
    assert len(d)==96 and d.district_id.nunique()==96
    assert d.loc[d.district_id.eq('10'),'nm_distrito_municipal'].iloc[0]=='BRAS'
    old_area = d.area.copy()
    d['source_valid'] = d.is_valid
    repair = []
    for idx in d.index[~d.is_valid]:
        old = d.geometry[idx]
        fixed = polygon_only(shapely.make_valid(old))
        repair.append({'district_id':d.district_id[idx], 'reason':shapely.is_valid_reason(old),
                       'old_area_m2':float(old.area), 'new_area_m2':float(fixed.area),
                       'delta_m2':float(fixed.area-old.area), 'new_parts':len(shapely.get_parts(fixed)),
                       'discarded_nonpolygon_components':True})
        d.loc[idx,'geometry'] = fixed
    assert d.is_valid.all() and not d.is_empty.any()
    d['gross_area_m2'] = d.area
    d['land_area_m2'] = np.nan
    d['land_area_status'] = 'blocked_no_verified_water_mask'
    d['area_change_m2'] = d.area-old_area
    d['stored_area_delta_m2'] = d.area-pd.to_numeric(d.qt_area_metro)
    d = d.sort_values('district_id').reset_index(drop=True)
    overlaps = []
    for i,j in zip(*d.sindex.query(d.geometry,predicate='intersects')):
        if i>=j: continue
        a = d.geometry.iloc[i].intersection(d.geometry.iloc[j]).area
        if a>0: overlaps.append({'district_a':d.district_id[i], 'district_b':d.district_id[j], 'overlap_m2':float(a)})
    union = shapely.union_all(d.geometry.values)
    municipal = gpd.GeoDataFrame({'municipality_id':['3550308'],'boundary_source':['union_of_96_districts_not_independent_reference']},geometry=[union],crs=d.crs)
    write_geo(d,OUT/'01_districts/districts.parquet')
    write_geo(municipal,OUT/'01_districts/municipal_union.parquet')
    gpkg = OUT/'01_districts/districts.gpkg'
    pyogrio.write_dataframe(d,gpkg,layer='districts',driver='GPKG')
    pyogrio.write_dataframe(municipal,gpkg,layer='municipal_union',driver='GPKG')
    holes = [shapely.Polygon(r) for p in shapely.get_parts(union) for r in p.interiors]
    report = {'rows':len(d),'repairs':repair,'invalid_after':int((~d.is_valid).sum()),
              'overlaps':overlaps,'sum_district_area_m2':float(d.area.sum()),'union_area_m2':float(union.area),
              'union_interior_holes':len(holes),'union_hole_area_m2':float(sum(x.area for x in holes)),
              'independent_gap_check':'blocked_no_independent_municipal_boundary',
              'land_area':'blocked_no_verified_water_mask'}
    dump(OUT/'01_districts/qa.json',report)
    return report


def assign_polygons(g, d):
    """Whole-object assignment by maximum overlap, then representative point, then ID."""
    choices = [[] for _ in range(len(g))]
    a,b = d.sindex.query(g.geometry,predicate='intersects')
    for i,j in zip(a,b): choices[i].append(j)
    ids=[]; counts=[]; ties=[]; fractions=[]
    for geom, candidates in zip(g.geometry,choices):
        counts.append(len(candidates))
        if not candidates:
            ids.append(None); ties.append(False); fractions.append(np.nan); continue
        if len(candidates)==1 and d.geometry.iloc[candidates[0]].covers(geom):
            ids.append(d.district_id.iloc[candidates[0]]);ties.append(False);fractions.append(1.);continue
        areas=[geom.intersection(d.geometry.iloc[j]).area for j in candidates]
        maximum=max(areas)
        if maximum<=0:
            ids.append(None);ties.append(False);fractions.append(0.);continue
        selected=[j for j,area in zip(candidates,areas) if abs(area-maximum)<=1e-8]
        tied=len(selected)>1
        rp=geom.representative_point()
        selected.sort(key=lambda j:(not d.geometry.iloc[j].covers(rp),d.district_id.iloc[j]))
        ids.append(d.district_id.iloc[selected[0]]); ties.append(tied); fractions.append(maximum/geom.area)
    return pd.DataFrame({'assigned_district_id':ids,'intersecting_district_count':counts,
                         'assignment_tie':ties,'largest_overlap_fraction':fractions})


def parcels_tax():
    folder=OUT/'02_parcels_tax';folder.mkdir(exist_ok=True)
    d=gpd.read_parquet(OUT/'01_districts/districts.parquet')
    total=0
    recovery=OUT/'parcel_geometry_recovery.json'
    recovery_data=json.loads(recovery.read_text()) if recovery.exists() else {}
    for p in sorted((CAD/'Lotes').glob('*.gpkg')):
        code=re.search(r'LOTES_(\d+)_',p.name)[1]
        target=folder/'parcel_records'/f'{code}.parquet'
        recovered=recovery_data.get(p.name,{})
        if (recovered and recovered.get('preparation_script_sha256')==sha(__file__)
                and recovered.get('config_sha256')==sha(CONFIG_PATH)
                and recovered.get('source_sha256')==sha(p) and target.exists()
                and recovered.get('output_sha256')==sha(target)
                and recovered.get('assignment_method_sha256')==hashlib.sha256(inspect.getsource(assign_polygons).encode()).hexdigest()
                and recovered.get('district_sha256')==sha(OUT/'01_districts/districts.parquet')):
            total+=recovered['rows']
            log(f'parcel district {code}: validated recovery reused')
            continue
        g=read_geo(p)
        for col,width in [('lo_setor',3),('lo_quadra',3),('lo_lote',4),('lo_condomi',2)]:
            g[col]=g[col].astype('string').str.zfill(width)
        g['sql_key']=g.lo_setor+g.lo_quadra+g.lo_lote
        g['condo_key']=g.lo_setor+g.lo_quadra+g.lo_condomi
        g['source_file']=str(p.relative_to(ROOT));g['source_district_id']=code
        g['source_record_id']=code+':'+g.source_fid.astype(str)
        assert g.is_valid.all() and not g.is_empty.any() and not g.geometry.isna().any()
        g['geometry_hash']=[hashlib.sha256(w).hexdigest() for w in shapely.to_wkb(shapely.normalize(g.geometry.values),byte_order=1)]
        # SQL is included: coincident geometries with differing SQL remain distinct candidates.
        g['parcel_candidate_id']=[hashlib.sha256((s+':'+h).encode()).hexdigest() for s,h in zip(g.sql_key,g.geometry_hash)]
        assignments=assign_polygons(g,d)
        g=pd.concat([g.reset_index(drop=True),assignments],axis=1)
        write_geo(g,folder/'parcel_records'/f'{code}.parquet')
        total+=len(g)
        log(f'parcel district {code}: {len(g):,} records normalized')
    log('Parcel geometry complete; building identity tables')
    c=con()
    c.read_parquet(str(folder/'parcel_records/*.parquet')).create_view('p')
    copy(c,'''SELECT parcel_candidate_id,sql_key,geometry_hash,min(assigned_district_id) district_id,
      count(*) source_record_count,count(distinct lo_condomi) condo_code_count,
      count(distinct lo_tp_lote) parcel_type_count,count(distinct lo_tp_quad) block_type_count,
      min(largest_overlap_fraction) largest_overlap_fraction,
      max(intersecting_district_count) intersecting_district_count,
      bool_or(assignment_tie) assignment_tie FROM p GROUP BY ALL''',folder/'parcel_candidates.parquet')
    c.read_parquet(str(folder/'parcel_candidates.parquet')).create_view('candidates')
    copy(c,'''SELECT sql_key,count(distinct parcel_candidate_id) geometry_candidates,
      count(*) raw_records,count(distinct source_district_id) source_districts,
      count(distinct lo_condomi) condominium_codes FROM p GROUP BY sql_key''',folder/'sql_identity.parquet')
    c.read_parquet(str(folder/'sql_identity.parquet')).create_view('identity')
    copy(c,'''SELECT a.*, CASE WHEN i.geometry_candidates>1 THEN 'unresolved_multiple_geometries'
      WHEN a.condo_code_count>1 OR a.parcel_type_count>1 OR a.block_type_count>1 THEN 'unresolved_metadata_conflict'
      WHEN a.district_id IS NULL THEN 'outside_districts'
      ELSE 'unique_geometry_candidate_semantics_pending' END identity_status
      FROM candidates a JOIN identity i USING(sql_key)''',folder/'parcel_identity_status.parquet')
    copy(c,'''SELECT source_record_id,source_file,source_fid,parcel_candidate_id,sql_key,
      condo_key,lo_condomi,lo_tp_lote,lo_tp_quad,source_district_id,assigned_district_id,
      intersecting_district_count,assignment_tie,largest_overlap_fraction FROM p''',folder/'parcel_lineage.parquet')
    copy(c,"SELECT * FROM p WHERE sql_key IN (SELECT sql_key FROM identity WHERE geometry_candidates>1)",folder/'unresolved_parcel_records.parquet')
    log('Normalizing full tax register with bounded memory and unordered output')
    c.sql("SELECT * FROM read_csv(?,delim=';',header=true,all_varchar=true,strict_mode=true)", params=[str(CAD/'IPTU_2026.csv')]).create_view('raw_tax')
    copy(c,'''SELECT *, "NUMERO DO CONTRIBUINTE" taxpayer_id,
      substr(regexp_replace("NUMERO DO CONTRIBUINTE",'[^0-9]','','g'),1,10) sql_key,
      substr(regexp_replace("NUMERO DO CONTRIBUINTE",'[^0-9]','','g'),1,6)||substr("NUMERO DO CONDOMINIO",1,2) condo_key,
      regexp_full_match("NUMERO DO CONTRIBUINTE",'[0-9]{10}-[0-9]') taxpayer_format_valid,
      try_cast("ANO DO EXERCICIO" AS INTEGER) tax_year,
      try_cast("AREA DO TERRENO" AS DOUBLE) land_area_m2,
      try_cast("AREA CONSTRUIDA" AS DOUBLE) constructed_area_m2,
      try_cast("AREA OCUPADA" AS DOUBLE) occupied_area_m2,
      try_cast("FRACAO IDEAL" AS DOUBLE) ideal_fraction,
      try_cast("QUANTIDADE DE PAVIMENTOS" AS DOUBLE) floors,
      "TIPO DE USO DO IMOVEL" use_raw FROM raw_tax''',folder/'tax_accounts.parquet')
    log('Tax register exported; constructing candidate crosswalk')
    c.read_parquet(str(folder/'tax_accounts.parquet')).create_view('tax')
    c.execute('''CREATE TABLE exact_keys AS SELECT sql_key,count(*) candidate_count,
      CASE WHEN count(*)=1 THEN min(parcel_candidate_id) END parcel_candidate_id FROM candidates GROUP BY sql_key''')
    c.execute('''CREATE TABLE condo_keys AS SELECT condo_key,count(distinct parcel_candidate_id) candidate_count,
      CASE WHEN count(distinct parcel_candidate_id)=1 THEN min(parcel_candidate_id) END parcel_candidate_id
      FROM p WHERE lo_condomi!='00' GROUP BY condo_key''')
    copy(c,'''SELECT t.taxpayer_id,t.sql_key,t.condo_key,t.taxpayer_format_valid,
      coalesce(e.candidate_count,0) exact_candidate_count,
      coalesce(k.candidate_count,0) condo_candidate_count,
      CASE WHEN NOT t.taxpayer_format_valid THEN NULL WHEN e.candidate_count=1 THEN e.parcel_candidate_id
           WHEN e.candidate_count IS NULL AND k.candidate_count=1 THEN k.parcel_candidate_id END parcel_candidate_id,
      CASE WHEN NOT t.taxpayer_format_valid THEN 'invalid_taxpayer_format'
           WHEN e.candidate_count=1 THEN 'exact_sql_candidate'
           WHEN e.candidate_count>1 THEN 'ambiguous_exact_sql'
           WHEN k.candidate_count=1 THEN 'condominium_candidate'
           WHEN k.candidate_count>1 THEN 'ambiguous_condominium' ELSE 'unmatched' END match_method,
      CASE WHEN e.candidate_count=1 AND k.candidate_count=1
           THEN e.parcel_candidate_id!=k.parcel_candidate_id ELSE false END exact_condo_disagreement,
      false accepted_for_area_aggregation
      FROM tax t LEFT JOIN exact_keys e USING(sql_key)
      LEFT JOIN condo_keys k ON t.condo_key=k.condo_key AND t."NUMERO DO CONDOMINIO"!='00-0' ''',folder/'tax_parcel_crosswalk.parquet')
    c.read_parquet(str(folder/'tax_parcel_crosswalk.parquet')).create_view('crosswalk')
    copy(c,'''SELECT w.*,p.district_id FROM crosswalk w LEFT JOIN candidates p USING(parcel_candidate_id)
       WHERE match_method NOT IN ('exact_sql_candidate','condominium_candidate') OR exact_condo_disagreement''',folder/'tax_linkage_exceptions.parquet')
    join_report=records(c,'''SELECT w.match_method,p.district_id,count(*) tax_accounts,
      sum(t.constructed_area_m2) raw_constructed_area_mass_m2,
      count(*) FILTER(WHERE w.exact_condo_disagreement) conflicting_keys
      FROM crosswalk w JOIN tax t USING(taxpayer_id) LEFT JOIN candidates p USING(parcel_candidate_id) GROUP BY ALL ORDER BY 1,2''')
    dump(folder/'candidate_join_by_district.json',join_report)
    copy(c,'''SELECT use_raw,count(*) tax_account_count, NULL::VARCHAR mapped_use,
      'pending_dictionary_review' mapping_status FROM tax GROUP BY use_raw''',folder/'use_mapping_review.parquet')
    copy(c,'''SELECT lo_tp_quad,lo_tp_lote,count(*) record_count,
      'pending_official_definition' status FROM p GROUP BY ALL''',folder/'parcel_type_review.parquet')
    copy(c,'''SELECT condo_key,count(*) accounts,sum(constructed_area_m2) unvalidated_sum_constructed_area,
      min(land_area_m2) min_land_area,max(land_area_m2) max_land_area,
      sum(ideal_fraction) fraction_sum,min(floors) min_floors,max(floors) max_floors
      FROM tax WHERE "NUMERO DO CONDOMINIO"!='00-0' GROUP BY condo_key''',folder/'condominium_aggregation_diagnostics.parquet')
    report={'raw_parcel_rows':total,'identity':records(c,'SELECT geometry_candidates,count(*) sql_groups FROM identity GROUP BY 1 ORDER BY 1'),
      'candidate_count':c.execute('SELECT count(*) FROM candidates').fetchone()[0],
      'cross_file_sql_groups':c.execute('SELECT count(*) FROM identity WHERE source_districts>1').fetchone()[0],
      'coincident_geometry_different_sql_groups':c.execute('SELECT count(*) FROM (SELECT geometry_hash FROM candidates GROUP BY 1 HAVING count(distinct sql_key)>1)').fetchone()[0],
      'tax':records(c,'''SELECT count(*) records,count(distinct taxpayer_id) unique_taxpayers,
        count(*) FILTER(WHERE NOT taxpayer_format_valid) invalid_format,
        count(*) FILTER(WHERE land_area_m2 IS NULL OR constructed_area_m2 IS NULL OR occupied_area_m2 IS NULL OR floors IS NULL OR ideal_fraction IS NULL) numeric_parse_null,
        count(*) FILTER(WHERE tax_year!=2026 OR tax_year IS NULL) wrong_year FROM tax'''),
      'matches':records(c,'SELECT match_method,count(*) records FROM crosswalk GROUP BY 1 ORDER BY 1'),
      'raw_constructed_area_total_m2':c.execute('SELECT sum(constructed_area_m2) FROM tax').fetchone()[0],
      'accepted_area_aggregation':False,
      'reason':'Candidate linkage does not validate physical identity or condominium area semantics'}
    assert report['tax'][0]['records']==report['tax'][0]['unique_taxpayers']
    assert c.execute('SELECT count(*) FROM crosswalk').fetchone()[0]==report['tax'][0]['records']
    assert sum(r['tax_accounts'] for r in join_report)==report['tax'][0]['records']
    dump(folder/'qa.json',report)
    c.close()
    return report


def streets():
    folder=OUT/'03_streets';folder.mkdir(exist_ok=True)
    d=gpd.read_parquet(OUT/'01_districts/districts.parquet')
    s=read_geo(CAD/'SIRGAS_GPKG_logradouronbl.gpkg')
    t=read_geo(CAD/'geoportal_classificacao_viaria_cet.gpkg')
    for g,label in [(s,'streets'),(t,'cet')]:
        g['geometry_valid']=g.is_valid & ~g.is_empty & g.geometry.notna()
        g['validity_reason']=shapely.is_valid_reason(g.geometry.values)
        write_geo(g,folder/f'{label}_source.parquet')
        write_geo(g.loc[~g.geometry_valid],folder/f'{label}_quarantine.parquet')
    street_invalid=int((~s.geometry_valid).sum());cet_invalid=int((~t.geometry_valid).sum())
    s=s.loc[s.geometry_valid].explode(index_parts=False).reset_index(drop=True)
    assert s.geom_type.eq('LineString').all()
    s['part_id']=s.groupby('source_fid').cumcount()
    s['edge_id']=s.lg_seg_id.astype(str)+':'+s.part_id.astype(str)
    s['length_m']=s.length
    s['geometry_hash']=[hashlib.sha256(w).hexdigest() for w in shapely.to_wkb(shapely.normalize(s.geometry.values),byte_order=1)]
    s['canonical_geometry_id']=s.geometry_hash
    s['duplicate_geometry_count']=s.groupby('geometry_hash').edge_id.transform('size')
    s['street_universe_status']='pending_type_dictionary_and_carriageway_policy'
    s['topology_status']='source_geometry_not_verified_junctions'
    t['cet_segment_id']=t.cd_identificador_segmento_logradouro.astype('Int64')
    class_groups=t.groupby('cet_segment_id').agg(cet_records=('source_fid','size'),
       class_count=('dc_tipo_classificacao_viaria','nunique'),
       class_candidate=('dc_tipo_classificacao_viaria','first')).reset_index()
    class_groups.loc[class_groups.class_count.ne(1),'class_candidate']=None
    s=s.merge(class_groups,how='left',left_on='lg_seg_id',right_on='cet_segment_id',validate='many_to_one')
    # Use all valid CET geometries for a segment; repeated entries do not multiply edges.
    valid_t=t.loc[t.geometry_valid]
    geometries=valid_t.groupby('cet_segment_id').geometry.apply(lambda x:shapely.union_all(x.values)).to_dict()
    s['cet_hausdorff_m']=[float(shapely.hausdorff_distance(g,geometries[k])) if k in geometries else np.nan for g,k in zip(s.geometry,s.lg_seg_id)]
    s['class_match_status']=np.select([s.class_count.isna(),s.class_count.ne(1),s.cet_hausdorff_m.isna(),s.cet_hausdorff_m.gt(CFG['cet_alignment_diagnostic_m'])],
       ['unmatched_id','conflicting_or_missing_class','no_valid_class_geometry','alignment_review'],default='aligned_candidate')
    s['class_accepted_for_model']=False
    write_geo(s,folder/'edge_candidates.parquet')
    class_groups.to_parquet(folder/'cet_id_crosswalk.parquet',index=False)
    s[['edge_id','lg_seg_id','source_fid','part_id','geometry_hash','canonical_geometry_id','duplicate_geometry_count','class_candidate','class_match_status','cet_hausdorff_m']].to_parquet(folder/'edge_lineage_and_class_review.parquet',index=False)
    pd.DataFrame({'lg_tipo':s.lg_tipo.fillna('').unique(),'include_morphology':None,'status':'pending_dictionary_review'}).to_csv(folder/'street_type_review.csv',index=False)
    # Exact endpoints are a diagnostic substrate only. No crossing splits or snap.
    endpoints=[]
    for edge,g in zip(s.edge_id,s.geometry):
        for pos,coord in [('start',g.coords[0]),('end',g.coords[-1])]: endpoints.append((edge,pos,coord[0],coord[1]))
    ep=pd.DataFrame(endpoints,columns=['edge_id','position','x','y'])
    ep['endpoint_id']=[hashlib.sha256(f'{x.hex()}:{y.hex()}'.encode()).hexdigest() for x,y in zip(ep.x,ep.y)]
    ep.to_parquet(folder/'edge_endpoints.parquet',index=False)
    nodes=ep.groupby('endpoint_id').agg(x=('x','first'),y=('y','first'),incident_source_edges=('edge_id','nunique')).reset_index()
    ng=gpd.GeoDataFrame(nodes,geometry=gpd.points_from_xy(nodes.x,nodes.y),crs=s.crs)
    ng['status']='endpoint_candidate_not_accepted_junction'
    write_geo(ng,folder/'endpoint_candidates.parquet')
    coverage=[]
    for _,row in d.iterrows():
        subset=s.iloc[s.sindex.query(row.geometry,predicate='intersects')]
        lengths=subset.geometry.intersection(row.geometry).length
        total=float(lengths.sum())
        coverage.append({'district_id':row.district_id,'source_edges_intersecting':len(subset),'valid_source_length_m':total,
          'id_matched_length_fraction':float(lengths[subset.class_count.notna()].sum()/total) if total else None,
          'aligned_candidate_length_fraction':float(lengths[subset.class_match_status.eq('aligned_candidate')].sum()/total) if total else None,
          'scope':'source_edge_diagnostic_not_M1_or_M6; duplicate geometry and road-type inclusion not resolved'})
    dump(folder/'class_coverage_by_district.json',coverage)
    report={'source_streets':len(s)+street_invalid,'quarantined_streets':street_invalid,'valid_working_edges':len(s),
       'source_cet':len(t),'quarantined_cet':cet_invalid,'cet_unique_segment_ids':len(class_groups),
       'duplicate_geometry_excess_edges':int(s.geometry_hash.duplicated().sum()),
       'class_match_status':s.class_match_status.value_counts().to_dict(),
       'endpoint_candidates':len(ng),'accepted_junctions':0,
       'topology_gate':'grade separation, snapping, junction consolidation and carriageway policy unresolved',
       'cet_export_completeness':'unverified_75000_rows; local inventory cannot prove remote completeness',
       'bras':next(x for x in coverage if x['district_id']=='10')}
    dump(folder/'qa.json',report)
    return report


def checkpoint_valid(path, fingerprint):
    data=json.loads(path.read_text())
    return (data.get('fingerprint')==fingerprint and bool(data.get('outputs'))
        and all((OUT/p).is_file() and sha(OUT/p)==h for p,h in data['outputs'].items()))


def main():
    assert not CFG['attribute_construction_authorized']
    assert not set(CFG['removed_families']) & set(CFG['active_families'])
    log('Hashing and inventorying all SP source files')
    manifest=inventory()
    fingerprint=hashlib.sha256(json.dumps({'files':[(r['path'],r['sha256']) for r in manifest],
        'config':sha(CONFIG_PATH),'script':sha(__file__)},sort_keys=True).encode()).hexdigest()
    dump(OUT/'run_environment.json',{'config':CFG,'fingerprint':fingerprint,'python':platform.python_version(),
         'packages':{p:importlib.metadata.version(p) for p in ['geopandas','shapely','duckdb','pyogrio','pandas','pyarrow','pyproj']}})
    for name,fn in [('01_districts',districts),('02_parcels_tax',parcels_tax),('03_streets',streets)]:
        checkpoint=OUT/name/'checkpoint.json'
        if checkpoint.exists() and checkpoint_valid(checkpoint, fingerprint):
            log(f'{name}: checkpoint reusable');continue
        log(f'{name}: starting')
        try:
            report=fn()
            dump(checkpoint,{'fingerprint':fingerprint,'execution_status':'completed_with_reported_semantic_gates','completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()), 'outputs':{str(p.relative_to(OUT)):sha(p) for p in sorted((OUT/name).rglob('*')) if p.is_file() and p.name!='checkpoint.json'}})
            log(f'{name}: completed')
        except Exception:
            dump(OUT/'failure.json',{'stage':name,'traceback':traceback.format_exc()})
            raise
    changed=[]
    for row in manifest:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns']: changed.append(row['path'])
    assert not changed,changed
    dump(OUT/'run_status.json',{'fingerprint':fingerprint,'execution_status':'preparation_executed_with_open_validation_gates',
         'raw_size_mtime_unchanged':True,'features_constructed':False,'model_fitted':False,
         'stages_executed':['00_inventory','01_districts','02_parcels_tax','03_streets'],
         'not_executed':['04_blocks_buildings','05_population_activity_transit','06_features','07_feature_qa','08_similarity','09_grid_and_accessibility']})
    log('Preparation complete; attribute construction has not started')


if __name__=='__main__':
    main()

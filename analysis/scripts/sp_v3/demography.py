from . import common as C
import geopandas as gpd,numpy as np,pandas as pd,shapely,gc

def demography():
 out=C.OUT/'N07';d=C.districts();g=C.read(C.RAW/'Socioeconomico/densidade_demografica.gpkg')
 g['sector_id']=g.cd_setor_censitario_densidade.astype(str);g['source_valid']=g.is_valid;g.geometry=[C.polygon_only(shapely.make_valid(x)) if not x.is_valid else x for x in g.geometry]
 assert g.sector_id.is_unique and g.qt_populacao.notna().all() and g.qt_populacao.ge(0).all()
 li,ri=d.sindex.query(g.geometry,predicate='intersects');area=shapely.area(shapely.intersection(g.geometry.values[li],d.geometry.values[ri]));positive=area>0;li=li[positive];ri=ri[positive];area=area[positive]
 alloc=pd.DataFrame({'sector_id':g.sector_id.values[li],'district_id':d.district_id.values[ri],'intersection_area_m2':area,'source_sector_area_m2':g.area.values[li],'population_source':g.qt_populacao.values[li]})
 alloc['allocation_weight']=alloc.intersection_area_m2/alloc.source_sector_area_m2;alloc['population_allocated']=alloc.population_source*alloc.allocation_weight;alloc['method']='whole_sector_area_weighting_with_explicit_outside_residual'
 alloc.to_parquet(out/'census_district_allocation.parquet',index=False);C.write(g,out/'census_sectors.parquet')
 source_population=float(g.qt_populacao.sum());allocated=float(alloc.population_allocated.sum());assert allocated<=source_population+.01
 source_sectors=len(g);repairs=int((~g.source_valid).sum());del g,alloc;gc.collect()
 C.log('N07 census allocated; preparing postal address evidence')
 c=C.con();c.sql("SELECT COD_UNICO_ENDERECO address_id,CEP cep_raw,lpad(regexp_replace(CEP,'[^0-9]','','g'),8,'0') cep,COD_ESPECIE species,NV_GEO_COORD geolevel,try_cast(LATITUDE as double) lat,try_cast(LONGITUDE as double) lon FROM read_csv(?,delim=';',header=true,all_varchar=true)",params=[str(C.RAW/'Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv')]).create_view('addresses')
 C.copy(c,'SELECT * FROM addresses',out/'address_reference.parquet');c.read_parquet(str(out/'address_reference.parquet')).create_view('a')
 query="""SELECT address_id,min(cep) cep,min(lat) lat,min(lon) lon,count(distinct cep) cep_variants,count(distinct (lat,lon)) coordinate_variants
  FROM a WHERE species IN ('3','4','5','6','8') AND geolevel IN ('1','2') AND lat BETWEEN -24.2 AND -23.1 AND lon BETWEEN -47.3 AND -45.6
  AND regexp_full_match(cep,'[0-9]{8}') AND cep!='00000000' GROUP BY address_id"""
 ca=c.execute(query).fetchdf();ca=ca.loc[ca.cep_variants.eq(1)&ca.coordinate_variants.eq(1)].reset_index(drop=True)
 ag=gpd.GeoDataFrame(ca,geometry=gpd.points_from_xy(ca.lon,ca.lat),crs=4326).to_crs(C.CFG['metric_crs']);ag['district_id']=C.point_assign(ag,d);C.write(ag,out/'establishment_address_evidence.parquet');qualified=len(ag);del ca,ag;gc.collect()
 c.read_parquet(str(out/'establishment_address_evidence.parquet')).create_view('ap')
 C.copy(c,'SELECT cep,district_id,count(*) evidence_addresses FROM ap WHERE district_id IS NOT NULL GROUP BY ALL',out/'cep_cnefe_candidates.parquet')
 c.read_parquet(str(C.OUT/'N03/fiscal_records.parquet')).create_view('f')
 C.copy(c,"SELECT cep,district_id,count(*) evidence_tax_accounts FROM f WHERE location_candidate AND category NOT IN ('residential','vacant') AND regexp_full_match(cep,'[0-9]{8}') AND cep!='00000000' GROUP BY ALL",out/'cep_tax_candidates.parquet')
 c.read_parquet(str(out/'cep_cnefe_candidates.parquet')).create_view('cn');c.read_parquet(str(out/'cep_tax_candidates.parquet')).create_view('tx')
 c.execute('CREATE TABLE cs AS SELECT cep,count(*) district_count,min(district_id) district_id,sum(evidence_addresses) evidence_count FROM cn GROUP BY cep')
 c.execute('CREATE TABLE ts AS SELECT cep,count(*) district_count,min(district_id) district_id,sum(evidence_tax_accounts) evidence_count FROM tx GROUP BY cep')
 c.read_csv(str(C.RAW/'Socioeconomico/rais_empregos_sp_2022.csv'),all_varchar=True).create_view('jobs')
 C.copy(c,"""SELECT j.cep,cast(j.empregos as bigint) formal_jobs,coalesce(cs.district_count,0) cnefe_districts,coalesce(ts.district_count,0) tax_districts,
  cs.district_id cnefe_district_id,ts.district_id tax_district_id,cs.evidence_count establishment_address_count,
  CASE WHEN cs.district_count=1 AND (ts.district_count IS NULL OR (ts.district_count=1 AND ts.district_id=cs.district_id)) THEN cs.district_id END allocated_district_id,
  CASE WHEN cs.district_count=1 AND ts.district_count=1 AND cs.district_id=ts.district_id THEN 'single_district_corroborated'
       WHEN cs.district_count=1 AND ts.district_count IS NULL THEN 'single_district_cnefe_only'
       WHEN cs.district_count>1 OR ts.district_count>1 THEN 'multi_district_review'
       WHEN cs.district_count=1 AND ts.district_count=1 THEN 'cross_source_conflict'
       WHEN cs.district_count IS NULL AND ts.district_count=1 THEN 'tax_only_candidate'
       ELSE 'unmatched' END allocation_status,
  'observed_postal_evidence_proxy_not_authoritative_CEP_polygon' allocation_basis,
  right(j.cep,3)='000' generic_suffix_review_flag
  FROM jobs j LEFT JOIN cs USING(cep) LEFT JOIN ts USING(cep)""",out/'formal_job_allocation.parquet')
 c.read_parquet(str(out/'formal_job_allocation.parquet')).create_view('j')
 C.copy(c,"SELECT * FROM j WHERE allocated_district_id IS NULL ORDER BY formal_jobs DESC",out/'unresolved_job_ceps.parquet')
 C.copy(c,"SELECT * FROM j ORDER BY formal_jobs DESC LIMIT 100",out/'large_employer_cep_review.parquet')
 jq=C.records(c,"select count(*) cep_rows,count(distinct cep) unique_ceps,sum(formal_jobs) total_jobs,sum(formal_jobs) filter(where allocated_district_id is not null) allocated_jobs,sum(formal_jobs) filter(where allocated_district_id is null) unresolved_jobs from j")[0]
 assert jq['cep_rows']==jq['unique_ceps']==29594 and jq['total_jobs']==5387474;assert jq['allocated_jobs']+jq['unresolved_jobs']==jq['total_jobs']
 jq['allocated_fraction']=jq['allocated_jobs']/jq['total_jobs'];jq['status_counts']=C.records(c,'select allocation_status,count(*) ceps,sum(formal_jobs) jobs from j group by 1 order by 1')
 C.dump(out/'qa.json',{'population':{'source_sectors':source_sectors,'repaired_geometries':repairs,'source_population':source_population,'allocated_population':allocated,'outside_residual_population':source_population-allocated,'allocated_fraction':allocated/source_population,'method':'area-weighted proxy; vulnerability layer not appended'},'precise_establishment_addresses':qualified,'employment':jq,'upstream_rais_coverage':'saved_csv_only; null-CEP exclusions before export not independently reconciled','job_geography':'unique observed CNEFE postal district, corroborated where tax evidence exists; ambiguous and tax-only mass withheld; no residential weighting','attributes_constructed':False});c.close()

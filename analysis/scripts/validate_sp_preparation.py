"""Independent full-table preparation checks; writes no model attributes."""
from pathlib import Path
import hashlib
import json
import sqlite3
import duckdb
import geopandas as gpd
import numpy as np
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/processed/SP/sp_prep_2026_09_09_v2'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 checks={}
 def check(name,condition):
  checks[name]=bool(condition)
  if not condition: raise AssertionError(name)
 cfg=json.loads((ROOT/'analysis/config/sp_preparation_v2.json').read_text())
 check('13_active_families',len(cfg['active_families'])==13)
 check('M5_U5_absent',not {'M5','U5'} & set(cfg['active_families']))
 check('features_unauthorized',cfg['attribute_construction_authorized'] is False)
 d=gpd.read_parquet(OUT/'01_districts/districts.parquet')
 check('96_unique_districts',len(d)==d.district_id.nunique()==96)
 check('one_bras',d.district_id.eq('10').sum()==1)
 check('valid_districts',d.is_valid.all() and not d.is_empty.any())
 check('metric_crs',d.crs.to_epsg()==31983)
 check('land_area_not_fabricated',d.land_area_m2.isna().all())
 conn=sqlite3.connect(f'file:{OUT}/01_districts/districts.gpkg?mode=ro',uri=True)
 check('district_gpkg_integrity',conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok');conn.close()
 c=duckdb.connect(config={'memory_limit':'768MB','threads':2,'temp_directory':str(OUT/'validation_temp')})
 folder=OUT/'02_parcels_tax'
 for name,path in [('p',folder/'parcel_records/*.parquet'),('candidates',folder/'parcel_candidates.parquet'),('tax',folder/'tax_accounts.parquet'),('w',folder/'tax_parcel_crosswalk.parquet'),('status',folder/'parcel_identity_status.parquet')]:
  c.read_parquet(str(path)).create_view(name)
 scalar=lambda q:c.execute(q).fetchone()[0]
 check('all_96_parcel_partitions',len(list((folder/'parcel_records').glob('*.parquet')))==96)
 check('parcel_source_ids_unique',scalar('select count(*)=count(distinct source_record_id) from p'))
 check('candidate_ids_unique',scalar('select count(*)=count(distinct parcel_candidate_id) from candidates'))
 check('candidate_lineage_count_conserved',scalar('select sum(source_record_count) from candidates')==scalar('select count(*) from p'))
 check('every_parcel_has_candidate',scalar('select count(*) from p left join candidates using(parcel_candidate_id) where candidates.parcel_candidate_id is null')==0)
 check('tax_accounts_unique',scalar('select count(*)=count(distinct taxpayer_id) from tax'))
 check('one_crosswalk_row_per_account',scalar('select count(*)=count(distinct taxpayer_id) from w') and scalar('select count(*) from w')==scalar('select count(*) from tax'))
 check('no_unvalidated_area_accepted',scalar('select count(*) from w where accepted_for_area_aggregation')==0)
 check('ambiguous_matches_not_assigned',scalar("select count(*) from w where match_method in ('ambiguous_exact_sql','ambiguous_condominium','invalid_taxpayer_format','unmatched') and parcel_candidate_id is not null")==0)
 check('crosswalk_candidate_references_valid',scalar('select count(*) from w left join candidates using(parcel_candidate_id) where w.parcel_candidate_id is not null and candidates.parcel_candidate_id is null')==0)
 mass=scalar('select sum(constructed_area_m2) from tax')
 join_mass=scalar('select sum(constructed_area_m2) from tax join w using(taxpayer_id)')
 check('tax_mass_conserved_by_join',abs(mass-join_mass)<.01)
 check('valid_sql_format',scalar("select count(*) from p where not regexp_full_match(sql_key,'[0-9]{10}') or sql_key is null")==0)
 summaries={
  'parcel_rows':scalar('select count(*) from p'),
  'candidate_rows':scalar('select count(*) from candidates'),
  'tax_rows':scalar('select count(*) from tax'),
  'tax_raw_constructed_area_m2':mass,
  'tax_years':c.execute('select tax_year,count(*) records from tax group by 1').fetchdf().to_dict('records'),
  'tax_launches':c.execute('select "NUMERO DA NL" launch,count(*) records from tax group by 1').fetchdf().to_dict('records'),
  'tax_phases':c.execute('select "FASE DO CONTRIBUINTE" phase,count(*) records from tax group by 1').fetchdf().to_dict('records'),
  'zero_floors_retained':scalar('select count(*) from tax where floors=0'),
  'exact_condo_disagreement_accounts':scalar('select count(*) from w where exact_condo_disagreement'),
  'parcel_assignment':c.execute('select assigned_district_id,count(*) records from p group by 1 order by 1').fetchdf().to_dict('records'),
  'source_district_disagreement_rows':scalar('select count(*) from p where source_district_id!=assigned_district_id'),
  'unassigned_parcel_rows':scalar('select count(*) from p where assigned_district_id is null'),
  'identity_status':c.execute('select identity_status,count(*) candidates from status group by 1').fetchdf().to_dict('records')}
 s=gpd.read_parquet(OUT/'03_streets/edge_candidates.parquet')
 check('working_edge_ids_unique',s.edge_id.is_unique)
 check('working_geometry_valid',s.is_valid.all() and not s.is_empty.any())
 check('working_lengths_finite_positive',np.isfinite(s.length_m).all() and s.length_m.gt(0).all())
 check('no_class_accepted_prematurely',not s.class_accepted_for_model.any())
 ep=pq.read_table(OUT/'03_streets/edge_endpoints.parquet').to_pandas()
 check('two_endpoints_per_edge',len(ep)==2*len(s) and ep.groupby('edge_id').size().eq(2).all())
 source_count=pq.ParquetFile(OUT/'03_streets/streets_source.parquet').metadata.num_rows
 rejected=pq.ParquetFile(OUT/'03_streets/streets_quarantine.parquet').metadata.num_rows
 check('street_count_conserved',s.source_fid.nunique()+rejected==source_count)
 coverage=json.loads((OUT/'03_streets/class_coverage_by_district.json').read_text())
 check('96_district_join_diagnostics',len(coverage)==96)
 check('aligned_coverage_subset',all(0<=r['aligned_candidate_length_fraction']<=r['id_matched_length_fraction']<=1 for r in coverage))
 manifest=json.loads((OUT/'source_manifest.json').read_text())
 check('all_raw_content_hashes_unchanged',all(sha(ROOT/r['path'])==r['sha256'] for r in manifest))
 env=json.loads((OUT/'run_environment.json').read_text())
 for stage in ['01_districts','02_parcels_tax','03_streets']:
  checkpoint=json.loads((OUT/stage/'checkpoint.json').read_text())
  check(stage+'_fingerprint',checkpoint['fingerprint']==env['fingerprint'])
  check(stage+'_output_hashes',all(sha(OUT/p)==h for p,h in checkpoint['outputs'].items()))
 result={'checks':checks,'checks_passed':len(checks),'summary':summaries,
   'interpretation':'Technical invariants passed; semantic, topology, boundary and coverage gates remain open. No model features computed.'}
 (OUT/'validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
 print(json.dumps({'checks_passed':len(checks),'parcel_rows':summaries['parcel_rows'],'tax_rows':summaries['tax_rows']},indent=2))

if __name__=='__main__':main()

from . import common as C
import pandas as pd,openpyxl,json

# Explicit reviewed label dictionary; mixed/account ancillary uses are not guessed into residential.
def use_category(s):
 if s=='Terreno':return 'vacant'
 if 'Garagem' in s and 'uso exclusivamente residencial' in s:return 'residential'
 if 'Garagem' in s and 'escritórios, consultórios ou misto' in s:return 'commerce/services'
 if 'Garagem' in s or s=='Posto de serviço':return 'transport/utilities'
 if s=='Depósito Condomínio Residencial':return 'residential'
 if s in ['Indústria','Armazéns gerais e depósitos']:return 'industry/warehouse'
 if s in ['Escola','Templo','Hospital, ambulatório, casa de saúde e assemelhados','Asilo, orfanato, creche, seminário ou convento']:return 'institutional'
 if s in ['Não residencial','Outras edificações de uso especial, com utilização múltipla','Outras edificações de uso coletivo, com utilização múltipla'] or ' e residência ' in s or 'e outro uso' in s or 'uso misto' in s:return 'mixed/other'
 if s.startswith(('Residência','Apartamento','Cortiço','Flat residencial')) or 'uso exclusivamente residencial' in s:return 'residential'
 if s.startswith(('Loja','Escritório','Prédio de escritório','Flat de uso comercial','Hotel','Oficina','Cinema','Clube','Estação radioemissora','Outras edificações de uso comercial','Outras edificações de uso de serviço')):return 'commerce/services'
 raise ValueError('Unmapped source use: '+s)

def fiscal():
 out=C.OUT/'N03';base=C.BASE/'02_parcels_tax';c=C.con();c.execute("SET memory_limit='768MB'");c.execute('SET threads=1')
 for name,file in [('tax','tax_accounts.parquet'),('links','tax_parcel_crosswalk.parquet'),('identity','parcel_identity_status.parquet')]:c.read_parquet(str(base/file)).create_view(name)
 c.read_parquet(str(base/'parcel_lineage.parquet')).create_view('lineage')
 w=openpyxl.load_workbook(C.RAW/'Cadastro e Vias/Dicionario_dados_IPTU.xlsx',read_only=True,data_only=True)
 C.dump(out/'iptu_dictionary.json',[{'field':a,'definition':b} for a,b in w.active.values if a])
 uses=c.execute('select use_raw,count(*) n from tax group by 1 order by 1').fetchdf();uses['category']=uses.use_raw.map(use_category);uses['mapping_basis']='explicit_description_mapping_v3';uses.to_csv(out/'use_mapping.csv',index=False);c.register('use_map',uses)
 c.execute("CREATE TABLE entity_keys AS SELECT parcel_candidate_id,case when lo_condomi!='00' then 'condo:'||condo_key else 'sql:'||sql_key end entity_key,lo_condomi,lo_tp_lote,lo_tp_quad FROM lineage")
 assert c.execute('select count(*)=count(distinct parcel_candidate_id) from entity_keys').fetchone()[0]
 c.execute('CREATE TABLE entity_counts AS SELECT entity_key,count(*) geometry_count FROM entity_keys GROUP BY entity_key')
 C.copy(c,"""SELECT i.*,k.entity_key,k.lo_condomi,k.lo_tp_lote,k.lo_tp_quad,e.geometry_count,
   case when e.geometry_count>1 then 'unresolved_entity_multiple_geometries'
   when exists(select 1 from identity j where j.geometry_hash=i.geometry_hash and j.sql_key!=i.sql_key) then 'coincident_distinct_sql_review'
   else 'unique_geometry_candidate' end geometry_status,
   'registered_cadastral_entity_proxy; source type codes retained' parcel_scope
   FROM identity i JOIN entity_keys k USING(parcel_candidate_id) JOIN entity_counts e USING(entity_key)""",out/'parcel_identity.parquet')
 c.read_parquet(str(out/'parcel_identity.parquet')).create_view('pi')
 # Each taxpayer kept once; conditions separate location, fiscal semantics and potential aggregation.
 C.copy(c,"""SELECT t.taxpayer_id,t.sql_key,t.condo_key,t.tax_year,t."FASE DO CONTRIBUINTE" phase,t."NUMERO DA NL" launch,
       t."CEP DO IMOVEL" cep_raw,lpad(regexp_replace(t."CEP DO IMOVEL",'[^0-9]','','g'),8,'0') cep,
       t.constructed_area_m2,t.land_area_m2,t.occupied_area_m2,t.ideal_fraction,t.floors,t.use_raw,u.category,
       l.parcel_candidate_id,p.district_id,l.match_method,l.exact_condo_disagreement,p.geometry_status,
       (l.parcel_candidate_id is not null and not l.exact_condo_disagreement and p.geometry_status='unique_geometry_candidate') location_candidate,
       (l.parcel_candidate_id is not null and not l.exact_condo_disagreement and p.geometry_status='unique_geometry_candidate') accepted_area_aggregation,
       'declared_unique_unit_constructed_area_proxy_no_fraction_reapplication' area_rule
       FROM tax t JOIN links l USING(taxpayer_id) LEFT JOIN pi p USING(parcel_candidate_id) JOIN use_map u USING(use_raw)""",out/'fiscal_records.parquet')
 c.read_parquet(str(out/'fiscal_records.parquet')).create_view('f')
 C.copy(c,"SELECT * FROM f WHERE NOT coalesce(location_candidate,false) OR exact_condo_disagreement",out/'location_exceptions.parquet')
 C.copy(c,"""SELECT parcel_candidate_id,min(district_id) district_id,count(*) tax_accounts,
   count(distinct floors) FILTER(WHERE floors>0 AND use_raw NOT LIKE 'Garagem (unidade autônoma)%' AND use_raw!='Depósito Condomínio Residencial') distinct_positive_floor_reports,
   CASE WHEN count(distinct floors) FILTER(WHERE floors>0 AND use_raw NOT LIKE 'Garagem (unidade autônoma)%' AND use_raw!='Depósito Condomínio Residencial')=1 THEN min(floors) FILTER(WHERE floors>0 AND use_raw NOT LIKE 'Garagem (unidade autônoma)%' AND use_raw!='Depósito Condomínio Residencial') END floor_count_candidate,
   count(*) FILTER(WHERE floors<=0 OR floors IS NULL) zero_or_unknown_reports,
   sum(constructed_area_m2) unit_sum_constructed_area_candidate_m2,
   min(land_area_m2) min_reported_land_m2,max(land_area_m2) max_reported_land_m2,
   sum(ideal_fraction) fraction_sum_diagnostic,
   count(distinct category) distinct_uses,
   case when count(distinct category)=1 then min(category) else 'mixed/other' end parcel_use_candidate,
   (count(distinct floors) FILTER(WHERE floors>0 AND use_raw NOT LIKE 'Garagem (unidade autônoma)%' AND use_raw!='Depósito Condomínio Residencial')=1) floor_proxy_eligible,true declared_unit_area_proxy_eligible
   FROM f WHERE location_candidate GROUP BY parcel_candidate_id""",out/'parcel_fiscal_profiles.parquet')
 C.copy(c,"SELECT district_id,geometry_status,count(*) candidates FROM pi GROUP BY ALL",out/'identity_coverage.parquet')
 C.copy(c,"SELECT district_id,location_candidate,count(*) accounts,sum(constructed_area_m2) raw_area_mass_m2 FROM f GROUP BY ALL",out/'fiscal_location_coverage.parquet')
 C.copy(c,"SELECT * FROM f WHERE exact_condo_disagreement",out/'competing_keys.parquet')
 # Brás review queue preserves actual rows for falsifiable case reconciliation.
 C.copy(c,"SELECT * FROM f WHERE district_id='10' AND (match_method='condominium_candidate' OR exact_condo_disagreement) ORDER BY constructed_area_m2 DESC LIMIT 200",out/'bras_condominium_review.parquet')
 q=C.records(c,"select count(*) records,count(distinct taxpayer_id) unique_accounts,sum(constructed_area_m2) raw_area_m2,count(*) filter(where exact_condo_disagreement) competing_keys,count(*) filter(where location_candidate) location_candidates,sum(constructed_area_m2) filter(where location_candidate) candidate_area_m2 from f")[0]
 assert q['records']==q['unique_accounts']==3920972;assert abs(q['raw_area_m2']-597424198)<.01
 q['raw_area_candidate_coverage']=q['candidate_area_m2']/q['raw_area_m2'];q['mapping_labels']=len(uses)
 q['floor_profiles']=C.records(c,"select distinct_positive_floor_reports,count(*) parcels from read_parquet('"+str(out/'parcel_fiscal_profiles.parquet')+"') group by 1 order by 1")
 q['execution_resources']={'duckdb_memory_limit':'768MB','threads':1,'reason':'512MB triple-join allocation failed; bounded stage override'}
 q['entity_resolution']=C.records(c,"select lo_condomi!='00' condominium,count(*) geometries,count(distinct entity_key) entity_keys,count(*) filter(where geometry_status='unique_geometry_candidate') single_geometry_candidates from pi group by 1")
 q['acceptance']='declared cadastral proxies: condo entities keyed by sector-block-condo, noncondos by SQL; competing/multiple geometry cases excluded. Unit-area sum is the user-selected fiscal proxy, not independent common-area verification. B2 excludes ancillary autonomous garage/storage reports and retains floor conflicts.'
 q['district_assignment']='inherited v2 largest-overlap assignment; N02 changes only documented 22 square metre boundary overlap allocation'
 C.dump(out/'qa.json',q);c.close()

"""Read-only September 9 readiness audit; aggregate evidence, no model fitting."""
from pathlib import Path
import json
import re
import sys
import duckdb
import geopandas as gpd
import pandas as pd
import pyogrio

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'analysis/data/SP'
OUT = ROOT/'analysis/outputs/sp_readiness_2026_09_09'
OUT.mkdir(parents=True, exist_ok=True)


def main():
    report = {}
    if '--reuse-parcels' in sys.argv:
        report=json.loads((OUT/'parcel_audit.json').read_text())
        p=pd.read_parquet(OUT/'parcel_keys.parquet')
    else:
        parcels = []
        inventory = []
        for path in sorted((DATA/'Cadastro e Vias/Lotes').glob('*.gpkg')):
            g = pyogrio.read_dataframe(path)
            district = re.search(r'LOTES_(\d+)_',path.name)[1]
            key = g.lo_setor.str.zfill(3)+g.lo_quadra.str.zfill(3)+g.lo_lote.str.zfill(4)
            condo = g.lo_setor.str.zfill(3)+g.lo_quadra.str.zfill(3)+g.lo_condomi.str.zfill(2)
            inventory.append({'file':path.name,'district':district,'rows':len(g),
                'crs':str(g.crs),'invalid':int((~g.is_valid).sum()),'empty':int(g.is_empty.sum()),
                'null_geometry':int(g.geometry.isna().sum()),'unique_sql':int(key.nunique()),
                'condominium_codes':g.lo_condomi.value_counts().head(5).to_dict()})
            parcels.append(pd.DataFrame({'sql_key':key,'condo':condo,'district':district,'lo_condomi':g.lo_condomi}))
        p=pd.concat(parcels,ignore_index=True)
        report['parcel_files']=inventory
        report['parcels']={'files':len(inventory),'rows':len(p),'unique_sql':p.sql_key.nunique(),
            'missing_file_codes':sorted(set(f'{i:02}' for i in range(1,97))-set(p.district)),
            'duplicate_sql_rows':int(p.sql_key.duplicated().sum()),'invalid':sum(x['invalid'] for x in inventory)}
        print('Parcels:',report['parcels'],flush=True)
        (OUT/'parcel_audit.json').write_text(json.dumps(report,default=int))
        p.to_parquet(OUT/'parcel_keys.parquet',index=False)
    con=duckdb.connect(config={'memory_limit':'2GB','threads':4,'temp_directory':str(OUT/'temp')})
    con.register('parcels',p)
    iptu=DATA/'Cadastro e Vias/IPTU_2026.csv'
    con.execute('''CREATE TABLE iptu AS SELECT
        "NUMERO DO CONTRIBUINTE" taxpayer,
        substr(regexp_replace("NUMERO DO CONTRIBUINTE",'[^0-9]','','g'),1,10) sql_key,
        substr(regexp_replace("NUMERO DO CONTRIBUINTE",'[^0-9]','','g'),1,6) || substr("NUMERO DO CONDOMINIO",1,2) condo,
        "NUMERO DO CONDOMINIO" condominium,"ANO DO EXERCICIO" AS tax_year,"NUMERO DA NL" nl,
        try_cast("QUANTIDADE DE PAVIMENTOS" AS DOUBLE) floors,
        try_cast("AREA CONSTRUIDA" AS DOUBLE) floor_area,
        try_cast("AREA DO TERRENO" AS DOUBLE) land_area,
        try_cast("AREA OCUPADA" AS DOUBLE) occupied_area,
        try_cast("FRACAO IDEAL" AS DOUBLE) fraction,
        "TIPO DE USO DO IMOVEL" use_type
        FROM read_csv(?,delim=';',header=true,all_varchar=true,strict_mode=true)''',[str(iptu)])
    def record(q):return json.loads(con.execute(q).fetchdf().to_json(orient='records'))
    report['iptu']=record('''SELECT count(*) AS n_rows,count(distinct taxpayer) unique_taxpayers,
        count(distinct sql_key) unique_sql,count(*) FILTER(WHERE floors>0) positive_floors,
        count(*) FILTER(WHERE floors=0) zero_floors,count(*) FILTER(WHERE floors IS NULL) null_floors,
        max(floors) max_floors,count(*) FILTER(WHERE floor_area>0) positive_floor_area,
        count(*) FILTER(WHERE floor_area=0) zero_floor_area,count(*) FILTER(WHERE floor_area IS NULL) null_floor_area,
        count(*) FILTER(WHERE land_area<=0 OR land_area IS NULL) invalid_land_area,
        count(distinct use_type) use_categories,count(*) FILTER(WHERE use_type IS NULL) missing_use,
        count(*) FILTER(WHERE condominium != '00-0') condominium_rows FROM iptu''')[0]
    report['iptu_years']=record('SELECT tax_year,count(*) AS n_rows FROM iptu GROUP BY tax_year')
    report['iptu_nl']=record('SELECT nl,count(*) AS n_rows FROM iptu GROUP BY nl ORDER BY n_rows DESC')
    report['iptu_use_categories']=record('SELECT use_type,count(*) AS n_rows FROM iptu GROUP BY use_type ORDER BY n_rows DESC')
    report['join_direct']=record('''SELECT count(*) AS n_rows,
        count(*) FILTER(WHERE EXISTS(SELECT 1 FROM iptu i WHERE i.sql_key=p.sql_key)) AS match_count
        FROM parcels p''')[0]
    report['join_direct_bras']=record('''SELECT count(*) AS n_rows,
        count(*) FILTER(WHERE EXISTS(SELECT 1 FROM iptu i WHERE i.sql_key=p.sql_key)) AS match_count
        FROM parcels p WHERE district='10' ''')[0]
    report['iptu_to_parcel']=record('''SELECT count(*) AS n_rows,
        count(*) FILTER(WHERE EXISTS(SELECT 1 FROM parcels p WHERE p.sql_key=i.sql_key)) AS match_count
        FROM iptu i''')[0]
    report['condo_candidate']=record('''SELECT count(*) AS n_rows,
        count(*) FILTER(WHERE EXISTS(SELECT 1 FROM parcels p WHERE p.condo=i.condo AND p.lo_condomi!='00')) AS match_count
        FROM iptu i WHERE condominium!='00-0' ''')[0]
    print('IPTU:',report['iptu'],'joins',report['join_direct'],report['join_direct_bras'],flush=True)
    cnefe=DATA/'Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv'
    con.execute('''CREATE TABLE cnefe AS SELECT COD_UNICO_ENDERECO id,COD_MUNICIPIO municipality,
        COD_DISTRITO district,COD_SETOR sector,COD_ESPECIE species,NV_GEO_COORD geolevel,
        COD_INDICADOR_ESTAB_ENDERECO establishment_indicator,
        try_cast(LATITUDE AS DOUBLE) lat,try_cast(LONGITUDE AS DOUBLE) lon
        FROM read_csv(?,delim=';',header=true,all_varchar=true,strict_mode=true)''',[str(cnefe)])
    report['cnefe']=record('''SELECT count(*) AS n_rows,count(distinct id) unique_ids,
        count(distinct district) districts,count(distinct sector) sectors,
        count(*) FILTER(WHERE lat IS NULL OR lon IS NULL) missing_coordinates,
        count(*) FILTER(WHERE NOT (lat BETWEEN -24.1 AND -23.1 AND lon BETWEEN -47.3 AND -45.6)) outside_broad_extent,
        min(lat) min_lat,max(lat) max_lat,min(lon) min_lon,max(lon) max_lon FROM cnefe''')[0]
    for field in ['species','geolevel','municipality','establishment_indicator']:
        report['cnefe_'+field]=record(f'SELECT {field},count(*) AS n_rows FROM cnefe GROUP BY {field} ORDER BY n_rows DESC')
    print('CNEFE:',report['cnefe'],flush=True)
    streets=pyogrio.read_dataframe(DATA/'Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg')
    classes=pyogrio.read_dataframe(DATA/'Cadastro e Vias/geoportal_classificacao_viaria_cet.gpkg')
    ids=set(classes.cd_identificador_segmento_logradouro.dropna())
    matched=streets.lg_seg_id.isin(ids)
    bras=pyogrio.read_dataframe(DATA/'Cadastro e Vias/distrito_municipal_v2.gpkg',where="nm_distrito_municipal='BRAS'").geometry.iloc[0]
    b=streets.loc[streets.intersects(bras)]
    lengths=b.geometry.intersection(bras).length
    report['streets']={'rows':len(streets),'crs':str(streets.crs),'types':streets.geom_type.value_counts().to_dict(),
        'invalid':int((~streets.is_valid).sum()),'empty':int(streets.is_empty.sum()),
        'unique_segment_ids':int(streets.lg_seg_id.nunique()),'zero_length':int(streets.length.eq(0).sum()),
        'road_type_counts':streets.lg_tipo.value_counts().to_dict(),
        'class_matched_rows':int(matched.sum()),'class_matched_length_share':float(streets.loc[matched].length.sum()/streets.length.sum()),
        'bras_rows':len(b),'bras_class_matched_rows':int(b.lg_seg_id.isin(ids).sum()),
        'bras_class_matched_length_share':float(lengths[b.lg_seg_id.isin(ids)].sum()/lengths.sum())}
    report['road_classes']={'rows':len(classes),'unique_segment_ids':int(classes.cd_identificador_segmento_logradouro.nunique()),
        'invalid':int((~classes.is_valid).sum()),'class_counts':classes.dc_tipo_classificacao_viaria.value_counts(dropna=False).to_dict(),
        'id_min':int(classes.cd_identificador.min()),'id_max':int(classes.cd_identificador.max()),
        'conflicting_segment_classes':int((classes.groupby('cd_identificador_segmento_logradouro').dc_tipo_classificacao_viaria.nunique()>1).sum())}
    identities={
        'address_groups':record('''SELECT count(*) AS duplicate_id_groups, sum(n-1) AS excess_rows,
          sum(species_n>1) AS multi_species_groups,sum(coord_n>1) AS different_coordinate_groups,
          sum(district_n>1) AS different_district_groups FROM
          (SELECT id,count(*) n,count(distinct species) species_n,count(distinct (lat,lon)) coord_n,
           count(distinct district) district_n FROM cnefe GROUP BY id HAVING count(*)>1)'''),
        'eligible_activity':record("SELECT count(*) n_rows,count(distinct id) unique_ids FROM cnefe WHERE species IN ('3','4','5','6','8')"),
        'parcel_identity':{'unique_sql_condo':len(p[['sql_key','lo_condomi']].drop_duplicates()),'raw_rows':len(p)},
        'condo_geometry_candidates':record("SELECT count(*) AS n_groups,sum(n>1) groups_multiple_sql FROM (SELECT condo,count(distinct sql_key) n FROM parcels WHERE lo_condomi!='00' GROUP BY condo)"),
        'sql_cross_district':record('SELECT count(*) AS n_groups FROM (SELECT sql_key FROM parcels GROUP BY sql_key HAVING count(distinct district)>1)')}
    (OUT/'identity_checks.json').write_text(json.dumps(identities,indent=2))
    print('Identity checks:',identities,flush=True)
    print('Streets:',report['streets'],flush=True)
    (OUT/'readiness_evidence.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,default=int))
    print('Saved aggregate evidence:',OUT,flush=True)


if __name__=='__main__':main()

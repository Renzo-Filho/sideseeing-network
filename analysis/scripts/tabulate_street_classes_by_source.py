"""Tabulate street length by each source's own class, clipped to the city, with no imputation or filtering."""
from pathlib import Path
import geopandas as gpd
import pandas as pd
import shapely

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'analysis/data'
OUT=ROOT/'analysis/results/SP_CHI/street_class_inventory_2026_09_30'
SPV=D/'SP/Cadastro e Vias'
ELIGIBLE={'motorway','trunk','primary','secondary','tertiary','residential','living_street','pedestrian','unclassified','unknown'}

def city_length_km(g,mask):
    """Per-row length inside the city mask; rows entirely inside skip the costly intersection."""
    g=g.iloc[g.sindex.query(mask,predicate='intersects')].copy()
    shapely.prepare(mask)
    inside=shapely.contains(mask,g.geometry.values)
    g['km']=g.geometry.length/1000
    g.loc[~inside,'km']=shapely.length(shapely.intersection(g.geometry.values[~inside],mask))/1000
    return g[g.km>0]

def table(g,city,source,field,qualifier=None):
    g=g.copy()
    g['class_value']=g[field].fillna('(missing)').astype(str)
    g['qualifier']=g[qualifier].fillna('(missing)').astype(str) if qualifier else ''
    t=g.groupby(['class_value','qualifier']).km.agg(features='size',km='sum').reset_index()
    t.insert(0,'source',source);t.insert(0,'city',city)
    t['class_field']=field
    t['share_of_source']=t.km/t.km.sum()
    return t

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    chi_mask=gpd.read_file(D/'Chicago/Boundaries_-_Community_Areas_20260831.geojson').to_crs(26916).union_all()
    sp_mask=gpd.read_file(SPV/'distrito_municipal_v2.gpkg').to_crs(31983).union_all()
    # Chicago local: every record, CLASS x STATUS as published.
    g=gpd.read_file(D/'Chicago/steet_center_lines_20260915.geojson').to_crs(26916)
    rows.append(table(city_length_km(g,chi_mask),'Chicago','city_street_centerlines','class','status'))
    # SP local: classvias carries the class on its own geometry; CET is a partial export; logradouro has street type only.
    for f,lay,fld,src,crs in [('classvias.gpkg','classvias','Classifica','classvias',None),
                             ('geoportal_classificacao_viaria_cet.gpkg',None,'dc_tipo_classificacao_viaria','cet_export_75000_rows',None),
                             ('SIRGAS_GPKG_logradouronbl.gpkg',None,'lg_tipo','logradouro_street_type_no_class',None)]:
        g=gpd.read_file(SPV/f,layer=lay).to_crs(31983)
        rows.append(table(city_length_km(g,sp_mask),'Sao Paulo',src,fld))
    # Overture: raw class x subtype, all subtypes, flag whether the M1 eligible-class rule would keep it.
    for city,mask,crs in [('Chicago',chi_mask,26916),('Sao Paulo',sp_mask,31983)]:
        g=gpd.read_parquet(D/('Chicago' if city=='Chicago' else 'SP')/'overture_2026_08_19/segment/part_0000.parquet').to_crs(crs)
        t=table(city_length_km(g,mask),city,'overture_2026-08-19.0','class','subtype')
        t['m1_eligible']=t.qualifier.eq('road')&t.class_value.isin(ELIGIBLE)
        rows.append(t)
    t=pd.concat(rows,ignore_index=True)
    t.to_csv(OUT/'street_class_inventory.csv',index=False)
    b=t.groupby(['city','source','class_field','class_value']).agg(features=('features','sum'),km=('km','sum')).reset_index()
    b['share_of_source']=b.km/b.groupby(['city','source']).km.transform('sum')
    b.sort_values(['city','source','km'],ascending=[True,True,False]).to_csv(OUT/'street_class_by_class.csv',index=False)

if __name__=='__main__':main()

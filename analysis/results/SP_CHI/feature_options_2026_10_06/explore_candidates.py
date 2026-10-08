"""Exploratory proposals only; no acceptance gate or model fit."""
import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd,shapely,pyogrio
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'analysis/scripts'))
import evaluate_b1_step4 as b1
from evaluate_m1_m6_step6 import TEN,CHI_LOCAL_CLASSES
OUT=ROOT/'analysis/results/SP_CHI/feature_options_2026_10_06'
OUT.mkdir(parents=True,exist_ok=True)

def directions(lines,u,label):
    a,b=u.sindex.query(lines.geometry,predicate='intersects')
    pieces=shapely.intersection(lines.geometry.values[a],u.geometry.values[b])
    parts,ix=shapely.get_parts(pieces,return_index=True)
    keep=shapely.get_type_id(parts)==1
    parts=parts[keep];unit=u.unit_id.values[b[ix[keep]]]
    xy,pi=shapely.get_coordinates(parts,return_index=True)
    valid=(pi[1:]==pi[:-1])
    d=xy[1:]-xy[:-1];lens=np.hypot(d[:,0],d[:,1]); valid &= np.isfinite(lens)&(lens>0)
    d=d[valid];lens=lens[valid];ids=unit[pi[:-1][valid]]
    theta=np.arctan2(d[:,1],d[:,0])
    z=pd.DataFrame({'unit_id':ids,'length':lens,'x4':lens*np.cos(4*theta),'y4':lens*np.sin(4*theta),'x2':lens*np.cos(2*theta),'y2':lens*np.sin(2*theta)})
    g=z.groupby('unit_id').sum()
    return pd.DataFrame({label+'_r4':np.hypot(g.x4,g.y4)/g.length,label+'_r2':np.hypot(g.x2,g.y2)/g.length,label+'_km':g.length/1000})

rows=[]
for city,folder,crs in [('CHI','Chicago',26916),('SP','SP',31983)]:
    u=b1.land_units(city)
    ov=gpd.read_parquet(ROOT/f'analysis/data/{folder}/overture_2026_08_19/segment/part_0000.parquet',columns=['subtype','class','subclass','geometry']).to_crs(crs)
    ov=ov[ov.subtype.eq('road')&ov['class'].isin(TEN)].reset_index(drop=True)
    t=directions(ov,u,'overture')
    local=ov[~ov['class'].isin(['motorway','trunk'])&~ov.subclass.eq('link')]
    t=t.join(directions(local,u,'without_motorway_trunk_links'))
    if city=='CHI':
        muni=pyogrio.read_dataframe(ROOT/'analysis/data/Chicago/steet_center_lines_20260915.geojson',columns=['class','status']).to_crs(crs)
        muni=muni[muni.status.eq('N')&muni['class'].isin(CHI_LOCAL_CLASSES)]
    else:
        muni=pyogrio.read_dataframe(ROOT/'analysis/data/SP/Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg',columns=[]).to_crs(crs)
        xy,idx=shapely.get_coordinates(muni.geometry.values,return_index=True)
        for i in np.unique(idx[~np.isfinite(xy).all(axis=1)]):
            c=shapely.get_coordinates(muni.geometry.iloc[i]);muni.iloc[i,muni.columns.get_loc('geometry')]=shapely.LineString(c[np.isfinite(c).all(axis=1)])
    t=t.join(directions(muni,u,'municipal'));t['city']=city;rows.append(t)
    print(city,'done',flush=True)
d=pd.concat(rows);d.to_csv(OUT/'direction_coherence_exploratory.csv')
contract = OUT/'model_contract_snapshot.json'
config=json.loads(contract.read_text());parts=[]
for f in config['families']:
    p=ROOT/f['table'];a=pd.read_parquet(p) if p.suffix=='.parquet' else pd.read_csv(p)
    if 'unit_id' in a:a=a.set_index('unit_id')
    cols=f.get('columns',[f.get('column')]);cols=[c for c in cols if c in a]
    parts.append(a[cols])
x=pd.concat(parts,axis=1)
sp=pd.read_parquet(ROOT/'analysis/results/SP_CHI/u3_sp_catchup_2026_10_05/tables/u3_sp.parquet').set_index('unit_id')
x['u3_residents']=x.u3_acs_land_km2.combine_first(sp.u3_land_km2);x=x.drop(columns='u3_acs_land_km2')
a=pd.read_csv(ROOT/'analysis/results/SP_CHI/m3_m4_m7_step8_2026_10_06/m3_m4_m7_by_unit.csv').set_index('unit_id')
x['block_spread']=a.ov_m3_wiqr_ln
x['street_direction_coherence']=d.overture_r4
summary={}
corr=[]
for city in ['CHI','SP']:
    q=d[d.city.eq(city)];z=x[x.index.str.startswith(city+':')];aa=a[a.city.eq(city)]
    row={'n':len(q),'direction_overture_municipal_spearman':q.overture_r4.corr(q.municipal_r4,method='spearman'),'direction_source_abs_difference_median':(q.overture_r4-q.municipal_r4).abs().median(),'direction_source_abs_difference_max':(q.overture_r4-q.municipal_r4).abs().max(),'direction_source_rank_shift_max':(q.overture_r4.rank()-q.municipal_r4.rank()).abs().max(),'direction_road_scope_spearman':q.overture_r4.corr(q.without_motorway_trunk_links_r4,method='spearman'),'direction_p10_p50_p90':q.overture_r4.quantile([.1,.5,.9]).to_dict(),'direction_lowest':q.overture_r4.nsmallest(3).to_dict(),'direction_highest':q.overture_r4.nlargest(3).to_dict(),'block_spread_official_spearman':aa.ov_m3_wiqr_ln.corr(aa.official_m3_wiqr_ln,method='spearman'),'block_spread_municipal_spearman':aa.ov_m3_wiqr_ln.corr(aa.muni_m3_wiqr_ln,method='spearman')}
    for candidate in ['block_spread','street_direction_coherence']:
        r=z.corr(method='spearman')[candidate].drop([candidate]);r=r.drop(['block_spread','street_direction_coherence'],errors='ignore').dropna()
        row[candidate+'_top_overlaps']=r.reindex(r.abs().sort_values(ascending=False).index).head(6).to_dict()
        corr.extend({'city':city,'candidate':candidate,'existing_column':c,'spearman':v} for c,v in r.items())
    summary[city]=row
(OUT/'exploratory_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
pd.DataFrame(corr).to_csv(OUT/'candidate_existing_correlations.csv',index=False)
print(json.dumps(summary,indent=2))

"""Full Chicago footprint union, paired SP reuse and independent SP pilot checks."""
from pathlib import Path
import hashlib,json
import pandas as pd,numpy as np,geopandas as gpd,shapely,pyogrio
from harmonization.geometry import union_coverage,polygonal
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'analysis';OUT=A/'results/SP_CHI/harmonization_2026_09_22_h1_h3/footprints'

def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[];checks=[];receipts=[]
 for city,base,landpath in [('Chicago','Chicago/chi_local_2026_09_16_v1','Chicago/chi_functional_2026_09_16_v2/district_hydro_land.parquet'),('SP','SP/sp_prep_2026_09_10_v3/N02','SP/sp_prep_2026_09_10_v3/N02/district_land.parquet')]:
  dp=A/'work/prepared'/base/'districts.parquet';lp=A/'work/prepared'/landpath
  d=gpd.read_parquet(dp);land=gpd.read_parquet(lp)
  if city=='SP':
   d['unit_id']='SP:'+d.district_id.astype(str).str.zfill(2);land['unit_id']='SP:'+land.district_id.astype(str).str.zfill(2)
   bp=A/'data/SP/Edificacoes/sao_paulo_building_morphology.gpkg'
  else:
   bp=next((A/'data/Chicago/overture_2026_08_19/building').glob('*.parquet'))
   b=gpd.read_parquet(bp,columns=['id','geometry']).to_crs(d.crs)
   invalid=int((~b.is_valid).sum())
   if invalid:raise ValueError('Unexpected invalid building polygons')
  for p in [dp,lp,bp]:receipts.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()})
  for z in d.sort_values('unit_id').itertuples():
   geom=land.loc[land.unit_id.eq(z.unit_id)].geometry.item().intersection(z.geometry)
   if city=='SP':
    saved=A/'work/runs/sp_attributes_2026_09_11_v1/intermediates'/f'buildings_{z.district_id}.json'
    record=json.loads(saved.read_text());gross=record['union_gross_area_m2'];onland=record['union_land_area_m2'];summed=record['summed_individual_area_m2']
    receipts.append({'path':str(saved.relative_to(ROOT)),'sha256':hashlib.file_digest(saved.open('rb'),'sha256').hexdigest()})
    if str(z.district_id) in ['10','30','35']:
     b=gpd.GeoDataFrame(pyogrio.read_dataframe(bp,layer='buildings',columns=['building_id'],bbox=z.geometry.bounds))
     result=union_coverage(b,z.geometry,geom)
     checks.append({'unit_id':z.unit_id,'check':'SP_reuse_reconstructed_shared_algorithm','max_delta_m2':max(abs(x-y) for x,y in zip(result,[gross,onland,summed])),'passed':bool(np.allclose(result,[gross,onland,summed],rtol=1e-9,atol=.01))})
   else:
    gross,onland,summed=union_coverage(b,z.geometry,geom)
   valid=0<=onland<=geom.area+.01 and 0<=gross<=z.geometry.area+.01 and gross<=summed+.01
   checks.append({'unit_id':z.unit_id,'check':'footprint_bounds','passed':bool(valid)})
   rows.append({'unit_id':z.unit_id,'gross_area_m2':z.geometry.area,'land_area_m2':geom.area,'water_area_m2':z.geometry.area-geom.area,'footprint_union_gross_m2':gross,'footprint_union_land_m2':onland,'footprint_summed_m2':summed,'B1_coverage_land':onland/geom.area,'B1_coverage_gross':gross/z.geometry.area,'overlap_excess_fraction':(summed-gross)/summed if summed else 0.,'strict_cross_city_accepted':False,'provenance':'reused frozen SP exact unions; three shared-algorithm pilot reconstructions' if city=='SP' else 'recomputed native local metric tiled unions'})
   pd.DataFrame(rows).to_csv(OUT/'footprint_candidates.partial.csv',index=False)
   print(z.unit_id,'footprints complete',flush=True)
 pd.DataFrame(rows).to_csv(OUT/'footprint_candidates.csv',index=False)
 (OUT/'checks.json').write_text(json.dumps(checks,indent=2));(OUT/'source_receipts.json').write_text(json.dumps(receipts,indent=2))
 if not all(c['passed'] for c in checks):raise RuntimeError('Footprint checks failed')
 print('Footprints complete',len(rows),'checks',len(checks),flush=True)
if __name__=='__main__':main()

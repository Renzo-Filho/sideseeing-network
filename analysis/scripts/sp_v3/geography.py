from . import common as C
import geopandas as gpd,numpy as np,pandas as pd,pyogrio,shapely,json,hashlib

def land():
 out=C.OUT/'N02';d=gpd.read_parquet(C.BASE/'01_districts/districts.parquet')
 d=d.sort_values('district_id').reset_index(drop=True);covered=shapely.Polygon();fix=[]
 for i in d.index:
  old=d.geometry.iloc[i];new=C.polygon_only(old.difference(covered));fix.append(float(old.area-new.area));d.loc[i,'geometry']=new;covered=shapely.union_all([covered,new])
 water=C.read(C.RAW/'Meio Ambiente/massa_d_agua.gpkg');water_union=shapely.union_all(water.geometry.values)
 w=shapely.intersection(d.geometry.values,water_union);land=shapely.difference(d.geometry.values,water_union)
 d['gross_area_m2']=d.area;d['water_area_m2']=shapely.area(w);d['land_area_m2']=shapely.area(land);d['overlap_removed_m2']=fix
 d['land_area_status']='validated_arithmetic_source_mask';d['boundary_policy']='ascending_ID_overlap_ownership_internal_holes_preserved'
 assert np.allclose(d.gross_area_m2,d.water_area_m2+d.land_area_m2,rtol=1e-10,atol=.01)
 assert d.is_valid.all() and d.land_area_m2.gt(0).all()
 C.write(d,out/'districts.parquet');lg=gpd.GeoDataFrame({'district_id':d.district_id},geometry=land,crs=d.crs);wg=gpd.GeoDataFrame({'district_id':d.district_id},geometry=w,crs=d.crs)
 C.write(lg,out/'district_land.parquet');C.write(wg,out/'district_water.parquet')
 pyogrio.write_dataframe(d,out/'districts.gpkg',layer='districts',driver='GPKG');pyogrio.write_dataframe(lg,out/'districts.gpkg',layer='land',driver='GPKG');pyogrio.write_dataframe(wg,out/'districts.gpkg',layer='water',driver='GPKG')
 check=shapely.union_all(d.geometry.values)
 C.dump(out/'qa.json',{'districts':len(d),'overlap_removed_m2':sum(fix),'gross_area_m2':float(d.area.sum()),'water_area_m2':float(d.water_area_m2.sum()),'land_area_m2':float(d.land_area_m2.sum()),'district_union_difference_m2':float(d.area.sum()-check.area),'boundary_reference_status':'not_independently_adjudicated; explicit deterministic overlap allocation','water_categories_review':'all supplied water polygons retained; no land/park exclusion','pilots':d.loc[d.district_id.isin(C.CFG['pilot_districts']),['district_id','gross_area_m2','water_area_m2','land_area_m2']].to_dict('records')})

def buildings_blocks():
 out=C.OUT/'N06';d=C.districts()
 blocks=C.read(C.RAW/'Cadastro e Vias/quadra_viaria_editada.gpkg');blocks['source_valid']=blocks.is_valid
 blocks.geometry=[C.polygon_only(shapely.make_valid(g)) if not g.is_valid else g for g in blocks.geometry]
 assignment=C.assign(blocks,d);blocks['district_id']=assignment.district_id;blocks['inside_city_area_m2']=assignment.inside_area_m2;blocks['eligible_type']=blocks.tx_tipo_quadra_viaria.eq('Quadra');C.write(blocks,out/'blocks.parquet')
 C.dump(out/'blocks_qa.json',{'source_rows':len(blocks),'repaired':int((~blocks.source_valid).sum()),'invalid_after':int((~blocks.is_valid).sum()),'eligible_rows':int(blocks.eligible_type.sum()),'unassigned':int(blocks.district_id.isna().sum()),'category_counts':blocks.tx_tipo_quadra_viaria.value_counts().to_dict(),'note':'whole blocks retained; no block-size/shape model summaries'})
 paths=sorted((C.RAW/'Cadastro e Vias/Lotes').glob('*.gpkg'))
 bounds={p:shapely.box(*pyogrio.read_info(p)['total_bounds']) for p in paths}
 source=C.RAW/'Edificacoes/sao_paulo_building_morphology.gpkg';cols=['building_id','footprint_area_m2','height_m','floor_count','floor_count_imputed','overture_release']
 signature=C.sha(__file__)+C.sha(C.OUT/'N01/manifest.json')+C.sha(C.__file__)
 summaries=[]
 for _,row in d.iterrows():
  code=row.district_id;folder=out/'buildings'/code;folder.mkdir(parents=True,exist_ok=True);done=folder/'completed.json'
  if done.exists():
   old=json.loads(done.read_text())
   if old['signature']==signature and all((folder/k).exists() and C.sha(folder/k)==v for k,v in old['outputs'].items()):summaries.append(old['summary']);C.log('N06 district '+code+' checkpoint reused');continue
  count=0;links=0;matched=0;insidearea=0.;zeroarea=0;loaded={};part=0
  with pyogrio.open_arrow(source,layer='buildings',columns=cols,bbox=tuple(row.geometry.bounds),batch_size=C.CFG['building_batch_size'],use_pyarrow=True) as (meta,reader):
   for batch in reader:
    df=batch.to_pandas();geom=meta['geometry_name'];g=gpd.GeoDataFrame(df.drop(columns=geom),geometry=shapely.from_wkb(df[geom]),crs=meta['crs'])
    a=C.assign(g,d);keep=a.district_id.eq(code);g=g.loc[keep].reset_index(drop=True);a=a.loc[keep].reset_index(drop=True)
    if not len(g):continue
    assert g.is_valid.all()
    g['district_id']=code;g['inside_city_area_m2']=a.inside_area_m2;g['intersecting_districts']=a.district_candidates;g['source_file']=str(source.relative_to(C.ROOT));g['building_parcel_status']='overlap_candidates_only_no_tax_area_transfer'
    C.write(g,folder/f'buildings_{part:04}.parquet');count+=len(g);insidearea+=float(g.inside_city_area_m2.sum())
    bb=shapely.box(*g.total_bounds)
    for p,b in bounds.items():
     if b.intersects(bb) and p not in loaded:
      pc=p.name.split('LOTES_')[1].split('_')[0]
      pg=gpd.read_parquet(C.BASE/'02_parcels_tax/parcel_records'/f'{pc}.parquet',columns=['parcel_candidate_id','sql_key','geometry'])
      loaded[p]=pg
    candidates=[v for p,v in loaded.items() if bounds[p].intersects(bb)]
    if candidates:
     pg=gpd.GeoDataFrame(pd.concat(candidates,ignore_index=True),crs=d.crs).drop_duplicates('parcel_candidate_id').reset_index(drop=True)
     li,ri=pg.sindex.query(g.geometry,predicate='intersects');area=shapely.area(shapely.intersection(g.geometry.values[li],pg.geometry.values[ri]));positive=area>1e-8;li=li[positive];ri=ri[positive];area=area[positive]
     cross=pd.DataFrame({'building_id':g.building_id.values[li],'parcel_candidate_id':pg.parcel_candidate_id.values[ri],'overlap_area_m2':area,'footprint_overlap_fraction':area/g.footprint_area_m2.values[li]})
     cross['accepted_tax_transfer']=False;cross.to_parquet(folder/f'parcel_links_{part:04}.parquet',index=False);links+=len(cross);matched+=cross.building_id.nunique()
    part+=1
  summary={'district_id':code,'buildings':count,'parcel_links':links,'buildings_with_overlap_candidate':matched,'sum_individual_inside_city_footprint_area_m2':insidearea,'note':'summed source areas are QA only, not B1 union coverage'}
  outputs={p.name:C.sha(p) for p in folder.glob('*.parquet')};C.dump(done,{'signature':signature,'summary':summary,'outputs':outputs});summaries.append(summary);C.log(f'N06 district {code}: {count:,} buildings / {links:,} parcel links')
 c=C.con();c.read_parquet(str(out/'buildings/*/buildings_*.parquet')).create_view('b');q=C.records(c,'select count(*) records,count(distinct building_id) unique_ids,count(*) filter(where inside_city_area_m2<=0) nonpositive_city_overlap from b')[0];assert q['records']==q['unique_ids'] and q['nonpositive_city_overlap']==0;c.close()
 C.dump(out/'qa.json',{'buildings':q,'by_district':summaries,'municipal_membership':'positive city intersection, largest district intersection owns full entity','attribute_construction':False,'parcel_transfer':'overlap candidates only; all tax transfers false'})

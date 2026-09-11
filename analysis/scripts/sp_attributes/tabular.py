from . import core as C
import duckdb,geopandas as gpd,pandas as pd,numpy as np,shapely

def linear_parts(g):
 if g.geom_type in ('LineString','LinearRing'):yield g
 elif g.geom_type in ('MultiLineString','GeometryCollection'):
  for part in shapely.get_parts(g):yield from linear_parts(part)

def prepare():
 out=C.OUT/'intermediates';out.mkdir(exist_ok=True,parents=True)
 # Geometric area is computed from projected source geometry, not repeated IPTU land reports.
 folder=out/'parcel_areas';folder.mkdir(exist_ok=True)
 for f in sorted((C.OLD/'02_parcels_tax/parcel_records').glob('*.parquet')):
  dest=folder/f.name
  if dest.exists():continue
  g=gpd.read_parquet(f,columns=['parcel_candidate_id','geometry']);assert g.crs.to_epsg()==31983
  pd.DataFrame({'parcel_candidate_id':g.parcel_candidate_id,'physical_area_m2':g.area}).to_parquet(dest,index=False)
 c=duckdb.connect(config={'memory_limit':'512MB','threads':1})
 for name,path in [('pi',C.BASE/'N03/parcel_identity.parquet'),('p',C.BASE/'N03/parcel_fiscal_profiles.parquet'),('f',C.BASE/'N03/fiscal_records.parquet'),('a',folder/'*.parquet')]:c.read_parquet(str(path)).create_view(name)
 c.execute('create table area as select parcel_candidate_id,min(physical_area_m2) physical_area_m2 from a group by 1')
 q=c.execute("""select pi.district_id,pi.parcel_candidate_id,pi.entity_key,area.physical_area_m2,p.floor_count_candidate,p.floor_proxy_eligible,p.parcel_use_candidate,p.unit_sum_constructed_area_candidate_m2 from pi join area using(parcel_candidate_id) left join p using(parcel_candidate_id) where geometry_status='unique_geometry_candidate' and pi.district_id is not null""").fetchdf()
 assert q.parcel_candidate_id.is_unique and q.entity_key.is_unique and q.physical_area_m2.gt(0).all();q.to_parquet(out/'canonical_parcel_metrics.parquet',index=False)
 c.execute("copy (select district_id,sum(constructed_area_m2) area,count(*) accounts from f where accepted_area_aggregation group by 1) to '"+str(out/'fiscal_district_totals.parquet')+"' (format parquet)")
 c.close()

def run(codes):
 d=C.districts();F=C.Features();edges=gpd.read_parquet(C.BASE/'N04/edges.parquet');overlay=pd.read_parquet(C.ROOT/C.CFG['m6_overlay'],columns=['edge_id','class_model','class_imputed'])
 edges=edges.drop(columns=['class_model','class_imputed']).merge(overlay,on='edge_id',validate='one_to_one');edges=edges.loc[edges.canonical_edge].reset_index(drop=True)
 blocks=gpd.read_parquet(C.BASE/'N06/blocks.parquet');blocks=blocks.loc[blocks.eligible_type & blocks.district_id.notna()].copy();a,co,el=C.block_metrics(blocks.geometry.values);blocks['area']=a;blocks['compactness']=co;blocks['elongation']=el
 parcels=pd.read_parquet(C.OUT/'intermediates/canonical_parcel_metrics.parquet');fiscal=pd.read_parquet(C.OUT/'intermediates/fiscal_district_totals.parquet').set_index('district_id')
 population_source=pd.read_parquet(C.BASE/'N07/census_district_allocation.parquet');population=population_source.groupby('district_id').population_allocated.sum();population_counts=population_source.groupby('district_id').sector_id.nunique()
 nodes=gpd.read_parquet(C.ROOT/C.CFG['m2_overlay']);m2sens=pd.read_csv(C.ROOT/'analysis/outputs/sp_simplification_review_2026_09_10/m2_district_scenarios.csv',dtype={'district_id':str})
 u2dir=C.ROOT/C.CFG['u2_directory'];jobfiles=sorted(u2dir.glob('*_district_totals.csv'));jtable={p.name.removesuffix('_district_totals.csv'):pd.read_csv(p,dtype={'district_id':str}).set_index('district_id') for p in jobfiles}
 job_counts={name:pd.read_parquet(u2dir/(name+'_allocations.parquet'),columns=['district_id']).groupby('district_id').size() for name in jtable}
 classes=sorted(edges.class_model.unique());previous=shapely.Polygon();street_qa=[]
 for row in d.itertuples():
  code=row.district_id;shared=shapely.union_all(list(linear_parts(shapely.intersection(row.geometry.boundary,previous))));previous=shapely.union_all([previous,row.geometry])
  if code not in codes:continue
  gross=row.gross_area_m2;land=row.land_area_m2;km2=gross/1e6
  ids=edges.sindex.query(row.geometry,predicate='intersects');e=edges.iloc[ids].copy();pieces=shapely.intersection(e.geometry.values,row.geometry)
  if not shared.is_empty:
   pieces=np.array([shapely.union_all(list(linear_parts(z))) for z in pieces],dtype=object)
   pieces=shapely.difference(pieces,shared)
  e['length']=shapely.length(pieces);e=e.loc[e['length'].gt(0)];total=e['length'].sum();observed=e.loc[~e.class_imputed,'length'].sum()
  F.add(code,'M1','street_density_km_km2',total/1000/km2,'km/km²',num=total/1000,den=km2,n=len(e),primary=True,method=C.CFG['street_universe'])
  for cl in classes:
   slug=cl.lower().replace(' ','_');v=e.loc[e.class_model.eq(cl),'length'].sum();o=e.loc[e.class_observed.eq(cl),'length'].sum()
   for variant,val in [('model',v),('observed',o)]:F.add(code,'M6',f'street_class_{variant}_share_{slug}',val/total,'fraction',num=val,den=total,coverage=observed/total,n=len(e),status='assumed_local_residual',primary=variant=='model',method='class shares of canonical clipped length; all unknown Local')
  F.add(code,'M6','street_class_imputed_share',1-observed/total,'fraction',num=total-observed,den=total,n=len(e),status='diagnostic')
  street_qa.append({'district_id':code,'length_m':total,'edge_pieces':len(e),'observed_length_m':observed})
  n=nodes.loc[nodes.district_id.eq(code)&nodes.selected_m2_proxy];F.add(code,'M2','intersection_density_proxy_5m_km2',len(n)/km2,'nodes/km²',num=len(n),den=km2,n=len(n),primary=True,status='approved_proxy',method='at least 3 source arms; exclude PONTE/VIADUTO/TUNEL distance <=5m')
  for threshold in [0,10,20]:
   ss=m2sens.loc[m2sens.district_id.eq(code)&m2sens.structure_group.eq('bridge_tunnel')&m2sens.distance_m.eq(threshold)].iloc[0]
   F.add(code,'M2',f'intersection_density_proxy_{threshold}m_km2',ss.far/km2,'nodes/km²',num=int(ss.far),den=km2,n=int(ss.far),status='sensitivity')
  b=blocks.loc[blocks.district_id.eq(code)]
  for family,field,unit,names in [('M3','area','m²',['median','p25','p75','iqr']),('M3','log_area','ln(m²/1m²)',['median','iqr']),('M4','compactness','dimensionless',['median','iqr']),('M4','elongation','dimensionless',['median','iqr'])]:
   vals=np.log(b.area) if field=='log_area' else b[field];q=vals.quantile([.25,.5,.75]);values={'median':q.loc[.5],'p25':q.loc[.25],'p75':q.loc[.75],'iqr':q.loc[.75]-q.loc[.25]}
   for name in names:F.add(code,family,'block_'+field+'_'+name,values[name],unit,n=len(vals),primary=(family=='M4' or field=='log_area'),method='whole eligible Quadra; largest overlap ownership; perimeter includes holes')
  p=parcels.loc[parcels.district_id.eq(code)];count=len(p)
  F.add(code,'M7','cadastral_parcel_density_km2',count/km2,'entities/km²',num=count,den=km2,n=count,primary=True,status='cadastral_proxy',method='unique accepted entity key; cadastral completeness not independently measured')
  for name,value in [('median',np.log(p.physical_area_m2).median()),('iqr',np.log(p.physical_area_m2).quantile(.75)-np.log(p.physical_area_m2).quantile(.25))]:F.add(code,'M7','parcel_log_area_'+name,value,'ln(m²/1m²)',n=count,status='cadastral_proxy')
  valid=p.loc[p.floor_proxy_eligible.fillna(False),'floor_count_candidate'].dropna()
  for name,quantile in [('median',.5),('p75',.75),('p90',.9)]:F.add(code,'B2','cadastral_floor_count_'+name,valid.quantile(quantile) if len(valid) else None,'floors',coverage=len(valid)/count,n=len(valid),missing=count-len(valid),status='cadastral_proxy',primary=name in ['median','p90'],method='one distinct positive report per accepted cadastral entity; ancillary/conflicting reports excluded')
  ar=float(fiscal.loc[code,'area']);F.add(code,'B3','cadastral_floor_area_density',ar/land,'m²/m²',num=ar,den=land,coverage=None,n=int(fiscal.loc[code,'accounts']),status='cadastral_proxy',primary=True,coverage_basis='district source completeness unknown; city fiscal mass located 97.3032%',method='unique fiscal unit area sum; no ideal-fraction reapplication; whole parcel district')
  known=p.loc[p.parcel_use_candidate.notna()];cats=C.CFG['u1_categories']
  for weighting,weights in [('count',known.parcel_use_candidate.value_counts().reindex(cats,fill_value=0)),('land_area',known.groupby('parcel_use_candidate').physical_area_m2.sum().reindex(cats,fill_value=0))]:
   cov=len(known)/count if weighting=='count' else known.physical_area_m2.sum()/p.physical_area_m2.sum()
   F.add(code,'U1','land_use_entropy_'+weighting,C.entropy(weights),'normalized entropy',coverage=cov,n=len(known),missing=count-len(known),primary=weighting=='count',status='cadastral_proxy',method='fixed 7 categories; entropy on classified mass; mixed entity counted once')
   for cat,w in weights.items():F.add(code,'U1','land_use_'+weighting+'_share_'+cat.replace('/','_').replace(' ','_'),w/weights.sum() if weights.sum()>0 else None,'fraction',num=float(w),den=float(weights.sum()),coverage=cov,n=len(known),status='diagnostic')
  for name,j in jtable.items():
   v=float(j.loc[code,'total_jobs']);glob=float(j.loc[j.index!='UNLOCATED','total_jobs'].sum())/5387474
   F.add(code,'U2','formal_job_density_'+name+'_km2',v/km2,'job links/km²',num=v,den=km2,n=int(job_counts[name].get(code,0)),coverage=glob,status='incomplete_geographic_proxy' if 'prior' not in name else 'citywide_imputed_sensitivity',primary=name==C.CFG['u2_primary'],coverage_basis='citywide allocated fraction; district missing mass unknown',method='2022 RAIS CEP allocation '+name)
  pop=float(population.loc[code]);F.add(code,'U3','population_density_km2',pop/km2,'people/km²',num=pop,den=km2,n=int(population_counts.loc[code]),primary=True,status='area_allocated_proxy',coverage=11446054.473149512/11451999,coverage_basis='citywide source population within district union',method='2022 sector area allocation; outside residual retained')
 C.dump(C.OUT/('intermediates/street_qa_'+('pilot' if len(codes)==3 else 'all')+'.json'),street_qa)
 return F.frame()

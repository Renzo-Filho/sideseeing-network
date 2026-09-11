from . import common as C
import geopandas as gpd,numpy as np,pandas as pd,shapely,hashlib

def normalize_code(s):return s.fillna('').astype(str).str.replace(r'[^0-9]','',regex=True).str.zfill(6)
def range_compatible(a,b,c,d):
 return ((a==0)|(b==0)|(c==0)|(d==0)|((np.minimum(a,b)<=np.maximum(c,d))&(np.maximum(a,b)>=np.minimum(c,d))))

def classes():
 out=C.OUT/'N04';s=gpd.read_parquet(C.BASE/'03_streets/edge_candidates.parquet')
 s=s[['edge_id','lg_seg_id','lg_codlog','lg_tipo','lg_ini_par','lg_fim_par','lg_ini_imp','lg_fim_imp','geometry_hash','source_fid','geometry']].copy()
 t=C.read(C.RAW/'Cadastro e Vias/classvias.gpkg',layer='classvias').reset_index().rename(columns={'index':'class_source_row'})
 s['codlog']=normalize_code(s.lg_codlog);t['codlog']=normalize_code(t.Lg_codlog);t['Classifica']=t.Classifica.str.strip()
 # Conservative spatial/code/range matcher; candidates grouped by class before coverage evaluation.
 li,ri=t.sindex.query(s.geometry,predicate='dwithin',distance=C.CFG['class_match_tolerance_m'])
 same=(s.codlog.values[li]==t.codlog.values[ri])&(s.codlog.values[li]!='000000')
 li=li[same];ri=ri[same]
 par=range_compatible(s.lg_ini_par.values[li],s.lg_fim_par.values[li],t.Lg_ini_par.fillna(0).values[ri],t.Lg_fim_par.fillna(0).values[ri])
 imp=range_compatible(s.lg_ini_imp.values[li],s.lg_fim_imp.values[li],t.Lg_ini_imp.fillna(0).values[ri],t.Lg_fim_imp.fillna(0).values[ri])
 # Either valid parity range supports a candidate; unknown ranges are explicitly permissive.
 keep=par|imp;li=li[keep];ri=ri[keep]
 pairs=pd.DataFrame({'edge_row':li,'class_row':ri,'class_raw':t.Classifica.values[ri]});buffers=shapely.buffer(t.geometry.values,C.CFG['class_match_tolerance_m'])
 coverage=[]
 for (i,category),p in pairs.dropna(subset='class_raw').groupby(['edge_row','class_raw'],sort=False):
  area=shapely.union_all(buffers[p.class_row.values]);covered=s.geometry.iloc[i].intersection(area).length
  coverage.append({'edge_row':int(i),'class_raw':category,'coverage':float(min(1,covered/s.geometry.iloc[i].length)),'source_class_rows':','.join(map(str,p.class_row))})
 cv=pd.DataFrame(coverage);cv.to_parquet(out/'class_candidates.parquet',index=False)
 eligible=cv.loc[cv.coverage.ge(C.CFG['class_min_geometry_coverage'])]
 best=eligible.sort_values(['edge_row','coverage','class_raw'],ascending=[True,False,True]).drop_duplicates('edge_row').set_index('edge_row')
 conflicts=cv.loc[cv.coverage.ge(.2)].groupby('edge_row').class_raw.nunique().gt(1)
 s['class_observed']=best.class_raw.reindex(s.index);s['matched_fraction']=best.coverage.reindex(s.index)
 s['conflicting_classes']=conflicts.reindex(s.index).fillna(False).astype(bool);s.loc[s.conflicting_classes,'class_observed']=None
 s['class_match_method']=np.where(s.class_observed.notna(),'codlog_ranges_geometry','unmatched')
 # Identifier-independent fallback requires near-coincident whole geometries, not nearest-road guessing.
 missing=s.index[s.class_observed.isna() & ~s.conflicting_classes]
 x,y=t.sindex.query(s.geometry.loc[missing],predicate='dwithin',distance=1.0)
 xx=missing.values[x];distance=shapely.hausdorff_distance(s.geometry.values[xx],t.geometry.values[y])
 valid=(distance<=1.0)&t.Classifica.notna().values[y]
 fallback=pd.DataFrame({'edge_row':xx[valid],'class_row':y[valid],'class_raw':t.Classifica.values[y[valid]],'hausdorff_m':distance[valid]})
 fallback.to_parquet(out/'geometry_identity_fallback.parquet',index=False)
 counts=fallback.groupby('edge_row').class_raw.nunique();ok=counts.index[counts.eq(1)]
 fb=fallback.loc[fallback.edge_row.isin(ok)].sort_values(['edge_row','hausdorff_m']).drop_duplicates('edge_row').set_index('edge_row')
 s.loc[fb.index,'class_observed']=fb.class_raw
 s.loc[fb.index,'class_match_method']='whole_geometry_coincident_1m'
 s.loc[counts.index[counts.gt(1)],'conflicting_classes']=True
 s['class_imputed']=s.class_observed.isna() & ~s.conflicting_classes & s.lg_tipo.isin(C.CFG['minor_road_local_imputation_types'])
 s['class_model']=s.class_observed;s.loc[s.class_imputed,'class_model']='LOCAL';s['imputation_reason']=np.where(s.class_imputed,'declared_minor_road_residual_Local_assumption','not_imputed')
 s['geometry_group_size']=s.groupby('geometry_hash').edge_id.transform('size');s['canonical_edge']=~s.geometry_hash.duplicated()
 s['network_universe']='all_valid_logradouro_geometries_exact_geometry_dedup_sensitivity_required'
 C.write(s,out/'edges.parquet');C.write(t,out/'classification_source.parquet');s.drop(columns='geometry').to_parquet(out/'edge_lineage.parquet',index=False)
 d=C.districts();cover=[]
 for _,row in d.iterrows():
  g=s.loc[s.canonical_edge].iloc[s.loc[s.canonical_edge].sindex.query(row.geometry,predicate='intersects')]
  lengths=g.geometry.intersection(row.geometry).length;total=float(lengths.sum())
  cover.append({'district_id':row.district_id,'source_length_m':total,'observed_fraction':float(lengths[g.class_observed.notna()].sum()/total),'imputed_fraction':float(lengths[g.class_imputed].sum()/total),'unresolved_fraction':float(lengths[g.class_model.isna()].sum()/total),'conflict_fraction':float(lengths[g.conflicting_classes].sum()/total)})
 C.dump(out/'coverage.json',cover)
 C.dump(out/'qa.json',{'valid_source_edges':len(s),'class_source_rows':len(t),'candidate_pairs':len(pairs),'observed_edges':int(s.class_observed.notna().sum()),'geometry_fallback_edges':int(s.class_match_method.eq('whole_geometry_coincident_1m').sum()),'imputed_edges':int(s.class_imputed.sum()),'unresolved_edges':int(s.class_model.isna().sum()),'conflict_edges':int(s.conflicting_classes.sum()),'duplicate_geometry_excess':int((~s.canonical_edge).sum()),'method':'CODLOG + permissive compatible parity ranges + class-union 2m-buffer length coverage >=0.8; alternative class coverage >=0.2 quarantines observed label','fallback_method':'whole-geometry Hausdorff <=1m, one supported class; not unrestricted nearest assignment', 'status':'observed_match_and_declared_imputation; no district class attributes calculated','type_counts':s.lg_tipo.value_counts().to_dict()})

def topology():
 out=C.OUT/'N05';s=gpd.read_parquet(C.OUT/'N04/edges.parquet');s=s.loc[s.canonical_edge].reset_index(drop=True)
 structure=C.read(C.RAW/'Cadastro e Vias/obra_arte.gpkg');C.write(structure,out/'structures.parquet')
 li,ri=s.sindex.query(s.geometry,predicate='intersects');keep=li<ri;li=li[keep];ri=ri[keep]
 intersections=shapely.intersection(s.geometry.values[li],s.geometry.values[ri])
 rows=[];overlap=[]
 for a,b,g in zip(li,ri,intersections):
  if g.is_empty:continue
  if g.geom_type in ['LineString','MultiLineString']:
   if g.length>1e-6:overlap.append({'edge_a':s.edge_id[a],'edge_b':s.edge_id[b],'overlap_length_m':g.length})
   continue
  for p in shapely.get_parts(g):
   if p.geom_type=='Point':rows.append((p.x,p.y,int(a),int(b)))
 points=pd.DataFrame(rows,columns=['x','y','edge_a','edge_b'])
 points['node_id']=[hashlib.sha256(f'{x.hex()}:{y.hex()}'.encode()).hexdigest() for x,y in zip(points.x,points.y)]
 points.to_parquet(out/'crossing_edge_pairs.parquet',index=False);pd.DataFrame(overlap,columns=['edge_a','edge_b','overlap_length_m']).to_parquet(out/'collinear_overlap_review.parquet',index=False)
 unique=points.drop_duplicates('node_id')[['node_id','x','y']].reset_index(drop=True)
 ng=gpd.GeoDataFrame(unique,geometry=gpd.points_from_xy(unique.x,unique.y),crs=s.crs)
 # All incident edges, endpoint incidence one arm; an interior occurrence contributes two arms.
 incidence=pd.concat([points[['node_id','edge_a']].rename(columns={'edge_a':'edge_row'}),points[['node_id','edge_b']].rename(columns={'edge_b':'edge_row'})]).drop_duplicates()
 point_lookup=dict(zip(ng.node_id,ng.geometry));arms=[]
 for nid,e in zip(incidence.node_id,incidence.edge_row):
  p=point_lookup[nid];g=s.geometry.iloc[e];arms.append(1 if min(p.distance(shapely.Point(g.coords[0])),p.distance(shapely.Point(g.coords[-1])))<1e-7 else 2)
 incidence['source_arms']=arms;incidence['edge_id']=s.edge_id.values[incidence.edge_row];incidence.to_parquet(out/'crossing_incidence.parquet',index=False)
 ng['source_arm_count']=ng.node_id.map(incidence.groupby('node_id').source_arms.sum());ng['source_edge_count']=ng.node_id.map(incidence.groupby('node_id').size())
 ai,bi=structure.sindex.query(ng.geometry,predicate='dwithin',distance=C.CFG['junction_structure_review_distance_m'])
 assoc=pd.DataFrame({'node_id':ng.node_id.values[ai],'structure_id':structure.cd_identificador_obra_arte.values[bi],'structure_type':structure.tx_tipo_obra_arte.values[bi],'reference_year':structure.tx_ano_referencia.values[bi]})
 assoc.to_parquet(out/'structure_crossing_candidates.parquet',index=False)
 ng['near_structure']=ng.node_id.isin(assoc.node_id);ng['junction_candidate']=ng.source_arm_count.ge(3)
 ng['status']=np.where(ng.near_structure,'level_review_required','source_planar_candidate_topology_not_certified');ng['accepted_m2_junction']=False;ng['district_id']=C.point_assign(ng,C.districts());C.write(ng,out/'crossing_candidates.parquet')
 # Snap sensitivity reports spatial coincidences only; no tolerance silently changes graph connectivity.
 sensitivity=[]
 for tolerance in C.CFG['junction_snap_sensitivity_m']:
  if tolerance==0:n=len(ng)
  else:n=len(set(zip(np.round(ng.x/tolerance).astype('int64'),np.round(ng.y/tolerance).astype('int64'))))
  sensitivity.append({'grid_tolerance_m':tolerance,'coordinate_bins':n,'method':'diagnostic grid bins, not accepted junction clustering'})
 C.dump(out/'qa.json',{'point_crossing_candidates':len(ng),'at_least_three_source_arms':int(ng.junction_candidate.sum()),'near_structure':int(ng.near_structure.sum()),'collinear_overlaps':len(overlap),'accepted_junctions':0,'snap_diagnostics':sensitivity,'gate':'structure lines do not supply edge levels; grade separation, same-level approaches and carriageway consolidation require case-level verification'})

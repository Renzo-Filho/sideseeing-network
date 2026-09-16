"""Read-only audit of the user model; writes separate review evidence, never model outputs."""
from pathlib import Path
import ast,contextlib,copy,hashlib,io,json,os,subprocess,sys
import numpy as np,pandas as pd
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'analysis';OUT=args.output or A/'work/reviews/sp_model_validation_2026_09_15_v2';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(A/'scripts'))
from sp_model.transforms import fit_transform_scalars,transform_composition
from sp_model.distances import compute_distances
cfg=json.loads((A/'config/sp_urban_model_v2.json').read_text())
df=pd.read_csv(A/cfg['paths']['primary_attributes'],dtype={'district_id':str}).set_index('district_id');ids=df.index.tolist();b=ids.index('10');checks=[]
def check(name,passed,detail=None):checks.append(dict(check=name,passed=bool(passed),detail=detail))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[A/'scripts/model_sp_urban_similarity.py',A/'model_analysis.py',A/'model_analysis.ipynb',A/'config/sp_urban_model_v1.json',A/'config/sp_urban_model_v2.json',*sorted((A/'scripts/sp_model').glob('*.py')),*sorted((A/'results/SP/models/sp_urban_model_v1/tables').glob('*')),*sorted((A/'results/SP/tables').glob('*'))]
before={str(p.relative_to(ROOT)):sha(p) for p in protected}
# Independent implementation: NumPy quantiles, broadcast distances and explicit embedding.
Z={};E=[];r={};cal={};par={};weights=np.array([f['weight'] for f in cfg['families'].values()],float);weights/=weights.sum()
for (fam,fc),w in zip(cfg['families'].items(),weights):
 x=df[fc['columns']].to_numpy(float)
 if fc['type']=='composition':
  assert (x>=0).all() and np.all(np.abs(x.sum(1)-1)<1e-8)
  z=np.sqrt(x/x.sum(1)[:,None]);factor=.5
 else:
  x={'identity':lambda x:x,'log':np.log,'log1p':np.log1p}[fc['transform']](x)
  med=np.median(x,axis=0);iqr=np.quantile(x,.75,axis=0)-np.quantile(x,.25,axis=0);sd=np.std(x,axis=0,ddof=0)
  fallback=iqr<=1e-12*np.maximum(1,np.abs(x).max(0));scale=np.where(fallback,sd,iqr)
  assert (scale>0).all();z=(x-med)/scale;factor=1/x.shape[1]
  for j,c in enumerate(fc['columns']):par[c]={'median':med[j],'selected_scale':scale[j],'fallback':bool(fallback[j])}
 Z[fam]=z;r[fam]=factor*np.square(z[:,None,:]-z[None,:,:]).sum(2)
 positive=r[fam][np.triu_indices(len(df),1)];cal[fam]=float(np.median(positive[positive>0]));E.append(z*np.sqrt(w*factor/cal[fam]))
E=np.concatenate(E,axis=1);D=np.sqrt(np.square(E[:,None,:]-E[None,:,:]).sum(2))
sc,pa=fit_transform_scalars(df,cfg);co=transform_composition(df,cfg);actual,rs,bs,cs=compute_distances(sc,co,cfg)
check('Independent primary metric matches pipeline',np.allclose(D,actual,rtol=1e-12,atol=1e-12),float(np.max(np.abs(D-actual))))
primary_cols=[c for f in cfg['families'].values() for c in f['columns']]
wide=pd.read_parquet(A/cfg['paths']['wide_attributes']).set_index('district_id')
long=pd.read_parquet(A/cfg['paths']['long_attributes']);pivot=long.pivot(index='district_id',columns='feature_name',values='value')
check('Primary values match wide and long source tables',np.allclose(df[primary_cols],wide.loc[ids,primary_cols],rtol=1e-12,atol=1e-12) and np.allclose(df[primary_cols],pivot.loc[ids,primary_cols],rtol=1e-12,atol=1e-12))
saved_params=json.loads((A/'work/runs/sp_urban_model_v1/transform_params.json').read_text())
check('Saved scalar fitted parameters match independent fit',all(np.isclose(saved_params[c]['median'],p['median']) and np.isclose(saved_params[c]['selected_scale'],p['selected_scale']) and saved_params[c]['used_sd_fallback']==p['fallback'] for c,p in par.items()))
check('All family calibrations independently reproduced',all(np.isclose(cal[f],bs[f],rtol=1e-12) for f in cal))
check('Contributions sum to squared distances',np.allclose(sum(cs.values()),D**2,rtol=1e-12,atol=1e-12))
check('Finite symmetric nonnegative zero-diagonal distances',np.isfinite(D).all() and (D>=0).all() and np.allclose(D,D.T) and np.allclose(np.diag(D),0))
check('All 884736 triangle inequalities',all(np.all(D<=D[:,k,None]+D[k,None,:]+1e-10) for k in range(len(df))))
R=pd.DataFrame({'distance':D[b]},index=df.index).drop('10');R['rank']=R.distance.rank(method='min').astype(int);R['district_name']=df.district_name;R=R.reset_index().sort_values(['distance','district_id']);R.to_csv(OUT/'independent_bras_ranking.csv',index=False)
saved=pd.read_csv(A/'results/SP/models/sp_urban_model_v1/tables/pairwise_distances.csv',index_col=0);saved.index=saved.index.astype(str).str.zfill(2)
saved.columns=saved.columns.astype(str).str.zfill(2)
check('Saved pairwise matrix matches recomputation',np.allclose(saved.loc[ids,ids].values,D,rtol=1e-12,atol=1e-12),float(np.max(abs(saved.loc[ids,ids].values-D))))
savedr=pd.read_csv(A/'results/SP/models/sp_urban_model_v1/tables/bras_ranking.csv',dtype={'district_id':str}).set_index('district_id');ref=R.set_index('district_id')
check('Saved 95-row ranking matches independently',len(savedr)==95 and savedr.index.is_unique and set(savedr.index)==set(ref.index) and np.allclose(savedr.loc[ref.index,'distance'],ref.distance) and np.array_equal(savedr.loc[ref.index,'rank'],ref['rank']))
# Check the real CLI import without executing a write-producing run.
proc=subprocess.run([sys.executable,'-c','import sys;sys.path.insert(0,"analysis/scripts");import model_sp_urban_similarity'],cwd=ROOT,capture_output=True,text=True)
check('CLI imports in current environment',proc.returncode==0,proc.stderr.strip());(OUT/'cli_import.log').write_text(proc.stdout+proc.stderr)
v2=A/'results/SP/models/sp_urban_model_v2/tables/pairwise_distances.csv'
if v2.exists():
 vv=pd.read_csv(v2,index_col=0);vv.index=vv.index.astype(str).str.zfill(2);vv.columns=vv.columns.astype(str).str.zfill(2)
 check('Corrected v2 published matrix matches independent reference',np.allclose(vv.loc[ids,ids],D,rtol=1e-12,atol=1e-12))
# Probes of invalid input handling, state alignment, and weighting.
def rejected(fn):
 try:
  with np.errstate(all='ignore'):fn()
 except (ValueError,AssertionError):return True
 return False
bad=df.copy();bad.iloc[0,bad.columns.get_loc('street_density_km_km2')]=0
check('Reject log zero before producing invalid coordinates',rejected(lambda:fit_transform_scalars(bad,cfg)))
badinf=df.copy();badinf.iloc[0,badinf.columns.get_loc('street_density_km_km2')]=np.inf
check('Reject infinite scalar input',rejected(lambda:fit_transform_scalars(badinf,cfg)))
badcomp=df.copy();cols=cfg['families']['M6']['columns'];badcomp.loc[badcomp.index[0],cols]*=1.000001
check('Reject composition sum error 1e-6 above declared tolerance',rejected(lambda:transform_composition(badcomp,cfg)))
double=copy.deepcopy(cfg)
for f in double['families'].values():f['weight']*=2
D2,*_=compute_distances(sc,co,double)
check('Equivalent relative weights preserve distance',np.allclose(D2,actual),{'observed_distance_multiplier':float(D2[0,1]/actual[0,1])})
neg=copy.deepcopy(cfg);neg['families']['M1']['weight']=-1
check('Reject negative family weight',rejected(lambda:compute_distances(sc,co,neg)))
mis=co.iloc[::-1]
check('Reject mismatched scalar/composition ID order',rejected(lambda:compute_distances(sc,mis,cfg)))
order=np.random.default_rng(7).permutation(len(df));ss,pp=fit_transform_scalars(df.iloc[order],cfg);cc=transform_composition(df.iloc[order],cfg);dd,*_=compute_distances(ss,cc,cfg)
check('Consistent row permutation preserves result',np.allclose(dd,D[np.ix_(order,order)]))
# Clean, headless execution of both user artifacts. No cell outputs are written back.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
class Shell:
 def run_line_magic(self,*args,**kwargs):return None

def execute(code,label):
 ns={'__name__':'__audit__','get_ipython':lambda:Shell(),'display':lambda *args,**kwargs:None}
 old=os.getcwd();buf=io.StringIO();previous_show=plt.show;plt.show=lambda *a,**k:plt.close('all')
 try:
  os.chdir(A)
  with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):exec(compile(code,label,'exec'),ns)
  check(label+' clean headless execution',True)
 except Exception as e:check(label+' clean headless execution',False,repr(e))
 finally:os.chdir(old);plt.show=previous_show;plt.close('all');(OUT/(label+'.log')).write_text(buf.getvalue())
 return ns
nb=json.loads((A/'model_analysis.ipynb').read_text());nbcode='\n\n'.join(''.join(c['source']).replace("%matplotlib inline","get_ipython().run_line_magic('matplotlib','inline')") for c in nb['cells'] if c['cell_type']=='code')
ns=execute((A/'model_analysis.py').read_text(),'model_analysis_py');nn=execute(nbcode,'model_analysis_notebook')
check('Notebook and exported script numeric results match',all(k in ns and k in nn and np.allclose(ns[k],nn[k]) for k in ['total_dist','X','explained_var','pca_distances']))
if 'E_df' in ns and 'loadings' in ns:
 wrong=ns['loadings'].index.tolist();right=ns['E_df'].columns.tolist();mapping=pd.DataFrame({'position':range(23),'displayed_feature':wrong,'actual_feature':right});mapping['correct_label']=mapping.displayed_feature.eq(mapping.actual_feature);mapping.to_csv(OUT/'pca_loading_label_audit.csv',index=False)
 check('PCA loadings assigned to fitted feature order',mapping.correct_label.all(),{'mislabeled_columns':int((~mapping.correct_label).sum())})
 fixed=pd.DataFrame(ns['Vt'][:2,:].T,index=right,columns=['PC1','PC2']);fixed.to_csv(OUT/'corrected_pca_loadings.csv')
 check('Notebook primary distance matches independent metric',np.allclose(ns['total_dist'],D[b]))
 scores=ns['pca_scores'];full=np.sqrt(np.square(scores[:,None,:]-scores[None,:,:]).sum(2))
 check('Full unwhitened PCA preserves primary distances',np.allclose(full,D,rtol=1e-12,atol=1e-12))
 axes=ns['raw_subset'];rawz=(axes-axes.mean())/axes.std();clipped=[]
 for id in ['10',ref.index[0]]:
  clipped.extend([{'district_id':id,'feature':c,'raw_z':float(rawz.loc[id,c])} for c in axes if rawz.loc[id,c]<-2 or rawz.loc[id,c]>3.5])
 check('Displayed radar range contains plotted values',not clipped,clipped)
 results={'pca_90_components':int(ns['k_components']),'pca_2d_variance':float(ns['cumulative_var'][1]),'ward_best_k':int(ns['best_k']), 'top10':R.head(10).to_dict('records'),'radar_out_of_range':clipped}
else:results={}
check('Reviewed code and published inputs/outputs unchanged',all(sha(ROOT/p)==h for p,h in before.items()))
result={'scope':'independent audit, not a model release','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'results':results,'reviewed_hashes':before}
(OUT/'audit.json').write_text(json.dumps(result,indent=2,default=str));print(json.dumps(result,indent=2,default=str))

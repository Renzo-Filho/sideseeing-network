"""Prespecified source substitutions, metric comparisons and influence experiments."""
import copy
import json
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from .transforms import fit_transform_scalars, apply_scalar_transforms, transform_composition
from .distances import compute_distances, rank_target, normalized_weights


def run_sensitivities(df, wide, config, params, calibrations, primary, embedding, directory, groups=None):
    directory.mkdir(parents=True, exist_ok=True)
    ids = df.index.tolist();target = config['target_district_id']
    base = rank_target(primary, ids, target).set_index('district_id')
    rankings, summaries, registry = [], [], []

    def record(name, kind, distance, details):
        ranked = rank_target(distance, ids, target).set_index('district_id')
        ranked['baseline_rank'] = base['rank']
        ranked['rank_shift'] = ranked.baseline_rank - ranked['rank']
        ranked['scenario'] = name;ranked['kind'] = kind
        rankings.append(ranked.reset_index())
        corr = float(ranked['rank'].corr(base['rank'], method='spearman'))
        row = dict(scenario=name, kind=kind, spearman=corr, max_absolute_rank_shift=int(ranked.rank_shift.abs().max()))
        for k in [5,10,20]:
            left=set(base.sort_values(['distance','district_id']).head(k).index)
            right=set(ranked.sort_values(['distance','district_id']).head(k).index)
            cut=ranked.sort_values(['distance','district_id']).iloc[k-1].distance
            tie_right=set(ranked.index[ranked.distance<=cut])
            base_cut=base.sort_values(['distance','district_id']).iloc[k-1].distance
            tie_left=set(base.index[base.distance<=base_cut])
            row[f'top{k}_overlap']=len(left&right);row[f'top{k}_jaccard']=len(left&right)/len(left|right)
            row[f'top{k}_tie_expanded_size']=len(tie_right)
            row[f'top{k}_tie_expanded_jaccard']=len(tie_left&tie_right)/len(tie_left|tie_right)
        summaries.append(row);registry.append(dict(name=name,kind=kind,status='complete',**details))

    def scenario(name, kind, data=None, conf=None, refit=False, fitted_ids=None, unit_calibration=False, **details):
        data=df if data is None else data;conf=copy.deepcopy(config) if conf is None else conf
        try:
            scalar_names=[c for f in conf['families'].values() if f['type']=='scalar' for c in f['columns']]
            if refit:
                fitting=data if fitted_ids is None else data.loc[fitted_ids]
                fs,p=fit_transform_scalars(fitting,conf);fc=transform_composition(fitting,conf)
                _,_,b,_=compute_distances(fs,fc,conf)
            else:
                p={c:params[c] for c in scalar_names};b={f:calibrations[f] for f in conf['families']}
            if unit_calibration:b={f:1. for f in b}
            ss=apply_scalar_transforms(data,p);cc=transform_composition(data,conf)
            dist,*_=compute_distances(ss,cc,conf,calibrations=b)
            record(name,kind,dist,dict(refit_scales=refit,config=conf,fitted_ids=fitted_ids,
                                      fitted_params=p,calibrations=b,**details))
        except ValueError as error:
            registry.append(dict(name=name,kind=kind,status='failed',error=str(error),**details))

    # Values replace a primary coordinate, so the frozen primary transform applies unchanged.
    substitutions=[]
    for threshold in [0,10,20]:substitutions.append((f'M2_{threshold}m','intersection_density_proxy_5m_km2',f'intersection_density_proxy_{threshold}m_km2'))
    substitutions += [('B1_gross','building_coverage_land','building_coverage_gross'),('U1_land_entropy','land_use_entropy_count','land_use_entropy_land_area')]
    for c in wide.columns:
        if c.startswith('formal_job_density_') and c!='formal_job_density_area_first_km2':substitutions.append((c,'formal_job_density_area_first_km2',c))
        if c.startswith('bus_service_access_') and c!='bus_service_access_weekday_am_400m':substitutions.append((c,'bus_service_access_weekday_am_400m',c))
    for name,dest,source in substitutions:
        changed=df.copy();changed[dest]=wide.loc[ids,source]
        scenario(name,'source',data=changed,substitution={dest:source})
    changed=df.copy();cols=config['families']['M6']['columns'];observed=[c.replace('_model_','_observed_') for c in cols]
    shares=wide.loc[ids,observed].to_numpy();mass=shares.sum(axis=1)
    if (mass<=0).any():raise ValueError('Observed-only composition has zero support')
    changed[cols]=shares/mass[:,None]
    scenario('M6_observed_only','source',data=changed,observed_fraction=dict(zip(ids,mass.tolist())))
    for weighting in ['count','land_area']:
        conf=copy.deepcopy(config);cols=[c for c in wide if c.startswith(f'land_use_{weighting}_share_')]
        conf['families']['U1'].update(type='composition',columns=cols,transform='joint_sqrt_hellinger')
        changed=df.join(wide[cols]);scenario(f'U1_{weighting}_composition','representation',data=changed,conf=conf,refit=True)
    for family in config['families']:
        conf=copy.deepcopy(config);del conf['families'][family]
        scenario('without_'+family,'family_exclusion',conf=conf)
    for name,excluded in [('built_form_only',['U1','U2','U3','U4']),('without_U2_B3',['U2','B3'])]:
        conf=copy.deepcopy(config)
        for f in excluded:del conf['families'][f]
        scenario(name,'family_exclusion',conf=conf)
    conf=copy.deepcopy(config)
    for f,v in conf['families'].items():v['weight']=1/(3*{'M':6,'B':3,'U':4}[f[0]])
    scenario('equal_domains','weight_scheme',conf=conf)
    conf=copy.deepcopy(config);conf['scaling']['method']='standard_mean_sd'
    scenario('standard_scaling','scaling',conf=conf,refit=True)
    scenario('no_family_calibration','calibration',unit_calibration=True)
    scenario('fit_without_Bras','fit_influence',refit=True,fitted_ids=[i for i in ids if i!=target])
    if groups is not None:
        for group in sorted(groups.unique()):
            fit_ids=[i for i in ids if groups.loc[i]!=group]
            scenario('fit_without_subprefeitura_'+str(group),'spatial_fit_influence',refit=True,fitted_ids=fit_ids,excluded_group=str(group))
    else:
        registry.append(dict(name='subprefeitura_influence',kind='spatial_fit_influence',status='deferred',reason='Validated district group crosswalk unavailable'))
    rng=np.random.default_rng(config['random_seed'])
    for i in range(config['weight_draws']):
        conf=copy.deepcopy(config)
        for f,multiplier in zip(conf['families'].values(),rng.uniform(.5,1.5,len(conf['families']))):f['weight']*=float(multiplier)
        scenario(f'weight_{i:03d}','weight_perturbation',conf=conf)
    x=embedding.to_numpy();center=x.mean(axis=0);u,s,vt=np.linalg.svd(x-center,full_matrices=False)
    scores=(x-center)@vt.T;variance=s*s/np.sum(s*s);cumulative=np.cumsum(variance)
    pd.DataFrame(vt.T,index=embedding.columns,columns=[f'PC{i+1}' for i in range(len(vt))]).to_csv(directory/'pca_loadings.csv')
    pd.DataFrame({'component':np.arange(1,len(s)+1),'explained_variance':variance,'cumulative':cumulative}).to_csv(directory/'pca_variance.csv',index=False)
    for threshold in [.8,.9,.95]:
        k=int(np.searchsorted(cumulative,threshold)+1);q=scores[:,:k]
        dist=np.sqrt(np.square(q[:,None,:]-q[None,:,:]).sum(2))
        record(f'pca_{int(threshold*100)}','metric',dist,dict(components=k,explained_variance=float(cumulative[k-1]),whiten=False))
    full=np.sqrt(np.square(scores[:,None,:]-scores[None,:,:]).sum(2))
    if not np.allclose(full,primary,rtol=1e-11,atol=1e-11):raise ValueError('PCA full-distance conservation failed')
    lw=LedoitWolf().fit(x);eigen=np.linalg.eigvalsh(lw.covariance_)
    if eigen.min()<=0:raise ValueError('Covariance not positive definite')
    delta=x[:,None,:]-x[None,:,:];squared=np.einsum('ijk,kl,ijl->ij',delta,lw.precision_,delta)
    if not np.isfinite(squared).all() or squared.min() < -1e-10:raise ValueError('Invalid Mahalanobis distances')
    record('ledoit_wolf','metric',np.sqrt(np.maximum(squared,0)),dict(shrinkage=float(lw.shrinkage_),condition_number=float(eigen.max()/eigen.min()),equal_family_interpretation=False))
    np.savez_compressed(directory/'metric_state.npz',pca_center=center,pca_components=vt,pca_scores=scores,pca_singular_values=s,
                        covariance=lw.covariance_,precision=lw.precision_,covariance_center=lw.location_)
    ranks=pd.concat(rankings,ignore_index=True);summary=pd.DataFrame(summaries)
    ranks.to_csv(directory/'scenario_rankings.csv',index=False);summary.to_csv(directory/'scenario_summary.csv',index=False)
    # Fixed-k display membership with ties separately available in scenario diagnostics.
    weights=ranks.loc[ranks.kind.eq('weight_perturbation')]
    membership=weights.sort_values(['scenario','distance','district_id']).groupby('scenario').head(10).district_id.value_counts()
    freq=pd.DataFrame({'district_id':base.index,'top10_frequency':[membership.get(i,0)/config['weight_draws'] for i in base.index]})
    freq['weight_stable']=freq.top10_frequency.ge(config['publication_thresholds']['weight_stable_pct']/100)
    freq.to_csv(directory/'weight_stability.csv',index=False)
    (directory/'scenario_registry.json').write_text(json.dumps(registry,indent=2,allow_nan=False))
    return summary, registry

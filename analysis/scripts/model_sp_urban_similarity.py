"""Versioned, immutable SP model release, including prespecified robustness experiments."""
import argparse
import fcntl
import json
import re
import shutil
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from sp_model.inputs import freeze_inputs, hash_file
from sp_model.transforms import fit_transform_scalars, apply_scalar_transforms, transform_composition
from sp_model.distances import compute_distances, build_embedding, rank_target, normalized_weights
from sp_model.sensitivity import run_sensitivities


def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False))


def run_model(config_path=None, output_root=None):
    base=Path(__file__).resolve().parent.parent
    config_path=Path(config_path) if config_path else base/'config/sp_urban_model_v2.json'
    config,raw,manifest=freeze_inputs(config_path,base)
    run_id=config['run_id']
    if not re.fullmatch(r'[A-Za-z0-9_-]+',run_id):raise ValueError('Unsafe run ID')
    # --output-root isolates verification builds; normal outputs follow the documented layout.
    work=(Path(output_root)/'work'/run_id if output_root else base/'work/runs'/run_id)
    release=(Path(output_root)/'results'/run_id if output_root else base/'results/SP/models'/run_id)
    work.mkdir(parents=True,exist_ok=True)
    lock=(work/'runner.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    signature=__import__('hashlib').sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    manifest['signature']=signature
    mf=work/'metadata/manifest.json'
    if mf.exists():
        old=json.loads(mf.read_text())
        if old['signature']!=signature:raise ValueError('Inputs/config/code/environment changed: choose a new run ID')
        if (work/'progress.json').exists() and json.loads((work/'progress.json').read_text())['status']=='complete':
            inv=json.loads((work/'metadata/output_inventory.json').read_text())
            for root,items in [(work,inv['work']),(release,inv['release'])]:
                for name,digest in items.items():
                    if not (root/name).is_file() or hash_file(root/name)!=digest:raise ValueError('Completed run was modified: '+name)
            print('Verified complete run:',release,flush=True);return release
    elif any(p.name!='runner.lock' for p in work.iterdir()) or release.exists():
        raise ValueError('Refuse to overwrite an unrecognized existing run')
    dump(mf,manifest);dump(work/'progress.json',{'status':'running','stage':'primary'})
    try:
        df=raw.set_index('district_id');ids=df.index.tolist();target=config['target_district_id']
        ss,params=fit_transform_scalars(df,config);cc=transform_composition(df,config)
        D,mats,cal,contrib=compute_distances(ss,cc,config)
        E=build_embedding(ss,cc,config,cal)
        independent=np.sqrt(np.square(E.values[:,None,:]-E.values[None,:,:]).sum(2))
        assert np.allclose(D,independent,rtol=1e-12,atol=1e-12)
        assert np.allclose(sum(contrib.values()),D**2) and np.isfinite(D).all()
        assert np.allclose(D,D.T) and np.allclose(np.diag(D),0)
        assert all(np.all(D<=D[:,k,None]+D[k,None,:]+1e-10) for k in range(len(D)))
        assert np.allclose(ss,apply_scalar_transforms(df,json.loads(json.dumps(params))))
        tables=release/'tables';tables.mkdir(parents=True,exist_ok=True)
        (work/'intermediates').mkdir(exist_ok=True)
        rank=rank_target(D,ids,target).merge(raw[['district_id','district_name']],on='district_id',validate='one_to_one')
        rank.to_csv(tables/'bras_ranking.csv',index=False)
        pd.DataFrame(D,index=pd.Index(ids,name='district_id'),columns=ids).to_csv(tables/'pairwise_distances.csv')
        E.to_parquet(work/'intermediates/embedding.parquet');ss.to_parquet(work/'intermediates/scalar_coordinates.parquet');cc.to_parquet(work/'intermediates/composition_coordinates.parquet')
        np.savez_compressed(work/'intermediates/family_squared_distances.npz',**mats)
        dump(work/'metadata/fitted_state.json',dict(params=params,calibrations=cal,weights=normalized_weights(config),
                                                   embedding_columns=E.columns.tolist(),district_ids=ids,composition_adjustments=cc.attrs['max_sum_adjustments']))
        b=ids.index(target);rows=[]
        for f,c in contrib.items():
            for i,id in enumerate(ids):rows.append(dict(district_id=id,family=f,squared_distance_contribution=float(c[b,i]),
                                                        contribution_fraction=float(c[b,i]/D[b,i]**2) if D[b,i]>0 else None))
        pd.DataFrame(rows).to_csv(tables/'family_contributions.csv',index=False)
        profiles=[]
        coords=pd.concat([ss,cc],axis=1)
        for col in coords:
            for id in ids:profiles.append(dict(district_id=id,feature=col,raw_value=float(df.loc[id,col]),
                                               bras_raw_value=float(df.loc[target,col]),coordinate_difference=float(coords.loc[id,col]-coords.loc[target,col])))
        pd.DataFrame(profiles).to_csv(tables/'profiles.csv',index=False)
        # Actual quality metadata are carried alongside numerical scores, never used as hidden weights.
        long=pd.read_parquet(base/config['paths']['long_attributes'])
        long.loc[long.primary_feature,['district_id','family_id','feature_name','coverage_fraction','coverage_definition','quality_status','n_entities','n_missing']].to_csv(tables/'quality_annotations.csv',index=False)
        wide=pd.read_parquet(base/config['paths']['wide_attributes']).set_index('district_id')
        groups=None
        if 'district_groups' in config['paths']:
            group=pd.read_csv(base/config['paths']['district_groups'],dtype=str)
            if len(group)!=96 or not group.district_id.is_unique or set(group.district_id)!=set(ids) or group.subprefeitura_id.isna().any() or group.subprefeitura_id.nunique()!=32:raise ValueError('Invalid subprefeitura crosswalk')
            groups=group.set_index('district_id').subprefeitura_id
        dump(work/'progress.json',{'status':'running','stage':'sensitivities'})
        summary,registry=run_sensitivities(df,wide,config,params,cal,D,E,work/'scenarios',groups)
        failed=[x for x in registry if x['status']=='failed']
        if failed:raise ValueError('Failed scenarios: '+str([(x['name'],x['error']) for x in failed]))
        for name in ['scenario_summary.csv','scenario_rankings.csv','weight_stability.csv','pca_loadings.csv','pca_variance.csv']:
            shutil.copy2(work/'scenarios'/name,tables/name)
        dump(release/'validation/scenario_registry.json',[{k:v for k,v in x.items() if k not in ['config','fitted_params','calibrations']} for x in registry])
        geo=gpd.read_file(base/config['paths']['district_geometry'])[['district_id','geometry']].merge(rank,on='district_id',how='left',validate='one_to_one')
        geo.loc[geo.district_id.eq(target),['distance','rank']]=[0,0]
        geo.loc[geo.district_id.eq(target),'district_name']=raw.set_index('district_id').loc[target,'district_name']
        (release/'spatial').mkdir(exist_ok=True)
        geo.to_file(release/'spatial/district_similarity.gpkg',layer='similarity',driver='GPKG')
        reloaded=gpd.read_file(release/'spatial/district_similarity.gpkg')
        assert len(reloaded)==96 and reloaded.crs.to_epsg()==31983 and reloaded.is_valid.all()
        assert np.allclose(reloaded.set_index('district_id').loc[ids,'distance'],D[b])
        # Source files must be identical after the run.
        assert all(hash_file(base/v['path'])==v['sha256'] for v in manifest['inputs'].values())
        validation=dict(primary_invariants_passed=True,source_hashes_unchanged=True,scenario_count=len(summary),failed_scenarios=failed,
                        deferred=[x for x in registry if x['status']=='deferred'],geopackage_valid=True)
        dump(release/'validation/checks.json',validation)
        from sp_model.reporting import report
        report(release,config,rank,summary,validation)
        dump(work/'progress.json',{'status':'complete','stage':'released','signature':signature})
        inventory={}
        for label,root in [('work',work),('release',release)]:
            inventory[label]={str(p.relative_to(root)):hash_file(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name not in ('runner.lock','output_inventory.json')}
        dump(work/'metadata/output_inventory.json',inventory)
        print('Completed corrected SP release:',release,flush=True)
        print(rank.head(10).to_string(index=False),flush=True)
        return release
    except Exception as e:
        dump(work/'progress.json',{'status':'failed','error':str(e),'signature':signature});raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--output-root',type=Path)
    a=p.parse_args();run_model(a.config,a.output_root)

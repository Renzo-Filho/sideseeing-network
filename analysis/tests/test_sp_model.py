"""Mathematical regression tests for model review findings; no production writes."""
import copy
import json
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sp_model.transforms import fit_transform_scalars,apply_scalar_transforms,transform_composition
from sp_model.distances import compute_distances,build_embedding,rank_target


def fixture():
    frame=pd.DataFrame({'x':[1.,2,2,2,9],'a':[1.,.5,0,.3,.7],'b':[0.,.5,1,.7,.3]},index=pd.Index(['01','02','03','04','05'],name='district_id'))
    config={'families':{'A':{'type':'scalar','columns':['x'],'transform':'log','weight':1.},'C':{'type':'composition','columns':['a','b'],'weight':1.}},'scaling':{'method':'robust_median_iqr','fallback_to_sd_tolerance':1e-12}}
    return frame,config


class ModelInvariants(unittest.TestCase):
    def calculate(self,df,cfg):
        ss,p=fit_transform_scalars(df,cfg);cc=transform_composition(df,cfg)
        return ss,p,cc,compute_distances(ss,cc,cfg)

    def test_embedding_contributions_and_geometry(self):
        df,cfg=fixture();ss,p,cc,(d,r,b,c)=self.calculate(df,cfg)
        e=build_embedding(ss,cc,cfg,b).values
        np.testing.assert_allclose(d,np.linalg.norm(e[:,None,:]-e[None,:,:],axis=2),atol=1e-12)
        np.testing.assert_allclose(d*d,sum(c.values()),atol=1e-12)
        self.assertEqual(r['C'][0,2],1.)
        self.assertTrue(np.allclose(np.diag(d),0))
        for k in range(5):self.assertTrue(np.all(d<=d[:,k,None]+d[k,None,:]+1e-12))

    def test_sd_fallback_and_saved_state(self):
        df,cfg=fixture();ss,p=fit_transform_scalars(df,cfg)
        self.assertTrue(p['x']['used_sd_fallback'])
        np.testing.assert_allclose(ss,apply_scalar_transforms(df,json.loads(json.dumps(p))))

    def test_invalid_scalar_domains(self):
        for value in [0,-1,np.inf,np.nan]:
            df,cfg=fixture();df.loc['01','x']=value
            with self.assertRaises(ValueError):fit_transform_scalars(df,cfg)

    def test_composition_absolute_tolerance(self):
        df,cfg=fixture();df.loc['01',['a','b']]*=1.000001
        with self.assertRaises(ValueError):transform_composition(df,cfg)
        df,cfg=fixture();df.loc['01',['a','b']]*=1+1e-9
        out=transform_composition(df,cfg);np.testing.assert_allclose((out**2).sum(1),1)
        for values in [(-.1,1.1),(0,0),(np.inf,0)]:
            df,cfg=fixture();df.loc['01',['a','b']]=values
            with self.assertRaises(ValueError):transform_composition(df,cfg)

    def test_relative_weights_and_invalid_weights(self):
        df,cfg=fixture();ss,p,cc,(d,*_)=self.calculate(df,cfg)
        doubled=copy.deepcopy(cfg)
        for f in doubled['families'].values():f['weight']*=2
        np.testing.assert_allclose(d,compute_distances(ss,cc,doubled)[0])
        for value in [-1,np.nan,np.inf]:
            bad=copy.deepcopy(cfg);bad['families']['A']['weight']=value
            with self.assertRaises(ValueError):compute_distances(ss,cc,bad)
        zero=copy.deepcopy(cfg)
        for f in zero['families'].values():f['weight']=0
        with self.assertRaises(ValueError):compute_distances(ss,cc,zero)

    def test_index_alignment_permutation_duplicates(self):
        df,cfg=fixture();ss,p,cc,(d,*_)=self.calculate(df,cfg)
        with self.assertRaises(ValueError):compute_distances(ss,cc.iloc[::-1],cfg)
        ss2,p2,cc2,(d2,*_)=self.calculate(df.iloc[::-1],cfg)
        np.testing.assert_allclose(d2,d[::-1,::-1])
        bad=copy.deepcopy(cfg);bad['families']['A']['columns']=['x','x']
        with self.assertRaises(ValueError):compute_distances(ss,cc,bad)

    def test_frozen_fit_is_not_mutated(self):
        df,cfg=fixture();ss,p,cc,(d,r,b,c)=self.calculate(df,cfg);before=json.dumps([p,b],sort_keys=True)
        changed=df.copy();changed['x']*=3
        new=apply_scalar_transforms(changed,p)
        compute_distances(new,cc,cfg,calibrations=b)
        self.assertEqual(before,json.dumps([p,b],sort_keys=True))

    def test_constant_family_rejected(self):
        df,cfg=fixture();df['x']=1
        ss,p=fit_transform_scalars(df,cfg);self.assertFalse(p['x']['retained'])
        with self.assertRaises(ValueError):compute_distances(ss,transform_composition(df,cfg),cfg)

    def test_tied_rank_and_id_order(self):
        d=np.array([[0,1,1],[1,0,2],[1,2,0]],float)
        ranked=rank_target(d,['10','02','01'],'10')
        self.assertEqual(ranked.district_id.tolist(),['01','02']);self.assertEqual(ranked['rank'].tolist(),[1,1])


class SourceContract(unittest.TestCase):
    def test_current_release_passes_contract(self):
        from sp_model.inputs import freeze_inputs
        base=Path(__file__).resolve().parents[1]
        cfg,df,manifest=freeze_inputs(base/'config/sp_urban_model_v2.json',base)
        self.assertEqual(len(df),96);self.assertEqual(len(manifest['selected_columns']),23)
        self.assertIn('code',manifest);self.assertIn('scikit-learn',manifest['environment'])

    def test_duplicate_selection_and_invalid_ids_fail_before_writes(self):
        import tempfile
        from sp_model.inputs import freeze_inputs
        base=Path(__file__).resolve().parents[1]
        config=json.loads((base/'config/sp_urban_model_v2.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for key,rel in config['paths'].items():
                dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True)
                if key=='primary_attributes':dst.write_bytes((base/rel).read_bytes())
                else:dst.symlink_to(base/rel)
            conf=root/'config.json'
            bad=copy.deepcopy(config);bad['families']['M1']['columns']=['population_density_km2']
            conf.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):freeze_inputs(conf,root)
            conf.write_text(json.dumps(config))
            p=root/config['paths']['primary_attributes'];df=pd.read_csv(p,dtype={'district_id':str});df.loc[0,'district_id']='99';df.to_csv(p,index=False)
            with self.assertRaises(ValueError):freeze_inputs(conf,root)
            df.loc[0,'district_id']='01';df.loc[0,'street_density_km_km2']=np.inf;df.to_csv(p,index=False)
            with self.assertRaises(ValueError):freeze_inputs(conf,root)

if __name__=='__main__':unittest.main()

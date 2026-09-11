"""Isolated, checkpointed N01–N09 preparation. Does not construct attributes."""
import argparse,hashlib,importlib,importlib.metadata,json,sys,traceback,fcntl
from pathlib import Path
from sp_v3 import common as C
STAGES=[('N02','geography','land'),('N03','fiscal','fiscal'),('N04','network','classes'),('N05','network','topology'),('N06','geography','buildings_blocks'),('N07','demography','demography'),('N08','transit','transit'),('N09','acceptance','acceptance')]

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',default=str(C.ROOT/'analysis/config/sp_preparation_v3.json'));p.add_argument('--stages',nargs='*');args=p.parse_args();C.initialize(args.config)
 lock=(C.OUT/'runner.lock').open('a')
 try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise RuntimeError('Another v3 runner is active in this run directory')
 if args.stages and not set(args.stages)<=set(x[0] for x in STAGES):p.error('Unknown stage')
 source=[{'path':str(f.relative_to(C.ROOT)),'bytes':f.stat().st_size,'sha256':C.sha(f)} for f in sorted(C.RAW.rglob('*')) if f.is_file()]
 fingerprint=hashlib.sha256(json.dumps([source,C.CFG],sort_keys=True).encode()).hexdigest()
 freeze=C.OUT/'N01/manifest.json'
 if freeze.exists() and json.loads(freeze.read_text())['fingerprint']!=fingerprint:raise ValueError('Input/config changed: use a new run_id to preserve this run')
 if not freeze.exists():
  baseline={str(f.relative_to(C.BASE)):C.sha(f) for f in sorted(C.BASE.rglob('*')) if f.is_file()}
  C.dump(freeze,{'fingerprint':fingerprint,'sources':source,'config':C.CFG,'baseline_hashes':baseline,'packages':{n:importlib.metadata.version(n) for n in ['duckdb','geopandas','shapely','pyogrio','pyproj','pandas','pyarrow']}})
 C.log('N01: isolated manifest ready')
 status=C.OUT/'progress.json';progress=json.loads(status.read_text()) if status.exists() else {'run_id':C.CFG['run_id'],'completed':[],'attribute_construction_started':False,'model_fitted':False}
 for stage,module,fn in STAGES:
  if args.stages and stage not in args.stages:continue
  mod=importlib.import_module('sp_v3.'+module);func=getattr(mod,fn)
  dependencies={'N04':['N02'],'N05':['N04'],'N06':['N02'],'N07':['N02','N03'],'N08':['N02'],'N09':['N02','N03','N04','N05','N06','N07','N08']}.get(stage,[])
  dependency_hash=''.join(C.sha(C.OUT/k/'checkpoint.json') for k in dependencies)
  signature=hashlib.sha256((fingerprint+C.sha(mod.__file__)+C.sha(C.__file__)+dependency_hash).encode()).hexdigest();checkpoint=C.OUT/stage/'checkpoint.json'
  if checkpoint.exists():
   q=json.loads(checkpoint.read_text())
   if q['signature']==signature and all((C.OUT/k).is_file() and C.sha(C.OUT/k)==v for k,v in q['outputs'].items()):
    C.log(stage+': checkpoint reused');continue
  C.log(stage+': starting');progress['running']=stage;C.dump(status,progress)
  try:
   (C.OUT/stage).mkdir(exist_ok=True);func()
   outputs={str(f.relative_to(C.OUT)):C.sha(f) for f in sorted((C.OUT/stage).rglob('*')) if f.is_file() and f.name!='checkpoint.json'}
   C.dump(checkpoint,{'signature':signature,'outputs':outputs})
   if stage not in progress['completed']:progress['completed'].append(stage)
   progress['running']=None;C.dump(status,progress);C.log(stage+': executed; see QA acceptance flags')
  except Exception:
   progress['error']=traceback.format_exc();C.dump(status,progress);raise
 old=json.loads(freeze.read_text())['baseline_hashes'];assert all(C.sha(C.BASE/k)==v for k,v in old.items())
 progress.pop('error',None);progress['baseline_unchanged']=True;C.dump(status,progress)
if __name__=='__main__':main()

"""One-time, content-preserving folder migration; legacy paths remain resolvable."""
from pathlib import Path
import hashlib,json,os,shutil,re
A=Path(__file__).resolve().parents[1]
record=A/'work/organization_manifest.json'
if record.exists():
 print('Already organized; see',record);raise SystemExit(0)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
original={str(p.relative_to(A)):sha(p) for root in ['outputs','processed'] for p in (A/root).rglob('*') if p.is_file()}
moves=[]
def move(src,dst,link=True):
 dst.parent.mkdir(parents=True,exist_ok=True)
 assert not dst.exists(),dst
 src.rename(dst)
 if link:src.symlink_to(os.path.relpath(dst,src.parent),target_is_directory=dst.is_dir())
 moves.append({'from':str(src.relative_to(A)),'to':str(dst.relative_to(A))})
move(A/'outputs',A/'.compat/outputs')
move(A/'processed',A/'work/prepared')
evidence={'sp_audit':'source_inventory','sp_readiness_2026_09_09':'historical_readiness','sp_resolution_review_2026_09_10':'data_resolution','sp_simplification_review_2026_09_10':'road_classification_and_crossings','sp_allocation_experiments_2026_09_10':'job_allocation_experiments'}
for old,new in evidence.items():move(A/'.compat/outputs'/old,A/'work/evidence'/new)
runid='sp_attributes_2026_09_11_v1'
move(A/'.compat/outputs/sp_attributes'/runid,A/'work/runs'/runid)
run=A/'work/runs'/runid;results=A/'results/SP';locations={}
for f in list(run.iterdir()):
 if not f.is_file():continue
 name=f.name
 if name.startswith('attributes_') or name=='attribute_dictionary.csv':dest=results/'tables'/name
 elif f.suffix=='.gpkg':dest=results/'spatial'/name
 elif f.suffix=='.png':dest=results/'figures'/name
 elif name in ['outlier_review.csv','quality_status_summary.csv','primary_feature_summary.csv','population_support_qa.csv']:dest=results/'validation/tables'/name
 elif name in ['validation.json','pilot_validation.json','release_review.json','delivery_checks.json']:dest=results/'validation/checks'/name
 else:continue
 move(f,dest);locations[name]=dest
# Preserve the hash-bound original report; publish a reader copy with working links.
report=(run/'REPORT.md').read_text()
def target(m):
 t=m.group(1)
 if t in locations:return ']('+os.path.relpath(locations[t],results/'reports')+')'
 candidate=run/t
 if '://' not in t and candidate.exists():return ']('+os.path.relpath(candidate,results/'reports')+')'
 return m.group(0)
report=re.sub(r'\]\(([^)]+)\)',target,report)
(results/'reports').mkdir(parents=True,exist_ok=True)
(results/'reports/ATTRIBUTE_REPORT.md').write_text(report)
# Byte-for-byte preservation is checked through every original path.
failed=[p for p,h in original.items() if not (A/p).is_file() or sha(A/p)!=h]
assert not failed,failed
record.write_text(json.dumps({'purpose':'Folder organization only; no numerical or methodological change','original_files_verified':len(original),'all_original_paths_and_bytes_preserved':True,'moves':moves,'original_sha256':original,'published_report':'results/SP/reports/ATTRIBUTE_REPORT.md','published_report_note':'Reader copy of frozen report with relocated links'},indent=2))
print('Organized; verified',len(original),'original files and legacy paths',flush=True)

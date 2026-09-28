"""Validate Firecrawl workbook table extracts and retain Chicago-linked records.
Original XLSX downloads returned 403; extraction does not prove binary completeness.
"""
from pathlib import Path
import csv,hashlib,json,re
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
RES=ROOT/'analysis/results/Chicago/chicago_workbooks_2026_09_19'
OUT=ROOT/'analysis/data/Chicago/chicago_workbooks_2026_09_19';OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'analysis/data/Chicago/chicago_cadastral_2026_09_18'
def pins(text):
 return {v.replace('-','') for v in re.findall(r'(?<![0-9])(?:[0-9]{2}-[0-9]{2}-[0-9]{3}-[0-9]{3}-[0-9]{4}|[0-9]{14})(?![0-9])',str(text))}
def norm(x):return re.sub('[^a-z0-9]','',x.lower())
def cells(s):return [v.strip().replace('\\|','|') for v in re.split(r'(?<!\\)\|',s.strip())[1:-1]]
keys=set()
for p in (BASE/'cook_parcels_2024').glob('*.parquet'):keys.update(pd.read_parquet(p,columns=['PIN10']).PIN10.astype(str).str.zfill(10))
files=json.load(open(RES/'extractions.json'));sheets=[];records=[];problems=[];inventory=[]
for item in files:
 p=ROOT/item['extraction_file'];data=json.load(open(p));lines=data['markdown'].splitlines();sheet='';headers=None;stats=None
 for number,line in enumerate(lines,1):
  if line.startswith('## '):
   sheet=line[3:].strip();headers=None;stats=None
  if not line.startswith('|'):continue
  values=cells(line)
  if 'keypin' in [norm(x) for x in values]:
   headers=values;stats={'file':Path(item['file']).name,'sheet':sheet,'headers':headers,'rows':0,'chicago_rows':0,'summary_or_split':bool(re.search('summary|splitclass',sheet,re.I)),'field_nonempty':{h:0 for h in headers}}
   sheets.append(stats);continue
  if headers is None or all(re.fullmatch(r'[:\- ]*',x) for x in values):continue
  if len(headers)!=len(values):problems.append({'file':item['file'],'sheet':sheet,'line':number,'reason':'column count mismatch'});continue
  raw=dict(zip(headers,values));fields={norm(k):v for k,v in raw.items()}
  related=pins(fields.get('keypin','')+' '+fields.get('iasworldpins',fields.get('pins','')))
  if not related:
   problems.append({'file':item['file'],'sheet':sheet,'line':number,'reason':'no recognizable PIN'});continue
  stats['rows']+=1;matches=sorted(x for x in related if x[:10] in keys)
  if not matches:continue
  stats['chicago_rows']+=1
  for h,v in raw.items():stats['field_nonempty'][h]+=bool(v)
  if stats['summary_or_split']:continue
  records.append({'source_url':item['url'],'source_file':Path(item['file']).name,'sheet':sheet,'source_markdown_line':number,'chicago_matched_pins':matches,'keypin':next(iter(pins(fields.get('keypin',''))),''),'has_related_pin_without_chicago_geometry':any(x[:10] not in keys for x in related),'fields':raw})
 inventory.append({**item,'extraction_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'original_binary_acquired':False})
with (OUT/'chicago_detail_records.jsonl').open('w') as f:
 for r in records:f.write(json.dumps(r)+'\n')
fields={}
for r in records:
 for h,v in r['fields'].items():
  if re.search('stor|floor|gross|bldg|building|rentable|height',h,re.I):
   x=fields.setdefault(h,{'rows_with_column':0,'nonempty':0});x['rows_with_column']+=1;x['nonempty']+=bool(v)
api=pd.concat([pd.read_parquet(p,columns=['keypin']) for p in (BASE/'cook_commercial_2024').glob('*.parquet')],ignore_index=True)
a=set().union(*(pins(x) for x in api.keypin));b={r['keypin'] for r in records}
report={'files':len(files),'property_tables':len(sheets),'detail_records':len(records),'unique_keypins':len(b),'parse_issues':problems,'all_retained_records_match_chicago':all(r['chicago_matched_pins'] and all(p[:10] in keys for p in r['chicago_matched_pins']) for r in records),'relevant_fields':fields,'api_comparison':{'api_rows':len(api),'api_unique_keypins':len(a),'common_keypins':len(a&b),'extract_only_keypins':len(b-a),'api_only_keypins':len(a-b)},'binary_completeness_verified':False,'notes':['Firecrawl markdown values; no formula, hidden-sheet or original binary validation.','Summary/split-class tables excluded from detail records to avoid obvious repeated listings; other duplicates remain possible.','Missing numeric values are not zero. Entity areas are not clipped to Chicago.']}
for n,d in [('workbook_register',inventory),('sheet_validation',sheets),('validation',report)]: (RES/(n+'.json')).write_text(json.dumps(d,indent=2)+'\n')
(OUT/'manifest.json').write_text(json.dumps({'source_register':str(RES/'workbook_register.json'),'rows':len(records),'filter':'Any associated normalized PIN10 in spatially validated Chicago Cook parcels','sha256':hashlib.sha256((OUT/'chicago_detail_records.jsonl').read_bytes()).hexdigest(),'source_kind':'Firecrawl XLSX markdown extracts; originals unavailable'},indent=2)+'\n')
print(json.dumps(report,indent=2))

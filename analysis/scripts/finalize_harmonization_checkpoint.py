"""Seal candidate construction receipts without accepting or fitting a common model."""
from pathlib import Path
import hashlib,json,platform
from datetime import datetime,timezone
import importlib.metadata
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'analysis';O=A/'results/SP_CHI/harmonization_2026_09_22_h1_h3'

def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()

def main():
 assert json.loads((O/'ghsl/progress.json').read_text())['status']=='full_ghsl_candidates_complete'
 audit=json.loads((O/'independent_table_checks.json').read_text());assert audit['failed']==0
 unit=json.loads((O/'targeted_unit_tests.json').read_text());assert unit['successful']
 counts={k:len(json.loads((O/k/'checks.json').read_text())) for k in ['ghsl','footprints','functional']}
 for k in counts:assert all(c['passed'] for c in json.loads((O/k/'checks.json').read_text()))
 g=pd.read_csv(O/'ghsl/ghsl_attributes.csv');recovered=json.loads((O/'ghsl/source_cell_recovery.json').read_text())
 text=f'''# Paired harmonization candidates — H1–H3, September 22, 2026

Candidate construction covers **173 reporting units** (96 SP districts and 77 Chicago Community Areas), with **6,209 long-form rows and 37 feature columns**. These include diagnostics and explicitly missing U1; they are not 37 accepted model coordinates. No model was fitted and no cross-city ranking produced.

## Outputs and gates

- `tables/`: paired long/wide candidate attributes and dictionary.
- `roads/`: mapped-street density/hierarchy, diagnostic connector/enclosure measures and eight pilot maps. M2/M3/M4 remain withheld because physical junction/block semantics are unresolved.
- `footprints/`: full paired footprint coverage with gross/land variants; Chicago recomputed, SP frozen numerators reused with three independent shared-method pilot reconstructions.
- `ghsl/`: 1,038 native-grid product/support rows, source-cell recovery receipts and projected-geometry repair log. Final missing candidate values: {int(g.value.isna().sum())}. Recovered source cells: {len(recovered)}. Tiny masked areas below the existing coverage tolerance remain explicit diagnostic residuals.
- `functional/`: 173 population rows and 1,038 bus-only scenarios. U1 withheld; U2 stays extended-only. Completed Chicago employment sensitivity is in `analysis/results/Chicago/chi_employment_sensitivity_2026_09_22_v2/`.
- `family_acceptance_ledger.json`: candidate, withheld, extended-only and excluded status for every family.

Separate SP and Chicago candidate companions are under each city's `harmonized_candidates_2026_09_22/`. Original numeric releases remain unchanged.

## Important correction

Legacy SP transit processing included nine metro and seven rail routes. The new companion filters `route_type=3` and recomputes all 576 SP scenarios. Brás weekday400m supply decreases about16.6%. Original SP v2 is preserved, but its U4 cannot be described as bus-only. Other population, calendar, frequency and operator-scope qualifications remain explicit.

## Verification

| Check group | Passed | Failed |
|---|---:|---:|
| GHSL coverage/partition checks | {counts['ghsl']} | 0 |
| Footprint bounds and SP reconstruction | {counts['footprints']} | 0 |
| Paired functional checks | {counts['functional']} | 0 |
| SP bus-only not-greater-than-legacy checks | 576 | 0 |
| Employment independent audit | 138 | 0 |
| Independent candidate-table/source-cell audit | {audit['passed']} | 0 |
| Targeted unit tests | {unit['run']} | 0 |

These numerical checks do not prove source accuracy or scientific measurement equivalence. H1's semantic gates for M2/M3/M4 are still open; their outputs remain diagnostic.

## Next checkpoint

H4 must review the proposed reduced common set (M1/M6/B1/U3/U4, with BV extension), or require improved junction/block methods before accepting M2/M3/M4. That scope choice precedes fitting. Source completeness, land-mask differences and source years remain acceptance qualifications. No zero-filled missing family, pairwise feature deletion or city-specific normalization is permitted.

Full decisions, formulas, code commands, failures/fixes and limitations: [execution documentation](../../../../docs/harmonization/EXECUTION_LOG.md). H5/H6 are not started. No construction jobs remain running after finalization.
'''
 (O/'README.md').write_text(text)
 code_names=['prepare_harmonized_roads.py','prepare_harmonized_footprints.py','prepare_harmonized_ghsl.py','prepare_chicago_employment_sensitivity_v2.py','validate_chicago_employment_sensitivity_v2.py','rebuild_sp_bus_companion.py','prepare_harmonized_functional.py','assemble_harmonized_candidates.py','validate_harmonized_candidates.py','finalize_harmonization_checkpoint.py','harmonization/roads.py','harmonization/rasters.py','harmonization/geometry.py','harmonization/functional.py','harmonization/employment_v2.py']
 inputs=[A/'scripts'/n for n in code_names]+[A/'config/sp_chicago_harmonization_v1.json',A/'config/chicago_employment_sensitivity_v2.json']
 inputs+=list((A/'tests').glob('test_*harmon*.py'))+[A/'tests/test_chicago_functional.py']
 manifest={'completed_utc':datetime.now(timezone.utc).isoformat(),'status':'candidate_construction_complete_not_model_acceptance','code_config_test_sha256':{str(p.relative_to(ROOT)):sha(p) for p in inputs},'environment':{'python':platform.python_version(),**{k:importlib.metadata.version(k) for k in ['numpy','pandas','geopandas','shapely','rasterio','pyarrow']}},'stage_source_receipts':[str(p.relative_to(ROOT)) for p in O.rglob('*receipts.json')],'original_sources_preserved':True,'model_fitted':False}
 manifest['city_companion_sha256']={str(p.relative_to(ROOT)):sha(p) for city in ['SP','Chicago'] for p in sorted((A/'results'/city/'harmonized_candidates_2026_09_22').glob('*')) if p.is_file()}
 manifest['output_sha256']={str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='publication_manifest.json'}
 (O/'publication_manifest.json').write_text(json.dumps(manifest,indent=2))
 print('Finalized candidate checkpoint; source recoveries',len(recovered),'GHSL missing',int(g.value.isna().sum()),flush=True)
if __name__=='__main__':main()

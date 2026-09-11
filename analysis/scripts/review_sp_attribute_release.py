"""Independent release review, documentation and artifact inventory for N10."""
from pathlib import Path
import json,hashlib,shutil
import pandas as pd,numpy as np,geopandas as gpd
from sp_attributes import core as C

def main():
 R=C.OUT;f=pd.read_parquet(R/'attributes_long.parquet');v=json.loads((R/'validation.json').read_text());primary=f.loc[f.primary_feature];qa=[]
 def check(name,passed):
  qa.append({'check':name,'passed':bool(passed)})
  if not passed:raise AssertionError(name)
 check('96 by 77 unique feature grid',len(f)==96*77 and not f.duplicated(['district_id','feature_name']).any())
 check('Whole eligible blocks reconciled',f.loc[f.feature_name.eq('block_log_area_median'),'n_entities'].sum()==46798)
 check('Canonical cadastral entities reconciled',f.loc[f.feature_name.eq('cadastral_parcel_density_km2'),'numerator'].sum()==1667297)
 check('Eligible floor profiles reconciled',f.loc[f.feature_name.eq('cadastral_floor_count_median'),'n_entities'].sum()==1548308)
 check('Compactness bounds',f.loc[f.feature_name.eq('block_compactness_median'),'value'].between(0,1).all())
 check('Elongation lower bound',f.loc[f.feature_name.eq('block_elongation_median'),'value'].ge(1).all())
 for w in ['weekday_am','saturday_am','sunday_am']:
  a=f.loc[f.feature_name.eq(f'bus_service_access_{w}_400m')].set_index('district_id').value;b=f.loc[f.feature_name.eq(f'bus_service_access_{w}_800m')].set_index('district_id').value;check(w+' larger radius monotonicity',b.ge(a-1e-9).all())
 # Independent identity-level check of population-support masses and service averaging.
 pop=pd.read_parquet(C.BASE/'N07/census_district_allocation.parquet').groupby('district_id').population_allocated.sum();support_counts=[]
 for code in C.districts().district_id:
  p=gpd.read_parquet(R/'intermediates'/f'population_points_{code}.parquet');q=pd.read_parquet(R/'intermediates'/f'point_service_{code}.parquet')
  assert np.isclose(p.population_weight.sum(),pop.loc[code],rtol=1e-9,atol=.01)
  assert p.point_id.is_unique and not q.duplicated(['point_id','window','radius_m']).any()
  assert len(q)==len(p)*6 and np.allclose(q.groupby(['window','radius_m']).population_weight.sum(),pop.loc[code])
  s=q.loc[q.window.eq('weekday_am')&q.radius_m.eq(400)];value=float((s.population_weight*s.expected_route_direction_supply).sum()/s.population_weight.sum());stored=float(f.loc[f.district_id.eq(code)&f.feature_name.eq('bus_service_access_weekday_am_400m'),'value'].iloc[0]);assert np.isclose(value,stored)
  support_counts.append({'district_id':code,'population_points':len(p),'population_weight':p.population_weight.sum()})
 check('All 96 population supports conserve mass and reconstruct U4',True);pd.DataFrame(support_counts).to_csv(R/'population_support_qa.csv',index=False)
 # Verify raw and both historical prepared runs remain unchanged, using their frozen manifests.
 m=json.loads((C.BASE/'N01/manifest.json').read_text())
 check('v2 baseline unchanged',all(C.sha(C.OLD/k)==x for k,x in m['baseline_hashes'].items()))
 check('Raw SP files unchanged',all(C.sha(C.ROOT/x['path'])==x['sha256'] for x in m['sources']))
 for cp in sorted(C.BASE.glob('N*/checkpoint.json')):
  data=json.loads(cp.read_text());check(cp.parent.name+' prepared files unchanged',all(C.sha(C.BASE/k)==x for k,x in data['outputs'].items()))
 # Outliers are review candidates, not automatic exclusions. No fitted transformation/ranking.
 rows=[]
 for name,part in primary.groupby('feature_name'):
  q=part.value.quantile([.25,.5,.75]);iqr=q.loc[.75]-q.loc[.25]
  for row in part.itertuples():
   if iqr>0 and (row.value<q.loc[.25]-3*iqr or row.value>q.loc[.75]+3*iqr):rows.append({'district_id':row.district_id,'feature_name':name,'value':row.value,'median':q.loc[.5],'iqr':iqr,'flag':'outside Q1-3IQR to Q3+3IQR; review, do not automatically delete'})
 pd.DataFrame(rows,columns=['district_id','feature_name','value','median','iqr','flag']).to_csv(R/'outlier_review.csv',index=False)
 summary=primary.groupby(['family_id','feature_name']).value.agg(['min','median','max','nunique']);summary.to_csv(R/'primary_feature_summary.csv')
 quality=f.groupby(['family_id','quality_status']).size().rename('rows').reset_index();quality.to_csv(R/'quality_status_summary.csv',index=False)
 C.dump(R/'release_review.json',{'checks':qa,'all_passed':True,'raw_outlier_flags':len(rows),'primary_constant_columns':[str(x) for x in summary.loc[summary['nunique'].eq(1)].index],'model_fitted':False})
 # Human-readable release report with enough provenance for continuation.
 family=primary.groupby('family_id').feature_name.nunique().to_dict();pilot=pd.read_parquet(R/'pilot_attributes_long.parquet');sens=pd.read_csv(R/'population_support_sensitivity/comparison.csv',dtype={'district_id':str});sens=sens.loc[sens.feature_name.eq('bus_service_access_weekday_am_400m')]
 def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n'
 text=f'''# São Paulo district attributes — N10 construction report

Run `{C.CFG['run_id']}`, completed 11 September 2026. The user authorized construction after approving M2/M6 and accepting the recommended U2 policy. This release contains **96 districts, 77 attributes/diagnostics/sensitivity columns, and 23 primary candidate columns across 13 families**. M5/U5 are excluded. The long table has **7,392 rows**. No similarity model, fitted scaling, PCA or ranking has been produced.

## Deliverables and use

- [attributes_long.parquet](attributes_long.parquet) and [CSV](attributes_long.csv): one district/feature row with value, unit, numerator, denominator, source version/period, coverage definition, entity/missing counts, method, quality status and primary flag.
- [attributes_wide.csv](attributes_wide.csv) / [Parquet](attributes_wide.parquet): all 77 numeric columns plus district ID/name.
- [attributes_primary.csv](attributes_primary.csv): 23 raw primary candidate columns plus ID/name. These are not scaled model inputs; the six M6 shares sum to one and must be handled compositionally or have one redundant column removed during modeling.
- [attribute_dictionary.csv](attribute_dictionary.csv): family, units, primary flag and method/coverage definitions.
- [sao_paulo_district_attributes.gpkg](sao_paulo_district_attributes.gpkg): 96 district geometries and all numeric columns, EPSG:31983.
- [validation.json](validation.json), [release_review.json](release_review.json), [primary_feature_summary.csv](primary_feature_summary.csv), [outlier_review.csv](outlier_review.csv), and [quality_status_summary.csv](quality_status_summary.csv).

Read district IDs as strings, e.g. `pd.read_csv(path, dtype={{"district_id": str}})`, to preserve leading zeros. Join metadata from the long table; the numeric-only wide tables cannot express source limitations by themselves.

## Family definitions implemented

'''
 definitions={'M1':'Canonical source street length / gross district area; source carriageways retained; shared boundary length owned once by ascending district ID.','M2':'Selected three-arm planar nodes farther than 5 m from PONTE/VIADUTO/TUNEL / gross area. Other distances are sensitivity columns.','M3':'Whole Quadra block area distributions; primary median and IQR of natural-log area.','M4':'Median/IQR of 4πA/P² compactness (holes included in perimeter) and minimum-rectangle elongation.','M6':'Observed and model street-class shares; all unclassified Local. Imputed share retained.','M7':'Unique accepted cadastral entity count / gross area; whole-parcel log-area diagnostics.','B1':'Footprint union clipped to land / land area; gross-area and overlap-excess diagnostics.','B2':'Median/P90 of one eligible positive cadastral floor report per entity; P75 and missing coverage retained.','B3':'Unique fiscal-unit constructed-area sum / land area; no ideal-fraction reapplication.','U1':'Fixed-seven-category entropy and shares; entity-count primary, entity-land-area sensitivity; unknowns excluded from entropy with coverage retained.','U2':'area_first allocated RAIS job links / gross area; 508,844 unlocated jobs kept outside primary district totals. Nine alternative scenarios retained.','U3':'Area-allocated census population / gross area; outside municipal residual retained.','U4':'Population-weighted expected bus supply, maximum reachable stop service per route/direction then sum; 400 m weekday primary, 800 m and weekend sensitivities.'}
 text+=table(['Family','Primary columns','Implemented measure'],[(k,family[k],definitions[k]) for k in C.CFG['active_families']])
 text+='''
## Construction, issues and tests

Preparation is frozen in `sp_prep_2026_09_10_v3`; approved M2/M6 overlays and U2 experiment allocations are bound in the construction config. Original raw data and both historical preparation runs were verified unchanged. The runner validated Brás, Itaim Bibi and Grajaú first, then computed all districts. Per-district building/access outputs are checkpointed; source/config changes require a new run ID.

B1 reads the existing indexed Overture GeoPackage, not another cloud download. Within each district, exact footprint intersections are unioned inside disjoint 2 km tiles and summed; clipping to land excludes water. This prevents overlapping footprint polygons from inflating coverage. Footprints are selected spatially, not only from the district owning their whole-object ID, so cross-boundary footprints contribute their actual clipped area.

U4 intersects a fixed 250 m metric grid (origin 0,0) with each census sector and district. Each nonempty piece receives a within-polygon representative point and population proportional to its share of source-sector area. This conserves district allocated population but assumes uniform distribution within sectors. Stops outside the reporting district remain eligible. Frequency-based service is expected service from the prepared GTFS scenarios, not passenger counts or a walking-network route calculation.

Two implementation errors were caught before release: GeoPandas' `.length` property bypassed a same-named clipped-length column, causing M6 shares not to sum to one; explicit column indexing corrected it. GEOS also rejected mixed point/line boundary differences; filtering zero-dimensional contacts before line subtraction corrected the dimension issue without removing measurable street length. The final citywide audit initially differed by 40.00085 m: two source edges retrace 40.00088 m of their own linework. Polygon intersection removes these duplicate traversals, whereas the optimized audit initially measured untouched interior lines. Normalizing each non-simple source edge independently aligns the audit with geometric length, while retaining separate source edges/carriageways. The district attributes required no numerical change; the independent audit now reconciles within centimetre tolerance.

Five synthetic tests passed: square/rectangle area and shape, entropy bounds and missing mass, footprint union conservation across tiles, shared-boundary point/line handling, and self-retraced edge normalization. Release checks cover complete/unique district-feature keys, finite values and positive denominators, fraction/entropy bounds, U1/M6 share sums, projected valid GeoPackage geometry, extensive numerators, larger-radius monotonicity and all 96 population-support reconstructions. Outlier flags identify extreme source/proxy values for review, not grounds for automatic deletion.

## Conservation and pilot results

'''
 text+=table(['Quantity','Reconciled result'],[(k,f'{x:,.3f}') for k,x in v['citywide_numerators'].items()]);text+=f"\nIndependent clipped city street length: {v['street_length_conservation']['independent_city_clip_m']:,.3f} m; sum across districts: {v['street_length_conservation']['district_sum_m']:,.3f} m.\n\n"
 selected=['street_density_km_km2','intersection_density_proxy_5m_km2','building_coverage_land','cadastral_floor_count_p90','formal_job_density_area_first_km2','bus_service_access_weekday_am_400m'];pv=pilot.loc[pilot.feature_name.isin(selected)].pivot(index='feature_name',columns='district_id',values='value');text+=table(['Feature','Brás','Itaim Bibi','Grajaú'],[(x,*[f'{pv.loc[x,c]:,.4f}' for c in ['10','35','30']]) for x in selected]);text+='\n![Pilot attribute review](pilot_attribute_qa.png)\n\n'
 text+='A 125 m population-support refinement was tested in the pilots. It is a sensitivity reference, not ground truth:\n\n';text+=table(['District','U4 at 250 m support','U4 at 125 m support','Relative change'],[(x.district_id,f'{x.value_250m:.3f}',f'{x.value_125m:.3f}',f'{x.relative_change:.2%}') for x in sens.itertuples()])
 text+='''
## Distribution review

The review flags **38 district/feature pairs** outside Q1−3×IQR to Q3+3×IQR; no primary column is constant. Marsilac is flagged for log block-area median and dispersion. República and Sé are flagged for expected bus supply; Bela Vista and República for cadastral floor-area density; eight districts for formal-job density. Sparse street classes account for many remaining flags, so these flags are not evidence of bad records. Zero-IQR columns are skipped by this rule; their min/max and unique-value counts remain in the summary. No rows were removed, clipped or winsorized. Review these values alongside underlying source counts and U2 scenarios before selecting model transformations.

## Executed task ledger and recovery

1. **Bind accepted inputs.** Created the versioned N10 configuration and manifest from frozen v3 preparation, v2 parcel geometry, approved M2/M6 overlays and U2 experiments. Input hashes protect against silent source changes. Raw data and both prepared baselines passed the final preservation audit.
2. **Construct reusable parcel metrics.** Projected parcel geometry areas were materialized by district and joined to accepted unique entity keys and eligible fiscal profiles. Reconciled 1,667,297 entities and 1,548,308 eligible floor profiles. Fiscal area uses accepted unique accounts, with 581,313,100 m² conserved.
3. **Implement tabular district families.** Constructed M1/M2/M3/M4/M6/M7/B2/B3/U1/U2/U3, retaining numerators, denominators, entity counts, coverage definitions and sensitivity columns. Boundary-coincident streets have deterministic single ownership; whole blocks and cadastral entities use their prepared assignments.
4. **Implement footprint coverage.** Constructed B1 through indexed footprint reads, exact district/land clipping and tiled unions. Saved each district's union and summed-footprint diagnostics and a hash-checked feature checkpoint.
5. **Implement population-weighted bus access.** Constructed U4 with saved population points and per-point service outputs for six window/radius combinations. Independently reconstructed primary U4 and population totals in all 96 districts. Tested 125 m support in Brás, Itaim Bibi and Grajaú; retained the 250 m primary support.
6. **Pilot, then municipal execution.** Validated the three pilots before releasing all districts. Reused completed B1/U4 checkpoints while correcting street audit and entity metadata issues; tabular features were recomputed. The five synthetic tests and 20 independent release-review checks passed, alongside runner validations.
7. **Package and document.** Exported long/wide/primary tables, the feature dictionary and projected district GeoPackage. Reopened the GeoPackage to check all 96 valid geometries. Saved distribution/quality summaries, diagnostics, logs, code/output hashes and updated the current handoff, implementation plan and method decisions.

The complete run is recorded in `progress.json`. The two expensive modules have per-district checkpoints under `parts/`; recovery with the same configuration skips only hash-valid outputs. A changed source or attribute definition requires a new run ID. Code is in `analysis/scripts/sp_attributes/` and the entry point is `analysis/scripts/construct_sp_attributes.py`; the final review is `analysis/scripts/review_sp_attribute_release.py`. Frozen N05/N07 acceptance failures remain historical evidence of physical-connectivity/geolocation limitations and are not overwritten to make proxies appear measured.

## Interpretation and next step

All 13 families now have constructed values under their declared methods. That does not establish complete real-world coverage. B2/B3/U1/M7 are cadastral proxies; B1 reflects mapped footprints; M2 is a structure-exclusion proxy; M6 includes assumed Local classes; U2 is partially located and geographically modeled; U3/U4 rely on population allocation. B3 district completeness is unknown and explicitly null in the coverage field; its 97.3% citywide fiscal-source match must not be treated as all-building coverage. U2's 90.56% coverage is a citywide allocation fraction, not a measured per-district completeness rate. Some other coverage fields describe eligible source records only; read `coverage_definition`.

The primary matrix includes six dependent M6 class shares and families with different column counts. N11 must choose transformations, compositional handling, family weights and covariance regularization, review outliers and test sensitivity to U2 and other proxies before calculating Brás similarity. No unlocated jobs were silently assigned to the primary matrix. Chicago comparison, robustness-grid attributes and pedestrian accessibility outcomes remain later work.

## Reproduction and continuation

```bash
.venv/bin/python analysis/scripts/construct_sp_attributes.py --phase both
.venv/bin/python analysis/scripts/check_sp_population_support.py
.venv/bin/python analysis/scripts/plot_sp_attribute_qa.py
.venv/bin/python analysis/scripts/review_sp_attribute_release.py
```

Configuration: `analysis/config/sp_attributes_2026_09_11.json`; current method binding: `analysis/config/sp_current_methods.json`. The runner uses `parts/<module>/<district>/checkpoint.json`; completed building/access parts are reused only when code/config/input signatures and feature-file hashes match. Tabular features are recomputed on a rerun. Keep the original run immutable when changing definitions. The final release inventory records code and output hashes. For project history and issue/decision explanations, see `analysis/notes/SP_DATA_RESOLUTION_HANDOFF.md` and `SP_METHOD_DECISIONS.md`.
'''
 (R/'REPORT.md').write_text(text)
 logs=R/'logs';logs.mkdir(exist_ok=True)
 for name in ['sp-attributes-pilot.log','sp-attributes-pilot-fixed.log','sp-attributes-all.log','sp-attributes-all-fixed.log','sp-pop-support.log','sp-attributes-final-metadata.log','sp-attributes-final.log','sp-release-review.log']:
  src=Path('/tmp')/name
  if src.exists():shutil.copy2(src,logs/name)
 files=[p for p in R.rglob('*') if p.is_file() and p.name not in ['release_inventory.json','runner.lock']]
 C.dump(R/'release_inventory.json',{'code_hashes':{str(p.relative_to(C.ROOT)):C.sha(p) for p in [C.ROOT/'analysis/scripts/construct_sp_attributes.py',*sorted((C.ROOT/'analysis/scripts/sp_attributes').glob('*.py')),C.ROOT/'analysis/scripts/check_sp_population_support.py',C.ROOT/'analysis/scripts/plot_sp_attribute_qa.py',C.ROOT/'analysis/tests/test_sp_attributes.py',C.ROOT/'analysis/config/sp_attributes_2026_09_11.json',Path(__file__)]},'outputs':{str(p.relative_to(R)):C.sha(p) for p in files},'model_fitted':False})
 print('Release review passed; report and artifact inventory written',flush=True)
if __name__=='__main__':main()

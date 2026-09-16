"""Human-readable release report from saved results, with explicit interpretation limits."""
import json
import numpy as np
import pandas as pd
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/sp-model-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def markdown_table(frame):
    return '| ' + ' | '.join(frame.columns) + ' |\n|' + '|'.join(['---']*len(frame.columns)) + '|\n' + '\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))


def report(release,config,rank,summary,validation):
    figures=release/'figures';figures.mkdir(exist_ok=True)
    tables=release/'tables'
    contributions=pd.read_csv(tables/'family_contributions.csv',dtype={'district_id':str})
    order=rank.head(10).district_id.tolist()
    pivot=contributions.pivot(index='district_id',columns='family',values='squared_distance_contribution').loc[order]
    pivot.index=rank.set_index('district_id').loc[order,'district_name']
    ax=pivot.plot.bar(stacked=True,figsize=(11,6),colormap='tab20');ax.set_ylabel('Squared distance to Brás');ax.set_xlabel('')
    ax.legend(bbox_to_anchor=(1.02,1),loc='upper left',title='Family');plt.tight_layout();plt.savefig(figures/'family_contributions.png',dpi=150);plt.close()
    variance=pd.read_csv(tables/'pca_variance.csv');fig,ax=plt.subplots(figsize=(7,4));ax.plot(variance.component,variance.cumulative,marker='o');ax.axhline(.9,color='gray',linestyle='--');ax.set(xlabel='Retained principal components',ylabel='Cumulative variance',ylim=(0,1.02));fig.tight_layout();fig.savefig(figures/'pca_variance.png',dpi=150);plt.close(fig)
    selected=summary.loc[~summary.kind.eq('weight_perturbation')].nsmallest(15,'top10_overlap')
    fig,ax=plt.subplots(figsize=(10,6));ax.barh(selected.scenario,selected.top10_overlap);ax.set(xlabel='Members retained from primary top 10',xlim=(0,10));fig.tight_layout();fig.savefig(figures/'largest_top10_changes.png',dpi=150);plt.close(fig)
    import geopandas as gpd
    geo=gpd.read_file(release/'spatial/district_similarity.gpkg');fig,ax=plt.subplots(figsize=(7,7));geo.plot(column='distance',cmap='viridis_r',legend=True,ax=ax);geo.loc[geo.district_id.eq(config['target_district_id'])].boundary.plot(ax=ax,color='red',linewidth=1.5);ax.set_axis_off();ax.set_title('Primary distance to Brás (outlined red)');fig.tight_layout();fig.savefig(figures/'distance_map.png',dpi=150);plt.close(fig)
    freq=pd.read_csv(tables/'weight_stability.csv',dtype={'district_id':str})
    source=summary.loc[summary.kind.eq('source')]
    lines=['# Corrected SP urban similarity model — v2','',
           'The original v1 primary metric is preserved. The v2 release fixes input validation, PCA labeling, normalized weights, row alignment, CLI dependencies and persisted provenance, and executes the previously missing sensitivity experiments. It is a descriptive district similarity model, not a causal or predictive validation of urban equivalence.','',
           f"Primary cohort: 96 districts; Brás 10; 13 families; 23 original coordinates. Executed {len(summary)} scenarios, including {config['weight_draws']} seeded weight perturbations, source substitutions, family exclusions, 32 subprefeitura fit exclusions, PCA and regularized Mahalanobis.",'',
           '## Primary ranking','',markdown_table(rank.head(10)),'',
           '![Family contributions](../figures/family_contributions.png)','',
           '## Robustness findings','',
           f"Across source substitutions, top-10 retention ranges from {source.top10_overlap.min()} to {source.top10_overlap.max()} of the original ten. Weight-stable candidates (at least 80% top-10 inclusion in the prespecified weight experiments): {int(freq.weight_stable.sum())}. These frequencies describe a designed perturbation set, not statistical confidence or probabilities of true equivalence.",'',
           markdown_table(summary.loc[~summary.kind.eq('weight_perturbation'),['scenario','kind','spearman','top10_overlap','max_absolute_rank_shift']].sort_values(['top10_overlap','scenario']).head(20)),'',
           '![Largest changes](../figures/largest_top10_changes.png)','',
           'Numerical source substitutions reuse the primary scalar transforms and family calibrations. U1 composition replacements fit a new representation. Fit-cohort, scaling and covariance/PCA alternatives are separate experiments. Negative weights are rejected and every weight scheme sums to one. Subprefeitura exclusions change the fitting cohort and then score all 96 districts; they are influence tests, not prediction accuracy.','',
           '## PCA and interpretation','',
           'PCA is fitted to the already weighted 23-coordinate embedding. Correct feature labels follow the embedding column order. Full unwhitened PCA preserves primary distances; truncation changes the metric while retaining its initial weighting assumptions. Mahalanobis uses Ledoit–Wolf regularization and does not imply exact equal-family influence. Loadings describe variance, not causal importance. Ward results in the notebook are descriptive, not independent confirmation of real urban classes.','',
           '![PCA variance](../figures/pca_variance.png)','',
           '## Validation and limitations','',
           'Checked finite values, identities, cross-file agreement, transform serialization, composition sums, contribution reconstruction, symmetric/nonnegative distances, every triangle inequality, exact embedding equivalence, full-PCA distance conservation, positive covariance, source hash preservation and reopened EPSG:31983 GeoPackage. Automated regression tests and the separate model audit cover the original defects. Complete numerical checks do not establish independent empirical truth.','',
           'U2 still leaves 508,844 jobs unlocated in the primary scenario. M2 remains the accepted 5 m structure-exclusion proxy; M6 includes Local imputation. Cadastral entity/floor/use semantics, mixed source years, district scale and Euclidean bus access remain limitations. The 125 m population-support experiment covers only three pilots; full-city refinement and 250/500 m morphology grids remain deferred source work.','',
           '## Executed tasks and provenance','',
           '1. Validated the immutable attribute release and exact district/feature identities.','2. Fitted scalar transforms and M6 composition through shared tested modules; saved fit/apply state.','3. Computed calibrated family distances, an exact embedding, rankings and signed profile differences.','4. Ran source/representation, weighting, omission, spatial-fit, PCA and covariance scenarios with saved specifications.','5. Exported family contributions, source-quality annotations, distributions, maps, metadata and validation evidence.','6. Preserved the original v1 outputs for independent comparison.','',
           'Run metadata and full scenario fitted states are under `analysis/work/runs/sp_urban_model_v2/`. The manifest hashes source files, executable code, configuration and environment. Completed runs verify output hashes and reject changed signatures; changed inputs or methods require a new run ID. No pedestrian outcome enters the features.','',
           'The next cross-city step is the Chicago harmonization plan, not applying the current SP feature names to unmatched Chicago sources.']
    (release/'reports').mkdir(exist_ok=True);(release/'reports/MODEL_REPORT.md').write_text('\n'.join(lines)+'\n')
    (release/'README.md').write_text('# SP urban similarity — corrected v2\n\n[Model report](reports/MODEL_REPORT.md) · [Brás ranking](tables/bras_ranking.csv) · [Scenario summary](tables/scenario_summary.csv) · [Weight stability](tables/weight_stability.csv) · [Validation](validation/checks.json)\n\nTables include complete rankings, family contributions, raw/fitted profile differences and source quality. Maps are under `spatial/` and `figures/`. Original v1 results remain unchanged. Distances are descriptive, not probabilities of equivalence.\n')

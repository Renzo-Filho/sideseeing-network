"""Strict SP release input contract; no writes during input validation."""
import hashlib
import json
import sys
from importlib.metadata import version
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from .distances import normalized_weights


def hash_file(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def freeze_inputs(config_path, base_dir):
    base_dir = Path(base_dir)
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    paths = {k: base_dir / p for k, p in config['paths'].items()}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    df = pd.read_csv(paths['primary_attributes'], dtype={'district_id': str})
    ids = [f'{i:02d}' for i in range(1, 97)]
    if len(df) != 96 or not df.district_id.is_unique or set(df.district_id) != set(ids):
        raise ValueError('Require exact 96 municipal district IDs 01..96')
    if config['target_district_id'] not in ids or config['fitting_cohort'] != 'all_96':
        raise ValueError('Invalid target or unsupported primary fitting cohort')
    expected_families = {'M1','M2','M3','M4','M6','M7','B1','B2','B3','U1','U2','U3','U4'}
    if set(config['families']) != expected_families:
        raise ValueError('Unexpected primary family selection')
    normalized_weights(config)
    selected = [c for fc in config['families'].values() for c in fc['columns']]
    dictionary = pd.read_csv(paths['attribute_dictionary'])
    primary = dictionary.loc[dictionary.primary_feature.eq(True)]
    if len(selected) != 23 or set(selected) != set(primary.feature_name):
        raise ValueError('Primary feature selection differs from released dictionary')
    for fam, fc in config['families'].items():
        if set(fc['columns']) != set(primary.loc[primary.family_id.eq(fam), 'feature_name']):
            raise ValueError(f'Incorrect family membership: {fam}')
    if not np.isfinite(df[selected].to_numpy(float)).all():
        raise ValueError('Primary values must be finite')
    wide = pd.read_parquet(paths['wide_attributes'])
    long = pd.read_parquet(paths['long_attributes'])
    geo = gpd.read_file(paths['district_geometry'])
    for label, frame in [('wide', wide), ('geometry', geo)]:
        if len(frame) != 96 or not frame.district_id.is_unique or set(frame.district_id) != set(ids):
            raise ValueError(f'Cross-file district identity mismatch: {label}')
    if geo.crs.to_epsg() != 31983 or not geo.is_valid.all():
        raise ValueError('Invalid projected district geometry')
    if len(long) != 96 * 77 or long.duplicated(['district_id', 'feature_name']).any():
        raise ValueError('Invalid long-table keys')
    if set(long.run_id) != {config['source_release']}:
        raise ValueError('Source release mismatch')
    pivot = long.pivot(index='district_id', columns='feature_name', values='value')
    ref = df.set_index('district_id').loc[ids, selected]
    for frame in [wide.set_index('district_id'), pivot, geo.set_index('district_id')]:
        if not np.allclose(ref, frame.loc[ids, selected], rtol=1e-12, atol=1e-12):
            raise ValueError('Cross-file attribute values differ')
    code = [base_dir/'scripts/model_sp_urban_similarity.py', *sorted((base_dir/'scripts/sp_model').glob('*.py'))]
    packages = ['numpy','pandas','scipy','scikit-learn','geopandas','pyogrio','shapely']
    manifest = dict(config=config, config_hash=hash_file(config_path),
                    inputs={k: dict(path=str(p.relative_to(base_dir)), sha256=hash_file(p)) for k,p in paths.items()},
                    code={str(p.relative_to(base_dir)):hash_file(p) for p in code},
                    environment={'python':sys.version, **{p:version(p) for p in packages}},
                    district_ids=df.district_id.tolist(), selected_columns=selected)
    return config, df, manifest

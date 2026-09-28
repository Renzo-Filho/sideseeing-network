"""Bounded U1 ontology screen using published district summaries only.

Select six units per city before comparing distributions. This script does not
open raw IPTU, parcel geometry, or the Chicago LUI GeoPackage.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/results/SP_CHI/u1_summary_pilot_2026_09_22'
SEED = 20260922
SOURCES = {
    'SP': ROOT / 'analysis/results/SP/tables/attributes_wide.parquet',
    'CHI': ROOT / 'analysis/results/Chicago/chi_local_2026_09_16_v1/tables/attributes_wide.parquet',
    'SP_LONG': ROOT / 'analysis/results/SP/tables/attributes_long.parquet',
}
COMMON = ['residential', 'commerce_services', 'industrial', 'institutional',
          'transport_utilities', 'vacant']
SOURCE_TO_COMMON = {
    'SP': {
        'residential': 'residential', 'commerce_services': 'commerce_services',
        'industry_warehouse': 'industrial', 'institutional': 'institutional',
        'transport_utilities': 'transport_utilities', 'vacant': 'vacant',
        'mixed_other': None,
    },
    'CHI': {
        'residential': 'residential', 'commercial': 'commerce_services',
        'industrial': 'industrial', 'institutional': 'institutional',
        'transport_utilities': 'transport_utilities',
        'vacant_construction': 'vacant', 'agriculture': None, 'open_space': None,
    },
}


def source_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def prepared(city: str) -> pd.DataFrame:
    frame = pd.read_parquet(SOURCES[city])
    frame['district_id'] = frame['district_id'].astype(str).str.zfill(2)
    prefix = 'land_use_land_area_share_' if city == 'SP' else 'land_use_share_'
    for source, target in SOURCE_TO_COMMON[city].items():
        frame[f'source_{source}'] = frame[prefix + source].astype(float)
    if city == 'SP':
        long = pd.read_parquet(SOURCES['SP_LONG'], columns=[
            'district_id', 'feature_name', 'coverage_fraction'],
            filters=[('feature_name', '=', 'land_use_entropy_land_area')])
        long = long[['district_id', 'coverage_fraction']]
        long['district_id'] = long.district_id.astype(str).str.zfill(2)
        frame = frame.merge(long.rename(columns={'coverage_fraction': 'source_coverage'}),
                            on='district_id', validate='one_to_one')
        frame['coverage_basis'] = 'classified area / accepted cadastral entity area'
        frame['original_entropy'] = frame.land_use_entropy_land_area
        anchor = '10'
    else:
        frame['source_coverage'] = frame.lui_classified_land.astype(float)
        frame['coverage_basis'] = 'classified LUI area / district land area'
        frame['original_entropy'] = frame.land_use_entropy_cmap_area8
        anchor = '32'
    for common in COMMON:
        source = next(k for k, v in SOURCE_TO_COMMON[city].items() if v == common)
        frame[f'common_{common}'] = frame[f'source_{source}']
    frame['candidate_mass'] = frame[[f'common_{x}' for x in COMMON]].sum(axis=1)
    frame['excluded_mass'] = 1 - frame.candidate_mass
    frame['source_mass'] = frame[[f'source_{x}' for x in SOURCE_TO_COMMON[city]]].sum(axis=1)
    assert len(frame) == (96 if city == 'SP' else 77)
    assert np.allclose(frame.source_mass, 1, atol=1e-8)
    assert frame.district_id.is_unique and anchor in set(frame.district_id)
    return frame


def select(frame: pd.DataFrame, city: str) -> pd.DataFrame:
    """One anchor plus seeded random choice in five predeclared strata."""
    rng = np.random.default_rng(SEED + (1 if city == 'SP' else 2))
    anchor = '10' if city == 'SP' else '32'
    chosen = [(anchor, 'fixed_anchor')]
    specs = [
        ('residential_top_quintile', 'common_residential', 'high'),
        ('industrial_top_quintile', 'common_industrial', 'high'),
        ('excluded_mass_top_quintile', 'excluded_mass', 'high'),
        ('source_coverage_bottom_quintile', 'source_coverage', 'low'),
        ('original_entropy_middle_fifth', 'original_entropy', 'middle'),
    ]
    for label, column, direction in specs:
        available = frame.loc[~frame.district_id.isin([x[0] for x in chosen])]
        if direction == 'high':
            candidates = available.loc[available[column] >= frame[column].quantile(.8)]
        elif direction == 'low':
            candidates = available.loc[available[column] <= frame[column].quantile(.2)]
        else:
            candidates = available.loc[available[column].between(
                frame[column].quantile(.4), frame[column].quantile(.6))]
        assert len(candidates) > 0, (city, label)
        options = sorted(candidates.district_id.tolist())
        chosen.append((options[int(rng.integers(len(options)))], label))
    selected = frame.set_index('district_id').loc[[key for key, _ in chosen]].reset_index()
    selected.insert(0, 'city', city)
    selected['unit_id'] = city + ':' + selected.district_id
    selected.insert(3, 'selection_stratum', [label for _, label in chosen])
    return selected


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    selected = pd.concat([select(prepared(city), city) for city in ('SP', 'CHI')],
                         ignore_index=True)
    parts = np.array(selected[[f'common_{x}' for x in COMMON]], dtype=float)
    mass = parts.sum(axis=1)
    probabilities = parts / mass[:, None]
    selected['candidate_entropy6'] = -(np.where(probabilities > 0,
        probabilities * np.log(np.clip(probabilities, 1e-300, None)), 0).sum(axis=1)) / np.log(6)
    selected['candidate_land_coverage'] = np.where(selected.city.eq('CHI'),
        selected.source_coverage * selected.candidate_mass, np.nan)
    keep = ['city', 'unit_id', 'district_id', 'district_name', 'selection_stratum',
            'coverage_basis', 'source_coverage', 'original_entropy', 'candidate_mass',
            'excluded_mass', 'candidate_land_coverage', 'candidate_entropy6'] + [f'common_{x}' for x in COMMON]
    result = selected[keep].copy()
    result.to_csv(OUT / 'sampled_ontology_screen.csv', index=False)
    crosswalk = pd.DataFrame([
        {'city': city, 'source_category': source, 'candidate_category': target or 'excluded_residual',
         'note': ('CMAP commercial includes some primary mixed-use codes'
                  if city == 'CHI' and source == 'commercial' else
                  'Source-specific meaning requires map review')}
        for city, mapping in SOURCE_TO_COMMON.items() for source, target in mapping.items()])
    crosswalk.to_csv(OUT / 'proposed_category_crosswalk.csv', index=False)
    checks = {
        'scope': 'existing district summaries only; no raw parcel, IPTU, LUI geometry or POI reads',
        'seed': SEED, 'source_rows': {'SP': 96, 'CHI': 77},
        'selected_rows': {'SP': int((result.city == 'SP').sum()),
                          'CHI': int((result.city == 'CHI').sum())},
        'source_sha256': {name: source_hash(path) for name, path in SOURCES.items()},
        'unique_unit_ids': bool(result.unit_id.is_unique),
        'source_mass_max_abs_error': float(np.abs(selected.source_mass - 1).max()),
        'candidate_plus_residual_max_abs_error': float(np.abs(result.candidate_mass + result.excluded_mass - 1).max()),
        'candidate_entropy_finite_bounded': bool(np.isfinite(result.candidate_entropy6).all()
            and result.candidate_entropy6.between(0, 1).all()),
        'coverage_not_cross_city_comparable': True,
        'semantic_accepted': False,
    }
    assert checks['selected_rows'] == {'SP': 6, 'CHI': 6}
    assert checks['unique_unit_ids'] and checks['candidate_entropy_finite_bounded']
    assert checks['candidate_plus_residual_max_abs_error'] < 1e-8
    (OUT / 'checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(result[['unit_id', 'district_name', 'selection_stratum', 'source_coverage',
                  'excluded_mass', 'candidate_entropy6']].round(3).to_string(index=False))


if __name__ == '__main__':
    main()

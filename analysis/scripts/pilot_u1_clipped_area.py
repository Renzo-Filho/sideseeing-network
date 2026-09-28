"""Exact six-unit U1 land support check; no citywide U1 construction."""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from shapely.strtree import STRtree

from pilot_u1_source_samples import LAND, SP_METRICS, SP_RECORDS, UNITS, chi_data, park_data

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/results/SP_CHI/u1_developed_area_2026_09_22'
SAMPLED_POINTS = ROOT / 'analysis/results/SP_CHI/u1_source_samples_2026_09_22/sampled_land_points.csv'
SP_BLOCKS = ROOT / 'analysis/data/SP/Cadastro e Vias/quadra_viaria_editada.gpkg'
BROAD = ('residential', 'commerce_services', 'industrial', 'institutional', 'transport_utilities', 'vacant')
OCCUPIED = ('residential', 'commerce_services', 'industrial', 'institutional')


def normalized_entropy(areas: dict[str, float], categories: tuple[str, ...]) -> float | None:
    weights = np.array([areas.get(category, 0.0) for category in categories], dtype=float)
    if weights.sum() <= 0:
        return None
    shares = weights / weights.sum()
    return float(-np.sum(np.where(shares > 0, shares * np.log(np.maximum(shares, 1e-300)), 0)) / np.log(len(categories)))


def raw_sp_lots(district: str, land: shapely.Geometry, all_lands: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, list[str]]:
    # Source files follow GeoSampa source districts; accepted fiscal IDs use
    # assigned districts. Include immediate neighboring source files at edges.
    neighbors = [code for code, geom in all_lands.geometry.items() if geom.intersects(land.buffer(50))]
    parts = []
    for code in neighbors:
        frame = gpd.read_parquet(SP_RECORDS / f'{code}.parquet', columns=['parcel_candidate_id', 'geometry'])
        frame['origin_partition'] = code
        parts.append(frame.loc[frame.geometry.intersects(land)])
    joined = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry='geometry', crs=all_lands.crs)
    return joined.drop_duplicates('parcel_candidate_id'), neighbors


def accepted_sp_uses(raw: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    con = duckdb.connect()
    con.execute('SET threads=1')
    con.execute("SET memory_limit='512MB'")
    con.register('candidate_ids', raw[['parcel_candidate_id']])
    metrics = con.execute('SELECT m.parcel_candidate_id,m.parcel_use_candidate FROM read_parquet(?) m JOIN candidate_ids i USING(parcel_candidate_id)', [str(SP_METRICS)]).df()
    con.close()
    matched = raw.merge(metrics, on='parcel_candidate_id', how='inner', validate='one_to_one')
    matched = gpd.GeoDataFrame(matched, geometry='geometry', crs=raw.crs)
    matched['source_id'] = matched.parcel_candidate_id.astype(str)
    matched['raw_code'] = matched.parcel_use_candidate.fillna('unknown')
    matched['category'] = matched.parcel_use_candidate.fillna('source_unclassified').replace({
        'commerce/services': 'commerce_services', 'industry/warehouse': 'industrial',
        'transport/utilities': 'transport_utilities', 'mixed/other': 'mixed_other'})
    return matched


def source_partition(land: shapely.Geometry, source: gpd.GeoDataFrame) -> tuple[dict[str, float], shapely.Geometry, shapely.Geometry]:
    by_category = {}
    for category, group in source.groupby('category', dropna=False):
        union = shapely.union_all(group.geometry.to_numpy())
        by_category[str(category)] = shapely.intersection(union, land)
    pairs = []
    names = list(by_category)
    for left, right in combinations(names, 2):
        overlap = shapely.intersection(by_category[left], by_category[right])
        if overlap.area > 0:
            pairs.append(overlap)
    conflict = shapely.union_all(pairs) if pairs else shapely.GeometryCollection()
    exclusive = {name: float(shapely.difference(geom, conflict).area) for name, geom in by_category.items()}
    union = shapely.union_all(list(by_category.values()))
    exclusive['overlap_conflict'] = float(conflict.area)
    exclusive['unmapped_source'] = float(shapely.difference(land, union).area)
    assert abs(sum(exclusive.values()) - land.area) < max(0.01, land.area * 1e-8)
    return exclusive, union, conflict


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lands = {city: gpd.read_parquet(path).set_index('district_id') for city, path in LAND.items()}
    sampled = pd.read_csv(SAMPLED_POINTS)
    rows, category_rows, point_rows = [], [], []
    for city, ids in UNITS.items():
        for district in ids:
            unit_id = f'{city}:{district}'
            land = lands[city].loc[district, 'geometry']
            if city == 'SP':
                raw, neighbors = raw_sp_lots(district, land, lands['SP'])
                source = accepted_sp_uses(raw)
            else:
                source = chi_data(land)
            source = source.loc[source.geometry.notna() & ~source.geometry.is_empty]
            assert bool(np.all(shapely.is_valid(source.geometry.to_numpy())))
            areas, accepted_union, conflict = source_partition(land, source)
            extras = {}
            if city == 'SP':
                raw_union = shapely.intersection(shapely.union_all(raw.geometry.to_numpy()), land)
                blocks = pyogrio.read_dataframe(SP_BLOCKS, bbox=tuple(land.bounds), columns=['tx_tipo_quadra_viaria'], use_arrow=True)
                blocks = blocks.loc[blocks.geometry.intersects(land)]
                block_union = shapely.intersection(shapely.union_all(blocks.geometry.to_numpy()), land)
                ordinary_blocks = blocks.loc[blocks.tx_tipo_quadra_viaria.eq('Quadra')]
                planted_blocks = blocks.loc[blocks.tx_tipo_quadra_viaria.eq('Praca_Canteiro')]
                ordinary_union = shapely.intersection(shapely.union_all(ordinary_blocks.geometry.to_numpy()), land)
                planted_union = shapely.intersection(shapely.union_all(planted_blocks.geometry.to_numpy()), land)
                no_raw_geometry = shapely.difference(land, raw_union)
                parks = park_data(land)
                park_union = shapely.intersection(shapely.union_all(parks.geometry.to_numpy()), land) if len(parks) else shapely.GeometryCollection()
                extras = {
                    'raw_lot_union_m2': raw_union.area,
                    'adjacent_partition_raw_area_m2': shapely.intersection(shapely.union_all(raw.loc[raw.origin_partition.ne(district), 'geometry'].to_numpy()), land).area,
                    'adjacent_partition_count': len(neighbors)-1,
                    'accepted_use_union_m2': accepted_union.area,
                    'raw_lot_without_accepted_use_m2': shapely.difference(raw_union, accepted_union).area,
                    'no_raw_lot_m2': no_raw_geometry.area,
                    'no_raw_lot_inside_mapped_quadra_m2': shapely.intersection(no_raw_geometry, block_union).area,
                    'no_raw_lot_inside_ordinary_quadra_m2': shapely.intersection(no_raw_geometry, ordinary_union).area,
                    'no_raw_lot_inside_praca_canteiro_m2': shapely.intersection(no_raw_geometry, planted_union).area,
                    'no_raw_lot_outside_mapped_quadra_m2': shapely.difference(no_raw_geometry, block_union).area,
                    'park_union_m2': park_union.area,
                    'park_outside_accepted_use_m2': shapely.difference(park_union, accepted_union).area,
                    'park_outside_raw_lot_m2': shapely.difference(park_union, raw_union).area,
                }
                raw_index = STRtree(raw.geometry.to_numpy())
                accepted_index = STRtree(source.geometry.to_numpy())
                for point in sampled.loc[sampled.unit_id.eq(unit_id)].itertuples():
                    pt = gpd.GeoSeries.from_xy([point.lon], [point.lat], crs=4326).to_crs(lands[city].crs).iloc[0]
                    accepted_matches = accepted_index.query(pt, predicate='intersects')
                    corrected_categories = sorted(set(source.category.iloc[accepted_matches].astype(str)))
                    corrected_status = ('overlap_conflict' if len(corrected_categories) > 1 else
                        corrected_categories[0] if corrected_categories else
                        'mapped_park_without_cadastral_use' if park_union.intersects(pt) else 'unmapped_source')
                    point_rows.append({'unit_id': unit_id, 'sample_no': point.sample_no,
                        'previous_status': point.land_source_status, 'corrected_status': corrected_status,
                        'in_raw_lot': bool(len(raw_index.query(pt, predicate='intersects'))),
                        'in_accepted_use': bool(len(accepted_matches)),
                        'in_mapped_park': bool(park_union.intersects(pt))})
            broad_area = sum(areas.get(c, 0) for c in BROAD)
            occupied_area = sum(areas.get(c, 0) for c in OCCUPIED)
            record = {'city': city, 'unit_id': unit_id, 'land_area_m2': land.area,
                'classified_six_m2': broad_area, 'classified_six_land_fraction': broad_area / land.area,
                'occupied_four_m2': occupied_area, 'occupied_four_land_fraction': occupied_area / land.area,
                'mixed_other_m2': areas.get('mixed_other', 0),
                'source_unclassified_m2': areas.get('source_unclassified', 0),
                'open_space_m2': areas.get('open_space', 0),
                'agriculture_m2': areas.get('agriculture', 0),
                'unmapped_source_m2': areas.get('unmapped_source', 0),
                'overlap_conflict_m2': areas.get('overlap_conflict', 0),
                'entropy_six_classified': normalized_entropy(areas, BROAD),
                'entropy_four_occupied': normalized_entropy(areas, OCCUPIED),
                'source_objects': len(source), **extras}
            rows.append(record)
            for category, area in sorted(areas.items()):
                category_rows.append({'city': city, 'unit_id': unit_id, 'category': category,
                    'area_m2': area, 'land_fraction': area / land.area})
            print(unit_id, 'land', round(land.area), 'six', round(broad_area / land.area, 3),
                  'unmapped', round(areas.get('unmapped_source', 0) / land.area, 3), flush=True)
    output = pd.DataFrame(rows)
    output.to_csv(OUT/'unit_coverage.csv', index=False)
    pd.DataFrame(category_rows).to_csv(OUT/'category_areas.csv', index=False)
    pd.DataFrame(point_rows).to_csv(OUT/'sp_point_gap_causes.csv', index=False)
    assert len(output) == 6 and len(point_rows) == 60
    assert np.allclose(pd.DataFrame(category_rows).groupby('unit_id').area_m2.sum().sort_index().values,
                       output.set_index('unit_id').land_area_m2.sort_index().values, rtol=1e-8, atol=0.01)
    checks = {'units': output.unit_id.tolist(), 'source_scope': 'three SP districts plus their 50 m adjacent source partitions, and three Chicago CMAP bounding boxes',
              'method': 'exact per-category union, district-land clip, cross-category conflict isolation, complement as unmapped',
              'category_mass_conserved': True, 'independent_truth_labels': False, 'u1_accepted': False}
    (OUT/'checks.json').write_text(json.dumps(checks, indent=2)+'\n')


if __name__ == '__main__':
    main()

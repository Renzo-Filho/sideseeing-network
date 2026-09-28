"""Bounded source-level U1 sampling in three selected districts per city.

Reads only selected SP parcel partitions, three Chicago LUI bounding boxes,
small district geometries and a parks layer. No full-city spatial overlay.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from shapely.geometry import Point
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/results/SP_CHI/u1_source_samples_2026_09_22'
SEED = 20260922
UNITS = {'SP': ['10', '02', '95'], 'CHI': ['32', '14', '23']}
LAND = {
    'SP': ROOT / 'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet',
    'CHI': ROOT / 'analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/district_land.parquet',
}
SP_RECORDS = ROOT / 'analysis/work/prepared/SP/sp_prep_2026_09_09_v2/02_parcels_tax/parcel_records'
SP_METRICS = ROOT / 'analysis/work/runs/sp_attributes_2026_09_11_v1/intermediates/canonical_parcel_metrics.parquet'
SP_PARKS = ROOT / 'analysis/data/SP/Meio Ambiente/GEOSAMPA_cadparcs_parque_unidade_conservacao.gpkg'
CHI_LUI = ROOT / 'analysis/data/Chicago/LUI_2023_view_332920193481040239.gpkg'


def chi_class(code: object) -> str:
    value = str(code).split('.')[0]
    for prefix, category in [('11', 'residential'), ('12', 'commerce_services'),
                              ('13', 'institutional'), ('14', 'industrial'),
                              ('15', 'transport_utilities'), ('2', 'agriculture'),
                              ('3', 'open_space'), ('4', 'vacant')]:
        if value.startswith(prefix):
            return category
    return 'source_unclassified'


def sp_data() -> dict[str, gpd.GeoDataFrame]:
    con = duckdb.connect()
    con.execute("SET threads=1")
    con.execute("SET memory_limit='512MB'")
    ids = ','.join(f"'{x}'" for x in UNITS['SP'])
    metrics = con.execute(f"""SELECT parcel_candidate_id,district_id,parcel_use_candidate
        FROM read_parquet('{SP_METRICS}') WHERE district_id IN ({ids})""").df()
    con.close()
    out = {}
    for district in UNITS['SP']:
        path = SP_RECORDS / f'{district}.parquet'
        polygons = gpd.read_parquet(path, columns=['parcel_candidate_id', 'geometry'])
        polygons = polygons.drop_duplicates(subset=['parcel_candidate_id'])
        matched = polygons.merge(metrics.loc[metrics.district_id.eq(district),
            ['parcel_candidate_id', 'parcel_use_candidate']], on='parcel_candidate_id',
            how='inner', validate='one_to_one')
        matched = gpd.GeoDataFrame(matched, geometry='geometry', crs=polygons.crs)
        matched['source_id'] = matched.parcel_candidate_id.astype(str)
        matched['raw_code'] = matched.parcel_use_candidate.fillna('unknown')
        matched['category'] = matched.parcel_use_candidate.fillna('source_unclassified').replace({
            'commerce/services': 'commerce_services', 'industry/warehouse': 'industrial',
            'transport/utilities': 'transport_utilities', 'mixed/other': 'mixed_other'})
        out[district] = matched[['source_id', 'raw_code', 'category', 'geometry']]
        print('SP', district, 'partition_rows', len(polygons), 'accepted_use_objects', len(matched), flush=True)
    return out


def chi_data(land: shapely.Geometry) -> gpd.GeoDataFrame:
    bbox = tuple(gpd.GeoSeries([land], crs=26916).to_crs(3857).total_bounds)
    frame = pyogrio.read_dataframe(CHI_LUI, bbox=bbox,
        columns=['GlobalID', 'LANDUSE', 'LANDUSE2'], use_arrow=True)
    frame = frame.to_crs(26916)
    frame = frame.loc[frame.geometry.intersects(land)].copy()
    frame['source_id'] = frame.GlobalID.astype(str)
    frame['raw_code'] = frame.LANDUSE.astype(str)
    frame['category'] = frame.LANDUSE.map(chi_class)
    return frame[['source_id', 'raw_code', 'category', 'geometry']]


def park_data(land: shapely.Geometry) -> gpd.GeoDataFrame:
    frame = pyogrio.read_dataframe(SP_PARKS, bbox=tuple(land.bounds),
        columns=['nm_area', 'tx_tipo_categoria'], use_arrow=True)
    return frame.loc[frame.geometry.intersects(land)]


def land_points(land: shapely.Geometry, n: int, rng: np.random.Generator) -> list[Point]:
    xmin, ymin, xmax, ymax = land.bounds
    points = []
    attempts = 0
    while len(points) < n:
        attempts += 1
        if attempts > 100000:
            raise RuntimeError('Land-point rejection sampling exceeded cap')
        point = Point(rng.uniform(xmin, xmax), rng.uniform(ymin, ymax))
        if land.contains(point):
            points.append(point)
    return points


def lonlat(geometries: list[shapely.Geometry], crs: object) -> list[tuple[float, float]]:
    projected = gpd.GeoSeries(geometries, crs=crs).to_crs(4326)
    return [(float(g.x), float(g.y)) for g in projected]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    lands = {city: gpd.read_parquet(path).set_index('district_id') for city, path in LAND.items()}
    sp = sp_data()
    points_rows, polygons_rows, summaries = [], [], []
    for city, districts in UNITS.items():
        for district in districts:
            land = lands[city].loc[district, 'geometry']
            name = {'SP': {'10':'BRAS','02':'ALTO DE PINHEIROS','95':'SAO DOMINGOS'},
                    'CHI': {'32':'LOOP','14':'ALBANY PARK','23':'HUMBOLDT PARK'}}[city][district]
            sources = sp[district] if city == 'SP' else chi_data(land)
            sources = sources.loc[sources.geometry.notna() & ~sources.geometry.is_empty].reset_index(drop=True)
            geoms = sources.geometry.to_numpy()
            index = STRtree(geoms)
            parks = park_data(land) if city == 'SP' else None
            park_index = STRtree(parks.geometry.to_numpy()) if parks is not None and len(parks) else None
            drawn = land_points(land, 20, rng)
            coords = lonlat(drawn, lands[city].crs)
            point_counts = {}
            for number, (point, (lon, lat)) in enumerate(zip(drawn, coords), 1):
                matches = index.query(point, predicate='intersects')
                cats = sorted(set(sources.category.iloc[matches].astype(str)))
                if len(matches) == 0:
                    park = bool(len(park_index.query(point, predicate='intersects'))) if park_index is not None else False
                    label = 'mapped_park_without_cadastral_use' if park else 'unmapped_source'
                elif len(cats) > 1:
                    label = 'overlap_conflict'
                else:
                    label = cats[0]
                point_counts[label] = point_counts.get(label, 0) + 1
                points_rows.append({'city':city,'unit_id':f'{city}:{district}', 'district_name':name,
                    'sample_no':number,'lon':lon,'lat':lat,'land_source_status':label,
                    'n_source_polygons_at_point':len(matches),
                    'source_ids':'|'.join(sources.source_id.iloc[matches].astype(str).head(5)),
                    'raw_codes':'|'.join(sorted(set(sources.raw_code.iloc[matches].astype(str))))})
            if len(sources) < 20:
                raise RuntimeError(f'{city}:{district} has fewer than 20 source polygons')
            indexes = rng.choice(len(sources), size=20, replace=False)
            selected = sources.iloc[indexes]
            centroids = [g.representative_point() for g in selected.geometry]
            positions = lonlat(centroids, lands[city].crs)
            for number, (row, (lon, lat)) in enumerate(zip(selected.itertuples(), positions), 1):
                polygons_rows.append({'city':city,'unit_id':f'{city}:{district}', 'district_name':name,
                    'sample_no':number,'source_id':row.source_id,'raw_code':row.raw_code,
                    'category':row.category,'lon':lon,'lat':lat,
                    'whole_polygon_area_m2':float(row.geometry.area),
                    'land_intersection_area_m2':float(row.geometry.intersection(land).area)})
            summaries.append({'city':city,'unit_id':f'{city}:{district}', 'district_name':name,
                'source_polygons_in_unit_bbox':len(sources),'sampled_land_points':20,
                'sampled_source_polygons':20,'point_category_counts':json.dumps(point_counts,sort_keys=True),
                'mapped_source_points':20-point_counts.get('unmapped_source',0)-point_counts.get('mapped_park_without_cadastral_use',0),
                'unmapped_source_points':point_counts.get('unmapped_source',0),
                'known_park_without_cadastral_points':point_counts.get('mapped_park_without_cadastral_use',0),
                'overlap_conflict_points':point_counts.get('overlap_conflict',0)})
            print(city,district,'source_objects',len(sources),'point_counts',point_counts,flush=True)
    pd.DataFrame(points_rows).to_csv(OUT/'sampled_land_points.csv',index=False)
    pd.DataFrame(polygons_rows).to_csv(OUT/'sampled_source_polygons.csv',index=False)
    pd.DataFrame(summaries).to_csv(OUT/'sample_summary.csv',index=False)
    checks={'seed':SEED,'units':{city:[f'{city}:{x}' for x in ids] for city,ids in UNITS.items()},
        'point_rows':len(points_rows),'polygon_rows':len(polygons_rows),
        'source_scope':'three SP parcel partitions and three Chicago LUI bounding boxes; one projected-column DuckDB lookup in accepted SP metrics',
        'independent_truth_labels':False,'semantic_accepted':False}
    assert len(points_rows)==len(polygons_rows)==120
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')


if __name__ == '__main__':
    main()

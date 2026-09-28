"""Check four fixed São Paulo POI points against municipal address-range lines.

Ranges bound the likely street segment only; they are not exact geocodes.
Published address sources are documented in the case-audit report.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/results/SP_CHI/u1_independent_cases_2026_09_23'
ROADS = ROOT / 'analysis/data/SP/Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg'
ADDRESSES = {
    'SP_10_matched': ('ANDRADE', 845, 845, 'Rua Monsenhor Andrade 845'),
    'SP_10_osm_only': ('RODRIGUES DOS SANTOS', 91, 490, 'Rua Rodrigues dos Santos 91–490'),
    'SP_02_overture_only': ('DIOGENES RIBEIRO DE LIMA', 1768, 1768, 'Avenida Diógenes Ribeiro de Lima 1768'),
    'SP_95_overture_only': ('JOAQUIM OLIVEIRA FREITAS', 2463, 2463, 'Rua Joaquim Oliveira Freitas 2463'),
}


def main():
    selected = pd.read_csv(OUT/'selected_poi_cases.csv').set_index('case_id')
    rows = []
    for case_id, (street, low, high, published) in ADDRESSES.items():
        case = selected.loc[case_id]
        point = gpd.GeoSeries([Point(float(case.lon), float(case.lat))], crs=4326).to_crs(31983).iloc[0]
        road = gpd.read_file(ROADS, where=f"lg_nome = '{street}'")
        road['distance_m'] = road.geometry.distance(point)
        match = ((road.lg_ini_par<=high)&(road.lg_fim_par>=low)) | ((road.lg_ini_imp<=high)&(road.lg_fim_imp>=low))
        nearest = road.loc[road.distance_m.idxmin()]
        last = road.loc[road[['lg_fim_par','lg_fim_imp']].max(axis=1).idxmax()]
        rows.append({'case_id': case_id, 'published_address': published,
                     'road_name_filter': street, 'published_number_low': low, 'published_number_high': high,
                     'road_segments': len(road), 'matching_number_range_segments': int(match.sum()),
                     'min_distance_to_matching_range_m': float(road.loc[match,'distance_m'].min()) if match.any() else None,
                     'nearest_same_street_m': float(nearest.distance_m),
                     'nearest_same_street_even_range': f'{nearest.lg_ini_par}–{nearest.lg_fim_par}',
                     'nearest_same_street_odd_range': f'{nearest.lg_ini_imp}–{nearest.lg_fim_imp}',
                     'largest_street_number_in_source': int(road[['lg_fim_par','lg_fim_imp']].max().max()),
                     'distance_to_last_numbered_segment_m': float(last.distance_m)})
    pd.DataFrame(rows).to_csv(OUT/'sp_poi_address_ranges.csv', index=False)


if __name__ == '__main__':
    main()

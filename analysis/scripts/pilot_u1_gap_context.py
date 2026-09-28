"""Local reference context for SP sample points lacking raw cadastral lots."""
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
from shapely.strtree import STRtree

from pilot_u1_source_samples import LAND

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/SP_CHI/u1_developed_area_2026_09_22'
BLOCKS=ROOT/'analysis/data/SP/Cadastro e Vias/quadra_viaria_editada.gpkg'
PLAZAS=ROOT/'analysis/data/SP/Cadastro e Vias/GEOSAMPA_v_praca_largo.gpkg'
POINTS=ROOT/'analysis/results/SP_CHI/u1_source_samples_2026_09_22/sampled_land_points.csv'


def main():
    previous=pd.read_csv(OUT/'sp_point_gap_causes.csv')
    coords=pd.read_csv(POINTS)
    p=previous.merge(coords[['unit_id','sample_no','lon','lat']],on=['unit_id','sample_no'],validate='one_to_one')
    p=p.loc[~p.in_raw_lot].copy()
    land=gpd.read_parquet(LAND['SP']).set_index('district_id')
    rows=[]
    for unit,part in p.groupby('unit_id'):
        district=unit.split(':')[1]
        bounds=tuple(land.loc[district,'geometry'].bounds)
        blocks=pyogrio.read_dataframe(BLOCKS,bbox=bounds,columns=['tx_tipo_quadra_viaria'],use_arrow=True)
        plazas=pyogrio.read_dataframe(PLAZAS,bbox=bounds,columns=['categoria','nome'],use_arrow=True)
        block_tree=STRtree(blocks.geometry.to_numpy())
        plaza_tree=STRtree(plazas.geometry.to_numpy())
        projected=gpd.GeoSeries(gpd.points_from_xy(part.lon,part.lat),crs=4326).to_crs(31983)
        for row,point in zip(part.itertuples(),projected):
            bm=block_tree.query(point,predicate='intersects')
            pm=plaza_tree.query(point,predicate='intersects')
            rows.append({'unit_id':unit,'sample_no':row.sample_no,'previous_status':row.previous_status,
                'in_mapped_park':row.in_mapped_park,
                'in_mapped_quadras':bool(len(bm)),'quadra_types':'|'.join(sorted(set(blocks.tx_tipo_quadra_viaria.iloc[bm].astype(str)))),
                'in_mapped_plaza':bool(len(pm)),'plaza_names':'|'.join(plazas.nome.iloc[pm].fillna('').astype(str).head(3))})
        print(unit,'no_lot_points',len(part),'block_features_in_bbox',len(blocks),'plaza_features_in_bbox',len(plazas))
    frame=pd.DataFrame(rows)
    frame.to_csv(OUT/'sp_no_lot_point_context.csv',index=False)
    print(frame.groupby(['unit_id','in_mapped_quadras','in_mapped_plaza']).size().to_string())


if __name__=='__main__':main()

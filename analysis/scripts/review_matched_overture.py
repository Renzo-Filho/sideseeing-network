"""Paired road candidates and Chicago footprint pilots; explicitly not model acceptance."""
from pathlib import Path
import json
import hashlib
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from harmonization.geometry import union_coverage
ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
RUN='overture_2026_08_19_review_v1'
CLASSES=['motorway','trunk','primary','secondary','tertiary','residential','living_street','unclassified','unknown']

def main():
    report={}
    for city in ['Chicago','SP']:
        source=A/'data'/city/'overture_2026_08_19'
        paths=sorted((source/'segment').glob('*.parquet'))
        roads=gpd.read_parquet(paths[0],columns=['id','geometry','subtype','class','subclass','connectors','access_restrictions','road_flags'])
        assert len(paths)==1,'Extend partition assembly before multi-part release'
        print('loaded roads',city,len(roads),flush=True)
        base=A/('work/prepared/Chicago/chi_local_2026_09_16_v1' if city=='Chicago' else 'work/prepared/SP/sp_prep_2026_09_10_v3/N02')
        districts=gpd.read_parquet(base/'districts.parquet')
        if 'unit_id' not in districts:districts['unit_id']='SP:'+districts.district_id.astype(str).str.zfill(2)
        roads=roads.to_crs(districts.crs)
        citygeom=districts.geometry.union_all()
        roads=roads.iloc[roads.sindex.query(citygeom,predicate='intersects')].copy()
        shapely.prepare(citygeom)
        inside=shapely.covers(citygeom,roads.geometry.values)
        lengths=roads.geometry.length.to_numpy()
        lengths[~inside]=shapely.length(shapely.intersection(roads.geometry.values[~inside],citygeom))
        inventory=roads.assign(length_inside_m=lengths).groupby(['subtype','class'],dropna=False).agg(records=('id','size'),length_inside_m=('length_inside_m','sum')).reset_index()
        selected=roads.loc[roads.subtype.eq('road')&roads['class'].isin(CLASSES)].reset_index(drop=True)
        out=A/'results'/city/RUN;out.mkdir(parents=True,exist_ok=True)
        work=A/'work/prepared'/city/RUN;work.mkdir(parents=True,exist_ok=True)
        inventory.to_csv(out/'source_class_inventory.csv',index=False)
        connectors=gpd.read_parquet(next((source/'connector').glob('*.parquet')),columns=['id','geometry']).to_crs(districts.crs)
        arms={}
        for row in selected.itertuples():
            for link in row.connectors:
                arms[link['connector_id']]=arms.get(link['connector_id'],0)+(1 if link['at'] in [0,1] else 2)
        connectors['incident_arms']=connectors.id.map(arms).fillna(0).astype(int)
        candidates=connectors.iloc[connectors.sindex.query(citygeom,predicate='intersects')].copy()
        candidates=candidates.loc[candidates.incident_arms.ge(3)].copy()
        candidate_counts={u:0 for u in districts.unit_id}
        owners=np.full(len(candidates),'',dtype=object)
        for district in districts.sort_values('unit_id').itertuples():
            ids=candidates.sindex.query(district.geometry,predicate='intersects')
            ids=ids[owners[ids]=='']
            owners[ids]=district.unit_id
            candidate_counts[district.unit_id]=len(ids)
        assert (owners!='').all()
        candidates.to_parquet(work/'connector_candidates.parquet',index=False)
        rows=[]
        assigned=0.
        # Ascending IDs own shared boundary-line lengths.
        for row in districts.sort_values('unit_id').itertuples():
            support=row.geometry
            neighbors=districts.iloc[districts.sindex.query(support,predicate='intersects')]
            previous=neighbors.loc[neighbors.unit_id.lt(row.unit_id)]
            shared=shapely.union_all([support.boundary.intersection(g.boundary) for g in previous.geometry])
            print('road district',row.unit_id,flush=True)
            ids=selected.sindex.query(support,predicate='intersects')
            shapely.prepare(support)
            geoms=selected.geometry.values[ids]
            full=shapely.covers(support,geoms)
            clipped=np.array(geoms,copy=True)
            clipped[~full]=shapely.intersection(geoms[~full],support)
            length=shapely.length(clipped)
            # A shared boundary survives polygon difference; remove previous district boundary linework.
            if not shared.is_empty:
                clipped=shapely.difference(clipped,shared)
                length=shapely.length(clipped)
            total=float(length.sum());assigned+=total
            rec={'unit_id':row.unit_id,'gross_area_km2':row.geometry.area/1e6,
                 'road_length_km':total/1000,'road_density_km_km2':total/1000/(row.geometry.area/1e6),
                 'connector_3arm_candidates':candidate_counts[row.unit_id],'strict_cross_city_accepted':False}
            for cls in CLASSES:rec['share_'+cls]=float(length[selected['class'].iloc[ids].eq(cls)].sum()/total)
            rows.append(rec)
        q=pd.DataFrame(rows);q.to_csv(out/'paired_road_candidates.csv',index=False)
        target=float(lengths[roads.subtype.eq('road')&roads['class'].isin(CLASSES)].sum())
        assert abs(target-assigned)<1.,(target,assigned)
        assert np.allclose(q.filter(like='share_').sum(axis=1),1)
        selected.to_parquet(work/'selected_roads.parquet',index=False)
        report[city]={'selected_segments':len(selected),'city_length_km':target/1000,'assignment_difference_m':assigned-target,
            'connector_candidates':len(candidates),'referenced_connectors_missing_buffer':len(set(arms)-set(connectors.id)),
            'access_restriction_records':int(selected.access_restrictions.notna().sum()),
            'selected_classes':CLASSES,'policy':'exclude all service/alleys/driveways and nonmotor classes; retain link ramps; retain carriageways; access restrictions not yet applied',
            'acceptance':'candidate only: unknown/access policies, physical arm duplication and consolidation unresolved'}
        (out/'README.md').write_text('# Matched Overture review\n\nCandidate road density and class shares use the same declared selection in both cities. Connector counts are diagnostics, not accepted M2. No similarity rankings.\n\nSee `review.json` for policies and checks. Whole selected roads and connector points remain in prepared work.\n')
        (out/'review.json').write_text(json.dumps(report[city],indent=2))
        print(city,report[city],flush=True)
    # Exact-union footprint pilots against the supplied historical municipal source.
    b=gpd.read_parquet(next((A/'data/Chicago/overture_2026_08_19/building').glob('*.parquet')),columns=['id','geometry']).to_crs(26916)
    invalid=int((~b.is_valid).sum());b.geometry=shapely.make_valid(b.geometry)
    municipal=gpd.read_parquet(A/'work/prepared/Chicago/chi_local_2026_09_16_v1/buildings.parquet',columns=['geometry'])
    districts=gpd.read_parquet(A/'work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet')
    land=gpd.read_parquet(A/'work/prepared/Chicago/chi_functional_2026_09_16_v2/district_hydro_land.parquet').set_index('unit_id')
    rows=[]
    for row in districts.loc[districts.district_id.isin(['24','28','30','32','76'])].itertuples():
        for name,data in [('overture',b),('municipal_2015',municipal)]:
            gross,onland,summed=union_coverage(data,row.geometry,land.loc[row.unit_id].geometry)
            rows.append({'unit_id':row.unit_id,'source':name,'union_gross_m2':gross,'union_hydro_land_m2':onland,
                         'coverage_gross':gross/row.geometry.area,'coverage_hydro_land':onland/land.loc[row.unit_id].geometry.area,
                         'summed_individual_m2':summed,'strict_cross_city_accepted':False})
        print('footprint pilot',row.unit_id,flush=True)
    out=A/'results/Chicago'/RUN
    pd.DataFrame(rows).to_csv(out/'footprint_source_pilots.csv',index=False)
    (out/'footprint_review.json').write_text(json.dumps({'invalid_overture_repaired':invalid,'pilots':5,'strict_cross_city_accepted':False,'note':'Exact union arithmetic; source omission/ancillary building distinctions and land mask age still require review'},indent=2))

if __name__=='__main__':main()

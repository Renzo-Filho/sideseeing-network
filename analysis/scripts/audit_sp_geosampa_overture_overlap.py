"""Compare each GeoSampa building with Overture footprints, district by district.

The result measures agreement between a historical municipal map and Overture.
It does not treat a GeoSampa-only polygon as proof of a current building.
"""

import gc
import glob
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "analysis"
GEO = ANALYSIS / "data/SP/geosampa_edificacao_2026_10_05"
OVERTURE = ANALYSIS / "data/SP/Edificacoes/sao_paulo_building_morphology.gpkg"
LAND = ANALYSIS / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet"
OUT = ANALYSIS / "results/SP_CHI/b1_geosampa_overture_overlap_2026_10_05"


def audit_district(district_id, district, pages):
    bounds = tuple(district.bounds)
    parts = []
    for page in pages:
        piece = gpd.read_file(f"zip://{page}", bbox=bounds)
        if len(piece):
            parts.append(piece[["cd_identif", "geometry"]])
    if not parts:
        return None, []

    geo = pd.concat(parts, ignore_index=True)
    geometries = shapely.make_valid(geo.geometry.values)
    keep = shapely.within(shapely.centroid(geometries), district)
    geo = geo.loc[keep].reset_index(drop=True)
    g = geometries[keep]
    area = shapely.area(g)
    positive = area > 0
    geo = geo.loc[positive].reset_index(drop=True)
    g, area = g[positive], area[positive]

    ov = pyogrio.read_dataframe(OVERTURE, layer="buildings", bbox=bounds, columns=[])
    o = shapely.make_valid(ov.geometry.values)
    tree = shapely.STRtree(o)
    pairs = tree.query(g, predicate="intersects")
    intersections = shapely.area(shapely.intersection(g[pairs[0]], o[pairs[1]]))
    # Capping overlapping Overture matches makes this a conservative (high) estimate
    # of overlap, and therefore a conservative (low) estimate of missing area.
    overlap = np.minimum(np.bincount(pairs[0], weights=intersections, minlength=len(g)), area)
    fraction = overlap / area

    near = np.zeros(len(g), dtype=bool)
    low = fraction < 0.05
    if low.any():
        near_pairs = tree.query(g[low], predicate="dwithin", distance=3.0)
        near[low] = np.bincount(near_pairs[0], minlength=low.sum()) > 0
    strong_unmatched = low & ~near & (area >= 50)
    near_unmatched = low & near & (area >= 50)

    row = {
        "district_id": district_id,
        "geosampa_buildings": len(g),
        "overture_bbox_buildings": len(o),
        "geosampa_area_m2": area.sum(),
        "geosampa_area_overlap_upper_m2": overlap.sum(),
        "geosampa_area_uncovered_lower_m2": (area - overlap).sum(),
        "geosampa_buildings_overlap_under_5pct": int(low.sum()),
        "geosampa_buildings_overlap_5_to_25pct": int(((fraction >= .05) & (fraction < .25)).sum()),
        "geosampa_buildings_overlap_25_to_75pct": int(((fraction >= .25) & (fraction < .75)).sum()),
        "geosampa_buildings_overlap_75pct_or_more": int((fraction >= .75).sum()),
        "geosampa_buildings_under_5pct_and_over_3m_away": int(strong_unmatched.sum()),
        "geosampa_area_under_5pct_and_over_3m_away_m2": area[strong_unmatched].sum(),
    }

    rng = np.random.default_rng(20261005 + int(district_id))
    candidates = np.flatnonzero(strong_unmatched)
    sampled = rng.choice(candidates, size=min(12, len(candidates)), replace=False)
    largest = candidates[np.argsort(area[candidates])[-5:]]
    near_candidates = np.flatnonzero(near_unmatched)
    near_sampled = rng.choice(near_candidates, size=min(12, len(near_candidates)), replace=False)
    picked = np.unique(np.r_[sampled, largest, near_sampled])
    points = shapely.centroid(g[picked])
    picks = [{
        "district_id": district_id,
        "geosampa_id": geo.cd_identif.iloc[int(i)],
        "x": float(shapely.get_x(point)),
        "y": float(shapely.get_y(point)),
        "geosampa_area_m2": float(area[i]),
        "overlap_fraction_upper": float(fraction[i]),
        "sample_type": ("largest" if i in largest else
                        "near_random" if i in near_sampled else "far_random"),
    } for i, point in zip(picked, points)]
    return row, picks


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    land = gpd.read_parquet(LAND).sort_values("district_id")
    pages = [str(Path(p).resolve()) for p in sorted(glob.glob(str(GEO / "page_*.zip")))]
    assert len(land) == 96 and len(pages) == 141
    rows, picks = [], []
    for n, district in enumerate(land.itertuples(), 1):
        row, district_picks = audit_district(district.district_id, district.geometry, pages)
        if row:
            rows.append(row)
            picks.extend(district_picks)
        print(f"{n}/96 district {district.district_id}: {row['geosampa_buildings'] if row else 0} GeoSampa buildings", flush=True)
        if n % 10 == 0:
            pd.DataFrame(rows).to_csv(OUT / "by_district.partial.csv", index=False)
        gc.collect()
    pd.DataFrame(rows).to_csv(OUT / "by_district.csv", index=False)
    pd.DataFrame(picks).to_csv(OUT / "imagery_candidates.csv", index=False)
    (OUT / "method.json").write_text(json.dumps({
        "date": "2026-10-05",
        "input_geosampa": str(GEO.relative_to(ROOT)),
        "input_overture": str(OVERTURE.relative_to(ROOT)),
        "assignment": "GeoSampa polygon centroid within district land",
        "overlap": "sum of exact pairwise intersection area, capped at GeoSampa polygon area; upper bound if Overture polygons overlap each other",
        "strong_unmatched": "under 5% overlap, no Overture geometry within 3 m, GeoSampa polygon at least 50 m2",
        "interpretation": "disagreement between sources, not proof that a historical GeoSampa building still exists",
    }, indent=2) + "\n")
    (OUT / "by_district.partial.csv").unlink(missing_ok=True)
    print("Done", flush=True)


if __name__ == "__main__":
    main()

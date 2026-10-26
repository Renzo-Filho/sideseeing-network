"""The geometry reference (plan section 8, phase 1): the City of Chicago's curb lines along a street, written for
trace.html, where they are checked against the 2025 orthophoto and the back of the sidewalk is traced.

    python -m graph.reference --out ../data/west_loop_reference      # from network/; downloads the curbs once

The city's sidewalk polygons (77cn-6x4c) are not used: on the imagery they cover the blocks, not the sidewalks.
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString

CURBS_URL = 'https://data.cityofchicago.org/download/5gv8-ktcg/application%2Fzip'  # December 2010
# Cook County's current parcels. Their terms forbid redistribution: they stay in data/, for evaluation only.
PARCELS_URL = 'https://gis.cookcountyil.gov/traditional/rest/services/cookVwrDynmc/MapServer/44/query'
MORGAN = LineString([(-87.65185, 41.8752), (-87.65215, 41.8917)])  # its axis, Tilden to Grand (lon, lat)
UTM = 32616


def near(curbs, axis, within_m=20.0):
    """The parts of the curbs (projected in metres) within within_m of `axis`, one row per piece, indexed by (curb,
    part). The city often draws one line around a corner and down the cross street; its part along the street stays."""
    pieces = curbs.assign(geometry=curbs.intersection(axis.buffer(within_m))).explode(index_parts=True)
    return pieces[(pieces.geom_type == 'LineString') & (pieces.length > 0.5)]


def across(lines, axis, min_deg=60.0, stub_m=4.0):
    """Straight two-point lines more than min_deg from the axis that cross it or are shorter than stub_m. Along Morgan
    these close the curb pieces at the edges of the expressway bridge and the railroad viaduct: structure edges, not
    curbs. The straight ends of cross-street curbs are longer and stay; corner curves have more points."""
    (x0, y0), (x1, y1) = axis.coords[0], axis.coords[-1]
    def angle(line):
        (a, b), (c, d) = line.coords[0], line.coords[-1]
        turn = np.degrees(np.arctan2(d - b, c - a) - np.arctan2(y1 - y0, x1 - x0))
        return abs((turn + 90) % 180 - 90)
    return lines.geometry.apply(lambda line: len(line.coords) == 2 and angle(line) > min_deg
                                and (line.intersects(axis) or line.length < stub_m))


def fetch_parcels(axis, cache, within_m=60.0, slices=10):
    """Cook County's parcels within within_m of the axis (projected), cached as GeoJSON. The service returns at most
    2000 features a request, so the box is fetched in slices along the street."""
    if not cache.exists():
        west, south, east, north = gpd.GeoSeries([axis.buffer(within_m)], crs=UTM).to_crs(4326).total_bounds
        parts = []
        for a, b in zip(np.linspace(south, north, slices + 1)[:-1], np.linspace(south, north, slices + 1)[1:]):
            query = urllib.parse.urlencode(dict(geometry=f'{west},{a},{east},{b}', geometryType='esriGeometryEnvelope',
                                                inSR=4326, spatialRel='esriSpatialRelIntersects', outFields='Pin10',
                                                outSR=4326, f='geojson'))
            with urllib.request.urlopen(f'{PARCELS_URL}?{query}', timeout=60) as response:
                found = json.load(response)['features']
            assert len(found) < 2000, 'a slice hit the service limit: use more slices'
            parts += found
        parcels = gpd.GeoDataFrame.from_features(parts, crs=4326)
        parcels = parcels[~parcels.geometry.to_wkb().duplicated()]  # parcels on two slices
        cache.parent.mkdir(parents=True, exist_ok=True)
        parcels.to_file(cache, driver='GeoJSON')
    return gpd.read_file(cache).to_crs(UTM)


def backs(parcels, axis, within_m=25.0):
    """The back of the sidewalk: the edges of the blocks (the parcels merged, slivers between them closed) within
    within_m of the axis. In Chicago the public sidewalk runs from the curb to the property line."""
    blocks = parcels.geometry.buffer(0.5).union_all().buffer(-0.5)
    lines = gpd.GeoSeries([blocks.boundary.intersection(axis.buffer(within_m))], crs=UTM).explode(index_parts=False)
    lines = lines[(lines.geom_type == 'LineString') & (lines.length > 1.0)].reset_index(drop=True)
    (x0, y0), (x1, y1) = axis.coords[0], axis.coords[-1]
    def right(line):
        x, y = line.interpolate(0.5, normalized=True).coords[0]
        return (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0) < 0
    side = np.where([right(line) for line in lines], 'E', 'W')  # right of the axis (north) is east
    return gpd.GeoDataFrame(dict(kind='back', side=side, source='Cook County parcels'), geometry=lines, crs=UTM)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cache', type=Path, default=Path('../data/chicago_planimetrics/5gv8-ktcg.zip'))
    args = parser.parse_args()
    if not args.cache.exists():
        args.cache.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(CURBS_URL, args.cache)

    axis = gpd.GeoSeries([MORGAN], crs=4326).to_crs(UTM)[0]
    box = tuple(gpd.GeoSeries([axis.buffer(200)], crs=UTM).to_crs(3435).total_bounds)  # the file is in ft (3435)
    curbs = gpd.read_file(f'zip://{args.cache.resolve()}!Curbs.shp', bbox=box).to_crs(UTM)
    pieces = near(curbs, axis)
    pieces = pieces[~across(pieces, axis)]
    curb, part = pieces.index.get_level_values(0), pieces.index.get_level_values(1)
    ids = pieces['CURBS_'].astype(int).astype(str)
    ids = ids.where(~curb.duplicated(keep=False), ids + '-' + part.astype(str))  # a line cut in two: '<id>-0', '<id>-1'
    morgan = gpd.GeoDataFrame(dict(city_id=ids.to_numpy()), geometry=pieces.geometry.to_numpy(), crs=UTM).to_crs(4326)

    args.out.mkdir(parents=True, exist_ok=True)
    morgan.to_file(args.out / 'morgan_city_curbs.geojson', driver='GeoJSON')
    (args.out / 'morgan_city_curbs.js').write_text(
        '// City of Chicago curb lines (5gv8-ktcg, December 2010) along Morgan St, for network/graph/trace.html\n'
        f'window.CITY_CURBS = {morgan.to_json()};\n')
    print(f'{len(morgan)} curb lines along Morgan -> {args.out}')

    parcels = fetch_parcels(axis, args.out / 'morgan_parcels.geojson')
    back = backs(parcels, axis).to_crs(4326)
    back.to_file(args.out / 'morgan_back.geojson', driver='GeoJSON')
    print(f'{len(parcels)} parcels -> {len(back)} back-of-sidewalk lines '
          f'({(back.side == "E").sum()} east, {(back.side == "W").sum()} west)')


if __name__ == '__main__':
    main()

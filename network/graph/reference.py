"""The geometry reference (plan section 8, phase 1): the City of Chicago's curb lines along a street, written for
trace.html, where they are checked against the 2025 orthophoto and the back of the sidewalk is traced.

    python -m graph.reference --out ../data/west_loop_reference      # from network/; downloads the curbs once

The city's sidewalk polygons (77cn-6x4c) are not used: on the imagery they cover the blocks, not the sidewalks.
"""
import argparse
import json
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString

CURBS_URL = 'https://data.cityofchicago.org/download/5gv8-ktcg/application%2Fzip'  # December 2010
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


if __name__ == '__main__':
    main()

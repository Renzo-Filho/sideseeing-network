"""The geometry reference (plan section 8, phase 1): a city's curb lines along a street, written for trace.html, where
they are checked against the orthophoto, and the back of the sidewalk from the county's parcels (the property line).
The sources (a zipped shapefile of curbs, an ArcGIS parcel service) are named in the area's config, [reference].

    python -m walk2net.evaluate.reference --area west_loop --street morgan [--out FOLDER]   # from network/; downloads once

Writes <street>_city_curbs.geojson and .js, <street>_parcels.geojson and <street>_back.geojson, by default into the
area's reference folder. In West Loop the City's sidewalk polygons (77cn-6x4c) are not used: on the imagery they cover
the blocks, not the sidewalks.
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np

from walk2net.config import Area


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


def fetch_parcels(axis, crs, url, id_field, cache, within_m=60.0, slices=10):
    """The parcels within within_m of the axis (projected in `crs`) from an ArcGIS feature service, cached as GeoJSON.
    The service returns at most 2000 features a request, so the box is fetched in slices along the street."""
    if not cache.exists():
        west, south, east, north = gpd.GeoSeries([axis.buffer(within_m)], crs=crs).to_crs(4326).total_bounds
        parts = []
        for a, b in zip(np.linspace(south, north, slices + 1)[:-1], np.linspace(south, north, slices + 1)[1:]):
            query = urllib.parse.urlencode(dict(geometry=f'{west},{a},{east},{b}', geometryType='esriGeometryEnvelope',
                                                inSR=4326, spatialRel='esriSpatialRelIntersects', outFields=id_field,
                                                outSR=4326, f='geojson'))
            with urllib.request.urlopen(f'{url}?{query}', timeout=60) as response:
                found = json.load(response)['features']
            assert len(found) < 2000, 'a slice hit the service limit: use more slices'
            parts += found
        parcels = gpd.GeoDataFrame.from_features(parts, crs=4326)
        parcels = parcels[~parcels.geometry.to_wkb().duplicated()]  # parcels on two slices
        cache.parent.mkdir(parents=True, exist_ok=True)
        parcels.to_file(cache, driver='GeoJSON')
    return gpd.read_file(cache).to_crs(crs)


def backs(parcels, axis, sides=('E', 'W'), within_m=25.0):
    """The back of the sidewalk: the edges of the blocks (the parcels merged, slivers between them closed) within
    within_m of the axis (in the parcels' projection). In Chicago the public sidewalk runs from the curb to the property
    line. `sides` names the right and left of the axis: east and west for a north-going axis, south and north for an
    east-going one."""
    blocks = parcels.geometry.buffer(0.5).union_all().buffer(-0.5)
    lines = gpd.GeoSeries([blocks.boundary.intersection(axis.buffer(within_m))], crs=parcels.crs).explode(index_parts=False)
    lines = lines[(lines.geom_type == 'LineString') & (lines.length > 1.0)].reset_index(drop=True)
    (x0, y0), (x1, y1) = axis.coords[0], axis.coords[-1]
    def right(line):
        x, y = line.interpolate(0.5, normalized=True).coords[0]
        return (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0) < 0
    side = np.where([right(line) for line in lines], *sides)
    return gpd.GeoDataFrame(dict(kind='back', side=side, source='Cook County parcels'), geometry=lines, crs=parcels.crs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--area', required=True, help='an area config: network/areas/<area>.toml')
    parser.add_argument('--street', required=True, help="a street of the area's config")
    parser.add_argument('--out', type=Path, help="default: the area's reference folder")
    args = parser.parse_args()
    area = Area.load(args.area)
    street, src, crs = area.streets[args.street], area.reference, area.crs
    out = args.out or area.reference_dir
    cache = area.path(src['curbs_cache'])
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(src['curbs_url'], cache)

    axis = street.projected(crs)
    box = tuple(gpd.GeoSeries([axis.buffer(200)], crs=crs).to_crs(src['curbs_crs']).total_bounds)
    curbs = gpd.read_file(f"zip://{cache.resolve()}!{src['curbs_layer']}", bbox=box).to_crs(crs)
    pieces = near(curbs, axis)
    pieces = pieces[~across(pieces, axis)]
    curb, part = pieces.index.get_level_values(0), pieces.index.get_level_values(1)
    ids = pieces[src['curbs_id']].astype(int).astype(str)
    ids = ids.where(~curb.duplicated(keep=False), ids + '-' + part.astype(str))  # a line cut in two: '<id>-0', '<id>-1'
    found = gpd.GeoDataFrame(dict(city_id=ids.to_numpy()), geometry=pieces.geometry.to_numpy(), crs=crs).to_crs(4326)

    name = street.key
    out.mkdir(parents=True, exist_ok=True)
    found.to_file(out / f'{name}_city_curbs.geojson', driver='GeoJSON')
    (out / f'{name}_city_curbs.js').write_text(
        f"// City curb lines ({src['curbs_url']}) along {street.name}, for network/walk2net/evaluate/trace.html\n"
        f'window.CITY_CURBS = {found.to_json()};\n')
    print(f'{len(found)} curb lines along {street.name} -> {out}')

    parcels = fetch_parcels(axis, crs, src['parcels_url'], src['parcels_id'], out / f'{name}_parcels.geojson')
    back = backs(parcels, axis, ('E', 'W') if street.orientation == 'NS' else ('S', 'N')).to_crs(4326)
    back.to_file(out / f'{name}_back.geojson', driver='GeoJSON')
    print(f'{len(parcels)} parcels -> {len(back)} back-of-sidewalk lines '
          f'({(back.side == "E").sum()} east, {(back.side == "W").sum()} west)')


if __name__ == '__main__':
    main()

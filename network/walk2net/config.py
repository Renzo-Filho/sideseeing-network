"""Settings read from files, never written in the code (docs/ARCHITECTURE.md, sections 2 and 3).

- An area (network/areas/<key>.toml): its data folder, its streets' axes, the planner's settings, the reference's
  sources and datum. Its metric projection is the UTM zone of its location unless the file names one.
- A protocol (network/protocols/<name>.toml): how a street is walked. Every protocol walks a street out on one side
  and back on the other, the out leg going north (north-south streets) or east (east-west streets); a protocol says on
  which side of the walker the road is, per street axis. The side of each leg follows from it.

Relative paths in these files start at network/ (ROOT).
"""
import math
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREAS, PROTOCOLS = ROOT / 'areas', ROOT / 'protocols'
AXES = {0.0: 'NS', 90.0: 'EW'}  # street bearing (degrees, modulo 180) -> axis name
OUT_SIDE = {('NS', 'left'): 'E', ('NS', 'right'): 'W', ('EW', 'left'): 'S', ('EW', 'right'): 'N'}  # northbound or eastbound


def utm_epsg(lon, lat):
    """EPSG code of the WGS 84 UTM zone holding a point (32616 for Chicago, 32723 for São Paulo)."""
    return (32600 if lat >= 0 else 32700) + int((lon + 180) // 6) + 1


def _toml(name_or_path, folder):
    path = Path(name_or_path)
    path = path if path.suffix == '.toml' else folder / f'{name_or_path}.toml'
    return path, tomllib.loads(path.read_text())


@dataclass(frozen=True)
class Street:
    key: str
    name: str
    axis: tuple  # ((lon, lat), (lon, lat)): from the street's start to its end

    @property
    def orientation(self):
        """'NS' or 'EW', from the axis's bearing."""
        (lon0, lat0), (lon1, lat1) = self.axis
        bearing = math.degrees(math.atan2((lon1 - lon0) * math.cos(math.radians(lat0)), lat1 - lat0)) % 180
        return 'EW' if 45 <= bearing < 135 else 'NS'

    def projected(self, crs):
        """The axis as a shapely LineString in `crs` (metres)."""
        import geopandas as gpd
        from shapely.geometry import LineString
        return gpd.GeoSeries([LineString(self.axis)], crs=4326).to_crs(crs)[0]


@dataclass(frozen=True)
class Area:
    key: str
    name: str
    data: Path
    crs: int
    grid_axes_deg: tuple
    streets: dict = field(default_factory=dict)
    plan: dict = field(default_factory=dict)
    reference: dict = field(default_factory=dict)

    @classmethod
    def load(cls, name_or_path):
        path, raw = _toml(name_or_path, AREAS)
        south, west, north, east = raw['plan']['bbox']
        streets = {key: Street(key, s['name'], tuple(map(tuple, s['axis']))) for key, s in raw.get('streets', {}).items()}
        return cls(key=path.stem, name=raw['name'], data=ROOT / raw['data'],
                   crs=raw.get('crs') or utm_epsg((west + east) / 2, (south + north) / 2),
                   grid_axes_deg=tuple(raw.get('grid_axes_deg', (0.0, 90.0))), streets=streets,
                   plan=raw['plan'], reference=raw.get('reference', {}))

    def path(self, relative):
        """A path from this area's config, relative to network/."""
        return ROOT / relative

    @property
    def field_log(self):
        return self.data / 'field_log.csv'

    @property
    def reference_dir(self):
        return self.data / 'reference'


@dataclass(frozen=True)
class Protocol:
    name: str
    description: str = ''
    road_side: dict = field(default_factory=dict)  # 'NS' / 'EW' -> 'left' or 'right'; empty for a free route

    @classmethod
    def load(cls, name_or_path):
        path, raw = _toml(name_or_path, PROTOCOLS)
        road = raw.get('road_side', {})
        assert set(road) <= {'NS', 'EW'} and set(road.values()) <= {'left', 'right'}, f'{path}: bad road_side {road}'
        return cls(name=path.stem, description=raw.get('description', ''), road_side=road)

    def road_side_along(self, axis):
        """The walker's road side along an axis ('NS', 'EW', or a bearing in AXES), or None if the protocol does not
        fix it."""
        return self.road_side.get(AXES.get(axis, axis))

    def out_side(self, axis):
        """The sidewalk side ('N', 'S', 'E', 'W') of the out leg along an axis, or None."""
        road = self.road_side_along(axis)
        return road and OUT_SIDE[(AXES.get(axis, axis), road)]

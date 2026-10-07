"""Curio dataflow for the cross-city methods: Index A (top lane), Index B (middle lane) and the harmonized
cross-city similarity model (bottom lane, H).

Each lane is a complete dataflow ending in the same three views: a top-10 table, the five Chicago areas closest to
Brás, and a map of Chicago areas by closeness to Brás. A and B: source loaders → factor nodes → merge → index.
H: one loader and one node per accepted feature family → one merge per domain → standardized profile (C6 hybrid)
→ distance between every pair of units (R1). Node code lives in nodes/*.py; this module only wires and places them.
"""
import json
import uuid
from pathlib import Path

NODES = Path(__file__).resolve().parent / 'nodes'
NS = uuid.UUID('6f1d3c2e-5a4b-4c7d-9e8f-0a1b2c3d4e5f')

# Dataset ids. Curio originally assigned opaque `imported.x…` ids to Discovery Catalog acquisitions;
# rename_imported_ids.py gives this project's imports source-based ids while keeping Curio's required
# `imported.` prefix. The prepared reporting units, Census blocks and São Paulo building heights stay
# registered by register_datasets.py (the São Paulo building GeoPackage exceeds the 512 MiB limit).
D = {
    'sp_units': 'data.sideseeing.sp-districts-prepared',                 # project-derived
    'chi_units': 'data.sideseeing.chicago-community-areas-prepared',     # project-derived
    'chi_blocks': 'data.census.chicago-blocks-pop20-lodes-2022',         # project-derived
    'buildings_sp': 'data.overture.building-heights-sao-paulo',          # project-derived
    'chi_areas_portal': 'imported.cityofchicago.community-areas',  # City of Chicago portal, igwz-8jzy
    'chi_hydro_portal': 'imported.cityofchicago.hydrography',       # City of Chicago portal, knfe-65pw
    'sp_districts_portal': 'imported.geosampa.sao-paulo-districts',  # GeoSampa WFS
    'places_chi': 'imported.overture.places-chicago-2026-08-19',
    'places_sp': 'imported.overture.places-sao-paulo-2026-08-19',
    'cnefe_sp': 'imported.ibge.cnefe-2022-sao-paulo',
    'segments_chi': 'imported.overture.road-segments-chicago-2026-08-19',
    'segments_sp': 'imported.overture.road-segments-sao-paulo-2026-08-19',
    'buildings_chi': 'imported.overture.buildings-chicago-2026-08-19',
    'gtfs_chi': {'stops': 'imported.cta.gtfs-chicago-stops', 'routes': 'imported.cta.gtfs-chicago-routes',
                 'trips': 'imported.cta.gtfs-chicago-trips', 'stop_times': 'imported.cta.gtfs-chicago-stop-times'},
    'gtfs_sp': {'stops': 'imported.sptrans.gtfs-sao-paulo-stops', 'routes': 'imported.sptrans.gtfs-sao-paulo-routes',
                'trips': 'imported.sptrans.gtfs-sao-paulo-trips', 'stop_times': 'imported.sptrans.gtfs-sao-paulo-stop-times'},
    'ghsl_chi': 'imported.ghsl.chicago-height-volume-rasters',
    'ghsl_sp': 'imported.ghsl.sao-paulo-height-volume-rasters',  # raster collections (folder source)
}
# Harmonized model (lane H): the accepted family tables of contract sp_chicago_model_v1, registered as project datasets.
H_TABLES = {  # table path in the repository -> dataset id
    'analysis/results/SP_CHI/m1_m6_step6_2026_10_06/m1_m6_by_unit.csv': 'data.sideseeing.feature-m1-m6',
    'analysis/results/SP_CHI/m3_m4_m7_step8_2026_10_06/m3_m4_m7_by_unit.csv': 'data.sideseeing.feature-m3-m4-m7',
    'analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/footprints/footprint_candidates.csv': 'data.sideseeing.feature-b1',
    'analysis/results/SP_CHI/bv_step5_2026_10_05/bv_step5_by_unit.csv': 'data.sideseeing.feature-bv',
    'analysis/results/SP_CHI/u2_jobs_step3_2026_10_05/tables/u2_jobs.parquet': 'data.sideseeing.feature-u2',
    'analysis/results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet': 'data.sideseeing.feature-u3-chicago',
    'analysis/results/SP_CHI/u3_sp_catchup_2026_10_05/tables/u3_sp.parquet': 'data.sideseeing.feature-u3-sao-paulo',
    'analysis/results/SP_CHI/u4_ptal_step2_2026_10_05/tables/u4_ptal.parquet': 'data.sideseeing.feature-u4',
    'analysis/results/SP_CHI/u6_activity_2026_10_06/u6_by_unit.csv': 'data.sideseeing.feature-u6',
    'analysis/results/SP_CHI/u1_step7_2026_10_06/u1_by_unit.csv': 'data.sideseeing.feature-u1',
}
H_DOMAINS = {'street morphology': ['M1', 'M3', 'M4', 'M6', 'M7'], 'built form': ['B1', 'BV'],
             'use and activity': ['U2', 'U3', 'U4', 'U6', 'U1']}
H_NAMES = {'M1': 'street density', 'M3': 'block size', 'M4': 'block shape', 'M6': 'street hierarchy', 'M7': 'parcel density',
           'B1': 'footprint coverage', 'BV': 'vertical form', 'U2': 'job density', 'U3': 'resident density', 'U4': 'transit access',
           'U6': 'activity composition', 'U1': 'land-use shares'}


def h_families():
    """Per family: the loader's datasets and, per input table, (accepted SHA-256, {source column: model column})."""
    root = Path(__file__).resolve().parents[3]
    chicago = json.loads((root / 'analysis/config/chicago_model_v1.json').read_text())
    cross = json.loads((root / 'analysis/config/sp_chicago_model_v1.json').read_text())
    out = {}
    for f in chicago['families']:
        cols = f.get('columns') or [f['column']]
        out[f['id']] = {'sources': {'table': H_TABLES[f['table']]}, 'tables': {'table': (f['table_sha256'], {c: c for c in cols})}}
    u3 = out['U3']   # U3 has one table per city: Chicago in the Chicago contract, São Paulo in the cross-city one
    out['U3'] = {'sources': {'chicago': u3['sources']['table'], 'sao_paulo': H_TABLES[cross['u3_sao_paulo_table']]},
                 'tables': {'chicago': u3['tables']['table'], 'sao_paulo': (cross['u3_sao_paulo_table_sha256'], {'u3_land_km2': 'u3_acs_land_km2'})}}
    return out


GHSL = {'anbh': 'H_ANBH_E2018', 'agbh': 'H_AGBH_E2018', 'volume': 'V_E2020'}
LABELS = {  # shown as a comment next to each id in the loaders, since imported ids say nothing
    D['sp_units']: 'São Paulo districts, prepared (project)', D['chi_units']: 'Chicago Community Areas, prepared (project)',
    D['chi_blocks']: 'Census 2020 blocks with housing units (project)', D['buildings_sp']: 'Overture building heights, São Paulo (project)',
    D['chi_areas_portal']: 'Discovery · City of Chicago portal · Boundaries - Community Areas',
    D['chi_hydro_portal']: 'Discovery · City of Chicago portal · Hydro',
    D['sp_districts_portal']: 'Discovery · GeoSampa · Distrito',
    D['places_chi']: 'Discovery · local folder · Overture Places, Chicago', D['places_sp']: 'Discovery · local folder · Overture Places, São Paulo',
    D['cnefe_sp']: 'Discovery · local folder · IBGE CNEFE 2022, São Paulo',
    D['segments_chi']: 'Discovery · local folder · Overture road segments, Chicago', D['segments_sp']: 'Discovery · local folder · Overture road segments, São Paulo',
    D['buildings_chi']: 'Discovery · local folder · Overture buildings, Chicago',
    **{v: f'Discovery · local folder · CTA GTFS {k}' for k, v in D['gtfs_chi'].items()},
    **{v: f'Discovery · local folder · SPTrans GTFS {k}' for k, v in D['gtfs_sp'].items()},
    D['ghsl_chi']: 'Discovery · local folder · GHSL rasters, Chicago', D['ghsl_sp']: 'Discovery · local folder · GHSL rasters, São Paulo',
}
UNITS = {'sp_units': D['sp_units'], 'chi_units': D['chi_units']}
SOURCES = {
    'commercial': {**UNITS, 'places_sp': D['places_sp'], 'places_chi': D['places_chi']},
    'residential': {**UNITS, 'cnefe_sp': D['cnefe_sp'], 'chi_blocks': D['chi_blocks']},
    'hubs': {**UNITS, 'gtfs_sp': D['gtfs_sp'], 'gtfs_chi': D['gtfs_chi']},
    'height_overture': {**UNITS, 'buildings_sp': D['buildings_sp'], 'buildings_chi': D['buildings_chi']},
    'streets': {**UNITS, 'segments_sp': D['segments_sp'], 'segments_chi': D['segments_chi']},
    'height_ghsl': {'sp_units_municipal': D['sp_districts_portal'], 'chi_units_geojson': D['chi_areas_portal'],
                    'ghsl_sp': ('collection', D['ghsl_sp']), 'ghsl_chi': ('collection', D['ghsl_chi'])},
    'land': {**UNITS, 'chi_hydrography': D['chi_hydro_portal']},
}
FACTOR_CODE = {'commercial': 'factor_commercial', 'residential': 'factor_residential', 'hubs': 'factor_hubs',
               'height_overture': 'factor_height_overture', 'streets': 'factor_streets', 'height_ghsl': 'factor_height_ghsl', 'land': 'land_area'}
TITLES = {'commercial': 'C · commercial establishments', 'residential': 'R · residential establishments (dwellings)',
          'hubs': 'H · transportation hubs', 'height_overture': 'V · building height (Overture)', 'streets': 'N, L · streets and their length',
          'height_ghsl': 'V · building height (GHSL volume ÷ surface)', 'land': 'Land area (unit minus hydrography)'}
LANES = {'A': ['commercial', 'residential', 'hubs', 'height_overture', 'streets'],
         'B': ['commercial', 'residential', 'hubs', 'height_ghsl', 'streets', 'land']}
LANE_Y = {'A': 0, 'B': 3400, 'H': 7400}
MERGE_SLOTS = 5  # Curio canvas limit for Merge Flow inputs (in_0 … in_4)
RETIRED = {'merge-tail': ('B', 'merge', 'tail')}  # node ids from earlier versions, removed by patch_project.py


def nid(*parts):
    return str(uuid.uuid5(NS, '/'.join(parts)))


def loader_code(lane, factor):
    def note(v):
        key = v[1] if isinstance(v, tuple) else v
        return f'  # {LABELS[key]}' if isinstance(key, str) and key in LABELS else ''

    def render(v, indent):
        if isinstance(v, dict):
            pad = ' ' * (indent + 4)
            return '{\n' + ''.join(f"{pad}'{k}': {render(x, indent + 4)},{note(x)}\n" for k, x in v.items()) + ' ' * indent + '}'
        if isinstance(v, tuple):  # a raster collection: one path per GHSL product
            return f'rasters(curio_collection("{v[1]}"))'
        return f'curio_dataset_path("{v}")'
    head = f'# Method {lane} · sources for {TITLES[factor]}. Paths only: the factor node opens the files.\n'
    if any(isinstance(v, tuple) for v in SOURCES[factor].values()):
        head += ('# GHSL rasters come from Discovery Catalog collections; each row of a collection is one raster file.\n'
                 f'PRODUCTS = {GHSL!r}\n\n\ndef rasters(c):\n    paths = dict(zip(c["product"], c["path"]))\n'
                 '    return {key: paths[product] for key, product in PRODUCTS.items()}\n\n\n')
    return head + 'return ' + render(SOURCES[factor], 0) + '\n'


def collection_ids():
    return sorted(v[1] for src in SOURCES.values() for v in src.values() if isinstance(v, tuple))


def code(name):
    return (NODES / f'{name}.py').read_text()


def dataset_ids():
    out = set()
    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, tuple):
            out.add(v[1])
        else:
            out.add(v)
    walk(SOURCES)
    out |= set(H_TABLES.values())
    return sorted(out)


def map_spec(lane):
    """Vega-Lite map: all 77 areas shaded by index gap to Brás (H: model distance; darker = closer); the five closest
    outlined and numbered."""
    accent = '#d95f02'
    if lane == 'H':
        field, rank, title = 'distance', 'distance_rank', 'Distance to Brás'
        text, sub = 'Harmonized model: Chicago Community Areas by closeness to Brás', 'Darker = smaller model distance (R1, C6 hybrid); the five closest are outlined and numbered by rank'
        tooltip = [{'field': 'name', 'title': 'Area'}, {'field': rank, 'title': 'Rank'}, {'field': field, 'title': 'Distance'}]
    else:
        field, rank, title = 'gap', 'gap_rank', 'Index gap to Brás'
        text, sub = f'Method {lane}: Chicago Community Areas by closeness to Brás', 'Darker = smaller index gap; the five closest are outlined and numbered by rank'
        tooltip = [{'field': 'name', 'title': 'Area'}, {'field': 'gap_rank', 'title': 'Rank'},
                   {'field': 'index', 'title': f'Index {lane}'}, {'field': 'gap', 'title': 'Gap'}]
    return json.dumps({
        '$schema': 'https://vega.github.io/schema/vega-lite/v6.json',
        'title': {'text': text, 'subtitle': sub},
        'width': 560, 'height': 700, 'projection': {'type': 'mercator'},
        'layer': [
            {'mark': {'type': 'geoshape', 'stroke': '#ffffff', 'strokeWidth': 0.6},
             'encoding': {'color': {'field': field, 'type': 'quantitative', 'title': title, 'scale': {'scheme': 'blues', 'reverse': True}},
                          'tooltip': tooltip}},
            {'transform': [{'filter': 'datum.top5'}], 'mark': {'type': 'geoshape', 'filled': False, 'stroke': accent, 'strokeWidth': 3}},
            {'transform': [{'filter': 'datum.top5'}], 'mark': {'type': 'text', 'fontSize': 16, 'fontWeight': 'bold', 'color': accent, 'dy': -2},
             'encoding': {'longitude': {'field': 'lon', 'type': 'quantitative'}, 'latitude': {'field': 'lat', 'type': 'quantitative'},
                          'text': {'field': rank, 'type': 'quantitative'}}},
        ]}, indent=2, ensure_ascii=False)


def graph():
    """Nodes and edges for both lanes. Execution order: list order (topological)."""
    nodes, edges = [], []

    def node(i, ntype, title, x, y, content=None, w=850, h=425):
        n = {'id': i, 'type': ntype, 'x': x, 'y': y, 'width': w, 'height': h, 'title': title, 'in': 'DEFAULT', 'out': 'DEFAULT',
             'saveOutputDataset': False, 'metadata': {'keywords': []}}
        if content is not None:
            n['content'] = content
        nodes.append(n)
        return i

    def edge(s, t, handle='in'):
        edges.append({'id': nid('edge', s, t, handle), 'source': s, 'target': t, 'sourceHandle': 'out', 'targetHandle': handle})

    for lane, factors in LANES.items():
        y0 = LANE_Y[lane]
        merge = nid(lane, 'merge')
        factor_ids = []
        for row, f in enumerate(factors):
            y = y0 + row * 520
            src = node(nid(lane, f, 'sources'), 'curio.builtin/data-loading', f'{lane} · sources · {TITLES[f]}', 0, y, loader_code(lane, f), 800, 300)
            fac = node(nid(lane, f), 'curio.builtin/computation-analysis', f'{lane} · {TITLES[f]}', 950, y, code(FACTOR_CODE[f]))
            edge(src, fac)
            factor_ids.append(fac)
        mid = y0 + (len(factors) - 1) * 260
        x = 2000
        node(merge, 'curio.builtin/merge-flow', f'{lane} · all factors per unit', x, mid, '', 400, 300)
        for k, fac in enumerate(factor_ids[:MERGE_SLOTS]):
            edge(fac, merge, f'in_{k}')
        last = merge
        if len(factor_ids) > MERGE_SLOTS:
            # Curio's Merge Flow takes at most five inputs, and a merge cannot feed a merge (the sandbox resolves one
            # level): join the five factors into one table first, then merge it with the remaining inputs.
            join = node(nid(lane, 'join'), 'curio.builtin/computation-analysis', f'{lane} · join factors per unit', x + 550, mid, code('join_factors'))
            edge(merge, join)
            last = node(nid(lane, 'merge', 'with-land'), 'curio.builtin/merge-flow', f'{lane} · factors and land area', x + 1550, mid, '', 400, 300)
            for k, src in enumerate([join] + factor_ids[MERGE_SLOTS:]):
                edge(src, last, f'in_{k}')
            x += 1550
        idx = node(nid(lane, 'index'), 'curio.builtin/computation-analysis', f'{lane} · index (scale and sum)', x + 550, mid, code('index_' + lane.lower()))
        edge(last, idx)
        x += 1550
        top = node(nid(lane, 'top10'), 'curio.builtin/computation-analysis', f'{lane} · top 10 units by index', x, mid - 330, code('top10'), 850, 300)
        near = node(nid(lane, 'closest'), 'curio.builtin/computation-analysis', f'{lane} · five Chicago areas closest to Brás', x, mid + 330, code('closest_to_bras'), 850, 300)
        edge(idx, top)
        edge(idx, near)
        edge(top, node(nid(lane, 'top10', 'view'), 'curio.builtin/vis-simple', f'{lane} · Top 10 (table)', x + 1000, mid - 330, None, 900, 520))
        edge(near, node(nid(lane, 'closest', 'view'), 'curio.builtin/vis-simple', f'{lane} · Closest to Brás (table)', x + 1000, mid + 330, None, 900, 520))
        cmap = node(nid(lane, 'map'), 'curio.builtin/computation-analysis', f'{lane} · Chicago areas by closeness to Brás (map data)', x, mid + 990, code('chicago_map'), 850, 300)
        edge(idx, cmap)
        edge(cmap, node(nid(lane, 'map', 'view'), 'curio.builtin/vis-vega', f'{lane} · Map: Chicago areas closest to Brás', x + 1000, mid + 990, map_spec(lane), 900, 1000))

    # Lane H: harmonized cross-city similarity model. One loader and one node per family; one merge (≤ 5 inputs) and one
    # join per domain; the three domain tables merge into the standardized profile, then the pairwise distance.
    fams, y, joins = h_families(), LANE_Y['H'], []
    for domain, members in H_DOMAINS.items():
        ids = []
        for f in members:
            src = node(nid('H', f, 'sources'), 'curio.builtin/data-loading', f'H · sources · {f} · {H_NAMES[f]}', 0, y, h_loader_code(f, fams[f]), 800, 300)
            fam = node(nid('H', f), 'curio.builtin/computation-analysis', f'H · {f} · {H_NAMES[f]}', 950, y, h_family_code(f, fams[f]))
            edge(src, fam)
            ids.append(fam)
            y += 520
        mid = y - 520 * (len(members) + 1) / 2
        merge = node(nid('H', domain, 'merge'), 'curio.builtin/merge-flow', f'H · {domain}: all families per unit', 2000, mid, '', 400, 300)
        for k, fam in enumerate(ids):
            edge(fam, merge, f'in_{k}')
        joins.append(node(nid('H', domain, 'join'), 'curio.builtin/computation-analysis', f'H · {domain} per unit', 2550, mid, code('join_factors')))
        edge(merge, joins[-1])
        y += 260
    mid = (LANE_Y['H'] + y - 780) / 2
    merge = node(nid('H', 'merge'), 'curio.builtin/merge-flow', 'H · all families per unit', 3600, mid, '', 400, 300)
    for k, j in enumerate(joins):
        edge(j, merge, f'in_{k}')
    prof = node(nid('H', 'profile'), 'curio.builtin/computation-analysis', 'H · standardized profile (transforms, C6 hybrid scaling)', 4150, mid, code('h_profile'))
    dist = node(nid('H', 'distance'), 'curio.builtin/computation-analysis', 'H · distance between every pair of units (R1, equal family budgets)', 5150, mid, code('h_distance'))
    edge(merge, prof)
    edge(prof, dist)
    x = 6200
    top = node(nid('H', 'top10'), 'curio.builtin/computation-analysis', 'H · top 10 units closest to Brás', x, mid - 330, code('h_top10'), 850, 300)
    near = node(nid('H', 'closest'), 'curio.builtin/computation-analysis', 'H · five Chicago areas closest to Brás', x, mid + 330, code('h_closest'), 850, 300)
    cmap = node(nid('H', 'map'), 'curio.builtin/computation-analysis', 'H · Chicago areas by closeness to Brás (map data)', x, mid + 990, code('h_chicago_map'), 850, 300)
    for t in (top, near, cmap):
        edge(dist, t)
    edge(top, node(nid('H', 'top10', 'view'), 'curio.builtin/vis-simple', 'H · Top 10 closest to Brás (table)', x + 1000, mid - 330, None, 900, 520))
    edge(near, node(nid('H', 'closest', 'view'), 'curio.builtin/vis-simple', 'H · Closest to Brás (table)', x + 1000, mid + 330, None, 900, 520))
    edge(cmap, node(nid('H', 'map', 'view'), 'curio.builtin/vis-vega', 'H · Map: Chicago areas closest to Brás', x + 1000, mid + 990, map_spec('H'), 900, 1000))
    return nodes, edges


def h_family_code(family, spec):
    """nodes/h_family.py with this family's constants inserted after its header comment."""
    lines = code('h_family').splitlines(keepends=True)
    k = next(i for i, line in enumerate(lines) if not line.startswith('#'))
    return ''.join(lines[:k]) + f'FAMILY = {family!r}\nTABLES = {spec["tables"]!r}\n' + ''.join(lines[k:])


def h_loader_code(family, spec):
    lines = ''.join(f"    '{k}': curio_dataset_path(\"{d}\"),  # accepted {family} table\n" for k, d in spec['sources'].items())
    return f'# Harmonized model · sources for {family} ({H_NAMES[family]}). Paths only: the family node opens and checks the files.\nreturn {{\n{lines}}}\n'


def spec(installed_at):
    nodes, edges = graph()
    return {'dataflow': {
        'nodes': nodes, 'edges': edges, 'name': 'Composite urban index: method A and method B',
        'task': 'Build the advisor’s composite index (A, top), the corrected index (B, middle) and the harmonized cross-city similarity '
                'model (H, bottom) for 96 São Paulo districts and 77 Chicago Community Areas',
        'description': 'Method A: counts per unit, pooled min–max, equal weights. Method B: counts per km² of land and GHSL height. '
                       'H: 12 accepted feature families, C6 hybrid scaling, calibrated distance with equal family budgets (sp_chicago_model_v1, R1). '
                       'Each lane ends in the top 10 table, the five Chicago areas closest to Brás and a map of Chicago areas by closeness to Brás.',
        'timestamp': installed_at, 'provenance_id': nid('provenance'), 'packages': ['curio.builtin@1'],
        'datasets': [{'datasetId': d, 'dirName': f'{d}@1', 'origin': 'imported', 'producerNodeId': None, 'consumerNodeIds': [],
                      'installedAt': installed_at} for d in dataset_ids()],
        'categories': {'tags': ['composite index', 'urban form'], 'city': ['São Paulo', 'Chicago'], 'topic': ['similarity'], 'complexity': ['Intermediate']}}}

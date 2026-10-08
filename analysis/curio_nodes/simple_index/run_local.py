"""Execute the lanes of the Curio dataflow outside Curio, the way the sandbox does (each node's code is the body of
userCode(arg); a merge passes the list of its inputs), and check the results against the published tables.

Usage (Curio venv): python run_local.py /path/to/curio/.curio/users/<user>/datasets [--lanes ABH]
"""
import json
from pathlib import Path
import sys
import textwrap
import time

import numpy as np
import pandas as pd

import dataflow

ROOT = Path(__file__).resolve().parents[3]
PUB = ROOT / 'analysis/results/SP_CHI/simple_index_ab_2026_10_01/tables'
PUB_H = ROOT / 'analysis/results/SP_CHI/sp_chicago_model_v2_2026_10_08/tables'
PUB_H_V1 = ROOT / 'analysis/results/SP_CHI/sp_chicago_model_v1_2026_10_06/tables'


def resolver(store):
    def curio_dataset_path(dataset_id):
        m = json.loads((store / f'{dataset_id}@1/manifest.json').read_text())
        return str(store / f'{dataset_id}@1' / m['dataFile'])
    return curio_dataset_path


def collection_reader(store):
    """curio_collection for a folder collection: the index rows, each with path = source root + relpath."""
    def curio_collection(dataset_id):
        m = json.loads((store / f'{dataset_id}@1/manifest.json').read_text())
        src = m['collection']['sourceId']
        root = json.loads((store.parents[2] / 'discovery' / src / 'manifest.json').read_text())['provider']['root']
        frame = pd.read_parquet(store / f'{dataset_id}@1' / m['dataFile'])
        frame['path'] = [str(Path(root) / rel) for rel in frame['relpath']]
        return frame
    return curio_collection


def run(store, lanes='ABH'):
    nodes, edges = dataflow.graph()
    # Curio rules: a Merge Flow keeps at most five inputs (in_0 … in_4) and is not fed by another merge; any other node has one input.
    kinds = {n['id']: n['type'] for n in nodes}
    for target in {e['target'] for e in edges}:
        handles = [e['targetHandle'] for e in edges if e['target'] == target]
        if kinds[target] == 'curio.builtin/merge-flow':
            assert len(handles) <= 5 and all(h in {f'in_{i}' for i in range(5)} for h in handles), f'merge {target} exceeds five inputs'
            assert not any(kinds[e['source']] == 'curio.builtin/merge-flow' for e in edges if e['target'] == target), \
                f'merge {target} is fed by a merge; the Curio sandbox resolves only one merge level'
        else:
            assert handles == ['in'], f'node {target} must have exactly one input'
    inputs = {}
    for e in edges:
        inputs.setdefault(e['target'], []).append(e)
    # Topological order (Kahn), as Curio schedules by dependencies rather than by list position.
    byid, order, done = {n['id']: n for n in nodes}, [], set()
    while len(order) < len(nodes):
        ready = [n for n in nodes if n['id'] not in done and all(e['source'] in done for e in inputs.get(n['id'], []))]
        assert ready, 'cycle in the dataflow'
        order += ready
        done |= {n['id'] for n in ready}
    out = {}
    order = [n for n in order if n['title'][0] in lanes]   # lanes are independent: every node title starts with its lane
    for n in order:
        ins = sorted(inputs.get(n['id'], []), key=lambda e: e['targetHandle'])
        if n['type'] == 'curio.builtin/merge-flow':
            out[n['id']] = [out[e['source']] for e in sorted(ins, key=lambda e: int(e['targetHandle'].split('_')[1]))]
            continue
        if n['type'] in ('curio.builtin/vis-simple', 'curio.builtin/vis-vega'):
            out[n['id']] = out[ins[0]['source']]
            continue
        arg = out[ins[0]['source']] if ins else None
        ns = {'curio_dataset_path': resolver(store), 'curio_collection': collection_reader(store)}
        exec('def userCode(arg):\n' + textwrap.indent(n['content'], '    '), ns)
        t = time.time()
        out[n['id']] = ns['userCode'](arg)
        print(f"{time.time() - t:7.1f} s  {n['title']}", flush=True)
    return {n['title']: out[n['id']] for n in order}


def matrix_diff(pairs, published):
    D = pairs.pivot(index='unit_id', columns='other_id', values='distance')
    pub = pd.read_csv(published, index_col=0)
    D = D.reindex(index=pub.index, columns=pub.columns).to_numpy(copy=True)
    np.fill_diagonal(D, 0)
    return float(np.abs(D - pub.to_numpy()).max())


def check_harmonized(res, profile=None, distance_code=None):
    """Lane H against the published v2 hybrid R1 fit (all pair distances, Brás's ranking, the worked example) and, when
    the profile and the distance node's code are given, the column weights: commerce at weight 0 must give v1."""
    pairs = res['H · distance between every pair of units (R1, equal family budgets)']
    parts = pairs[[c for c in pairs if c.startswith('d2_')]].sum(axis=1)
    rank = pd.read_csv(PUB_H / 'ranking_bras_hybrid_R1.csv', index_col=0)
    bras = pairs[pairs.unit_id == 'SP:10'].sort_values(['distance', 'other_id'])
    chi = bras[bras.other_city == 'Chicago']
    worked = pd.read_csv(PUB_H / 'worked_example_bras_vs_top_chicago.csv', index_col=0).drop('total')
    west = chi.iloc[0]
    shares = pd.Series({f: west['d2_' + f] for f in worked.index}) / west.distance ** 2
    near = res['H · five Chicago areas closest to Brás']
    mp = res['H · Chicago areas by closeness to Brás (map data)']
    out = {}
    if distance_code is not None:
        code = distance_code.replace('COLUMN_WEIGHTS = {}', "COLUMN_WEIGHTS = {'p_commerce': 0}", 1)
        assert code != distance_code
        ns = {}
        exec('def userCode(arg):\n' + textwrap.indent(code, '    '), ns)
        out['commerce_weight_0_v1_max_abs_diff'] = matrix_diff(ns['userCode'](profile), PUB_H_V1 / 'distance_hybrid_R1.csv')
    return {**out, 'max_abs_distance_diff': matrix_diff(pairs, PUB_H / 'distance_hybrid_R1.csv'),
            'family_parts_sum_to_d2': bool(np.allclose(parts, pairs.distance ** 2)),
            'bras_ranking_identical': bras.other_id.tolist() == rank.index.tolist(),
            'bras_chicago_top5': chi.other_name.head(5).tolist(),
            'worked_example_shares_max_diff': float((shares - worked.share).abs().max()),
            'top10_rows': len(res['H · top 10 units closest to Brás']),
            'map_77_areas_lonlat': bool(len(mp) == 77 and mp.crs.to_epsg() == 4326),
            'map_top5_matches_table': mp[mp.top5].sort_values('distance_rank')['name'].tolist() == near['Area'].tolist()}


if __name__ == '__main__':
    lanes = sys.argv[sys.argv.index('--lanes') + 1] if '--lanes' in sys.argv else 'ABH'
    res = run(Path(sys.argv[1]), lanes)
    pub = pd.read_csv(PUB / 'index_A_B.csv').set_index('unit_id')
    report = {}
    if 'H' in lanes:
        dist = next(n for n in dataflow.graph()[0] if n['title'] == 'H · distance between every pair of units (R1, equal family budgets)')
        report['H'] = check_harmonized(res, res['H · standardized profile (transforms, C6 hybrid scaling)'], dist['content'])
        print(res['H · top 10 units closest to Brás'].to_string(index=False))
        print(res['H · five Chicago areas closest to Brás'].to_string(index=False))
    for m in [x for x in 'AB' if x in lanes]:
        idx = res[f'{m} · index (scale and sum)'].set_index('unit_id')
        d = (idx['index'] - pub[f'{m}_index'].reindex(idx.index)).abs().max()
        ranks = bool((idx['rank'] == pub[f'{m}_rank'].reindex(idx.index)).all())
        raw = max(float(np.nanmax(np.abs(idx['raw_' + f] / pub[f'{m}_raw_{f}'].reindex(idx.index) - 1))) for f in 'CRHVNL')
        report[m] = {'max_abs_index_diff': float(d), 'ranks_identical': ranks, 'max_rel_raw_factor_diff': raw}
        print(f'\n== Method {m}: max |index − published| = {d:.3g}; ranks identical: {ranks}; max relative raw-factor diff {raw:.3g}')
        print(res[f'{m} · Top 10 (table)'].to_string(index=False))
        print(res[f'{m} · Closest to Brás (table)'].to_string(index=False))
    match = pd.read_csv(PUB / 'bras_chicago_match.csv')
    for m in [x for x in 'AB' if x in lanes]:
        expect = match[match.method == m].sort_values(['rank_by_index_gap', 'unit_id']).head(5)
        got = res[f'{m} · Closest to Brás (table)']
        report[m]['closest_names_identical'] = got['Area'].tolist() == expect['name'].tolist()
        report[m]['closest_profile_ranks_identical'] = got['Profile rank (of 77)'].tolist() == expect['rank_by_profile_distance'].tolist()
        mp = res[f'{m} · Chicago areas by closeness to Brás (map data)']
        report[m]['map_77_areas_lonlat'] = bool(len(mp) == 77 and mp.crs.to_epsg() == 4326)
        report[m]['map_top5_matches_table'] = mp[mp.top5].sort_values('gap_rank')['name'].tolist() == got['Area'].tolist()
    print('\n' + json.dumps(report, indent=2))
    path = Path(__file__).parent / 'run_local_report.json'          # keep the lanes not run this time
    path.write_text(json.dumps({**(json.loads(path.read_text()) if path.exists() else {}), **report}, indent=2) + '\n')

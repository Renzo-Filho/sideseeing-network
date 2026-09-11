"""Additional cross-file and sampling checks for the SP readiness assessment.

Uses the project Python environment. Optional --rais-only runs with pandas and xlrd
in the bundled Python environment to verify the legacy workbooks as well as CSVs.
"""
from pathlib import Path
import argparse
import io
import json
import re
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'analysis/data/SP'
OUT = ROOT / 'analysis/outputs/sp_audit'


def rais():
    result = {'csv_tables': [], 'sector_comparisons': [], 'workbooks': []}
    tables = {}
    with zipfile.ZipFile(DATA / 'Socioeconomico/RAIS_ESTAB_EMPR_PORTE.zip') as z:
        for name in z.namelist():
            if re.search(r'_\d{4}\.csv$', name):
                raw = z.read(name)
                try:
                    txt = raw.decode('utf-8-sig')
                except UnicodeDecodeError:
                    txt = raw.decode('latin1')
                delimiter = ';' if ';' in txt.splitlines()[0] else ','
                d = pd.read_csv(io.StringIO(txt), sep=delimiter, dtype=str)
                d.rename(columns={d.columns[0]: 'AEDS_2010'}, inplace=True)
                numeric = list(d.columns[11:19])
                for col in numeric:
                    # Counts are integers. Older files use comma thousands,
                    # newer exports use dot thousands; verify the grouping.
                    assert d[col].str.fullmatch(r'\d+|\d{1,3}(?:[.,]\d{3})+').all(), (name, col)
                    d[col] = pd.to_numeric(d[col].str.replace(r'[.,]', '', regex=True), errors='raise')
                year = int(name[-8:-4])
                sector = 'industry' if 'INDUSTRIA' in name else 'commerce_services'
                tables[sector, year] = d
                b = d[d.DISTRITO.eq('BRAS')]
                result['csv_tables'].append({'file': name, 'rows': len(d), 'year': year,
                    'districts': d.loc[d.AEDS_2010.str.fullmatch(r'\d{13}'), 'COD_DIST'].nunique(),
                    'unlocated_rows': int((~d.AEDS_2010.str.fullmatch(r'\d{13}')).sum()),
                    'duplicate_area_ids': int(d.iloc[:,0].duplicated().sum()),
                    'missing_numeric': int(d[numeric].isna().sum().sum()),
                    'bras_establishments': int(b[[c for c in numeric if c.startswith('ESTAB')]].sum().sum()),
                    'bras_jobs': int(b[[c for c in numeric if c.startswith('EMPR')]].sum().sum())})
        for year in sorted({y for _,y in tables}):
            a, b = tables['commerce_services',year], tables['industry',year]
            ac, bc = list(a.columns[11:19]), list(b.columns[11:19])
            av, bv = a.set_index(a.columns[0])[ac], b.set_index(b.columns[0])[bc]
            bv.columns = av.columns
            common = av.index.intersection(bv.index)
            common = common[common.str.fullmatch(r'\d{13}')]
            result['sector_comparisons'].append({'year': year, 'common_areas': len(common),
                'identical_all_eight_counts': int(av.loc[common].eq(bv.loc[common]).all(axis=1).sum())})
        for name in z.namelist():
            if not name.endswith('.xls'):
                continue
            book = pd.ExcelFile(io.BytesIO(z.read(name)))
            rec = {'file': name, 'sheets': []}
            for sheet in book.sheet_names:
                d = book.parse(sheet, header=None)
                sr = {'sheet': sheet, 'rows': len(d), 'columns': len(d.columns)}
                if re.search(r'\d{4}$',sheet):
                    year = int(sheet[-4:]); sector = 'industry' if 'INDUSTRIA' in name else 'commerce_services'
                    body = d.iloc[1:].copy()
                    body = body[body.iloc[:,0].astype(str).str.fullmatch(r'\d{13}')]
                    vals = body.iloc[:,11:19].apply(pd.to_numeric)
                    vals.index = body.iloc[:,0].astype(str)
                    csv = tables[sector,year].set_index('AEDS_2010').iloc[:,10:18]
                    vals.columns = csv.columns
                    common = csv.index.intersection(vals.index)
                    sr.update(data_rows=len(body), compared_rows=len(common),
                              rows_equal_csv=int(vals.loc[common].eq(csv.loc[common]).all(axis=1).sum()))
                rec['sheets'].append(sr)
            result['workbooks'].append(rec)
    return result


def spatial():
    import pyogrio
    import numpy as np
    def read(name):
        return pyogrio.read_dataframe(next(DATA.rglob(name+'.gpkg')))
    p = read('densidade_demografica')
    v = read('indice_paulista_vulnerabilidadesocial')
    key = 'cd_original_setor_censitario'
    a, b = p.set_index(key).sort_index(), v.set_index(key).sort_index()
    audit = read('auditoria_calcadas_bras')
    keep = audit.loc[~audit.descartar]
    blocks = read('quadra_viaria_editada')
    blocks = blocks.loc[blocks.tx_tipo_quadra_viaria.eq('Quadra') & blocks.geometry.is_valid]
    areas = blocks.geometry.area
    return {'population': {'rows': len(p), 'population_sum': float(p.qt_populacao.sum()),
                'same_ids_as_vulnerability': bool(a.index.equals(b.index)),
                'same_population_as_vulnerability': bool(a.qt_populacao.equals(b.qt_populacao)),
                'same_geometry_as_vulnerability': bool((a.geometry.to_wkb().values == b.geometry.to_wkb().values).all()),
                'stored_area_total_km2': float(p.qt_area_hectare.sum()/100),
                'density_max_abs_error_hab_ha': float((p.qt_populacao/p.qt_area_hectare-p.qt_habitante_hectare).abs().max())},
            'bras_observations': {'rows': len(audit), 'retained': len(keep),
                'discarded': int(audit.descartar.sum()), 'point_id_duplicates': int(audit.point_id.duplicated().sum()),
                'start': str(audit.timestamp_gps.min()), 'end': str(audit.timestamp_gps.max()),
                'retained_unique_sql': int(keep.sql.nunique()), 'retained_unique_cc_seg_id': int(keep.cc_seg_id.nunique()),
                'retained_missing_cc_seg_id': int(keep.cc_seg_id.isna().sum()),
                'retained_missing_sql': int(keep.sql.isna().sum()),
                'retained_sql_conflicting_use': int((keep.groupby('sql').tipo_uso.nunique()>1).sum()),
                'retained_sql_conflicting_floors': int((keep.groupby('sql').andares.nunique()>1).sum()),
                'bounds_wgs84': audit.total_bounds.tolist()},
            'citywide_valid_Quadra_only': {'count': len(blocks),
                'area_m2_quantiles': areas.quantile([.25,.5,.75,.9]).to_dict(),
                'compactness_quantiles': (4*np.pi*areas/blocks.length.pow(2)).quantile([.25,.5,.75]).to_dict()}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rais-only', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    name = 'rais_checks.json' if args.rais_only else 'spatial_checks.json'
    result = rais() if args.rais_only else spatial()
    (OUT/name).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))

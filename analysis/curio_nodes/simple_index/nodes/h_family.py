# Harmonized model · one accepted feature family for the 173 units (96 São Paulo districts, 77 Chicago Community Areas).
# FAMILY and TABLES, set by the dataflow below: for each input table, the SHA-256 recorded when the family was accepted
# (analysis/config/chicago_model_v1.json, sp_chicago_model_v2.json) and the columns it supplies. A changed table is refused.
import hashlib
import numpy as np
import pandas as pd


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


parts = []
for key, (digest, columns) in TABLES.items():
    path = arg[key]
    if sha256(path) != digest:
        raise ValueError(f'{FAMILY}: the {key} table changed since the family was accepted ({path})')
    t = pd.read_parquet(path) if path.endswith('.parquet') else pd.read_csv(path)
    t = t[t.unit_id.astype(str).str.match(r'^(SP|CHI):')].copy()
    if FAMILY == 'U1':  # S7-4: under 10% classified occupied land the shares are missing (O'Hare, Marsilac, Parelheiros)
        t.loc[t.occupied_coverage < 0.10, list(columns)] = np.nan
    parts.append(t[['unit_id', *columns]].rename(columns=columns))
out = pd.concat(parts, ignore_index=True)
assert len(out) == 173 and out.unit_id.is_unique, f'{FAMILY}: expected 173 units'
assert FAMILY == 'U1' or not out.isna().any().any(), f'{FAMILY}: missing values'
return out.sort_values('unit_id').reset_index(drop=True)

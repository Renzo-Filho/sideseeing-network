"""Read-only audit of every SP GIS layer; writes reproducible aggregate evidence.

Run from any directory: .venv/bin/python analysis/scripts/audit_sp_data.py
Dependencies: geopandas, pyogrio, pandas, numpy (project environment).
Raw inputs are never edited. ZIPs are read through GDAL's virtual filesystem.
"""
from pathlib import Path
import json
import zipfile

import numpy as np
import pandas as pd
import pyogrio

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "analysis/data/SP"
OUT = ROOT / "analysis/outputs/sp_audit"


def profile(uri, layer, source):
    info = pyogrio.read_info(uri, layer=layer)
    fields = []
    invalid = empty = missing = 0
    types = pd.Series(dtype="int64")
    for offset in range(0, info["features"], 50000):
        g = pyogrio.read_dataframe(uri, layer=layer, skip_features=offset, max_features=50000)
        valid = g.geometry.notna() & ~g.geometry.is_empty
        missing += int(g.geometry.isna().sum())
        empty += int(g.geometry.is_empty.sum())
        invalid += int((valid & ~g.geometry.is_valid).sum())
        types = types.add(g.geom_type.value_counts(), fill_value=0)
        fields.append(pd.DataFrame(g.drop(columns=g.geometry.name)))
    df = pd.concat(fields, ignore_index=True)
    stats = {}
    for c in df:
        s = df[c]
        v = s.dropna()
        record = {"dtype": str(s.dtype), "null": int(s.isna().sum()),
                  "blank": int(s.astype(str).str.strip().eq("").sum()),
                  "unique": int(s.nunique()),
                  "top_values": {str(k): int(n) for k, n in v.value_counts().head(12).items()}}
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            record.update(zero=int(s.eq(0).sum()), negative=int(s.lt(0).sum()),
                          quantiles={str(k): float(n) for k, n in v.quantile([0,.25,.5,.75,.9,1]).items()} if len(v) else {})
        elif pd.api.types.is_datetime64_any_dtype(s):
            record.update(min=str(v.min()), max=str(v.max()))
        stats[c] = record
    return {"source": source, "layer": layer, "features": len(df), "crs": info["crs"],
            "bounds": list(info["total_bounds"]), "geometry_types": types.astype(int).to_dict(),
            "geometry_invalid": invalid, "geometry_empty": empty, "geometry_missing": missing,
            "layer_metadata": info["layer_metadata"], "fields": stats}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for p in sorted(SOURCE.rglob("*")):
        sources = []
        if p.suffix == ".gpkg":
            sources = [(str(p), str(p.relative_to(ROOT)))]
        elif p.suffix == ".zip":
            with zipfile.ZipFile(p) as z:
                sources = [(f"/vsizip/{p}/{n}", f"{p.relative_to(ROOT)}!{n}")
                           for n in z.namelist() if n.endswith((".shp", ".gpkg"))]
        for uri, source in sources:
            for layer, _ in pyogrio.list_layers(uri):
                print(f"Profiling {layer}", flush=True)
                results.append(profile(uri, layer, source))
                (OUT / "gis_profiles.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False))
    (OUT / "gis_profiles.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False))
    pd.DataFrame([{k: v for k, v in r.items() if k != "fields"} for r in results]).to_csv(OUT / "gis_inventory.csv", index=False)
    print(f"Audited {len(results)} layers; output: {OUT}", flush=True)


if __name__ == "__main__":
    main()

"""São Paulo U3 catch-up: Census 2022 residents per km² of district land (same estimand as Chicago U3)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import evaluate_u4_ptal_step2 as u4

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/u3_sp_catchup_2026_10_05"


def main():
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    units, parts = u4.sp_units_and_people()          # tract -> district by area share; residents outside districts reported
    import geopandas as gpd
    d = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet")
    t = pd.DataFrame({"unit_id": "SP:" + d.district_id, "city": "SP", "name": d.nm_distrito_municipal,
                      "land_m2": d.land_area_m2.to_numpy(), "gross_area_m2": d.gross_area_m2.to_numpy()})
    t["residents"] = t.unit_id.map(parts.groupby("unit_id").residents.sum())
    t["u3_land_km2"] = t.residents / (t.land_m2 / 1e6)
    t["u3_gross_km2"] = t.residents / (t.gross_area_m2 / 1e6)
    t["rank_in_city"] = t.u3_land_km2.rank(ascending=False)
    checks = dict(u4.checks)
    prev = pd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N07/census_district_allocation.parquet")
    prev = prev.groupby(prev.district_id.astype(str).str.zfill(2)).population_allocated.sum()
    got = t.set_index(t.unit_id.str[3:]).residents
    checks["matches_sp_prep_v3_allocation"] = {"pass": bool(np.allclose(got.reindex(prev.index), prev, rtol=1e-6)),
                                               "max_abs_diff": float((got.reindex(prev.index) - prev).abs().max())}
    pts = pd.read_parquet(A / "results/SP_CHI/u4_ptal_step2_2026_10_05/tables/u4_ptal.parquet").set_index("unit_id")
    checks["matches_u4_resident_weights"] = {"pass": bool(np.allclose(t.set_index("unit_id").residents, pts.residents.reindex(t.unit_id), rtol=1e-9))}
    checks["no_missing_values"] = {"pass": bool(t.u3_land_km2.notna().all())}
    checks["gross_sensitivity"] = {"spearman": float(t.u3_land_km2.corr(t.u3_gross_km2, method="spearman")),
                                   "areas_moving_5_or_more_ranks": int((t.u3_gross_km2.rank(ascending=False) - t.rank_in_city).abs().ge(5).sum())}
    checks["summary"] = {"median": float(t.u3_land_km2.median()), "max": [t.loc[t.u3_land_km2.idxmax(), "name"], float(t.u3_land_km2.max())],
                         "min": [t.loc[t.u3_land_km2.idxmin(), "name"], float(t.u3_land_km2.min())],
                         "bras": [float(t.loc[t.unit_id == "SP:10", "u3_land_km2"].iloc[0]), int(t.loc[t.unit_id == "SP:10", "rank_in_city"].iloc[0])]}
    t.to_csv(OUT / "tables/u3_sp.csv", index=False)
    t.to_parquet(OUT / "tables/u3_sp.parquet", index=False)
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float, ensure_ascii=False) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float, ensure_ascii=False))


if __name__ == "__main__":
    main()

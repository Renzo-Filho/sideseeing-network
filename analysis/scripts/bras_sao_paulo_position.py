"""Brás's position within São Paulo on every column and family of the cross-city model (MODEL_REPORT §3.1).

Columns: value, São Paulo range and median, rank (1 = highest), within-city z (the all-relative reading) and rank by
|z| (1 = farthest from the São Paulo mean). U6 mix columns are shown as shares; their z is the city-centred log-ratio
standardized within São Paulo, for comparing extremeness only (the model reads them through the Aitchison block).
Families: each district's mean calibrated block gap to the other São Paulo districts (m_b / beta_b, equal weights
inside the family); rank 1 = the most unusual district. Run from the repo root: .venv/bin/python analysis/scripts/bras_sao_paulo_position.py
"""
from pathlib import Path
import numpy as np, pandas as pd
import chicago_model as cm
import sp_chicago_model as m

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/results/SP_CHI/bras_sao_paulo_position_2026_10_16"
U6 = ROOT / "analysis/results/SP_CHI/u6_activity_2026_10_06/u6_by_unit.csv"
REF = m.REFERENCE


def columns(df, fams, sp):
    z = m.scaled(df, fams, "all_relative")
    shares = pd.read_csv(U6, index_col="unit_id")
    fam_of = {c: f for f, cs in fams.items() for c in cs}
    rows = []
    for c in df.columns:
        if c in cm.CLR:
            v = shares.loc[sp, c.replace("u6_clr_city_", "share_")]
            clr = df.loc[sp, c]
            zc = (clr - clr.mean()) / clr.std(ddof=0)
        else:
            v = np.exp(df.loc[sp, c]) if c in ("u6_log_intensity", "ov_m3_wmedian_ln_m2") else df.loc[sp, c]
            zc = z.loc[sp, c]
        v = v.dropna()
        rows.append(dict(column=c, family=fam_of[c], bras=v[REF], sp_min=v.min(), sp_median=v.median(), sp_max=v.max(),
                         rank_highest_first=int(v.rank(ascending=False, method="min")[REF]), districts=len(v),
                         z_within_sao_paulo=round(float(zc[REF]), 3),
                         rank_by_abs_z=int(zc.dropna().abs().rank(ascending=False, method="min")[REF])))
    return pd.DataFrame(rows)


def families(df, subs, fams, sp, ids, scaling):
    i = np.flatnonzero(ids.isin(sp))
    bl = cm.blocks(m.frame_for(df, subs, scaling), fams, levels=m.levels(scaling))
    groups = {f: [b for b in bl if b["family"] == f] for f in fams}
    groups["U6 intensity"] = [b for b in bl if b["family"] == "U6" and b["block"] == "intensity"]
    groups["U6 mix"] = [b for b in bl if b["family"] == "U6" and b["block"] == "composition"]
    rows = []
    for name, bs in groups.items():
        num = sum(b["share"] * np.nan_to_num(b["M"][np.ix_(i, i)]) for b in bs)
        den = sum(b["share"] * ~np.isnan(b["M"][np.ix_(i, i)]) for b in bs)
        g = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
        np.fill_diagonal(g, np.nan)
        with np.errstate(all="ignore"):
            mean = pd.Series(np.nanmean(g, axis=1), index=ids[i]).dropna()   # districts without the family drop out
        rows.append(dict(family=name, scaling=scaling, bras_mean_gap=round(float(mean[REF]), 3),
                         rank_most_unusual=int(mean.rank(ascending=False, method="min")[REF]), districts=len(mean)))
    return pd.DataFrame(rows).sort_values("rank_most_unusual")


def main():
    x, df, subs, names, city, fams = m.load_inputs()
    ids = df.index
    sp = ids[ids.str.startswith("SP:")]
    OUT.mkdir(parents=True, exist_ok=True)
    col = columns(df, fams, sp)
    fam = pd.concat([families(df, subs, fams, sp, ids, s) for s in ("all_relative", "hybrid")])
    col.to_csv(OUT / "bras_columns.csv", index=False)
    fam.to_csv(OUT / "bras_families.csv", index=False)
    print(col.round(3).to_string(index=False), "\n", fam.to_string(index=False))


if __name__ == "__main__":
    main()

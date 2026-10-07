"""Diagnostic: how much existing M2 proxies overlap M1/M3/M7/B1/U3 in SP and Chicago, plus SP v2 omission recheck."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
SP = ROOT / "analysis/results/SP/tables/attributes_primary.csv"
MOD = ROOT / "analysis/results/SP/models/sp_urban_model_v2/tables"
CHI = ROOT / "analysis/results/Chicago/chi_local_2026_09_16_v1/tables"
OUT = ROOT / "analysis/results/SP_CHI/m2_redundancy_2026_09_30"


def rank_r2(y, X):
    """R² of ranked y on ranked X columns (OLS with intercept)."""
    r = lambda s: s.rank().to_numpy(float)
    A = np.column_stack([np.ones(len(y))] + [r(X[c]) for c in X])
    b, *_ = np.linalg.lstsq(A, r(y), rcond=None)
    res = r(y) - A @ b
    return 1 - res.var() / r(y).var()


def correlations(df, target, others, city):
    rows = []
    for name, col in others.items():
        ok = df[[target, col]].dropna()
        rho, p = spearmanr(ok[target], ok[col])
        rows.append({"city": city, "m2_variable": target, "other": name, "column": col,
                     "n": len(ok), "spearman": rho, "p": p})
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    out = {}

    # 1. Recheck SP v2 without_M2 against stored rankings.
    rk = pd.read_csv(MOD / "scenario_rankings.csv", dtype={"district_id": str})
    w = rk[rk.scenario == "without_M2"]
    rho = spearmanr(w["rank"], w["baseline_rank"]).statistic
    top10 = len(set(w.nsmallest(10, "baseline_rank").district_id) & set(w.nsmallest(10, "rank").district_id))
    stored = pd.read_csv(MOD / "scenario_summary.csv").set_index("scenario").loc["without_M2"]
    out["sp_v2_without_m2"] = {"n": len(w), "spearman_recomputed": rho, "spearman_stored": stored.spearman,
                               "top10_retained": top10, "max_rank_shift": int(w.rank_shift.abs().max())}

    # 2. M2 share of each district's squared distance to Brás in SP v2 baseline.
    fc = pd.read_csv(MOD / "family_contributions.csv", dtype={"district_id": str})
    m2 = fc[fc.family == "M2"].contribution_fraction
    share = fc.pivot(index="district_id", columns="family", values="contribution_fraction").mean().sort_values()
    out["sp_v2_family_share_mean"] = share.round(4).to_dict()
    out["sp_v2_m2_share"] = {"median": m2.median(), "max": m2.max(), "families": int(fc.family.nunique())}

    # 3. SP redundancy (96 districts; M2 = 5 m planar proxy).
    sp = pd.read_csv(SP, dtype={"district_id": str})
    sp["junctions_per_street_km"] = sp.intersection_density_proxy_5m_km2 / sp.street_density_km_km2
    sp_others = {"M1 street density": "street_density_km_km2", "M3 block log-area median": "block_log_area_median",
                 "M3 block log-area IQR": "block_log_area_iqr", "M4 compactness median": "block_compactness_median",
                 "M7 parcel density": "cadastral_parcel_density_km2", "B1 coverage (land)": "building_coverage_land",
                 "U3 population density": "population_density_km2", "U2 job density": "formal_job_density_area_first_km2"}
    rows = correlations(sp, "intersection_density_proxy_5m_km2", sp_others, "SP")
    rows += correlations(sp, "junctions_per_street_km", {k: v for k, v in sp_others.items() if k != "M1 street density"}
                         | {"M1 street density": "street_density_km_km2"}, "SP")

    # 4. Chicago (77; M2 = unaccepted endpoint diagnostic; M3 = experimental centerline enclosures).
    ch = pd.read_csv(CHI / "attributes_wide.csv", dtype={"district_id": str})
    ep = pd.read_csv(CHI / "m2_endpoint_candidates.csv", dtype={"district_id": str})
    ch = ch.merge(ep[["district_id", "candidate_density_km2"]], on="district_id", validate="one_to_one")
    ch["junctions_per_street_km"] = ch.candidate_density_km2 / ch.street_density_municipal_km_km2
    ch_others = {"M1 street density": "street_density_municipal_km_km2",
                 "M3 block log-area median (experimental)": "block_log_area_median_experimental",
                 "M3 block log-area IQR (experimental)": "block_log_area_iqr_experimental",
                 "M4 compactness median (experimental)": "block_compactness_median_experimental",
                 "B1 coverage (municipal, land)": "building_coverage_municipal_land"}
    rows += correlations(ch, "candidate_density_km2", ch_others, "Chicago")
    rows += correlations(ch, "junctions_per_street_km", ch_others, "Chicago")
    corr = pd.DataFrame(rows)
    corr.to_csv(OUT / "m2_spearman.csv", index=False)

    # 5. Rank R²: how much of M2's ranking do other families' rankings explain?
    r2 = []
    for city, df, y, sets in [
        ("SP", sp, "intersection_density_proxy_5m_km2",
         {"M1": ["street_density_km_km2"], "M3": ["block_log_area_median"],
          "M1+M3": ["street_density_km_km2", "block_log_area_median"],
          "M1+M3+M7": ["street_density_km_km2", "block_log_area_median", "cadastral_parcel_density_km2"],
          "M1+M3+M7+B1+U3": ["street_density_km_km2", "block_log_area_median", "cadastral_parcel_density_km2",
                             "building_coverage_land", "population_density_km2"]}),
        ("Chicago", ch, "candidate_density_km2",
         {"M1": ["street_density_municipal_km_km2"], "M3exp": ["block_log_area_median_experimental"],
          "M1+M3exp": ["street_density_municipal_km_km2", "block_log_area_median_experimental"],
          "M1+M3exp+B1": ["street_density_municipal_km_km2", "block_log_area_median_experimental",
                          "building_coverage_municipal_land"]})]:
        for label, cols in sets.items():
            d = df[[y] + cols].dropna()
            r2.append({"city": city, "predictors": label, "n": len(d), "rank_r2": rank_r2(d[y], d[cols])})
    pd.DataFrame(r2).to_csv(OUT / "m2_rank_r2.csv", index=False)

    # 6. Shared-denominator check: M1 and M2 both divide by gross area. Correlate log counts after
    #    removing log gross area from each (partial Pearson on logs) and compare with the density correlation.
    def partial(n2, l1, area):
        a = np.column_stack([np.ones(len(area)), np.log(area)])
        res = lambda v: np.log(v) - a @ np.linalg.lstsq(a, np.log(v), rcond=None)[0]
        return float(np.corrcoef(res(n2), res(l1))[0, 1])
    lg = pd.read_parquet(ROOT / "analysis/results/SP/tables/attributes_long.parquet")
    m1 = lg[lg.feature_name == "street_density_km_km2"].set_index("district_id")
    km2 = m1.denominator
    n2 = sp.set_index("district_id").intersection_density_proxy_5m_km2 * km2
    ch_km2 = ch.set_index("district_id").gross_area_m2 / 1e6
    ch_n2 = ep.set_index("district_id").candidate_count
    ch_l1 = ch.set_index("district_id").street_density_municipal_km_km2 * ch_km2
    out["shared_denominator"] = {
        "SP": {"pearson_log_density": float(np.corrcoef(np.log(n2 / km2), np.log(m1.numerator / km2))[0, 1]),
               "partial_log_counts_given_log_area": partial(n2, m1.numerator.loc[n2.index], km2.loc[n2.index]),
               "spearman_log_area_vs_m2": spearmanr(km2.loc[n2.index], n2 / km2).statistic},
        "Chicago": {"pearson_log_density": float(np.corrcoef(np.log(ch_n2 / ch_km2), np.log(ch_l1 / ch_km2))[0, 1]),
                    "partial_log_counts_given_log_area": partial(ch_n2, ch_l1, ch_km2.loc[ch_n2.index]),
                    "spearman_log_area_vs_m2": spearmanr(ch_km2.loc[ch_n2.index], ch_n2 / ch_km2).statistic}}

    out["checks"] = {"sp_rows": len(sp), "chicago_rows": len(ch),
                     "sp_v2_spearman_matches": bool(abs(out["sp_v2_without_m2"]["spearman_recomputed"]
                                                        - out["sp_v2_without_m2"]["spearman_stored"]) < 1e-9)}
    (OUT / "summary.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps(out, indent=2, default=float))
    print(corr.round(3).to_string())
    print(pd.DataFrame(r2).round(3).to_string())


if __name__ == "__main__":
    main()

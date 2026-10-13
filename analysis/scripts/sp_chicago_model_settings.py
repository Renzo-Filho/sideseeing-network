"""São Paulo–Chicago model under named settings (contracts sp_chicago_model_v3 and sp_chicago_model_v4).
Each contract keeps v2's inputs, columns, transforms and calibration rule and sets the scaling, the family weights and
the within-family column weights. Writes that version's tables; the explorer (viz/) offers each version as a preset and
is checked against its distance table.

    python analysis/scripts/sp_chicago_model_settings.py v3|v4"""
import json
import sys
import numpy as np, pandas as pd
import chicago_model as cm
import sp_chicago_model as m

REF = m.REFERENCE
VERSIONS = ("v3", "v4")
contract_path = lambda v: m.A / f"config/sp_chicago_model_{v}.json"


def budgets_of(weights, fams):
    s = sum(weights[f] for f in fams)
    return {f: weights[f] / s for f in fams}


def blocks(df, subs, fams, scaling, cols):
    """cm.blocks with within-family column weights v_j (default 1): m_b = Σ v_j Δ_j² / Σ v_j over v_j > 0, and the
    calibration β_b recomputed on the reweighted block, as viz/model.js and the Curio dataflow do. The U6 log-ratios
    form one composition and are not reweighted."""
    bl = cm.blocks(m.frame_for(df, subs, scaling), fams, levels=m.levels(scaling))
    for b in bl:
        v = np.array([float(cols.get(c, 1)) for c in b["columns"]])
        if b["block"] == "composition" or (v == 1).all():
            continue
        if not (v > 0).any():
            raise ValueError(f"every column of {b['family']} has weight 0: switch the family off instead")
        keep = v > 0
        X, v = b["X"][:, keep], v[keep]
        mm = (np.square(X[:, None, :] - X[None, :, :]) * v).sum(axis=2) / v.sum()      # NaN where a unit lacks the family
        up = mm[np.triu_indices(len(X), 1)]
        cal = float(np.median(up[~np.isnan(up) & (up > 0)]))
        b.update(X=X, columns=[c for c, k in zip(b["columns"], keep) if k], M=mm / cal, cal=cal)
    return bl


def fit(version):
    """The model under a version's settings: (contract, inputs, blocks, budgets, D, each family's part of D²)."""
    x, df, subs, names, city, fams = m.load_inputs(contract_path(version))
    st = x["settings"]
    if st["distance"] != "full":
        raise ValueError("the named settings use the full distance")
    budgets = budgets_of(st["family_weights"], fams)
    bl = blocks(df, subs, fams, st["scaling"], st["column_weights"])
    D, contrib = cm.distance(bl, budgets)
    return x, df, subs, names, city, fams, bl, budgets, D, contrib


def alternatives(version, df, subs, fams, st):
    """Named alternatives as distance matrices (compared with the version in comparison_<version>.csv)."""
    w, cols, s = st["family_weights"], st["column_weights"], st["scaling"]
    d = lambda scaling, weights, columns: cm.distance(blocks(df, subs, fams, scaling, columns), budgets_of(weights, fams))[0]
    eq = dict.fromkeys(fams, 1.0)
    pca = cm.pca(d(s, w, cols), df.index)
    out = {"v2 published (hybrid, equal weights, R1)": d("hybrid", eq, {}),
           "all-relative, equal weights (v2 all-relative R1)": d("all_relative", eq, {}),
           f"hybrid scaling, {version} weights": d("hybrid", w, cols),
           f"{version} weights, PCA distance ({pca['k']} components)": pca["D"]}
    if version == "v3":
        tweaks = [("user draft (B1 0, M3 0.05, U2 0.10)", {"B1": 0, "M3": .05, "U2": .10}), ("U2 0", {"U2": 0}), ("B1 0.05", {"B1": .05}),
                  ("M1 out, M3 0.10 (keep block size instead)", {"M1": 0, "M3": .10}), ("U1 0.10 (land use at the other families' level)", {"U1": .10})]
        out |= {k: d(s, w | t, cols) for k, t in tweaks}
    if version == "v4":
        v3 = json.loads(contract_path("v3").read_text())["settings"]
        out |= {"v3 settings": d(v3["scaling"], v3["family_weights"], v3["column_weights"]),
                "v4 family weights, equal weights inside U1 and M4": d(s, w, {})}
        tweaks = [("B1 0.10", {"B1": .10}), ("B1 0.30", {"B1": .30}), ("U1 0.15", {"U1": .15}), ("U1 0.35", {"U1": .35}),
                  ("U6 0.15", {"U6": .15}), ("U6 0.35", {"U6": .35}), ("BV 0.10 (v3 height weight)", {"BV": .10})]
        out |= {k: d(s, w | t, cols) for k, t in tweaks}
    return out


def main(version):
    x, df, subs, names, city, fams, bl, budgets, D, contrib = fit(version)
    st, OUT = x["settings"], m.ROOT / x["model"]["outputs"]
    ids = df.index.tolist()
    r = ids.index(REF)
    chi = [i for i, u in enumerate(ids) if u.startswith("CHI:")]
    sp = [i for i, u in enumerate(ids) if u.startswith("SP:")]
    pool = [ids[i] for i in chi]
    iu = np.triu_indices(len(ids), 1)
    parts = sum(contrib.values())
    assert np.isfinite(D).all() and np.allclose(D, D.T) and np.allclose(np.diag(D), 0) and np.allclose(parts[iu], D[iu] ** 2)
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    t = lambda name: OUT / "tables" / f"{name}_{version}.csv"

    pd.DataFrame(D, index=ids, columns=ids).to_csv(t("distance"))
    rank = cm.rank_target(D, ids, REF).assign(name=lambda d: d.index.map(names), city=lambda d: d.index.str.split(":").str[0])
    rank["rank_in_city"] = rank.groupby("city").distance.rank(method="min").astype(int)
    rank.to_csv(t("ranking_bras"))
    cm.neighbours(D, ids).assign(name=lambda d: d.unit_id.map(names), neighbour_name=lambda d: d.neighbour.map(names)).to_csv(t("neighbours"), index=False)

    active = {f: v for f, v in contrib.items() if budgets[f] > 0}
    shares = cm.contribution_shares(active, D)
    shares.insert(0, "weight", [budgets[f] for f in shares.index])
    shares.to_csv(t("family_contribution_shares"))

    top = rank[rank.city == "CHI"].head(10)
    ex = pd.DataFrame({f: [active[f][r, ids.index(u)] for u in top.index] for f in active}, index=top.index)
    ex = ex.div(ex.sum(axis=1), axis=0).round(4).assign(name=top.name, distance=top.distance, d2=top.distance ** 2)
    ex[["name", "distance", "d2"] + list(active)].to_csv(t("worked_example_bras_vs_top_chicago"))

    stab = m.reference_stability(bl, fams, budgets, ids, REF, pool).assign(name=lambda d: d.match.map(names))
    stab.to_csv(t("stability_bras_top5_chicago"), index=False)
    draws = cm.weight_draws(bl, fams, budgets, ids)
    draws.to_csv(OUT / "tables" / f"stability_{version}_weight_draws.csv", index=False)

    order = lambda M: [ids[j] for j in sorted(chi, key=lambda j: M[r, j])]
    base5, base10 = order(D)[:5], set(order(D)[:10])
    rows = []
    for name, A in alternatives(version, df, subs, fams, st).items():
        c = cm.compare(A, D)
        rows.append(dict(alternative=name, spearman_pairs=round(c["spearman_pairs"], 3), mean_topk_overlap=round(c["mean_topk_overlap"], 3),
                         bras_chicago_spearman=round(pd.Series(A[r, chi]).corr(pd.Series(D[r, chi]), method="spearman"), 3),
                         bras_chicago_top5_kept=len(set(order(A)[:5]) & set(base5)), bras_chicago_top10_kept=len(set(order(A)[:10]) & base10),
                         mean_other_city_neighbours=round(float(m.other_city_share(A, ids).mean()), 3),
                         bras_chicago_top5=", ".join(names[u] for u in order(A)[:5])))
    pd.DataFrame(rows).to_csv(t("comparison"), index=False)

    z = pd.concat([m.scaled(df, fams, st["scaling"]), df[cm.CLR]], axis=1)
    fam_of = {c: f for f, cs in fams.items() for c in cs}
    on = lambda c: budgets[fam_of[c]] > 0 and float(st["column_weights"].get(c, 1)) > 0
    cols = [c for c in z.columns if on(c)]
    rho = z[cols].corr(method="spearman")
    pairs = [dict(column_a=a, family_a=fam_of[a], column_b=b, family_b=fam_of[b], spearman=round(rho.loc[a, b], 3))
             for k, a in enumerate(cols) for b in cols[k + 1:] if fam_of[a] != fam_of[b] and abs(rho.loc[a, b]) >= .6]
    pd.DataFrame(pairs).sort_values("spearman", key=abs, ascending=False).to_csv(t("active_correlations"), index=False)

    # Brás's place within São Paulo on every column (the evidence the v4 weights cite): 1 = highest value.
    spi, zr = df.index[df.index.str.startswith("SP:")], m.scaled(df, fams, "all_relative")
    prof = pd.DataFrame({"family": [fam_of[c] for c in df.columns], "bras_value": df.loc[REF].values,
                         "rank_in_sao_paulo_highest_first": [int(df.loc[spi, c].rank(ascending=False, method="min")[REF]) for c in df.columns],
                         "units_with_value": [int(df.loc[spi, c].notna().sum()) for c in df.columns],
                         "z_within_sao_paulo": [round(float(zr.at[REF, c]), 3) if c in zr.columns else np.nan for c in df.columns]},
                        index=df.columns)
    prof.to_csv(t("bras_profile_sao_paulo"))

    # Match strength: how far Brás's best cross-city match is, against every unit's best cross-city match.
    best_cross = np.array([D[i, chi if i in sp else sp].min() for i in range(len(ids))])
    nn = (D + np.diag(np.full(len(ids), np.inf))).min(axis=1)
    strength = dict(bras_best_chicago_distance=round(float(D[r, chi].min()), 4),
                    median_best_cross_city_distance=round(float(np.median(best_cross)), 4),
                    bras_best_chicago_percentile_among_best_cross_city=round(float(np.mean(best_cross <= D[r, chi].min())), 4),
                    median_nearest_neighbour_distance=round(float(np.median(nn)), 4),
                    median_pair_distance=round(float(np.median(D[iu])), 4))
    run = dict(contract=x["contract_version"], settings=st, budgets={f: round(v, 6) for f, v in budgets.items()}, reference=REF,
               bras_chicago_top5=[names[u] for u in base5], first_chicago_rank_overall=int(rank[rank.city == "CHI"]["rank"].iloc[0]),
               match_strength=strength, top5_relations_stable=round(float(draws.stable.mean()), 3), seed=cm.SEED, draws=cm.DRAWS)
    (OUT / "run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: run[k] for k in ("contract", "bras_chicago_top5", "first_chicago_rank_overall", "match_strength", "top5_relations_stable")}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in VERSIONS:
        raise SystemExit(f"usage: sp_chicago_model_settings.py {'|'.join(VERSIONS)}")
    main(sys.argv[1])

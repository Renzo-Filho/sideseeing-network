"""São Paulo–Chicago model v3: the final settings (contract sp_chicago_model_v3, user decision 13 October 2026).
Same inputs, columns, transforms and calibration as v2; all-relative scaling, the full distance and the contract's family
weights. Writes the v3 tables; the explorer (viz/) and the Curio dataflow start from these settings and are checked
against tables/distance_v3.csv.

    python analysis/scripts/sp_chicago_model_v3.py"""
import json
import numpy as np, pandas as pd
import chicago_model as cm
import sp_chicago_model as m

CONTRACT = m.A / "config/sp_chicago_model_v3.json"
OUT = m.A / "results/SP_CHI/sp_chicago_model_v3_2026_10_13"
V2 = m.A / "results/SP_CHI/sp_chicago_model_v2_2026_10_08/tables"
REF = m.REFERENCE


def budgets_of(weights, fams):
    s = sum(weights[f] for f in fams)
    return {f: weights[f] / s for f in fams}


def fit():
    """The v3 model: (inputs, blocks, budgets, D, each family's part of D²)."""
    x, df, subs, names, city, fams = m.load_inputs(CONTRACT)
    st = x["settings"]
    if st["distance"] != "full" or any(v != 1 for v in st["column_weights"].values()):
        raise ValueError("v3 is the full distance with every column weight 1")
    budgets = budgets_of(st["family_weights"], fams)
    bl = cm.blocks(m.frame_for(df, subs, st["scaling"]), fams, levels=m.levels(st["scaling"]))
    D, contrib = cm.distance(bl, budgets)
    return x, df, subs, names, city, fams, bl, budgets, D, contrib


def alternatives(df, subs, fams, weights):
    """Named alternatives, each as a distance matrix (compared with v3 in comparison_v3.csv)."""
    blocks = {s: cm.blocks(m.frame_for(df, subs, s), fams, levels=m.levels(s)) for s in ("hybrid", "all_relative")}
    d = lambda s, w: cm.distance(blocks[s], budgets_of(w, fams))[0]
    eq = dict.fromkeys(fams, 1.0)
    D3 = d("all_relative", weights)
    pca = cm.pca(D3, df.index)
    return {
        "v2 published (hybrid, equal weights, R1)": d("hybrid", eq),
        "all-relative, equal weights (v2 all-relative R1)": d("all_relative", eq),
        "hybrid scaling, v3 weights": d("hybrid", weights),
        f"v3 weights, PCA distance ({pca['k']} components)": pca["D"],
        "user draft (B1 0, M3 0.05, U2 0.10)": d("all_relative", weights | {"B1": 0, "M3": .05, "U2": .10}),
        "U2 0": d("all_relative", weights | {"U2": 0}),
        "B1 0.05": d("all_relative", weights | {"B1": .05}),
        "M1 out, M3 0.10 (keep block size instead)": d("all_relative", weights | {"M1": 0, "M3": .10}),
        "U1 0.10 (land use at the other families' level)": d("all_relative", weights | {"U1": .10}),
    }


def main():
    x, df, subs, names, city, fams, bl, budgets, D, contrib = fit()
    ids = df.index.tolist()
    r, chi = ids.index(REF), [i for i, u in enumerate(ids) if u.startswith("CHI:")]
    pool = [ids[i] for i in chi]
    iu = np.triu_indices(len(ids), 1)
    parts = sum(contrib.values())
    assert np.isfinite(D).all() and np.allclose(D, D.T) and np.allclose(np.diag(D), 0) and np.allclose(parts[iu], D[iu] ** 2)
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    t = lambda name: OUT / "tables" / name

    pd.DataFrame(D, index=ids, columns=ids).to_csv(t("distance_v3.csv"))
    rank = cm.rank_target(D, ids, REF).assign(name=lambda d: d.index.map(names), city=lambda d: d.index.str.split(":").str[0])
    rank["rank_in_city"] = rank.groupby("city").distance.rank(method="min").astype(int)
    rank.to_csv(t("ranking_bras_v3.csv"))
    cm.neighbours(D, ids).assign(name=lambda d: d.unit_id.map(names), neighbour_name=lambda d: d.neighbour.map(names)).to_csv(t("neighbours_v3.csv"), index=False)

    active = {f: v for f, v in contrib.items() if budgets[f] > 0}
    shares = cm.contribution_shares(active, D)
    shares.insert(0, "weight", [budgets[f] for f in shares.index])
    shares.to_csv(t("family_contribution_shares_v3.csv"))

    top = rank[rank.city == "CHI"].head(10)
    ex = pd.DataFrame({f: [active[f][r, ids.index(u)] for u in top.index] for f in active}, index=top.index)
    ex = ex.div(ex.sum(axis=1), axis=0).round(4).assign(name=top.name, distance=top.distance, d2=top.distance ** 2)
    ex[["name", "distance", "d2"] + list(active)].to_csv(t("worked_example_bras_vs_top_chicago_v3.csv"))

    stab = m.reference_stability(bl, fams, budgets, ids, REF, pool).assign(name=lambda d: d.match.map(names))
    stab.to_csv(t("stability_bras_top5_chicago_v3.csv"), index=False)
    draws = cm.weight_draws(bl, fams, budgets, ids)
    draws.to_csv(t("stability_v3_weight_draws.csv"), index=False)

    order = lambda M: [ids[j] for j in sorted(chi, key=lambda j: M[r, j])]
    base5, base10 = order(D)[:5], set(order(D)[:10])
    rows = []
    for name, A in alternatives(df, subs, fams, x["settings"]["family_weights"]).items():
        c = cm.compare(A, D)
        rows.append(dict(alternative=name, spearman_pairs=round(c["spearman_pairs"], 3), mean_topk_overlap=round(c["mean_topk_overlap"], 3),
                         bras_chicago_spearman=round(pd.Series(A[r, chi]).corr(pd.Series(D[r, chi]), method="spearman"), 3),
                         bras_chicago_top5_kept=len(set(order(A)[:5]) & set(base5)), bras_chicago_top10_kept=len(set(order(A)[:10]) & base10),
                         mean_other_city_neighbours=round(float(m.other_city_share(A, ids).mean()), 3),
                         bras_chicago_top5=", ".join(names[u] for u in order(A)[:5])))
    pd.DataFrame(rows).to_csv(t("comparison_v3.csv"), index=False)

    z = pd.concat([m.scaled(df, fams, x["settings"]["scaling"]), df[cm.CLR]], axis=1)
    fam_of = {c: f for f, cs in fams.items() for c in cs}
    cols = [c for c in z.columns if budgets[fam_of[c]] > 0]
    rho = z[cols].corr(method="spearman")
    pairs = [dict(column_a=a, family_a=fam_of[a], column_b=b, family_b=fam_of[b], spearman=round(rho.loc[a, b], 3))
             for k, a in enumerate(cols) for b in cols[k + 1:] if fam_of[a] != fam_of[b] and abs(rho.loc[a, b]) >= .6]
    pd.DataFrame(pairs).sort_values("spearman", key=abs, ascending=False).to_csv(t("active_correlations_v3.csv"), index=False)

    run = dict(contract=x["contract_version"], settings=x["settings"], budgets={f: round(v, 6) for f, v in budgets.items()},
               reference=REF, bras_chicago_top5=[names[u] for u in base5], first_chicago_rank_overall=int(rank[rank.city == "CHI"]["rank"].iloc[0]),
               top5_relations_stable=round(float(draws.stable.mean()), 3), seed=cm.SEED, draws=cm.DRAWS)
    (OUT / "run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(run, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

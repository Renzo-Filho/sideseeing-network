"""Chicago-only urban similarity model (contract chicago_model_v1; MODEL_PLAN final review J-1 to J-10, runs R1 to R3).
Shared by analysis/chicago_model_analysis.ipynb: every number in docs/chicago/MODEL_REPORT.md comes from these functions."""
import hashlib, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.stats import norm
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
CONTRACT = A / "config/chicago_model_v1.json"
OUT = A / "results/Chicago/chicago_model_v1_2026_10_06"
SEED, DRAWS, CAP, TOPK, STABLE, MERGE_RHO, PRUNE_RHO, PCA_VAR = 20261006, 500, 3.0, 5, 0.80, 0.90, 0.70, 0.90
CLR = ["u6_clr_city_food_drink", "u6_clr_city_retail", "u6_clr_city_services_offices", "u6_clr_city_making_storing", "u6_clr_city_institutions"]
TRANSFORM = {"m1_km_per_km2": "log", "ov_m3_wmedian_ln_m2": "identity", "ov_m4_wmedian_compactness": "identity",   # J-5
             "ov_m4_wmedian_elongation": "log", "m6_major_share": "identity", "m7_parcels_per_km2": "log",
             "B1_coverage_land": "identity", "bv_height_built_m": "log", "u2_jobs_land_km2": "log", "u3_acs_land_km2": "log",
             "u4_ptai_avg_resident": "log", "u6_log_intensity": "identity",
             "p_residential": "identity", "p_commerce": "identity", "p_industrial": "identity", "p_institutional": "identity",
             # sensitivity substitutes (J-9)
             "ov_m3_median_ln_m2_unweighted": "identity", "m7_median_ln_m2": "identity", "bi_volume_per_land_m": "log"}
U1_MIN_COVERAGE = 0.10     # S7-4: below 10% classified occupied land the U1 composition is missing (extended from entropy to shares)
DOMAIN = {"M1": "street morphology", "M3": "street morphology", "M4": "street morphology", "M6": "street morphology",
          "M7": "street morphology", "B1": "built form", "BV": "built form", "U2": "use and activity", "U3": "use and activity",
          "U4": "use and activity", "U6": "use and activity", "U1": "use and activity"}
SUBSTITUTES = {"M3_unweighted": ("M3", "ov_m3_wmedian_ln_m2", "ov_m3_median_ln_m2_unweighted"),
               "M7_median_parcel_size": ("M7", "m7_parcels_per_km2", "m7_median_ln_m2"),
               "BV_volume": ("BV", "bv_height_built_m", "bi_volume_per_land_m")}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(p):
    return pd.read_csv(p) if str(p).endswith(".csv") else pd.read_parquet(p)


def load_inputs(contract=CONTRACT):
    """Frozen inputs: every family table is checked against the SHA-256 recorded at acceptance; Chicago rows only."""
    c = json.loads(Path(contract).read_text())
    families, frames, extra = {}, [], []
    for f in c["families"]:
        p = ROOT / f["table"]
        if sha(p) != f["table_sha256"]:
            raise ValueError(f"{f['id']}: {f['table']} changed since acceptance")
        t = read(p)
        t = t[t.unit_id.astype(str).str.startswith("CHI:")].set_index("unit_id")
        cols = f.get("columns") or [f["column"]]
        if f["id"] == "U1":
            t.loc[t.occupied_coverage < U1_MIN_COVERAGE, cols] = np.nan
        families[f["id"]] = cols
        frames.append(t[cols])
        extra.append(t[[k for _, old, k in SUBSTITUTES.values() if k in t.columns and old in cols]])
    df = pd.concat(frames, axis=1).sort_index()
    if len(df) != 77 or df.drop(columns=families.get("U1", [])).isna().any().any():
        raise ValueError("expected 77 Chicago rows, complete outside U1")
    subs = pd.concat(extra, axis=1).sort_index()
    ca = pd.read_csv(A / "results/SP_CHI/u2_jobs_step3_2026_10_05/tables/u2_jobs.csv").set_index("unit_id")
    names = ca.loc[df.index, "name"].str.title().str.replace("Ohare", "O'Hare").str.replace("Mckinley", "McKinley")
    order = [f for f in ["M1", "M3", "M4", "M6", "M7", "B1", "BV", "U2", "U3", "U4", "U6", "U1"] if f in families]
    return c, df, subs, names, {k: families[k] for k in order}


def transform(x, kind):
    return np.log(x) if kind == "log" else x.astype(float)


def scale(t, method="standard"):
    """J-6: z-score (population SD) capped at ±3; sensitivities: robust median/IQR and rank normal scores."""
    if method == "standard":
        return ((t - t.mean()) / t.std(ddof=0)).clip(-CAP, CAP)
    if method == "robust":
        iqr = t.quantile(.75) - t.quantile(.25)
        return (t - t.median()) / (iqr if iqr > 0 else t.std(ddof=0))
    if method == "rank":
        return pd.Series(norm.ppf((t.rank() - .5) / len(t)), index=t.index)
    raise ValueError(method)


def scale_column(x, col, method="standard", level="absolute"):
    """C6: 'absolute' standardizes over all rows given; 'relative' standardizes within each city (ID prefix before ':')."""
    t = transform(x, TRANSFORM[col])
    if level == "relative":
        return t.groupby(t.index.str.split(":").str[0]).transform(lambda g: scale(g, method))
    return scale(t, method)


def scaling_table(df, cols):
    rows = []
    for c in cols:
        t = transform(df[c], TRANSFORM[c])
        z = (t - t.mean()) / t.std(ddof=0)
        rows.append(dict(column=c, transform=TRANSFORM[c], mean=t.mean(), sd=t.std(ddof=0), median=t.median(),
                         iqr=t.quantile(.75) - t.quantile(.25), areas_capped=int((z.abs() > CAP).sum()),
                         capped=", ".join(z.index[z.abs() > CAP])))
    return pd.DataFrame(rows).set_index("column")


def blocks(df, families, method="standard", calibration="median", levels=None):
    """Distance blocks. Scalar family: mean squared difference of its scaled columns. U6: intensity block (½ budget) and
    Aitchison block on its unscaled log-ratios (½ budget). Each block is calibrated by its median positive pairwise value
    (J-7); calibration="mean" is a post-hoc sensitivity that equalizes average contributions."""
    out = []
    for fam, cols in families.items():
        scal = [c for c in cols if c not in CLR]
        comp = [c for c in cols if c in CLR]
        parts = []
        if scal:
            parts.append(("intensity" if fam == "U6" else fam,
                          np.column_stack([scale_column(df[c], c, method, (levels or {}).get(c, "absolute")) for c in scal]), scal))
        if comp:
            parts.append(("composition", df[comp].to_numpy(float), comp))
        for name, X, cs in parts:
            m = np.square(X[:, None, :] - X[None, :, :]).mean(axis=2)
            pos = m[np.triu_indices(len(X), 1)]
            pos = pos[~np.isnan(pos) & (pos > 0)]
            cal = float(np.median(pos) if calibration == "median" else np.mean(pos))
            out.append(dict(family=fam, block=name, columns=cs, X=X, M=m / cal, cal=cal, share=1 / len(parts)))
    return out


def contribution_shares(contrib, D):
    """Each family's share of D² over all pairs of areas (mean, median, 90th percentile) and pairs it dominates (> 50%)."""
    iu = np.triu_indices(len(D), 1)
    sh = pd.DataFrame({f: v[iu] / D[iu] ** 2 for f, v in contrib.items()})
    out = pd.DataFrame({"mean_share": sh.mean(), "median_share": sh.median(), "p90_share": sh.quantile(.9),
                        "pairs_over_half": (sh.gt(.5)).sum()})
    return out.sort_values("mean_share", ascending=False)


def equal_budgets(families, groups=()):
    """J-7 equal budget per family; J-4 merged groups share one budget."""
    b = {f: 1.0 for f in families}
    for g in groups:
        for f in g:
            if f in b:
                b[f] = 1.0 / len([x for x in g if x in b])
    s = sum(b.values())
    return {f: v / s for f, v in b.items()}


def domain_budgets(families):
    dom = pd.Series({f: DOMAIN[f] for f in families})
    return {f: 1 / dom.nunique() / (dom == dom[f]).sum() for f in families}


def distance(bl, budgets):
    """D² = Σ_blocks budget·share·calibrated block matrix over the blocks both areas have, divided by the budget of those
    blocks (J-8: pairs with a missing family use the families both areas have). Returns D and each family's part of D²."""
    num, den, contrib = 0, 0, {}
    for b in bl:
        w = budgets[b["family"]] * b["share"]
        ok = ~np.isnan(b["M"])
        num = num + w * np.where(ok, b["M"], 0)
        den = den + w * ok
        contrib[b["family"]] = contrib.get(b["family"], 0) + w * np.where(ok, b["M"], 0)
    return np.sqrt(num / den), {f: v / den for f, v in contrib.items()}


def embedding(bl, budgets, ids):
    """Coordinates whose Euclidean distance equals D exactly (used by PCA and Ward clustering)."""
    cols, names = [], []
    for b in bl:
        f = np.sqrt(budgets[b["family"]] * b["share"] / (b["X"].shape[1] * b["cal"]))
        cols.append(b["X"] * f)
        names += [f"{b['family']}:{c}" for c in b["columns"]]
    return pd.DataFrame(np.column_stack(cols), index=ids, columns=names)


def redundancy(df, families, thr=MERGE_RHO):
    """J-4: Spearman among the scalar columns; family pairs with any |rho| >= thr are merged into one budget group."""
    cols = [c for fam in families.values() for c in fam if c not in CLR]
    rho = df[cols].corr(method="spearman")
    fam_of = {c: f for f, cs in families.items() for c in cs}
    groups = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            if abs(rho.loc[a, b]) >= thr and fam_of[a] != fam_of[b]:
                g = {fam_of[a], fam_of[b]}
                for h in [h for h in groups if h & g]:
                    g |= h
                    groups.remove(h)
                groups.append(g)
    return rho, groups


def prune(df, families, thr=PRUNE_RHO):
    """R3: drop scalar columns until no pair has |rho| >= thr (most such pairs first; ties: higher mean |rho|, then later position)."""
    cols = [c for fam in families.values() for c in fam if c not in CLR]
    keep, log = list(cols), []
    while True:
        r = df[keep].corr(method="spearman").abs()
        np.fill_diagonal(r.values, 0)
        n = (r >= thr).sum()
        if n.max() == 0:
            break
        cand = n[n == n.max()].index
        mean = r.loc[cand].mean(axis=1)
        cand = mean[mean == mean.max()].index
        drop = max(cand, key=keep.index)
        log.append(dict(dropped=drop, pairs_at_or_above=int(n[drop]), mean_abs_rho=round(float(r.loc[drop].mean()), 3),
                        partners=", ".join(f"{p} ({r.loc[drop, p]:.2f})" for p in r.columns[r.loc[drop] >= thr])))
        keep.remove(drop)
    fams = {f: [c for c in cs if c in keep or c in CLR] for f, cs in families.items()}
    return {f: cs for f, cs in fams.items() if cs}, pd.DataFrame(log)


def pca(D, ids, coords=None, var=PCA_VAR):
    """R2: principal components of the R1 geometry, computed from D (principal-coordinate analysis). When every area has
    every family this equals PCA of the centred embedding exactly; it also places O'Hare, whose U1 is missing (J-8).
    Keep the fewest components reaching var; unwhitened scores. Loadings are correlations of scores with model columns."""
    n = len(D)
    J = np.eye(n) - 1 / n
    w, V = np.linalg.eigh(-.5 * J @ np.square(D) @ J)
    o = np.argsort(w)[::-1]
    w, V = w[o], V[:, o]
    pos = w > 1e-10 * w[0]
    scores = V[:, pos] * np.sqrt(w[pos])
    share = w[pos] / w[pos].sum()
    k = int(np.argmax(np.cumsum(share) >= var) + 1)
    S = pd.DataFrame(scores, index=ids, columns=[f"PC{i + 1}" for i in range(scores.shape[1])])
    load = None if coords is None else pd.DataFrame({p: coords.corrwith(S[p]) for p in S.columns[:6]})
    return dict(scores=S, loadings=load, explained=share, cumulative=np.cumsum(share), k=k,
                negative_mass=float(-w[w < 0].sum() / w[pos].sum()), D=squareform(pdist(scores[:, :k])))


def coordinates(bl, ids):
    """Model columns as the distance sees them (scaled scalars, unscaled log-ratios), for loadings and profiles."""
    return pd.DataFrame(np.column_stack([b["X"] for b in bl]), index=ids,
                        columns=[f"{b['family']}:{c}" for b in bl for c in b["columns"]])


def mahalanobis(bl):
    """Regularized (Ledoit-Wolf) Mahalanobis on all columns of complete families (U1 left out: O'Hare missing)."""
    Z = np.column_stack([b["X"] for b in bl if not np.isnan(b["X"]).any()])
    P = np.linalg.inv(LedoitWolf().fit(Z).covariance_)
    return squareform(pdist(Z, "mahalanobis", VI=P))


def rank_target(D, ids, target):
    s = pd.Series(D[list(ids).index(target)], index=ids).drop(target)
    r = pd.DataFrame({"distance": s, "rank": s.rank(method="min").astype(int)})
    return r.sort_values(["distance"], kind="stable")


def neighbours(D, ids, k=TOPK):
    ids = np.array(ids)
    rows = []
    for i, u in enumerate(ids):
        o = [j for j in np.lexsort((ids, D[i])) if j != i][:k]
        rows += [dict(unit_id=u, rank=r + 1, neighbour=ids[j], distance=D[i, j]) for r, j in enumerate(o)]
    return pd.DataFrame(rows)


def topk_sets(D, k=TOPK):
    Dm = D + np.diag(np.full(len(D), np.inf))
    return np.argsort(Dm, axis=1, kind="stable")[:, :k]


def compare(D, base, k=TOPK):
    """Target-free agreement with a baseline: Spearman of all pair distances and mean top-k overlap per area."""
    iu = np.triu_indices(len(D), 1)
    a, b = topk_sets(D, k), topk_sets(base, k)
    overlap = np.mean([len(set(x) & set(y)) / k for x, y in zip(a, b)])
    return dict(spearman_pairs=float(pd.Series(D[iu]).corr(pd.Series(base[iu]), method="spearman")), mean_topk_overlap=float(overlap))


def weight_draws(bl, families, base_budgets, ids, n=DRAWS, seed=SEED):
    """J-9: each family budget × U(0.5, 1.5), renormalised; share of draws in which each baseline top-5 neighbour stays."""
    rng = np.random.default_rng(seed)
    D0, _ = distance(bl, base_budgets)
    base = topk_sets(D0)
    keep = np.zeros(base.shape)
    fams = list(families)
    for _ in range(n):
        m = rng.uniform(.5, 1.5, len(fams))
        b = {f: base_budgets[f] * x for f, x in zip(fams, m)}
        s = sum(b.values())
        D, _ = distance(bl, {f: v / s for f, v in b.items()})
        cur = topk_sets(D)
        keep += np.array([[x in set(c) for x in row] for row, c in zip(base, cur)])
    ids = np.array(ids)
    rows = [dict(unit_id=ids[i], rank=r + 1, neighbour=ids[base[i, r]], share_of_draws=keep[i, r] / n) for i in range(len(ids)) for r in range(base.shape[1])]
    t = pd.DataFrame(rows)
    t["stable"] = t.share_of_draws >= STABLE
    return t


def u6_confidence_filtered(ids, threshold=0.3):
    """J-9 sensitivity: U6 recomputed without Overture places of confidence < threshold (Chicago)."""
    u6 = A / "results/SP_CHI/u6_activity_2026_10_06"
    p = pd.read_parquet(u6 / "overture_places_classified_CHI.parquet").merge(
        pd.concat([pd.read_parquet(f, columns=["id", "confidence"]) for f in sorted((A / "data/Chicago/overture_2026_08_19/place").glob("*.parquet"))]), on="id")
    cls = [c.replace("u6_clr_city_", "") for c in CLR]
    n = p[p["class"].isin(cls) & (p.confidence >= threshold)].groupby(["unit_id", "class"]).size().unstack(fill_value=0).reindex(index=ids, columns=cls, fill_value=0)
    dw = pd.read_csv(u6 / "u6_by_unit.csv").set_index("unit_id").dwellings.reindex(ids)
    lg = np.log(n + .5)
    out = (lg.sub(lg.mean(axis=1), axis=0)).set_axis(CLR, axis=1)
    out.insert(0, "u6_log_intensity", np.log(100 * n.sum(axis=1) / dw))
    return out


def u1_admission(thr=PRUNE_RHO):
    """J-3: a U1 land share is admitted only if max |Spearman| with U6 coordinates, B1 and M1 is < thr in both cities."""
    u1 = read(A / "results/SP_CHI/u1_step7_2026_10_06/u1_by_unit.csv").set_index("unit_id")
    u6 = read(A / "results/SP_CHI/u6_activity_2026_10_06/u6_by_unit.csv").set_index("unit_id")
    m1 = read(A / "results/SP_CHI/m1_m6_step6_2026_10_06/m1_m6_by_unit.csv").set_index("unit_id")
    b1 = read(A / "results/SP_CHI/harmonization_2026_09_22_h1_h3/footprints/footprint_candidates.csv").set_index("unit_id")
    others = pd.concat([u6[["u6_log_intensity"] + CLR], b1[["B1_coverage_land"]], m1[["m1_km_per_km2"]]], axis=1)
    u1 = u1[u1.occupied_coverage >= U1_MIN_COVERAGE]                 # S7-4 coverage rule (O'Hare, Marsilac, Parelheiros out)
    rows = []
    for s in ["p_residential", "p_commerce", "p_industrial", "p_institutional"]:
        r = {"share": s}
        for city in ("CHI", "SP"):
            j = pd.concat([u1[s], others], axis=1, join="inner")
            j = j[j.index.str.startswith(city)].dropna()
            rho = j.drop(columns=s).corrwith(j[s], method="spearman").abs()
            r[f"{city}_max_abs_rho"], r[f"{city}_with"] = round(float(rho.max()), 3), rho.idxmax()
        r["admitted"] = r["CHI_max_abs_rho"] < thr and r["SP_max_abs_rho"] < thr
        rows.append(r)
    return pd.DataFrame(rows).set_index("share")


if __name__ == "__main__":       # one runnable check: the embedding reproduces the distance exactly
    c, df, subs, names, fams = load_inputs()
    D, _ = distance(blocks(df, fams), equal_budgets(fams))
    assert np.isfinite(D).all() and np.allclose(D, D.T) and np.allclose(np.diag(D), 0), "full model distance invalid"
    complete = {f: v for f, v in fams.items() if f != "U1"}
    bl, bud = blocks(df, complete), equal_budgets(complete)
    D, _ = distance(bl, bud)
    E = embedding(bl, bud, df.index)
    assert np.allclose(squareform(pdist(E.to_numpy())), D), "embedding does not reproduce D"
    X = E.to_numpy() - E.to_numpy().mean(axis=0)
    sv = np.linalg.svd(X, compute_uv=False) ** 2
    assert np.allclose(pca(D, df.index)["explained"][:10], (sv / sv.sum())[:10]), "PCoA differs from PCA of the embedding"
    assert abs(sum(bud.values()) - 1) < 1e-12 and np.allclose(D, D.T) and np.allclose(np.diag(D), 0)
    print("ok:", len(df), "areas,", sum(len(b["columns"]) for b in bl), "columns,", len(bl), "blocks")

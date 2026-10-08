"""São Paulo–Chicago urban similarity model (contracts sp_chicago_model_v1 and v2; MODEL_PLAN cross-city X-1 to X-9).
Reuses the Chicago model's transforms, blocks, distance, PCA and robustness functions (chicago_model.py) and adds the
173-unit inputs and the C6 scaling variants. Shared by analysis/sp_chicago_model_analysis.ipynb.

SP_CHI_MODEL_VERSION selects the contract: v2 (default) adds the U1 commerce share; v1 reproduces the first fit."""
import json, os
import geopandas as gpd, numpy as np, pandas as pd
import chicago_model as cm

A, ROOT, CLR = cm.A, cm.ROOT, cm.CLR
VERSION = os.environ.get("SP_CHI_MODEL_VERSION", "v2")
CONTRACT = A / f"config/sp_chicago_model_{VERSION}.json"
OUT = {"v1": A / "results/SP_CHI/sp_chicago_model_v1_2026_10_06",          # each version publishes into its own folder
       "v2": A / "results/SP_CHI/sp_chicago_model_v2_2026_10_08"}[VERSION]
REFERENCE = "SP:10"
U3_SP = "analysis/results/SP_CHI/u3_sp_catchup_2026_10_05/tables/u3_sp.parquet"
RAW_CLR = {c: c.replace("u6_clr_city_", "clr_") for c in CLR}
ABSOLUTE = ["m1_km_per_km2", "ov_m3_wmedian_ln_m2", "ov_m4_wmedian_compactness", "ov_m4_wmedian_elongation",   # same instrument
            "m6_major_share", "m7_parcels_per_km2", "B1_coverage_land", "u3_acs_land_km2"]
RELATIVE = ["u2_jobs_land_km2", "u4_ptai_avg_resident", "bv_height_built_m", "u6_log_intensity",                 # instruments differ
            "p_residential", "p_commerce", "p_industrial", "p_institutional"]
SUB_OF = {new: old for _, old, new in cm.SUBSTITUTES.values()}            # a substitute keeps the level of the column it replaces
ACCENTS = {"Bras": "Brás", "Se": "Sé", "Republica": "República", "Consolacao": "Consolação", "Belem": "Belém", "Butanta": "Butantã",
           "Brasilandia": "Brasilândia", "Agua Rasa": "Água Rasa", "Tatuape": "Tatuapé", "Grajau": "Grajaú", "Jacana": "Jaçanã",
           "Jaragua": "Jaraguá", "Jaguare": "Jaguaré", "Cangaiba": "Cangaíba", "Sao Miguel": "São Miguel", "Sao Lucas": "São Lucas",
           "Sao Mateus": "São Mateus", "Sao Domingos": "São Domingos", "Sao Rafael": "São Rafael", "Cachoeirinha": "Cachoeirinha",
           "Itaim Paulista": "Itaim Paulista", "Jardim Sao Luis": "Jardim São Luís", "Vila Sonia": "Vila Sônia", "Penha": "Penha",
           "Santana": "Santana", "Mandaqui": "Mandaqui", "Limao": "Limão", "Jabaquara": "Jabaquara", "Saude": "Saúde",
           "Cidade Ademar": "Cidade Ademar", "Socorro": "Socorro", "Perus": "Perus", "Ermelino Matarazzo": "Ermelino Matarazzo"}


def levels(scaling):
    """C6 scaling: hybrid (X-4), all_absolute or all_relative; substitutes follow the column they replace."""
    base = {c: ("absolute" if (scaling == "all_absolute" or (scaling == "hybrid" and c in ABSOLUTE)) else "relative") for c in ABSOLUTE + RELATIVE}
    return base | {new: base[old] for new, old in SUB_OF.items()}


def load_inputs():
    """173 rows (96 São Paulo, 77 Chicago). Tables checked against the SHA-256 recorded at acceptance (Chicago contract)
    and, for São Paulo U3, in the cross-city contract."""
    c = json.loads(cm.CONTRACT.read_text())
    x = json.loads(CONTRACT.read_text())
    override = x.get("family_columns", {})          # v2: U1 adds p_commerce (same accepted table and SHA-256)
    families, frames, extra = {}, [], []
    for f in c["families"]:
        p = ROOT / f["table"]
        if cm.sha(p) != f["table_sha256"]:
            raise ValueError(f"{f['id']}: {f['table']} changed since acceptance")
        t = cm.read(p)
        t = t[t.unit_id.astype(str).str.match(r"^(SP|CHI):")].set_index("unit_id")
        cols = override.get(f["id"]) or f.get("columns") or [f["column"]]
        if f["id"] == "U1":
            t.loc[t.occupied_coverage < cm.U1_MIN_COVERAGE, cols] = np.nan
        if f["id"] == "U3":
            if cm.sha(ROOT / U3_SP) != x["u3_sao_paulo_table_sha256"]:
                raise ValueError("U3 São Paulo table changed")
            sp = cm.read(ROOT / U3_SP).set_index("unit_id").u3_land_km2.rename(cols[0]).to_frame()
            t = pd.concat([t[cols], sp])
        if f["id"] == "U6":
            extra.append(t[list(RAW_CLR.values())])
        families[f["id"]] = cols
        frames.append(t[cols])
        extra.append(t[[k for _, old, k in cm.SUBSTITUTES.values() if k in t.columns and old in cols]])
    df = pd.concat(frames, axis=1).sort_index()
    if len(df) != 173 or df.drop(columns=families["U1"]).isna().any().any():
        raise ValueError("expected 173 rows, complete outside U1")
    subs = pd.concat(extra, axis=1).reindex(df.index)
    chi = pd.read_csv(A / "results/SP_CHI/u2_jobs_step3_2026_10_05/tables/u2_jobs.csv").set_index("unit_id").name
    names = chi.reindex(df.index).str.title().str.replace("Ohare", "O'Hare").str.replace("Mckinley", "McKinley")
    names = names.map(lambda s: ACCENTS.get(s, s) if isinstance(s, str) else s)
    city = pd.Series(df.index.str.split(":").str[0], index=df.index, name="city")
    order = ["M1", "M3", "M4", "M6", "M7", "B1", "BV", "U2", "U3", "U4", "U6", "U1"]
    return x, df, subs, names, city, {k: families[k] for k in order}


def frame_for(df, subs, scaling):
    """All-absolute compares raw log-ratios; hybrid and all-relative use the city-centred ones (X-4)."""
    if scaling != "all_absolute":
        return df
    out = df.copy()
    for centred, raw in RAW_CLR.items():
        out[centred] = subs[raw]
    return out


def scaled(df, families, scaling, method="standard"):
    """Scaled scalar columns as the distance sees them (for R3 Spearman and profiles)."""
    lv = levels(scaling)
    cols = [c for cs in families.values() for c in cs if c not in CLR]
    return pd.DataFrame({c: cm.scale_column(df[c], c, method, lv[c]) for c in cols})


def geometry():
    """District and Community Area polygons with unit IDs (EPSG:4326)."""
    sp = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet")
    sp = gpd.GeoDataFrame({"unit_id": "SP:" + sp.district_id.astype(str).str.zfill(2)}, geometry=sp.geometry.values, crs=sp.crs).to_crs(4326)
    ch = gpd.read_file(A / "data/Chicago/Boundaries_-_Community_Areas_20260831.geojson")
    ch = gpd.GeoDataFrame({"unit_id": "CHI:" + ch.area_numbe.astype(int).astype(str).str.zfill(2)}, geometry=ch.geometry.values, crs=ch.crs).to_crs(4326)
    return sp, ch


def u6_confidence_filtered(ids, threshold=0.3):
    """U6 recomputed without Overture places of confidence < threshold, both cities (J-9 / X-7)."""
    u6 = A / "results/SP_CHI/u6_activity_2026_10_06"
    cls = [c.replace("u6_clr_city_", "") for c in CLR]
    dw = pd.read_csv(u6 / "u6_by_unit.csv").set_index("unit_id").dwellings
    parts = []
    for city, folder in (("CHI", "Chicago"), ("SP", "SP")):
        p = pd.read_parquet(u6 / f"overture_places_classified_{city}.parquet").merge(
            pd.concat([pd.read_parquet(f, columns=["id", "confidence"]) for f in sorted((A / f"data/{folder}/overture_2026_08_19/place").glob("*.parquet"))]), on="id")
        n = p[p["class"].isin(cls) & (p.confidence >= threshold)].groupby(["unit_id", "class"]).size().unstack(fill_value=0).reindex(columns=cls, fill_value=0)
        lg = np.log(n + .5)
        clr = lg.sub(lg.mean(axis=1), axis=0)
        clr = clr - clr.mean()                               # city-centred, as u6_clr_city_*
        clr.columns = CLR
        clr.insert(0, "u6_log_intensity", np.log(100 * n.sum(axis=1) / dw.reindex(n.index)))
        parts.append(clr)
    return pd.concat(parts).reindex(ids)


def reference_stability(bl, families, budgets, ids, ref, pool, k=5, n=cm.DRAWS, seed=cm.SEED):
    """Share of weight draws in which each of the reference's baseline top-k matches within `pool` (e.g. Chicago) stays top-k."""
    rng = np.random.default_rng(seed)
    ids = list(ids)
    r, cols = ids.index(ref), [ids.index(u) for u in pool]
    best = lambda D: [pool[j] for j in np.argsort(D[r, cols], kind="stable")[:k]]
    base = best(cm.distance(bl, budgets)[0])
    hits = dict.fromkeys(base, 0)
    fams = list(families)
    for _ in range(n):
        m = rng.uniform(.5, 1.5, len(fams))
        b = {f: budgets[f] * x for f, x in zip(fams, m)}
        t = sum(b.values())
        cur = set(best(cm.distance(bl, {f: v / t for f, v in b.items()})[0]))
        for u in base:
            hits[u] += u in cur
    return pd.DataFrame({"rank": range(1, k + 1), "match": base, "share_of_draws": [hits[u] / n for u in base]}).assign(stable=lambda d: d.share_of_draws >= cm.STABLE)


def other_city_share(D, ids):
    """Share of each unit's five nearest neighbours that belong to the other city."""
    top = cm.topk_sets(D)
    city = np.array([i.split(":")[0] for i in ids])
    return pd.Series([(city[t] != city[i]).mean() for i, t in enumerate(top)], index=ids)


if __name__ == "__main__":       # runnable check: hybrid R1 is finite and symmetric; the reference is present
    x, df, subs, names, city, fams = load_inputs()
    D, _ = cm.distance(cm.blocks(frame_for(df, subs, "hybrid"), fams, levels=levels("hybrid")), cm.equal_budgets(fams))
    assert np.isfinite(D).all() and np.allclose(D, D.T) and np.allclose(np.diag(D), 0) and REFERENCE in df.index
    print("ok:", x["contract_version"], len(df), "units,", sum(map(len, fams.values())), "columns;", city.value_counts().to_dict(),
          "; missing U1:", df.index[df.p_residential.isna()].tolist())

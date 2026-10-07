"""Step 7: U1 land-use mix (four occupied uses, area-weighted entropy) for Chicago (CMAP LUI 2023) and São Paulo (IPTU 2026 on fiscal lots)."""
import glob, hashlib, json
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
import evaluate_b1_step4 as b1

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
OUT = A / "results/SP_CHI/u1_step7_2026_10_06"
CACHE = A / "work/u1_step7_2026_10_06/sp_lot_areas.parquet"
# Decisions S7-1 to S7-6 fixed by the user on 6 October 2026 before this run (MODEL_PLAN Step 7).
OCC = ["residential", "commerce", "industrial", "institutional"]
SIX = OCC + ["transport", "vacant"]
MIN_COVERAGE, MIN_SPEARMAN = 0.10, 0.70
checks = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- crosswalks (S7-3)

def cmap_class(code):
    c = str(code)
    if c.startswith("11"):
        return "residential"
    if c.startswith("12"):
        return "commerce"                     # includes 1215/1216 mixed commercial with residential
    if c == "1360":
        return "open_space"                   # cemetery: not an occupied use (São Paulo IPTU has no cemetery use)
    if c.startswith("13"):
        return "institutional"
    if c.startswith("14"):
        return "industrial"
    if c.startswith("15"):
        return "transport"
    return {"2": "agriculture", "3": "open_space", "4": "vacant", "5": "water", "6": "nonparcel", "9": "unclassified"}.get(c[0], "unclassified")


SP_MIXED = {  # explicit residential + non-residential labels: commerce by rule S7-3; `pred_res` = sensitivity mapping
    "Loja e residência (predominância comercial)": ("commerce", "commerce"),
    "Residência e outro uso (predominância residencial)": ("commerce", "residential"),
    "Prédio de apartamento, não em condomínio, de uso misto (apartamentos e escritórios e/ou consultórios), com ou sem loja (predominância residencial)": ("commerce", "residential"),
    "Prédio de escritório, não em condomínio, de uso misto (apartamentos e escritórios e/ou consultórios) com ou sem loja (predominância comercial)": ("commerce", "commerce"),
}
SP_GENERIC = {"Não residencial", "Outras edificações de uso coletivo, com utilização múltipla", "Outras edificações de uso especial, com utilização múltipla"}
SP_CAT = {"residential": "residential", "commerce/services": "commerce", "industry/warehouse": "industrial",
          "institutional": "institutional", "transport/utilities": "transport", "vacant": "vacant"}


def sp_crosswalk():
    m = pd.read_csv(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N03/use_mapping.csv")
    prim, sens = {}, {}
    for r in m.itertuples():
        if r.use_raw in SP_MIXED:
            prim[r.use_raw], sens[r.use_raw] = SP_MIXED[r.use_raw]
        elif r.use_raw in SP_GENERIC:
            prim[r.use_raw] = sens[r.use_raw] = "unclassified"
        elif r.use_raw == "Posto de serviço":
            prim[r.use_raw] = sens[r.use_raw] = "commerce"     # fuel station: commercial in CMAP
        else:
            prim[r.use_raw] = sens[r.use_raw] = SP_CAT[r.category]
    return prim, sens


# ---------------------------------------------------------------- area accounting

def clip_areas(polys, units, cols):
    a, b = units.sindex.query(polys.geometry, predicate="intersects")
    part = shapely.intersection(polys.geometry.values[a], units.geometry.values[b])
    df = pd.DataFrame({"unit_id": units.unit_id.values[b], "m2": shapely.area(part)})
    for c in cols:
        df[c] = polys[c].values[a]
    return df[df.m2 > 0]


def summarise(areas, units, col, prefix):
    land = units.set_index("unit_id").geometry.area
    piv = areas.pivot_table(index="unit_id", columns=col, values="m2", aggfunc="sum", fill_value=0).reindex(land.index, fill_value=0)
    t = pd.DataFrame(index=land.index)
    t["land_m2"] = land
    for c in piv.columns:
        t[f"{prefix}share_land_{c}"] = piv[c] / land
    occ = piv.reindex(columns=OCC, fill_value=0)
    t[f"{prefix}occupied_coverage"] = occ.sum(axis=1) / land
    p = occ.div(occ.sum(axis=1), axis=0)
    for c in OCC:
        t[f"{prefix}p_{c}"] = p[c]
    h = -(p * np.log(p.where(p > 0))).sum(axis=1) / np.log(4)
    t[f"{prefix}u1_entropy4"] = h.where(t[f"{prefix}occupied_coverage"] >= MIN_COVERAGE)
    six = piv.reindex(columns=SIX, fill_value=0)
    q = six.div(six.sum(axis=1), axis=0)
    t[f"{prefix}entropy6"] = -(q * np.log(q.where(q > 0))).sum(axis=1) / np.log(6)
    covered = piv.sum(axis=1)
    t[f"{prefix}share_land_no_polygon"] = (land - covered).clip(lower=0) / land
    return t


def chicago():
    u = b1.land_units("CHI")
    bb = tuple(u.to_crs(3857).total_bounds)
    lui = pyogrio.read_dataframe(D / "Chicago/LUI_2023_view_332920193481040239.gpkg", bbox=bb, columns=["LANDUSE"]).to_crs(26916)
    lui["geometry"] = shapely.make_valid(lui.geometry.values)
    lui["cls"] = lui.LANDUSE.map(cmap_class)
    t = summarise(clip_areas(lui, u, ["cls"]), u, "cls", "")
    # S7-5: Cook Assessor 2024 PIN classes (major class 2 residential, 3 multi-family).
    pins = pd.concat([pd.read_parquet(f, columns=["class", "chicago_community_area_num"]) for f in sorted(glob.glob(str(D / "Chicago/chicago_cadastral_2026_09_18/cook_universe_2024/*.parquet")))])
    num = pd.to_numeric(pins.chicago_community_area_num, errors="coerce")
    checks["CHI_cook_pins_without_area"] = {"pins": int(num.isna().sum()), "of": len(pins)}
    pins = pins[num.notna()].assign(unit_id="CHI:" + num[num.notna()].astype(int).astype(str).str.zfill(2))
    pins["res"] = pins["class"].astype(str).str[0].isin(["2", "3"])
    t["ref_residential_pin_share"] = pins.groupby("unit_id").res.mean()
    return t


def sao_paulo():
    u = b1.land_units("SP")
    prim, sens = sp_crosswalk()
    cols = ["NUMERO DO CONTRIBUINTE", "NUMERO DO CONDOMINIO", "TIPO DE USO DO IMOVEL", "AREA CONSTRUIDA"]
    d = pd.read_csv(D / "SP/Cadastro e Vias/IPTU_2026.csv", sep=";", usecols=cols, dtype=str, encoding="utf-8")
    d["use"] = d["TIPO DE USO DO IMOVEL"].str.strip()
    unmapped = sorted(set(d.use.dropna()) - set(prim))
    checks["SP_iptu_use_labels_unmapped"] = {"pass": not unmapped, "labels": unmapped}
    d["built"] = pd.to_numeric(d["AREA CONSTRUIDA"].str.replace(",", "."), errors="coerce").fillna(0)
    c, condo = d["NUMERO DO CONTRIBUINTE"], d["NUMERO DO CONDOMINIO"].fillna("00-0").str.strip()
    d["lot"] = np.where(condo.eq("00-0"), c.str[:10], c.str[:6] + "C" + condo.str[:2])
    out = {}
    for name, xw in (("cls", prim), ("cls_pred", sens)):
        d["k"] = d.use.map(xw).fillna("unclassified")
        # Built area decides a lot's class; a tiny per-record weight breaks ties when nothing is built (vacant land).
        g = (d.groupby(["lot", "k"]).built.sum() + 1e-6 * d.groupby(["lot", "k"]).size()).unstack(fill_value=0)
        has_res, has_com = g.get("residential", 0) > 0, g.get("commerce", 0) > 0
        known = g.drop(columns=[k for k in ("unclassified",) if k in g.columns])
        lot_cls = known.idxmax(axis=1).where(known.sum(axis=1) > 0, "unclassified")
        if name == "cls":
            lot_cls = lot_cls.mask(has_res & has_com, "commerce")      # S7-3: residential + commercial units -> commerce
        out[name] = lot_cls
    lots = pd.DataFrame(out)
    lot_areas, join = sp_lot_areas(u)
    checks.update(join)
    checks["SP_lot_join"] = {**join["SP_lot_join"], "polygons_without_iptu": int((~lot_areas.lot.drop_duplicates().isin(lots.index)).sum()),
                             "iptu_lots": len(lots), "iptu_lots_without_polygon": int((~lots.index.isin(lot_areas.lot)).sum())}
    areas = lot_areas.merge(lots, left_on="lot", right_index=True, how="left")
    areas[["cls", "cls_pred"]] = areas[["cls", "cls_pred"]].fillna("lot_no_use")
    return sp_finish(u, areas)


def sp_lot_areas(u):
    """Lot polygons clipped to district land: (lot, unit_id, m2). Cached: about 17 minutes."""
    if CACHE.exists():
        return pd.read_parquet(CACHE), json.loads(CACHE.with_suffix(".json").read_text())
    parts = []
    for f in sorted(glob.glob(str(D / "SP/Cadastro e Vias/Lotes/*.gpkg"))):
        g = pyogrio.read_dataframe(f)
        g = g.set_crs(31983, allow_override=True) if g.crs is None else g.to_crs(31983)
        condo_lot = g.lo_condomi.fillna("00").ne("00")
        g["lot"] = np.where(condo_lot, g.lo_setor + g.lo_quadra + "C" + g.lo_condomi, g.lo_setor + g.lo_quadra + g.lo_lote)
        parts.append(g[["lot", "geometry"]])
    poly = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=31983)
    poly["geometry"] = shapely.make_valid(poly.geometry.values)
    dup = poly.lot.duplicated(keep=False)                          # a lot split across partition files is one lot
    merged = poly[dup].dissolve("lot").reset_index()
    poly = pd.concat([poly[~dup], merged], ignore_index=True)
    areas = clip_areas(poly, u, ["lot"])
    join = {"SP_lots_in_several_partitions": int(merged.shape[0]), "SP_lot_join": {"polygons": len(poly)}}
    areas.to_parquet(CACHE)
    CACHE.with_suffix(".json").write_text(json.dumps(join))
    return areas, join


def sp_finish(u, areas):
    t = summarise(areas, u, "cls", "")
    tp = summarise(areas.drop(columns="cls").rename(columns={"cls_pred": "cls"}), u, "cls", "pred_")
    t["pred_u1_entropy4"], t["pred_p_residential"] = tp.pred_u1_entropy4, tp.pred_p_residential
    # S7-5: CNEFE 2022 establishment addresses (species 4, 5, 6, 8) share, by audited district crosswalk.
    xw = pd.read_csv(A / "results/SP_CHI/simple_index_source_audit_2026_10_01/tables/cnefe_district_crosswalk.csv", dtype=str)
    xw = dict(zip(xw.cod, xw.modal_unit_id))
    cn = pd.read_csv(D / "SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv", sep=";", usecols=["COD_DISTRITO", "COD_ESPECIE"], dtype=str)
    cn["unit_id"] = cn.COD_DISTRITO.map(xw)
    cn["est"] = cn.COD_ESPECIE.isin(["4", "5", "6", "8"])
    t["ref_establishment_address_share"] = cn.groupby("unit_id").est.mean()
    return t


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    c, s = chicago(), sao_paulo()
    c.insert(0, "city", "CHI"); s.insert(0, "city", "SP")
    t = pd.concat([c, s])
    t.index.name = "unit_id"
    rho_c = t.loc[t.city == "CHI", "p_residential"].corr(t.loc[t.city == "CHI", "ref_residential_pin_share"], method="spearman")
    rho_s = t.loc[t.city == "SP", "p_commerce"].corr(t.loc[t.city == "SP", "ref_establishment_address_share"], method="spearman")
    checks["S7-5_CHI_residential_vs_cook_pins"] = {"pass": bool(rho_c >= MIN_SPEARMAN), "spearman": float(rho_c)}
    checks["S7-5_SP_commerce_vs_cnefe_establishments"] = {"pass": bool(rho_s >= MIN_SPEARMAN), "spearman": float(rho_s)}
    checks["missing_entropy_below_10pct_coverage"] = t.index[t.u1_entropy4.isna()].tolist()
    u2 = pd.read_parquet(A / "results/SP_CHI/u2_jobs_step3_2026_10_05/tables/u2_jobs.parquet").set_index("unit_id").u2_jobs_land_km2
    u3 = pd.concat([pd.read_parquet(A / "results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet").set_index("unit_id").u3_acs_land_km2,
                    pd.read_parquet(A / "results/SP_CHI/u3_sp_catchup_2026_10_05/tables/u3_sp.parquet").set_index("unit_id").u3_land_km2])
    b1v = pd.read_csv(b1.CAND).set_index("unit_id").B1_coverage_land
    for city, g in t.groupby("city"):
        checks[f"S7-6_{city}_descriptive"] = {
            "median_entropy4": float(g.u1_entropy4.median()), "median_occupied_coverage": float(g.occupied_coverage.median()),
            "min_occupied_coverage": [g.occupied_coverage.idxmin(), float(g.occupied_coverage.min())],
            "spearman_entropy4_vs_entropy6": float(g.u1_entropy4.corr(g.entropy6, method="spearman")),
            "spearman_u1_u2": float(g.u1_entropy4.corr(u2.reindex(g.index), method="spearman")),
            "spearman_u1_u3": float(g.u1_entropy4.corr(u3.reindex(g.index), method="spearman")),
            "spearman_u1_b1": float(g.u1_entropy4.corr(b1v.reindex(g.index), method="spearman")),
            "median_share_land": {k.replace("share_land_", ""): round(float(v), 4) for k, v in g.filter(regex="^share_land_").median().items()}}
    checks["SP_predominance_sensitivity_spearman"] = float(t.loc[t.city == "SP", "u1_entropy4"].corr(t.loc[t.city == "SP", "pred_u1_entropy4"], method="spearman"))
    checks["anchors"] = {u: {"entropy4": float(t.loc[u, "u1_entropy4"]), "entropy6": float(t.loc[u, "entropy6"])} for u in ("SP:10", "CHI:32")}
    t.to_csv(OUT / "u1_by_unit.csv")
    reg = {p.relative_to(ROOT).as_posix(): sha(p) for p in [D / "Chicago/LUI_2023_view_332920193481040239.gpkg", D / "SP/Cadastro e Vias/IPTU_2026.csv",
                                                             A / "work/prepared/SP/sp_prep_2026_09_10_v3/N03/use_mapping.csv",
                                                             D / "SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv"]}
    (OUT / "source_register.json").write_text(json.dumps(reg, indent=2) + "\n")
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float, ensure_ascii=False) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float, ensure_ascii=False)[:700])


if __name__ == "__main__":
    main()

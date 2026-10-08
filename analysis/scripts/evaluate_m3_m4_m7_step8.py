"""Step 8: M3 block size and M4 block shape from street faces of the M1 Overture network (area-weighted), and M7 mapped
ground-parcel density, Chicago and São Paulo, with municipal and official-block validation.
Decisions S8-1 to S8-8 fixed by the user on 6 October 2026 before this run (MODEL_PLAN Step 8)."""
import glob, hashlib, json
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
import evaluate_b1_step4 as b1
import evaluate_m1_m6_step6 as m1
import evaluate_chicago_m7_ground_pieces_2026_09_30 as gp
from harmonization.geometry import polygonal

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
OUT = A / "results/SP_CHI/m3_m4_m7_step8_2026_10_06"
CRS = {"CHI": 26916, "SP": 31983}
M3_LIKE, M4_LIKE, M3_OFFICIAL, M7_RULE = 0.90, 0.80, 0.80, 0.95
checks = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def gross_units(city):
    if city == "CHI":
        return gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet")[["unit_id", "geometry"]]
    g = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet")
    return gpd.GeoDataFrame({"unit_id": "SP:" + g.district_id.astype(str).str.zfill(2)}, geometry=g.geometry.values, crs=g.crs)


def water(city):
    if city == "CHI":
        h = pyogrio.read_dataframe(D / "Chicago/Hydro_20260916.geojson").to_crs(26916)
        return shapely.union_all(h.geometry.map(polygonal).values)
    return shapely.union_all(gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_water.parquet").geometry.values)


def overture_lines(city):
    folder = "Chicago" if city == "CHI" else "SP"
    s = gpd.read_parquet(next((D / f"{folder}/overture_2026_08_19/segment").glob("*.parquet")), columns=["subtype", "class", "geometry"])
    return s[s.subtype.eq("road") & s["class"].isin(m1.TEN)].to_crs(CRS[city]).geometry.values


def municipal_lines(city):
    if city == "CHI":                                   # same street universe as the M1 validation
        c = pyogrio.read_dataframe(D / "Chicago/steet_center_lines_20260915.geojson", columns=["class", "status"]).to_crs(26916)
        return c[c.status.eq("N") & c["class"].isin(m1.CHI_LOCAL_CLASSES)].geometry.values
    lg = pyogrio.read_dataframe(D / "SP/Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg", columns=["lg_id"]).to_crs(31983)
    out = []
    for g in lg.geometry.values:                        # 3 lines carry a NaN vertex mid-line: drop the vertex, keep the street (as M1)
        c = shapely.get_coordinates(g)
        ok = np.isfinite(c).all(axis=1)
        out.append(g if ok.all() else shapely.LineString(c[ok]))
    return np.array(out, dtype=object)


def faces(lines, wat):
    """Polygonize the noded network: whole faces with land area (water removed), exterior compactness and elongation."""
    noded = shapely.union_all(shapely.get_parts(lines))      # nodes crossings and dissolves duplicate segments
    f = shapely.get_parts(shapely.polygonize(shapely.get_parts(noded)))
    f = f[shapely.area(f) > 0]
    wet = shapely.area(shapely.intersection(f, wat)) if wat is not None else 0
    ext = shapely.polygons(shapely.get_exterior_ring(f))
    rect = shapely.get_coordinates(shapely.oriented_envelope(f)).reshape(-1, 5, 2)[:, :3]
    s1, s2 = np.hypot(*(rect[:, 1] - rect[:, 0]).T), np.hypot(*(rect[:, 2] - rect[:, 1]).T)
    return gpd.GeoDataFrame({"land_m2": shapely.area(f) - wet,
                             "compactness": 4 * np.pi * shapely.area(ext) / shapely.length(shapely.get_exterior_ring(f)) ** 2,
                             "elongation": np.maximum(s1, s2) / np.minimum(s1, s2)}, geometry=f)


def weights(polys, units):
    """Land of each polygon inside each unit (the polygon keeps its whole area as its value)."""
    a, b = units.sindex.query(polys.geometry.values, predicate="intersects")
    w = shapely.area(shapely.intersection(polys.geometry.values[a], units.geometry.values[b]))
    return pd.DataFrame({"i": a, "unit_id": units.unit_id.values[b], "w": w}).query("w > 1")


def wq(v, w, q):
    o = np.argsort(v)
    v, w = v[o], w[o]
    return float(np.interp(q * w.sum(), np.cumsum(w) - w / 2, v))


def summarise(polys, units, prefix, shape=True):
    p = polys[polys.land_m2 > 1].reset_index(drop=True)
    ww = weights(p, units)
    ww["lnA"] = np.log(p.land_m2.values[ww.i])
    if shape:
        ww["C"], ww["E"] = p.compactness.values[ww.i], p.elongation.values[ww.i]
    rows = {}
    for u, g in ww.groupby("unit_id"):
        v, w = g.lnA.values, g.w.values
        r = {f"{prefix}_m3_wmedian_ln_m2": wq(v, w, .5), f"{prefix}_m3_wiqr_ln": wq(v, w, .75) - wq(v, w, .25), f"{prefix}_land_in_faces_m2": w.sum()}
        if shape:
            r |= {f"{prefix}_m4_wmedian_compactness": wq(g.C.values, w, .5), f"{prefix}_m4_wmedian_elongation": wq(g.E.values, w, .5)}
        rows[u] = r
    t = pd.DataFrame.from_dict(rows, orient="index")
    own = ww.sort_values("w").drop_duplicates("i", keep="last")      # unweighted sensitivity: each face once, in its main unit
    own = own.assign(lnA=np.log(p.land_m2.values[own.i]))
    t[f"{prefix}_m3_median_ln_m2_unweighted"] = own.groupby("unit_id").lnA.median()
    t[f"{prefix}_faces"] = own.groupby("unit_id").size()
    if shape:
        t[f"{prefix}_m4_median_compactness_unweighted"] = own.assign(C=p.compactness.values[own.i]).groupby("unit_id").C.median()
    return t


def m3_m4(city, units):
    wat = water(city)
    o = faces(overture_lines(city), wat)
    checks[f"{city}_overture_faces"] = len(o)
    t = summarise(o, units, "ov")
    mu = faces(municipal_lines(city), wat)
    checks[f"{city}_municipal_faces"] = len(mu)
    t = t.join(summarise(mu, units, "muni"))
    if city == "SP":
        q = pyogrio.read_dataframe(D / "SP/Cadastro e Vias/quadra_viaria_editada.gpkg", columns=["tx_tipo_quadra_viaria"]).to_crs(31983)
        q = q[q.tx_tipo_quadra_viaria.eq("Quadra")].reset_index(drop=True)
        off = gpd.GeoDataFrame({"land_m2": shapely.area(shapely.make_valid(q.geometry.values))}, geometry=shapely.make_valid(q.geometry.values))
    else:
        bl = gpd.read_parquet(A / "work/prepared/Chicago/chi_functional_2026_09_16_v2/blocks.parquet")[["geometry"]].to_crs(26916)
        g = shapely.make_valid(bl.geometry.values)
        off = gpd.GeoDataFrame({"land_m2": shapely.area(g) - shapely.area(shapely.intersection(g, wat))}, geometry=g)
    checks[f"{city}_official_blocks"] = len(off)
    return t.join(summarise(off, units, "official", shape=False))


def m7_chicago(gross):
    g = pd.concat([gpd.read_parquet(f) for f in sorted(glob.glob(str(D / "Chicago/chicago_cadastral_2026_09_18/cook_parcels_2024/*.parquet")))], ignore_index=True)
    g["code"] = g.PARCELTYPE.map(gp.CODES).fillna(0).astype(int)
    p, _ = gp.pieces(g)                                   # 30 September rule: no Elevated*, overlaps >= 90% merged
    pt = gpd.GeoDataFrame({"ln_m2": np.log(p.geometry.area.values)}, geometry=p.representative_point().values, crs=26916)
    j = gpd.sjoin(pt, gross, predicate="within")
    checks["CHI_ground_pieces"] = {"pieces": len(p), "assigned": len(j)}
    u = pd.concat([pd.read_parquet(f, columns=["pin", "chicago_community_area_num"]) for f in glob.glob(str(D / "Chicago/chicago_cadastral_2026_09_18/cook_universe_2024/*.parquet"))])
    num = pd.to_numeric(u.chicago_community_area_num, errors="coerce")
    ref = u[num.notna()].assign(unit_id="CHI:" + num.dropna().astype(int).astype(str).str.zfill(2)).groupby("unit_id").pin.apply(lambda s: s.str[:10].nunique())
    return j.groupby("unit_id").size().rename("m7_parcels"), j.groupby("unit_id").ln_m2.median().rename("m7_median_ln_m2"), ref.rename("ref_records")


def m7_sao_paulo(gross):
    lots = pd.read_parquet(A / "work/u1_step7_2026_10_06/sp_lot_areas.parquet")      # (lot, unit_id, m2) clipped to district land
    tot = lots.groupby("lot").m2.sum()
    main = lots.sort_values("m2").drop_duplicates("lot", keep="last").set_index("lot").unit_id
    checks["SP_lots"] = {"lots": len(tot), "rows": len(lots)}
    ln = np.log(tot[tot > 0])
    d = pd.read_csv(D / "SP/Cadastro e Vias/IPTU_2026.csv", sep=";", usecols=["NUMERO DO CONTRIBUINTE", "NUMERO DO CONDOMINIO"], dtype=str, encoding="utf-8")
    c, condo = d["NUMERO DO CONTRIBUINTE"], d["NUMERO DO CONDOMINIO"].fillna("00-0").str.strip()
    key = pd.Series(np.where(condo.eq("00-0"), c.str[:10], c.str[:6] + "C" + condo.str[:2])).drop_duplicates()   # U1 lot key
    q = pyogrio.read_dataframe(D / "SP/Cadastro e Vias/geoportal_quadra_fiscal_gsc.gpkg", columns=["cd_setor_fiscal", "cd_quadra_fiscal"]).to_crs(31983)
    q["sq"] = q.cd_setor_fiscal.str.zfill(3) + q.cd_quadra_fiscal.str.zfill(3)
    q = gpd.GeoDataFrame({"sq": q.sq}, geometry=shapely.point_on_surface(shapely.make_valid(q.geometry.values)), crs=31983)
    sq = gpd.sjoin(q, gross, predicate="within").drop_duplicates("sq").set_index("sq").unit_id
    ku = key.str[:6].map(sq)
    checks["SP_iptu_lots"] = {"lots": len(key), "located_by_fiscal_block": round(float(ku.notna().mean()), 4)}
    return (main.groupby(main).size().rename("m7_parcels"), ln.groupby(main.reindex(ln.index)).median().rename("m7_median_ln_m2"),
            ku.value_counts().rename("ref_records"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for city in ("CHI", "SP"):
        units, gross = b1.land_units(city), gross_units(city).to_crs(CRS[city])
        t = m3_m4(city, units)
        land_km2 = units.set_index("unit_id").geometry.area / 1e6
        n, ln, ref = (m7_chicago if city == "CHI" else m7_sao_paulo)(gross)
        t = t.reindex(land_km2.index).join([n, ln, ref])
        t["land_km2"] = land_km2
        t["m7_parcels_per_km2"] = t.m7_parcels / t.land_km2
        t["ref_records_per_km2"] = t.ref_records / t.land_km2
        t["ov_land_in_faces_share"] = t.ov_land_in_faces_m2 / (t.land_km2 * 1e6)
        t.insert(0, "city", city)
        rows.append(t)
        print(city, "done", flush=True)
    t = pd.concat(rows)
    t.index.name = "unit_id"
    m = pd.read_csv(A / "results/SP_CHI/m1_m6_step6_2026_10_06/m1_m6_by_unit.csv").set_index("unit_id")
    t["m1"], t["u3"], t["b1"] = m.m1_km_per_km2, m.u3, m.b1
    sp = lambda c, a, b: float(c[a].corr(c[b], method="spearman"))
    for city, c in t.groupby("city"):
        r3, r3o = sp(c, "ov_m3_wmedian_ln_m2", "muni_m3_wmedian_ln_m2"), sp(c, "ov_m3_wmedian_ln_m2", "official_m3_wmedian_ln_m2")
        rc, re = sp(c, "ov_m4_wmedian_compactness", "muni_m4_wmedian_compactness"), sp(c, "ov_m4_wmedian_elongation", "muni_m4_wmedian_elongation")
        r7 = sp(c, "m7_parcels_per_km2", "ref_records_per_km2")
        checks[f"S8-4_{city}"] = {"M3_vs_municipal_faces": {"spearman": r3, "pass": r3 >= M3_LIKE},
                                  "M4_compactness_vs_municipal": {"spearman": rc, "pass": rc >= M4_LIKE},
                                  "M4_elongation_vs_municipal": {"spearman": re, "pass": re >= M4_LIKE},
                                  "M3_vs_official_blocks": {"spearman": r3o, "pass": r3o >= M3_OFFICIAL}}
        checks[f"S8-6_{city}"] = {"M7_density_vs_records": {"spearman": r7, "pass": r7 >= M7_RULE},
                                  "counts_spearman": sp(c, "m7_parcels", "ref_records"),
                                  "median_ratio_parcels_over_records": float((c.m7_parcels / c.ref_records).median()),
                                  "missing_m7": c.index[c.m7_parcels.isna()].tolist()}
        checks[f"S8-8_{city}"] = {
            "units_missing_m3": c.index[c.ov_m3_wmedian_ln_m2.isna()].tolist(),
            "median_land_in_faces_share": float(c.ov_land_in_faces_share.median()),
            "lowest_land_in_faces_share": c.ov_land_in_faces_share.nsmallest(3).round(3).to_dict(),
            "m3_median_block_m2": float(np.exp(c.ov_m3_wmedian_ln_m2.median())),
            "spearman_m3_weighted_vs_unweighted": sp(c, "ov_m3_wmedian_ln_m2", "ov_m3_median_ln_m2_unweighted"),
            "spearman_m3_m1": sp(c, "ov_m3_wmedian_ln_m2", "m1"), "spearman_m4c_m3": sp(c, "ov_m4_wmedian_compactness", "ov_m3_wmedian_ln_m2"),
            "spearman_m4e_m4c": sp(c, "ov_m4_wmedian_elongation", "ov_m4_wmedian_compactness"),
            "spearman_m7_m3": sp(c, "m7_parcels_per_km2", "ov_m3_wmedian_ln_m2"), "spearman_m7_b1": sp(c, "m7_parcels_per_km2", "b1"),
            "spearman_m7_u3": sp(c, "m7_parcels_per_km2", "u3"), "spearman_m7_m1": sp(c, "m7_parcels_per_km2", "m1")}
    for u in ("SP:10", "CHI:32"):
        checks[f"anchor_{u}"] = {k: round(float(t.loc[u, k]), 3) for k in ["ov_m3_wmedian_ln_m2", "ov_m4_wmedian_compactness", "ov_m4_wmedian_elongation", "m7_parcels_per_km2"]}
        checks[f"anchor_{u}"]["m3_block_m2"] = round(float(np.exp(t.loc[u, "ov_m3_wmedian_ln_m2"])))
    t.to_csv(OUT / "m3_m4_m7_by_unit.csv")
    reg = {p.relative_to(ROOT).as_posix(): sha(p) for p in [
        next((D / "Chicago/overture_2026_08_19/segment").glob("*.parquet")), next((D / "SP/overture_2026_08_19/segment").glob("*.parquet")),
        D / "Chicago/steet_center_lines_20260915.geojson", D / "SP/Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg",
        D / "SP/Cadastro e Vias/quadra_viaria_editada.gpkg", D / "SP/Cadastro e Vias/geoportal_quadra_fiscal_gsc.gpkg", D / "SP/Cadastro e Vias/IPTU_2026.csv",
        A / "work/u1_step7_2026_10_06/sp_lot_areas.parquet", A / "work/prepared/Chicago/chi_functional_2026_09_16_v2/blocks.parquet"]}
    (OUT / "source_register.json").write_text(json.dumps(reg, indent=2) + "\n")
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float, ensure_ascii=False) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float, ensure_ascii=False))


if __name__ == "__main__":
    main()

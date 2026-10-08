"""Step 4: B1 footprint-coverage validation (S4-1..S4-6). Usage: evaluate_b1_step4.py CHI|SP|summary."""
import glob, hashlib, json, sys
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
from harmonization.geometry import polygonal

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
OUT = A / "results/SP_CHI/b1_step4_2026_10_05"
TAB = OUT / "tables"
CAND = A / "results/SP_CHI/harmonization_2026_09_22_h1_h3/footprints/footprint_candidates.csv"
# Rules fixed by the user on 5 October 2026 before any test ran (MODEL_PLAN Step 4).
MIN_SPEARMAN, MAX_REL = 0.95, 0.25
TILE = 2000


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def land_units(city):
    if city == "CHI":
        u = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet")[["unit_id", "geometry"]]
        hydro = pyogrio.read_dataframe(D / "Chicago/Hydro_20260916.geojson").to_crs(26916)
        water = shapely.union_all(hydro.geometry.map(polygonal).values)
        u["geometry"] = shapely.difference(u.geometry.values, water)
        return u.sort_values("unit_id").reset_index(drop=True)
    land = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet")
    idc = next(c for c in land.columns if "district" in c.lower() or c == "unit_id")
    land["unit_id"] = land[idc] if str(land[idc].iloc[0]).startswith("SP:") else "SP:" + land[idc].astype(str).str.zfill(2)
    return land[["unit_id", "geometry"]].sort_values("unit_id").reset_index(drop=True)


def coverage(units, b, label):
    """Exact union of footprints clipped to each unit's land, in 2 km tiles (same method as B1.py)."""
    b = b[b.geometry.notna() & ~b.geometry.is_empty].reset_index(drop=True)
    b["geometry"] = shapely.make_valid(b.geometry.values)
    tree = shapely.STRtree(b.geometry.values)
    rows = []
    for u in units.itertuples():
        land = u.geometry
        covered = 0.0
        x0, y0, x1, y1 = land.bounds
        for x in np.arange(np.floor(x0 / TILE) * TILE, x1, TILE):
            for y in np.arange(np.floor(y0 / TILE) * TILE, y1, TILE):
                tile = shapely.box(x, y, x + TILE, y + TILE).intersection(land)
                if tile.area <= 0:
                    continue
                ids = tree.query(tile, predicate="intersects")
                if len(ids):
                    covered += shapely.union_all(shapely.intersection(b.geometry.values[ids], tile)).area
        rows.append({"unit_id": u.unit_id, f"{label}_footprint_m2": covered, "land_m2": land.area, label: covered / land.area})
        assert covered <= land.area + 0.01
    return pd.DataFrame(rows)


def lineage(units, b, src_col, label):
    """Footprint area share by first-listed source dataset, per unit (centroid assignment)."""
    pts = gpd.GeoDataFrame({"src": b[src_col], "a": b.geometry.area}, geometry=b.geometry.centroid, crs=b.crs)
    j = gpd.sjoin(pts, units, predicate="within")
    s = j.groupby(["unit_id", "src"]).a.sum().unstack(fill_value=0)
    return s.div(s.sum(axis=1), axis=0).add_prefix(f"{label}_src_")


def chicago():
    u = land_units("CHI")
    ov = gpd.read_parquet(D / "Chicago/overture_2026_08_19/building/part_0000.parquet", columns=["id", "sources", "geometry"]).to_crs(26916)
    ov["src"] = [s[0]["dataset"] if s is not None and len(s) else "none" for s in ov.sources]
    cook = pd.concat([gpd.read_parquet(f, columns=["geometry"]) for f in sorted(glob.glob(str(D / "Chicago/chicago_cadastral_2026_09_18/cook_buildings_2022/part_*.parquet")))])
    cook = gpd.GeoDataFrame(cook, geometry="geometry").to_crs(26916)
    muni = pyogrio.read_dataframe(D / "Chicago/Building_Footprints_20260915.geojson", columns=[]).to_crs(26916)
    t = coverage(u, ov[["geometry"]].copy(), "overture")
    for b, lab in [(cook, "cook2022"), (muni, "municipal2015")]:
        t = t.merge(coverage(u, b[["geometry"]].copy(), lab).drop(columns="land_m2"), on="unit_id")
        print(lab, "done", flush=True)
    t = t.merge(lineage(u, ov, "src", "overture"), left_on="unit_id", right_index=True, how="left")
    t.insert(1, "city", "CHI")
    t.to_csv(TAB / "b1_sources_CHI.csv", index=False)
    return {"overture_records": len(ov), "cook2022_records": len(cook), "municipal2015_records": len(muni)}


def iptu_occupied(u):
    """IPTU 2026 'AREA OCUPADA' once per physical lot (condominium units repeat it), summed by district via fiscal blocks."""
    cols = ["NUMERO DO CONTRIBUINTE", "NUMERO DO CONDOMINIO", "AREA OCUPADA"]
    d = pd.read_csv(D / "SP/Cadastro e Vias/IPTU_2026.csv", sep=";", usecols=cols, dtype=str, encoding="latin-1")
    d["occ"] = pd.to_numeric(d["AREA OCUPADA"].str.replace(",", "."), errors="coerce").fillna(0)
    c = d["NUMERO DO CONTRIBUINTE"]
    condo = d["NUMERO DO CONDOMINIO"].fillna("00-0").str.strip()
    d["block"] = c.str[:6]
    d["lot"] = np.where(condo.eq("00-0"), c.str[:10], c.str[:6] + "C" + condo)
    # 4.5% of condominium lots record different values across units: take the lot median, report the max-based bound.
    g = d.groupby("lot")
    lots = g.agg(occ=("occ", "median"), occ_max=("occ", "max"), block=("block", "first"), varies=("occ", "nunique")).reset_index()
    q = pyogrio.read_dataframe(D / "SP/Cadastro e Vias/geoportal_quadra_fiscal_gsc.gpkg")
    q["block"] = q.cd_setor_fiscal + q.cd_quadra_fiscal
    q = q.dissolve("block").reset_index()
    pts = gpd.GeoDataFrame(q[["block"]], geometry=q.geometry.representative_point(), crs=q.crs)
    b2u = gpd.sjoin(pts, u, predicate="within").set_index("block").unit_id
    lots = lots.assign(unit_id=lots.block.map(b2u))
    s = lots.groupby("unit_id").occ.sum()
    info = {"records": len(d), "physical_lots": len(lots), "lots_with_varying_value": int((lots.varies > 1).sum()),
            "occupied_m2_max_minus_median": float((lots.occ_max - lots.occ).sum()), "lots_without_district": int(lots.unit_id.isna().sum()),
            "occupied_m2_without_district": float(lots.loc[lots.unit_id.isna(), "occ"].sum()), "occupied_m2_total": float(lots.occ.sum())}
    return s, info


def sao_paulo():
    u = land_units("SP")
    g = pd.concat([gpd.read_file(f"zip://{f}") for f in sorted(glob.glob(str(D / "SP/geosampa_edificacao_2026_10_05/page_*.zip")))], ignore_index=True)
    g = g.set_crs(31983, allow_override=True) if g.crs is None else g.to_crs(31983)
    man = json.loads((D / "SP/geosampa_edificacao_2026_10_05/manifest.json").read_text())
    assert g.cd_identif.is_unique if "cd_identif" in g else True
    t = coverage(u, g[["geometry"]].copy(), "geosampa")
    occ, iptu_info = iptu_occupied(u)
    t["iptu_occupied"] = t.unit_id.map(occ).fillna(0) / t.land_m2
    # The full SP building file exhausts memory (see SIMPLE_INDEX.md); read in chunks and keep source, area and centroid only.
    f, n_ov, parts, step = D / "SP/Edificacoes/sao_paulo_building_morphology.gpkg", 0, [], 500_000
    total = pyogrio.read_info(f, layer="buildings")["features"]
    for start in range(0, total, step):
        ch = pyogrio.read_dataframe(f, layer="buildings", columns=["sources_json"], skip_features=start, max_features=step)
        n_ov += len(ch)
        parts.append(gpd.GeoDataFrame({"src": [json.loads(s)[0].get("dataset", "none") if s else "none" for s in ch.sources_json],
                                       "geometry": ch.geometry.centroid, "area": ch.geometry.area}, crs=ch.crs))
        del ch
    ov = pd.concat(parts, ignore_index=True)
    j = gpd.sjoin(ov, u, predicate="within")
    s = j.groupby(["unit_id", "src"]).area.sum().unstack(fill_value=0)
    t = t.merge(s.div(s.sum(axis=1), axis=0).add_prefix("overture_src_"), left_on="unit_id", right_index=True, how="left")
    t.insert(1, "city", "SP")
    t.to_csv(TAB / "b1_sources_SP.csv", index=False)
    return {"iptu": iptu_info, "geosampa_records": len(g), "geosampa_number_matched": man["number_matched"], "overture_records": n_ov,
            "geosampa_update_dates": [str(g.dt_atualiz.min()), str(g.dt_atualiz.max())] if "dt_atualiz" in g else None,
            "geosampa_creation_dates": [str(g.dt_criacao.min()), str(g.dt_criacao.max())] if "dt_criacao" in g else None}


def summary():
    cand = pd.read_csv(CAND).set_index("unit_id")
    checks = json.loads((OUT / "checks.json").read_text()) if (OUT / "checks.json").exists() else {}
    c = pd.read_csv(TAB / "b1_sources_CHI.csv").set_index("unit_id")
    s = pd.read_csv(TAB / "b1_sources_SP.csv").set_index("unit_id")
    # S4-1: existing B1 values and land denominators.
    u3 = pd.read_parquet(A / "results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet").set_index("unit_id")
    spl = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet")
    spl = pd.Series(spl.land_area_m2.to_numpy(), index="SP:" + spl.district_id)
    land_c2 = pd.concat([u3.land_m2, spl])
    checks["S4-1_land_equals_C2"] = {"pass": bool(np.allclose(cand.land_area_m2.reindex(land_c2.index), land_c2, atol=1.0)),
                                     "max_abs_diff_m2": float((cand.land_area_m2.reindex(land_c2.index) - land_c2).abs().max())}
    checks["S4-1_CHI_overture_recomputed"] = {"pass": bool(np.allclose(c.overture, cand.B1_coverage_land.reindex(c.index), atol=1e-6)),
                                              "max_abs_diff": float((c.overture - cand.B1_coverage_land.reindex(c.index)).abs().max())}
    s["overture"] = cand.B1_coverage_land.reindex(s.index)
    # S4-2 and S4-3: Overture against the independent reference, same rule.
    for city, t, ref in [("CHI", c, "cook2022"), ("SP", s, "geosampa")]:
        rel = t.overture / t[ref] - 1
        rho = t.overture.corr(t[ref], method="spearman")
        cases = rel[rel.abs() > MAX_REL]
        key = "S4-2_CHI_vs_cook2022" if city == "CHI" else "S4-3_SP_vs_geosampa"
        checks[key] = {"pass": bool(rho >= MIN_SPEARMAN and cases.empty), "spearman": float(rho),
                       "median_rel_diff": float(rel.median()), "cases": {k: round(float(v), 4) for k, v in cases.items()}}
        t["rel_vs_ref"] = rel
    rel = s.overture / s.iptu_occupied - 1
    checks["S4-3_SP_vs_iptu_occupied"] = {"pass": bool(s.overture.corr(s.iptu_occupied, method="spearman") >= MIN_SPEARMAN and (rel.abs() <= MAX_REL).all()),
                                          "spearman": float(s.overture.corr(s.iptu_occupied, method="spearman")), "median_rel_diff": float(rel.median()),
                                          "cases": {k: round(float(v), 4) for k, v in rel[rel.abs() > MAX_REL].items()}}
    checks["CHI_municipal2015_descriptive"] = {"spearman_vs_overture": float(c.overture.corr(c.municipal2015, method="spearman")),
                                               "median_rel_diff": float((c.overture / c.municipal2015 - 1).median())}
    # S4-6: Overture B1 / GHSL implied built fraction.
    g = pd.read_csv(A / "results/SP_CHI/bv_ghsl_lidar_evaluation_2026_09_30/tables/bv_variants_with_b1.csv").set_index("unit_id")
    r = (cand.B1_coverage_land / g.ghsl_built_fraction.reindex(cand.index)).rename("overture_over_ghsl")
    out = {}
    for city in ("CHI", "SP"):
        rc = r[r.index.str.startswith(city)]
        lo, hi = rc.quantile([.05, .95])
        out[city] = {"median": float(rc.median()), "p05": float(lo), "p95": float(hi), "outside": rc[(rc < lo) | (rc > hi)].round(3).to_dict()}
    checks["S4-6_overture_over_ghsl"] = out
    # S4-5: lineage summary.
    for city, t in [("CHI", c), ("SP", s)]:
        cols = [k for k in t.columns if k.startswith("overture_src_")]
        checks[f"S4-5_{city}_lineage_median_share"] = t[cols].median().round(4).to_dict()
    pd.concat([c, s]).join(r).to_csv(TAB / "b1_step4_by_unit.csv")
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float, ensure_ascii=False) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float, ensure_ascii=False)[:600])


if __name__ == "__main__":
    TAB.mkdir(parents=True, exist_ok=True)
    arg = sys.argv[1]
    if arg == "summary":
        summary()
    else:
        info = chicago() if arg == "CHI" else sao_paulo()
        p = OUT / f"run_{arg}.json"
        p.write_text(json.dumps(info, indent=2, default=str) + "\n")
        print(info)

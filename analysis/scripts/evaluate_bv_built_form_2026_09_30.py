"""Evaluate GHSL vertical-form (BV) variants: cell-level built fraction/height, overlap with B1, and a Chicago LiDAR-footprint check; writes CSVs to argv[1]."""
import sys, glob, pathlib
import numpy as np, pandas as pd, geopandas as gpd, rasterio, shapely, pyogrio
from rasterio.windows import Window, from_bounds
from scipy.stats import spearmanr

OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
H1 = "analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/tables/candidate_attributes_wide.csv"
PROD = "analysis/data/{c}/ghsl_public_2026_09_21/GHS_BUILT_{p}_E{y}_GLOBE_R2023A_54009_100.tif"
MOLL = "ESRI:54009"


def units():
    chi = gpd.read_file("analysis/data/Chicago/Boundaries_-_Community_Areas_20260831.geojson")
    chi["unit_id"] = "CHI:" + chi.area_numbe.astype(int).astype(str).str.zfill(2)
    sp = gpd.read_file("analysis/data/SP/Cadastro e Vias/distrito_municipal_v2.gpkg")
    sp["unit_id"] = "SP:" + sp.cd_distrito_municipal.astype(str).str.zfill(2)
    return {"Chicago": chi[["unit_id", "geometry"]], "SP": sp[["unit_id", "geometry"]]}


def wquantile(x, w, q):
    i = np.argsort(x); x, w = x[i], w[i]; c = np.cumsum(w); return float(np.interp(q * c[-1], c, x))


def ghsl_cells(city, gdf):
    """Per unit: gross-support, cell-overlap-weighted GHSL statistics from native 100 m cells (valid in all three products)."""
    rows = []
    with rasterio.open(PROD.format(c=city, p="H_ANBH", y=2018)) as a, rasterio.open(PROD.format(c=city, p="H_AGBH", y=2018)) as g, rasterio.open(PROD.format(c=city, p="V", y=2020)) as v:
        gdf = gdf.to_crs(a.crs)
        for u in gdf.itertuples():
            raw = from_bounds(*u.geometry.bounds, transform=a.transform)
            win = Window(int(np.floor(raw.col_off)), int(np.floor(raw.row_off)), int(np.ceil(raw.width)) + 1, int(np.ceil(raw.height)) + 1).intersection(Window(0, 0, a.width, a.height))
            A = a.read(1, window=win, masked=True); G = g.read(1, window=win, masked=True); V = v.read(1, window=win, masked=True)
            tr = a.window_transform(win)
            cell_area = abs(a.res[0] * a.res[1])
            ov = np.zeros(A.shape)
            for r, c in np.argwhere(~np.ma.getmaskarray(A)):
                x0, y0 = tr * (c, r + 1); x1, y1 = tr * (c + 1, r)
                ov[r, c] = shapely.box(x0, y0, x1, y1).intersection(u.geometry).area
            ok = (~np.ma.getmaskarray(A)) & (~np.ma.getmaskarray(G)) & (~np.ma.getmaskarray(V)) & (ov > 0)
            w = ov[ok]; an = A.data[ok].astype(float); ag = G.data[ok].astype(float); vol = V.data[ok].astype(float)
            frac = np.where(an > 0, ag / np.where(an > 0, an, 1), 0.0)
            built_w = w * frac
            rows.append(dict(
                unit_id=u.unit_id, support_m2=float(ov.sum()), valid_fraction=float(w.sum() / ov.sum()),
                anbh_mean_incl_zero=float((w * an).sum() / w.sum()),
                agbh_mean=float((w * ag).sum() / w.sum()),
                volume_density_m=float((w * vol / cell_area).sum() / w.sum()),
                ghsl_built_fraction=float(built_w.sum() / w.sum()),
                height_built_weighted=float((w * ag).sum() / built_w.sum()) if built_w.sum() > 0 else np.nan,
                anbh_p50_built=wquantile(an[built_w > 0], built_w[built_w > 0], .5) if built_w.sum() > 0 else np.nan,
                anbh_p90_built=wquantile(an[built_w > 0], built_w[built_w > 0], .9) if built_w.sum() > 0 else np.nan,
                share_area_zero_anbh=float(w[an == 0].sum() / w.sum()),
                anomaly_agbh_pos_anbh_zero=int(((ag > 0) & (an == 0)).sum()),
                n_cells=int(ok.sum())))
    return pd.DataFrame(rows)


def cook_lidar_chicago(chi):
    """Cook 2022 footprints (Height in US feet, NAVD88) assigned to Community Areas by centroid, in EPSG:26916."""
    a = chi.to_crs(26916)
    parts, nb = [], 0
    for f in sorted(glob.glob("analysis/data/Chicago/chicago_cadastral_2026_09_18/cook_buildings_2022/part_*.parquet")):
        g = gpd.read_parquet(f, columns=["geometry", "Height"]).to_crs(26916)
        nb += len(g)
        g["area_m2"] = g.geometry.area; g["h_m"] = g.Height * 0.3048006
        g["geometry"] = g.geometry.centroid
        parts.append(gpd.sjoin(g[["geometry", "area_m2", "h_m"]], a, how="inner", predicate="within")[["unit_id", "area_m2", "h_m"]])
    j = pd.concat(parts)
    j["vol_m3"] = j.area_m2 * j.h_m
    s = j.groupby("unit_id").agg(n=("area_m2", "size"), foot_m2=("area_m2", "sum"), vol_m3=("vol_m3", "sum"))
    s["gross_m2"] = a.set_index("unit_id").geometry.area.reindex(s.index)
    s["lidar_footprint_coverage_gross"] = s.foot_m2 / s.gross_m2
    s["lidar_volume_density_m"] = s.vol_m3 / s.gross_m2
    s["lidar_height_area_weighted_m"] = s.vol_m3 / s.foot_m2
    return s.reset_index(), nb


def sp(x, y):
    m = x.notna() & y.notna(); return round(float(spearmanr(x[m], y[m]).statistic), 3)


if __name__ == "__main__":
    U = units(); res = []
    cache = OUT / "ghsl_cell_level_by_unit.csv"
    if cache.exists():
        cells = pd.read_csv(cache)
    else:
        for city in ("Chicago", "SP"):
            res.append(ghsl_cells(city, U[city])); print(city, "cells done", flush=True)
        cells = pd.concat(res); cells.to_csv(cache, index=False)
    h1 = pd.read_csv(H1)[["unit_id", "footprint_coverage_gross", "footprint_coverage_land", "net_grid_height_gross", "gross_grid_height_gross", "volume_density_gross"]]
    m = cells.merge(h1, on="unit_id")
    m["city"] = m.unit_id.str.split(":").str[0]
    # reconciliation with the sealed H1-H3 values (gross support)
    m["d_anbh"] = m.anbh_mean_incl_zero - m.net_grid_height_gross
    m["d_agbh"] = m.agbh_mean - m.gross_grid_height_gross
    m["d_vol"] = m.volume_density_m - m.volume_density_gross
    recon = m.groupby("city")[["d_anbh", "d_agbh", "d_vol"]].agg(lambda s: s.abs().max()); recon.to_csv(OUT / "reconciliation_with_h1_h3.csv")
    print("RECON (max abs diff vs sealed H1-H3):\n", recon.to_string())
    cols = ["footprint_coverage_gross", "anbh_mean_incl_zero", "agbh_mean", "volume_density_m", "ghsl_built_fraction", "height_built_weighted", "anbh_p50_built", "anbh_p90_built"]
    for city, d in m.groupby("city"):
        mat = pd.DataFrame({a: {b: sp(d[a], d[b]) for b in cols} for a in cols}); mat.to_csv(OUT / f"spearman_{city}.csv")
        print(f"\nSPEARMAN {city} (n={len(d)})\n", mat.to_string())
        print(d[["ghsl_built_fraction", "footprint_coverage_gross", "height_built_weighted", "anbh_mean_incl_zero", "share_area_zero_anbh"]].describe().loc[["min", "50%", "max"]].round(3).to_string())
        print("anomaly cells (AGBH>0, ANBH=0):", int(d.anomaly_agbh_pos_anbh_zero.sum()), "  min valid_fraction:", round(d.valid_fraction.min(), 6))
    m.to_csv(OUT / "bv_variants_with_b1.csv", index=False)
    lid, nb = cook_lidar_chicago(U["Chicago"])
    lid.to_csv(OUT / "chicago_cook2022_lidar_by_area.csv", index=False)
    c = m[m.city == "CHI"].merge(lid, on="unit_id")
    print("\nCOOK 2022 LIDAR (Chicago)  buildings read:", nb, " assigned:", int(lid.n.sum()), " areas:", len(lid))
    for a, b in [("lidar_footprint_coverage_gross", "footprint_coverage_gross"), ("lidar_footprint_coverage_gross", "ghsl_built_fraction"),
                 ("lidar_volume_density_m", "volume_density_m"), ("lidar_height_area_weighted_m", "height_built_weighted"), ("lidar_height_area_weighted_m", "anbh_mean_incl_zero")]:
        print(f"  Spearman {a} vs {b}: {sp(c[a], c[b])}")
    c["ratio_lidar_cov_over_overture"] = c.lidar_footprint_coverage_gross / c.footprint_coverage_gross
    c["ratio_ghsl_vol_over_lidar_vol"] = c.volume_density_m / c.lidar_volume_density_m
    print(c[["ratio_lidar_cov_over_overture", "ratio_ghsl_vol_over_lidar_vol"]].describe().round(3).to_string())
    c.to_csv(OUT / "chicago_comparison.csv", index=False)

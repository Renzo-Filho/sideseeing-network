"""Step 5 follow-up: GHSL building height vs LiDAR building height per 100 m GHSL cell, São Paulo 2020 sample tiles and Chicago (Cook 2022)."""
import glob, hashlib, json
from pathlib import Path
import geopandas as gpd, laspy, numpy as np, pandas as pd, pyogrio, rasterio, shapely
from pyproj import Transformer
from scipy.interpolate import LinearNDInterpolator

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
OUT = A / "results/SP_CHI/bv_step5_2026_10_05/lidar_sample"
ANBH = str(D / "{c}/ghsl_public_2026_09_21/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100.tif")
LAZ = D / "SP/MDS-MDT"
FT = 0.3048006
MIN_FP_M2 = 500          # cell must hold at least this much footprint area with a LiDAR height
MIN_PTS = 5              # building-class points needed inside a footprint
STAT = "p95"             # per-footprint LiDAR height; "max" mirrors Cook's maximum-point height exactly (sensitivity)
CLASSES = [0, 8, 15, 25, 1e9]
LABELS = ["<8 m", "8-15 m", "15-25 m", ">=25 m"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ghsl_cells(city, box31983=None, crs=None, bounds=None):
    """GHSL ANBH cells as polygons in the city's metric CRS, optionally only cells wholly inside a box."""
    with rasterio.open(ANBH.format(c=city)) as r:
        to_m = Transformer.from_crs(crs, r.crs, always_xy=True)
        x0, y0, x1, y1 = bounds
        xs, ys = to_m.transform([x0, x1, x0, x1], [y0, y0, y1, y1])
        win = rasterio.windows.from_bounds(min(xs), min(ys), max(xs), max(ys), r.transform).round_offsets().round_lengths()
        # Clip to the raster: reading past its edge returns a smaller array whose transform would shift every cell.
        win = win.intersection(rasterio.windows.Window(0, 0, r.width, r.height))
        a = r.read(1, window=win, masked=True)
        tr = r.window_transform(win)
    rr, cc = np.nonzero(~np.ma.getmaskarray(a))
    back = Transformer.from_crs("ESRI:54009", crs, always_xy=True)
    polys = []
    for r_, c_ in zip(rr, cc):
        corners = [tr * (c_, r_), tr * (c_ + 1, r_), tr * (c_ + 1, r_ + 1), tr * (c_, r_ + 1)]
        polys.append(shapely.Polygon([back.transform(*p) for p in corners]))
    g = gpd.GeoDataFrame({"cell": [f"{r_}_{c_}" for r_, c_ in zip(rr, cc)], "ghsl_anbh_m": a.data[rr, cc].astype(float)}, geometry=polys, crs=crs)
    if box31983 is not None:
        g = g[g.within(box31983)]
    return g


def cell_heights(cells, fp, label):
    """Footprint-area-weighted building height per GHSL cell (footprints by centroid)."""
    pts = gpd.GeoDataFrame({"h": fp.h.to_numpy(), "a": fp.geometry.area.to_numpy()}, geometry=fp.geometry.centroid, crs=fp.crs)
    j = gpd.sjoin(pts, cells[["cell", "geometry"]], predicate="within")
    s = j.groupby("cell").apply(lambda x: pd.Series({f"{label}_m": (x.h * x.a).sum() / x.a.sum(), "fp_m2": x.a.sum(), "n_fp": len(x)}), include_groups=False)
    return cells.merge(s, left_on="cell", right_index=True)


def sp_tile(tile, sample):
    mds, mdt = LAZ / f"MDS_{tile}_1000.laz", LAZ / f"MDT_{tile}_1000.laz"
    g = laspy.read(mdt)
    terrain = LinearNDInterpolator(np.c_[g.x, g.y], np.asarray(g.z))
    s = laspy.read(mds)
    b = np.asarray(s.classification) == 6
    x, y, z = np.asarray(s.x)[b], np.asarray(s.y)[b], np.asarray(s.z)[b]
    hag = z - terrain(x, y)
    ok = np.isfinite(hag) & (hag > 0)
    x, y, hag = x[ok], y[ok], hag[ok]
    grid = gpd.read_file(D / "SP/geosampa_lidar_2020/quadricula_mdt_mds_2020.geojson").set_index("cd_quadricula")
    box = grid.loc[tile].geometry
    fp = pyogrio.read_dataframe(D / "SP/Edificacoes/sao_paulo_building_morphology.gpkg", layer="buildings", bbox=box.bounds, columns=["building_id"])
    fp = fp[fp.within(box)].reset_index(drop=True)
    tree = shapely.STRtree(fp.geometry.values)
    pi, fi = tree.query(shapely.points(x, y), predicate="within")
    d = pd.DataFrame({"fp": fi, "h": hag[pi]})
    st = d.groupby("fp").h.agg(["size", lambda v: np.percentile(v, 95), "max"])
    st.columns = ["n", "p95", "max"]
    st = st[st.n >= MIN_PTS]
    fp = fp.loc[st.index].assign(h=st[STAT].to_numpy())
    cells = ghsl_cells("SP", box, 31983, box.bounds)
    c = cell_heights(cells, fp, "lidar")
    c.insert(0, "tile", tile)
    c.insert(1, "district", sample.loc[tile, "district"])
    info = {"tile": tile, "building_points": int(b.sum()), "footprints_with_height": len(fp), "cells_inside_tile": len(cells),
            "mds_sha256": sha(mds), "mdt_sha256": sha(mdt)}
    return c, info


def chicago():
    u = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet").to_crs(26916)
    city = u.union_all()
    parts = []
    for f in sorted(glob.glob(str(D / "Chicago/chicago_cadastral_2026_09_18/cook_buildings_2022/part_*.parquet"))):
        g = gpd.read_parquet(f, columns=["geometry", "Height"]).to_crs(26916)
        parts.append(g[g.Height > 0].assign(h=lambda x: x.Height * FT)[["h", "geometry"]])
    fp = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=26916)
    cells = ghsl_cells("Chicago", None, 26916, city.bounds)
    cells = cells[cells.within(city)]
    return cell_heights(cells, fp, "lidar").assign(tile="Chicago", district="Chicago")


def summarise(c, by):
    c = c[(c.fp_m2 >= MIN_FP_M2) & (c.ghsl_anbh_m > 0)].copy()
    c["ratio"] = c.ghsl_anbh_m / c.lidar_m
    c["class"] = pd.cut(c.lidar_m, CLASSES, right=False, labels=LABELS)
    out = {}
    for k, g in c.groupby(by):
        out[k] = {"cells": len(g), "spearman": float(g.ghsl_anbh_m.corr(g.lidar_m, method="spearman")) if len(g) > 2 else None,
                  "median_ratio": float(g.ratio.median()), "median_lidar_m": float(g.lidar_m.median()), "median_ghsl_m": float(g.ghsl_anbh_m.median()),
                  "by_class": g.groupby("class", observed=True).ratio.agg(["size", "median"]).round(3).to_dict(orient="index")}
    return out


def main():
    import sys
    global STAT, OUT
    if len(sys.argv) > 1:
        STAT = sys.argv[1]
    OUT = OUT if STAT == "p95" else OUT.parent / f"lidar_sample_{STAT}"
    OUT.mkdir(parents=True, exist_ok=True)
    sample = pd.read_csv(D / "SP/geosampa_lidar_2020/sample_tiles.csv").set_index("tile")
    sp, infos = [], []
    for tile in sample.index:
        c, info = sp_tile(tile, sample)
        sp.append(c); infos.append(info)
        print(info, flush=True)
    sp = pd.concat(sp, ignore_index=True)
    chi = chicago()
    sp, chi = pd.DataFrame(sp.drop(columns="geometry")), pd.DataFrame(chi.drop(columns="geometry"))   # different CRSs
    allc = pd.concat([sp, chi], ignore_index=True)
    allc.to_csv(OUT / "cells_ghsl_vs_lidar.csv", index=False)
    allc["city"] = np.where(allc.tile == "Chicago", "CHI", "SP")
    res = {"by_city": summarise(allc, "city"), "by_sp_district": summarise(sp, "district"), "tiles": infos,
           "method": "GHSL ANBH 2018 per 100 m cell vs footprint-area-weighted LiDAR building height; SP: Overture footprints, 95th percentile of class-6 points above MDT terrain (GeoSampa LiDAR 2020); Chicago: Cook 2022 Height (max point minus ground, feet to m); cells with >= 500 m2 footprint area and ANBH > 0"}
    (OUT / "summary.json").write_text(json.dumps(res, indent=2, default=float, ensure_ascii=False) + "\n")
    print(json.dumps(res["by_city"], indent=1, default=float))
    print(json.dumps(res["by_sp_district"], indent=1, default=float))


if __name__ == "__main__":
    main()

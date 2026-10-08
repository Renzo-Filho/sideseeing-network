"""S4-4/S4-7: footprint sources in one São Paulo district (default Brás) with imagery windows. Usage: evaluate_b1_bras.py [district_id] [n_windows]."""
import glob, hashlib, io, json, math, sys
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, requests, shapely
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile"
HEAD = {"User-Agent": "sideseeing-network bounded academic image audit"}
Z, WIN, N_WIN, SEED = 19, 150, 6, 20261005


def union_share(geoms, area):
    g = shapely.make_valid(np.asarray(geoms))
    return shapely.union_all(shapely.intersection(g, area)).area / area.area


def tile_mosaic(bounds3857):
    """Esri World Imagery tiles covering a Web Mercator box; returns image and its extent."""
    R = 6378137.0
    world = 2 * math.pi * R
    n = 2 ** Z
    tx = lambda x: int((x + world / 2) / world * n)
    ty = lambda y: int((world / 2 - y) / world * n)
    x0, y0, x1, y1 = bounds3857
    cols, rows = range(tx(x0), tx(x1) + 1), range(ty(y1), ty(y0) + 1)
    canvas = Image.new("RGB", (256 * len(cols), 256 * len(rows)))
    hashes = []
    for i, c in enumerate(cols):
        for j, r in enumerate(rows):
            resp = requests.get(f"{TILES}/{Z}/{r}/{c}", headers=HEAD, timeout=60)
            resp.raise_for_status()
            canvas.paste(Image.open(io.BytesIO(resp.content)).convert("RGB"), (256 * i, 256 * j))
            hashes.append(hashlib.sha256(resp.content).hexdigest())
    size = world / n
    extent = (cols[0] * size - world / 2, (cols[-1] + 1) * size - world / 2,
              world / 2 - (rows[-1] + 1) * size, world / 2 - rows[0] * size)
    return canvas, extent, hashes


def main(district="10", n_win=N_WIN):
    OUT = A / "results/SP_CHI/b1_step4_2026_10_05" / ("bras" if district == "10" else f"district_{district}")
    OUT.mkdir(parents=True, exist_ok=True)
    land = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet")
    bras = land.loc[land.district_id == district].geometry.iloc[0]
    bb4326 = tuple(gpd.GeoSeries([bras], crs=31983).to_crs(4326).total_bounds)
    src = {}
    src["overture"] = pyogrio.read_dataframe(D / "SP/Edificacoes/sao_paulo_building_morphology.gpkg", layer="buildings",
                                             bbox=tuple(bras.bounds), columns=["sources_json"])
    ms = [pyogrio.read_dataframe(f"/vsigzip/{f}", bbox=bb4326) for f in sorted(glob.glob(str(D / "SP/microsoft_buildings_2026_08_13/raw_tiles/*.geojsonl.gz")))]
    src["microsoft"] = pd.concat(ms, ignore_index=True).set_crs(4326, allow_override=True).to_crs(31983)
    osm = pyogrio.read_dataframe(D / "shared/osm_geofabrik/sudeste-latest.osm.pbf", layer="multipolygons", bbox=bb4326, columns=["building"])
    src["osm"] = osm[osm.building.notna()].to_crs(31983)
    gs = sorted(glob.glob(str(D / "SP/geosampa_edificacao_2026_10_05/page_*.zip")))
    if (D / "SP/geosampa_edificacao_2026_10_05/manifest.json").exists():
        g = pd.concat([gpd.read_file(f"zip://{f}", bbox=tuple(bras.bounds)) for f in gs], ignore_index=True)
        src["geosampa"] = g.set_crs(31983, allow_override=True) if g.crs is None else g.to_crs(31983)
    for k in src:
        src[k] = src[k][src[k].intersects(bras)]
    ghsl = pd.read_csv(A / "results/SP_CHI/bv_ghsl_lidar_evaluation_2026_09_30/tables/bv_variants_with_b1.csv").set_index("unit_id").loc[f"SP:{district}", "ghsl_built_fraction"]
    res = {"land_km2": bras.area / 1e6, "ghsl_built_fraction": float(ghsl)}
    for k, g in src.items():
        areas = shapely.area(g.geometry.values)
        res[k] = {"records": len(g), "coverage": union_share(g.geometry.values, bras),
                  "median_polygon_m2": float(np.median(areas)), "p90_polygon_m2": float(np.quantile(areas, 0.9))}
    lin = src["overture"].sources_json.map(lambda s: json.loads(s)[0].get("dataset", "none") if s else "none")
    by_src = pd.Series(shapely.area(src["overture"].geometry.values), index=lin.values).groupby(level=0).sum()
    res["overture_area_share_by_source"] = (by_src / by_src.sum()).round(4).to_dict()
    # Windows: random 150 m squares wholly inside Brás land.
    rng = np.random.default_rng(SEED)
    x0, y0, x1, y1 = bras.bounds
    wins = []
    while len(wins) < n_win:
        x, y = rng.uniform(x0, x1 - WIN), rng.uniform(y0, y1 - WIN)
        w = shapely.box(x, y, x + WIN, y + WIN)
        if bras.contains(w):
            wins.append(w)
    rows = []
    colors = {"overture": "red", "microsoft": "cyan", "osm": "yellow", "geosampa": "lime"}
    for i, w in enumerate(wins):
        row = {"window": i, "x": w.bounds[0], "y": w.bounds[1]}
        for k, g in src.items():
            row[k] = union_share(g.geometry.values[g.intersects(w).to_numpy()], w)
        w3857 = gpd.GeoSeries([w], crs=31983).to_crs(3857)
        img, ext, hashes = tile_mosaic(w3857.total_bounds)
        row["tile_hashes"] = hashes
        fig, axes = plt.subplots(1, 1 + len(src), figsize=(5 * (1 + len(src)), 5))
        for ax, k in zip(axes, ["imagery"] + list(src)):
            ax.imshow(img, extent=ext)
            if k != "imagery":
                gpd.GeoSeries(src[k].geometry.values, crs=31983).to_crs(3857).boundary.plot(ax=ax, color=colors[k], linewidth=0.8)
            ax.set_xlim(w3857.total_bounds[[0, 2]]); ax.set_ylim(w3857.total_bounds[[1, 3]])
            ax.set_title(k if k == "imagery" else f"{k}: {row[k]:.2f}"); ax.set_xticks([]); ax.set_yticks([])
        fig.tight_layout(); fig.savefig(OUT / f"window_{i}.png", dpi=110); plt.close(fig)
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "windows.csv", index=False)
    (OUT / "bras_sources.json").write_text(json.dumps(res, indent=2, default=float) + "\n")
    print(json.dumps(res, indent=2, default=float))
    print(pd.DataFrame(rows).drop(columns="tile_hashes").round(3).to_string(index=False))


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["10"]), *(int(a) for a in sys.argv[2:3]))

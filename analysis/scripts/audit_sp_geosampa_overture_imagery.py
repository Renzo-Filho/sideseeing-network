"""Render a fixed random sample of historical-only footprint candidates on dated imagery."""

import glob
import hashlib
import io
import json
import math
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio
import requests
import shapely
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/b1_geosampa_overture_overlap_2026_10_05"
OVERTURE = A / "data/SP/Edificacoes/sao_paulo_building_morphology.gpkg"
GEO = A / "data/SP/geosampa_edificacao_2026_10_05"
BASE = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"
TILE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile"
HEAD = {"User-Agent": "sideseeing-network building-map comparison"}
Z = 19


def tile_mosaic(bounds):
    radius = 6378137.0
    world = 2 * math.pi * radius
    n = 2 ** Z
    tx = lambda x: int((x + world / 2) / world * n)
    ty = lambda y: int((world / 2 - y) / world * n)
    x0, y0, x1, y1 = bounds
    cols, rows = range(tx(x0), tx(x1) + 1), range(ty(y1), ty(y0) + 1)
    canvas = Image.new("RGB", (256 * len(cols), 256 * len(rows)))
    hashes = []
    for i, col in enumerate(cols):
        for j, row in enumerate(rows):
            res = requests.get(f"{TILE}/{Z}/{row}/{col}", headers=HEAD, timeout=60)
            res.raise_for_status()
            canvas.paste(Image.open(io.BytesIO(res.content)).convert("RGB"), (256 * i, 256 * j))
            hashes.append(hashlib.sha256(res.content).hexdigest())
    size = world / n
    extent = (cols[0] * size - world / 2, (cols[-1] + 1) * size - world / 2,
              world / 2 - (rows[-1] + 1) * size, world / 2 - rows[0] * size)
    return canvas, extent, hashes


def image_metadata(lon, lat):
    params = {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
              "spatialRel": "esriSpatialRelIntersects", "outFields": "SRC_DATE,SRC_RES,SRC_ACC,NICE_NAME,NICE_DESC",
              "returnGeometry": "false", "f": "json"}
    res = requests.get(f"{BASE}/0/query", params=params, headers=HEAD, timeout=60)
    res.raise_for_status()
    features = res.json().get("features", [])
    return features[0]["attributes"] if features else {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    far = pd.read_csv(OUT / "imagery_candidates.csv", dtype={"district_id": str, "geosampa_id": str})
    # The first citywide run stored only far candidates; a later targeted run
    # stored near candidates separately. A fresh citywide run stores both in
    # imagery_candidates.csv.
    near_file = OUT / "imagery_candidates_near.csv"
    near = (pd.read_csv(near_file, dtype={"district_id": str, "geosampa_id": str})
            if near_file.exists() else far)
    # One random candidate per category in each district. Both the candidate
    # sampling and this second-stage draw use fixed seeds.
    district_ids = ["01", "05", "10", "15", "21", "27", "35", "41", "54", "55", "71", "81"]
    chosen = []
    for district_id in district_ids:
        rng = np.random.default_rng(20261006 + int(district_id))
        for group, candidates, labels in [("far", far, ["random", "far_random"]),
                                          ("near", near, ["near_random"])]:
            pool = candidates[(candidates.district_id == district_id) &
                              (candidates.sample_type.isin(labels))]
            if len(pool):
                chosen.append((group, pool.iloc[int(rng.integers(len(pool)))]))
    pages = [str(Path(p).resolve()) for p in sorted(glob.glob(str(GEO / "page_*.zip")))]
    records = []
    image_dir = OUT / "imagery_review_v2"
    image_dir.mkdir(exist_ok=True)
    for n, (group, row) in enumerate(chosen):
        x, y = float(row.x), float(row.y)
        box = shapely.box(x - 65, y - 65, x + 65, y + 65)
        bounds = tuple(box.bounds)
        geo = pd.concat([gpd.read_file(f"zip://{p}", bbox=bounds) for p in pages], ignore_index=True)
        ov = pyogrio.read_dataframe(OVERTURE, layer="buildings", bbox=bounds, columns=[])
        win = gpd.GeoSeries([box], crs=31983).to_crs(3857)
        img, extent, hashes = tile_mosaic(win.total_bounds)
        point = gpd.GeoSeries([shapely.Point(x, y)], crs=31983).to_crs(4326).iloc[0]
        metadata = image_metadata(point.x, point.y)

        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        for ax in axes:
            ax.imshow(img, extent=extent)
            ax.set_xlim(win.total_bounds[[0, 2]])
            ax.set_ylim(win.total_bounds[[1, 3]])
            ax.set_xticks([])
            ax.set_yticks([])
        gpd.GeoSeries(geo.geometry.values, crs=31983).to_crs(3857).boundary.plot(ax=axes[1], color="lime", linewidth=.8)
        if len(ov):
            gpd.GeoSeries(ov.geometry.values, crs=31983).to_crs(3857).boundary.plot(ax=axes[2], color="red", linewidth=.8)
        target = geo[geo.cd_identif.astype(str) == str(row.geosampa_id)]
        if len(target):
            gpd.GeoSeries(target.geometry.values, crs=31983).to_crs(3857).boundary.plot(ax=axes[1], color="yellow", linewidth=2)
        axes[0].set_title(f"Imagery {metadata.get('SRC_DATE', 'date unknown')}")
        axes[1].set_title("GeoSampa; target in yellow")
        axes[2].set_title("Overture")
        fig.tight_layout()
        filename = f"{group}_{n:02d}_district_{row.district_id}.png"
        fig.savefig(image_dir / filename, dpi=140)
        plt.close(fig)
        records.append({**row.to_dict(), **metadata, "review_group": group, "image_file": filename, "tile_sha256": json.dumps(hashes)})
        print(f"{n + 1}/{len(chosen)} {filename}: {metadata.get('SRC_DATE')}", flush=True)
    pd.DataFrame(records).to_csv(image_dir / "imagery_sample.csv", index=False)


if __name__ == "__main__":
    main()

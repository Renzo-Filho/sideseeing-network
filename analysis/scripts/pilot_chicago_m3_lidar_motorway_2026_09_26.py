"""Bounded Cook 2022 DTM/DSM structural check on frozen CHI:11 motorway faces."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
import requests
import shapely
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/results/Chicago/chicago_m3_lidar_motorway_pilot_2026_09_26"
WORK = ROOT / "analysis/work/chicago_m3_lidar_motorway_pilot_2026_09_26"
PREVIOUS = ROOT / "analysis/results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26"
SERVICES = {
    "dtm": "https://data.isgs.illinois.edu/arcgis/rest/services/Elevation/IL_Cook_DTM_2022/ImageServer",
    "dsm": "https://data.isgs.illinois.edu/arcgis/rest/services/Elevation/IL_Cook_DSM_2022/ImageServer",
}
SIZE = 1200
HALF_WIDTH_M = 300


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acquire(name: str, service: str, bbox: list[float]) -> dict:
    raster = WORK / f"CHI_11_MZ1_{name}_2022.tif"
    metadata = WORK / f"CHI_11_MZ1_{name}_service.json"
    if not metadata.exists():
        response = requests.get(service, params={"f": "json"}, timeout=60)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise RuntimeError(payload["error"])
        metadata.write_text(json.dumps(payload, indent=2) + "\n")
    if not raster.exists():
        response = requests.get(service + "/exportImage", params={
            "bbox": ",".join(map(str, bbox)), "bboxSR": 26916, "imageSR": 26916,
            "size": f"{SIZE},{SIZE}", "format": "tiff", "pixelType": "F32",
            "interpolation": "RSP_BilinearInterpolation", "f": "image",
        }, timeout=180)
        response.raise_for_status()
        if not response.content[:4] in (b"II*\x00", b"MM\x00*"):
            raise RuntimeError(f"Unexpected {name} export: {response.text[:400]}")
        raster.write_bytes(response.content)
    with rasterio.open(raster) as src:
        info = {"path": str(raster.relative_to(ROOT)), "sha256": sha(raster),
                "crs": str(src.crs), "bounds": list(src.bounds), "shape": list(src.shape),
                "dtype": src.dtypes[0], "nodata": src.nodata}
    return {"service_url": service, "service_metadata_sha256": sha(metadata), **info}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    zone = json.loads((PREVIOUS / "motorway_zone_selection.json").read_text())["zone"]
    x, y = zone["x"], zone["y"]
    bbox = [x-HALF_WIDTH_M, y-HALF_WIDTH_M, x+HALF_WIDTH_M, y+HALF_WIDTH_M]
    receipts = {name: acquire(name, url, bbox) for name, url in SERVICES.items()}
    with rasterio.open(WORK / "CHI_11_MZ1_dtm_2022.tif") as ground, \
         rasterio.open(WORK / "CHI_11_MZ1_dsm_2022.tif") as surface:
        assert ground.crs == surface.crs and ground.transform == surface.transform
        dtm = ground.read(1, masked=True)
        dsm = surface.read(1, masked=True)
        # The source metadata declares NAVD88 vertical units as US survey feet.
        delta_m = (dsm - dtm) * (1200/3937)
        valid = ~np.ma.getmaskarray(delta_m) & np.isfinite(np.ma.filled(delta_m, np.nan))
        candidates = pd.read_csv(PREVIOUS / "motorway_complete_candidate_inventory.csv")
        candidates = candidates[candidates.method.eq("cook_row_edge_alley_open_3m")]
        rows = []
        for _, r in candidates.iterrows():
            geometry = shapely.from_wkt(r.geometry_wkt)
            inside = geometry_mask([geometry], out_shape=ground.shape, transform=ground.transform, invert=True)
            arr = np.ma.filled(delta_m[inside & valid], np.nan)
            arr = arr[np.isfinite(arr)]
            rows.append({"candidate_index": int(r.candidate_index), "candidate_area_m2": r.area_m2,
                         "motorway_exposure": r.motorway_exposure, "valid_pixels": len(arr),
                         "height_p50_m": float(np.median(arr)) if len(arr) else None,
                         "height_p90_m": float(np.percentile(arr, 90)) if len(arr) else None,
                         "height_gt_2_5m_fraction": float(np.mean(arr > 2.5)) if len(arr) else None,
                         "height_gt_5m_fraction": float(np.mean(arr > 5)) if len(arr) else None})
        table = pd.DataFrame(rows)
        fig, ax = plt.subplots(figsize=(10, 9))
        image = ax.imshow(np.ma.filled(delta_m, np.nan), extent=[*ground.bounds[::2], *ground.bounds[1::2]],
                          origin="upper", cmap="viridis", vmin=0, vmax=10)
        for _, r in candidates.iterrows():
            geometry = shapely.from_wkt(r.geometry_wkt)
            color = "cyan" if int(r.candidate_index) in (52, 60, 65, 66, 72) else "magenta"
            xline, yline = geometry.exterior.xy
            ax.plot(xline, yline, color=color, linewidth=1)
            point = geometry.representative_point()
            ax.text(point.x, point.y, str(int(r.candidate_index)), fontsize=7, color="white",
                    ha="center", va="center", bbox={"facecolor": "black", "alpha": .6, "pad": 1})
        ax.set_xlim(x-220, x+220)
        ax.set_ylim(y-220, y+220)
        ax.set_aspect("equal")
        ax.set_title("Cook 2022 DSM − DTM; cyan: built faces, magenta: motorway slivers")
        fig.colorbar(image, ax=ax, label="Surface above terrain (m)")
        fig.tight_layout()
        fig.savefig(OUT / "ndsm_candidate_overlay.png", dpi=180)
        plt.close(fig)
    table.to_csv(OUT / "candidate_height_support.csv", index=False)
    summary = {"purpose": "structural signal only, not block classification or independent validation",
               "zone_id": zone["zone_id"], "bbox_epsg26916": bbox,
               "raster_export_pixel_size_m": (2*HALF_WIDTH_M)/SIZE,
               "candidate_count": len(table),
               "candidate_source_sha256": sha(PREVIOUS / "motorway_complete_candidate_inventory.csv"),
               "receipts": receipts,
               "cautions": ["DTM/DSM differ by buildings, vegetation and elevated structures; a flat true block may have zero height signal.",
                            "The 2022 LiDAR predates the 2025 orthophoto and may not show later change.",
                            "This diagnostic uses rasters, not classified point-cloud road/bridge returns."]}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()

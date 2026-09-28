"""Extract one Cook 2022 LAS ZIP member and audit point classes in M3 faces."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import zlib

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import shapely
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "analysis/work/chicago_m3_lidar_point_pilot_2026_09_26"
OUT = ROOT / "analysis/results/Chicago/chicago_m3_lidar_point_pilot_2026_09_26"
PREVIOUS = ROOT / "analysis/results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26"
ZIP_URL = "https://clearinghouse.isgs.illinois.edu/distribute/district1/cook/2022/cook-las3.zip"
MEMBER = "13259350.las"
MEMBER_OFFSET = 561661162323
MEMBER_COMPRESSED_SIZE = 633728392
MEMBER_UNCOMPRESSED_SIZE = 1046669819
TARGET_IDS = [52, 56, 57, 69, 71, 72, 74, 75, 79]


def read_range(session: requests.Session, start: int, stop: int) -> bytes:
    r = session.get(ZIP_URL, headers={"Range": f"bytes={start}-{stop}"}, timeout=60)
    r.raise_for_status()
    if r.status_code != 206 or len(r.content) != stop-start+1:
        raise RuntimeError(f"Incomplete range {start}-{stop}: {r.status_code}, {len(r.content)} bytes")
    return r.content


def fetch_member(path: Path, member: str = MEMBER, offset: int = MEMBER_OFFSET,
                 compressed_size: int = MEMBER_COMPRESSED_SIZE,
                 uncompressed_size: int = MEMBER_UNCOMPRESSED_SIZE) -> dict:
    with requests.Session() as session:
        header = read_range(session, offset, offset+29)
        signature, version, flags, method, mtime, mdate, crc, compressed, uncompressed, name_len, extra_len = struct.unpack("<IHHHHHIIIHH", header)
        assert signature == 0x04034B50 and method == 8
        name = read_range(session, offset+30, offset+29+name_len).decode()
        assert name == member
        start = offset+30+name_len+extra_len
        stop = start+compressed_size-1
        assert compressed in (0, 0xFFFFFFFF, compressed_size)
        decoder = zlib.decompressobj(-15)
        digest = hashlib.sha256()
        output_bytes = 0
        output_crc = 0
        with path.open("wb") as handle:
            # Requests returns an HTTP byte-range stream; only this member is transferred.
            response = session.get(ZIP_URL, headers={"Range": f"bytes={start}-{stop}"}, stream=True, timeout=180)
            response.raise_for_status()
            if response.status_code != 206:
                raise RuntimeError("Archive server did not honor Range")
            for block in response.iter_content(4*1024*1024):
                if not block:
                    continue
                digest.update(block)
                decoded = decoder.decompress(block)
                handle.write(decoded)
                output_bytes += len(decoded)
                output_crc = zlib.crc32(decoded, output_crc)
            tail = decoder.flush()
            handle.write(tail)
            output_bytes += len(tail)
            output_crc = zlib.crc32(tail, output_crc)
        assert decoder.eof and output_bytes == uncompressed_size
        assert output_crc == crc
        return {"url": ZIP_URL, "member": member, "member_header_offset": offset,
                "compressed_range": [start, stop], "compressed_bytes": compressed_size,
                "uncompressed_bytes": output_bytes, "compressed_sha256": digest.hexdigest(),
                "zip_crc32": crc}


def parse_header(path: Path) -> dict:
    with path.open("rb") as file:
        h = file.read(375)
    assert h[:4] == b"LASF"
    version = f"{h[24]}.{h[25]}"
    offset = struct.unpack_from("<I", h, 96)[0]
    point_format = h[104] & 0x3F
    record_length = struct.unpack_from("<H", h, 105)[0]
    count = struct.unpack_from("<I", h, 107)[0]
    if version == "1.4":
        extended = struct.unpack_from("<Q", h, 247)[0]
        if extended:
            count = extended
    scales = struct.unpack_from("<ddd", h, 131)
    offsets = struct.unpack_from("<ddd", h, 155)
    return {"version": version, "point_offset": offset, "point_format": point_format,
            "point_record_length": record_length, "point_count": count,
            "xyz_scales": scales, "xyz_offsets": offsets}


def audit(path: Path, header: dict) -> pd.DataFrame:
    fmt = header["point_format"]
    class_offset = 16 if fmt >= 6 else 15
    dtype = np.dtype({"names": ["X", "Y", "Z", "classification"],
                      "formats": ["<i4", "<i4", "<i4", "u1"],
                      "offsets": [0, 4, 8, class_offset],
                      "itemsize": header["point_record_length"]})
    points = np.memmap(path, dtype=dtype, mode="r", offset=header["point_offset"],
                       shape=(header["point_count"],))
    frame = pd.read_csv(PREVIOUS / "motorway_complete_candidate_inventory.csv")
    frame = frame[(frame.method == "cook_row_edge_alley_open_3m") & frame.candidate_index.isin(TARGET_IDS)]
    polygons = gpd.GeoSeries.from_wkt(frame.geometry_wkt, crs=26916).to_crs(6455)
    labels = list(zip(frame.candidate_index.astype(int), polygons))
    scales, offsets = header["xyz_scales"], header["xyz_offsets"]
    bounds = shapely.union_all(list(polygons)).bounds
    records = []
    for start in range(0, len(points), 1_000_000):
        part = points[start:start+1_000_000]
        x = part["X"].astype("float64")*scales[0]+offsets[0]
        y = part["Y"].astype("float64")*scales[1]+offsets[1]
        mask = (x>=bounds[0])&(x<=bounds[2])&(y>=bounds[1])&(y<=bounds[3])
        if not mask.any():
            continue
        x,y,c = x[mask],y[mask],part["classification"][mask]
        for cid,polygon in labels:
            inside = shapely.contains_xy(polygon,x,y)
            if inside.any():
                values,counts=np.unique(c[inside],return_counts=True)
                records.extend({"candidate_index":cid,"classification":int(v),"count":int(n)}
                               for v,n in zip(values,counts))
    if not records:
        raise RuntimeError("No points fell inside target candidates; check CRS and LAS header")
    data = pd.DataFrame(records).groupby(["candidate_index","classification"],as_index=False)["count"].sum()
    totals = data.groupby("candidate_index")["count"].sum().rename("total_points")
    data = data.join(totals,on="candidate_index")
    data["fraction"] = data["count"]/data["total_points"]
    return data


def bridge_profile(path: Path, header: dict) -> pd.DataFrame:
    """Diagnostic profile at a class-17 cluster west of the motorway core."""
    dtype = np.dtype({"names": ["X", "Y", "Z", "classification"],
                      "formats": ["<i4", "<i4", "<i4", "u1"],
                      "offsets": [0, 4, 8, 16], "itemsize": header["point_record_length"]})
    points = np.memmap(path, dtype=dtype, mode="r", offset=header["point_offset"],
                       shape=(header["point_count"],))
    cx, cy = Transformer.from_crs(26916, 6455, always_xy=True).transform(434740, 4648125)
    scales, offsets = header["xyz_scales"], header["xyz_offsets"]
    x = points["X"].astype("float64")*scales[0]+offsets[0]
    y = points["Y"].astype("float64")*scales[1]+offsets[1]
    vicinity = (abs(x-cx)<65)&(abs(y-cy)<65)
    rows = []
    for cls in (2, 11, 17):
        selected = points[vicinity & (points["classification"] == cls)]
        z = selected["Z"].astype("float64")*scales[2]+offsets[2]
        rows.append({"class": cls, "count": len(z),
                     "z_p10_ft": float(np.percentile(z,10)) if len(z) else None,
                     "z_p50_ft": float(np.median(z)) if len(z) else None,
                     "z_p90_ft": float(np.percentile(z,90)) if len(z) else None})
    return pd.DataFrame(rows)


def main() -> None:
    WORK.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    path = WORK/MEMBER
    receipt_path = OUT/"member_receipt.json"
    if not path.exists():
        receipt=fetch_member(path)
        receipt_path.write_text(json.dumps(receipt,indent=2)+"\n")
    else:
        receipt=json.loads(receipt_path.read_text())
    header=parse_header(path)
    if path.stat().st_size != MEMBER_UNCOMPRESSED_SIZE:
        raise RuntimeError("LAS tile size differs from archive directory")
    table=audit(path,header)
    table.to_csv(OUT/"candidate_point_classes.csv",index=False)
    bridge = bridge_profile(path,header)
    bridge.to_csv(OUT/"bridge_class_profile.csv",index=False)
    summary={"source":receipt,"las_header":header,"target_candidate_indices":TARGET_IDS,
             "candidate_geometry_sha256":hashlib.sha256((PREVIOUS/"motorway_complete_candidate_inventory.csv").read_bytes()).hexdigest(),
             "status":"single-tile targeted class diagnostic; not a complete block validation"}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(table.pivot_table(index="candidate_index",columns="classification",values="fraction",fill_value=0).round(3).to_string())


if __name__=="__main__":
    main()

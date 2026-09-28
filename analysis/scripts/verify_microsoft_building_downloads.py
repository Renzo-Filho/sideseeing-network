"""Verify the six supplied Microsoft tiles and their redundant plain copies."""

import argparse
import csv
import gzip
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SELECTED = ROOT / "analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review/selected_tiles.csv"
SOURCES = {"CHI": ROOT / "predios_chicago_raw", "SP": ROOT / "predios_sp_raw"}


def verify_pair(compressed, plain):
    compressed_hash = hashlib.sha256()
    with compressed.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            compressed_hash.update(chunk)
    stream_hash = hashlib.sha256()
    lines = 0
    first = None
    with gzip.open(compressed, "rb") as source, plain.open("rb") as counterpart:
        while chunk := source.read(1024 * 1024):
            expected = counterpart.read(len(chunk))
            if chunk != expected:
                raise ValueError(f"Decompressed mismatch: {compressed} and {plain}")
            stream_hash.update(chunk)
            lines += chunk.count(b"\n")
            if first is None:
                first = json.loads(chunk.split(b"\n", 1)[0])
        if counterpart.read(1):
            raise ValueError(f"Plain copy has trailing content: {plain}")
    if first is None or first.get("type") != "Feature" or first.get("geometry", {}).get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"Unexpected GeoJSONL schema: {compressed}")
    if set(first.get("properties", {})) != {"height", "confidence"}:
        raise ValueError(f"Unexpected properties: {compressed}")
    return {
        "compressed_sha256": compressed_hash.hexdigest(),
        "decompressed_sha256": stream_hash.hexdigest(),
        "compressed_bytes": compressed.stat().st_size,
        "decompressed_bytes": plain.stat().st_size,
        "line_count": lines,
        "first_properties": first["properties"],
        "plain_copy_exact": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selected = list(csv.DictReader(SELECTED.open(newline="")))
    if len(selected) != 6:
        raise ValueError("Expected six selected tiles")
    output = []
    expected_names = {city: set() for city in SOURCES}
    for row in selected:
        city, key = row["city"], row["quadkey"]
        if not re.fullmatch(r"[0-3]{9}", key):
            raise ValueError(f"Unexpected key: {key}")
        stem = f"{city}_{int(key)}.geojsonl"
        compressed, plain = SOURCES[city] / f"{stem}.gz", SOURCES[city] / stem
        expected_names[city].update((compressed.name, plain.name))
        if not compressed.is_file() or not plain.is_file():
            raise FileNotFoundError(f"Missing selected pair: {compressed}, {plain}")
        result = verify_pair(compressed, plain)
        output.append({"city": city, "quadkey": key, "source_url": row["url"],
                       "compressed_path": str(compressed.relative_to(ROOT)),
                       "plain_path": str(plain.relative_to(ROOT)), **result})
        print(city, key, result["line_count"], "records", flush=True)
    for city, folder in SOURCES.items():
        extra = {p.name for p in folder.iterdir()} - expected_names[city]
        if extra:
            raise ValueError(f"Unexpected files in {folder}: {sorted(extra)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"tiles": output, "all_plain_copies_exact": True}, indent=2) + "\n")


if __name__ == "__main__":
    main()

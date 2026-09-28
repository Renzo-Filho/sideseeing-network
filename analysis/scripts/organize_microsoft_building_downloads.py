"""Move verified Microsoft gzip originals; remove only identical plain copies."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "analysis/results/SP_CHI/microsoft_footprints_2026_09_22_review"
DESTINATIONS = {
    "CHI": ROOT / "analysis/data/Chicago/microsoft_buildings_2026_08_13/raw_tiles",
    "SP": ROOT / "analysis/data/SP/microsoft_buildings_2026_08_13/raw_tiles",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    verified = json.loads((REVIEW / "local_file_inventory.json").read_text())
    if not verified["all_plain_copies_exact"] or len(verified["tiles"]) != 6:
        raise ValueError("Incomplete prior verification")
    for row in verified["tiles"]:
        compressed = ROOT / row["compressed_path"]
        plain = ROOT / row["plain_path"]
        if not compressed.is_file() or not plain.is_file():
            raise FileNotFoundError("Source pair changed after verification")
        if sha256(compressed) != row["compressed_sha256"]:
            raise ValueError(f"Compressed tile changed: {compressed}")
        if sha256(plain) != row["decompressed_sha256"]:
            raise ValueError(f"Plain copy changed: {plain}")
        destination = DESTINATIONS[row["city"]] / f"{row['quadkey']}.geojsonl.gz"
        if destination.exists():
            raise FileExistsError(destination)
    organized = []
    for row in verified["tiles"]:
        compressed = ROOT / row["compressed_path"]
        plain = ROOT / row["plain_path"]
        destination = DESTINATIONS[row["city"]] / f"{row['quadkey']}.geojsonl.gz"
        destination.parent.mkdir(parents=True, exist_ok=True)
        compressed.rename(destination)
        if sha256(destination) != row["compressed_sha256"]:
            raise ValueError(f"Moved tile hash mismatch: {destination}")
        plain.unlink()
        organized.append({
            "city": row["city"], "quadkey": row["quadkey"],
            "source_url": row["source_url"],
            "path": str(destination.relative_to(ROOT)),
            "sha256": row["compressed_sha256"],
            "compressed_bytes": row["compressed_bytes"],
            "record_lines": row["line_count"],
            "deleted_redundant_plain_path": row["plain_path"],
            "deleted_plain_sha256": row["decompressed_sha256"],
        })
        print(destination.relative_to(ROOT), flush=True)
    (REVIEW / "organized_inventory.json").write_text(
        json.dumps({"tiles": organized, "plain_copies_deleted": 6}, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()

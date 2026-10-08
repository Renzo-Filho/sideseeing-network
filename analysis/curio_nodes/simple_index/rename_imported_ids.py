"""Rename this dataflow's opaque Curio dataset IDs to source-based IDs.

Curio currently identifies account imports by the ``imported.`` prefix. Keep
that prefix so the renamed datasets remain visible in the account catalog.

Dry run: python3 rename_imported_ids.py /path/to/curio
Apply:   python3 rename_imported_ids.py /path/to/curio --apply
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile


PROJECT_ID = "4e6b8d2a-af2e-44f2-9ce9-32b1646553f3"
PROJECT_NAME = "Composite urban index: method A and method B"
USER_KEY = "3"

# Old ID -> (new ID, source label shown in Curio's dataset detail panel).
RENAMES = {
    "imported.x23a14d9b8587": ("imported.overture.places-chicago-2026-08-19", "Overture Maps"),
    "imported.x2db17569c3a0": ("imported.overture.buildings-chicago-2026-08-19", "Overture Maps"),
    "imported.x3727f2fda51e": ("imported.cta.gtfs-chicago-stop-times", "CTA"),
    "imported.x4aa4b4cc31c3": ("imported.overture.road-segments-sao-paulo-2026-08-19", "Overture Maps"),
    "imported.x64515f91c2a9": ("imported.cityofchicago.hydrography", "City of Chicago Data Portal"),
    "imported.x66198cc633dd": ("imported.cta.gtfs-chicago-stops", "CTA"),
    "imported.x662f76045de9": ("imported.cityofchicago.community-areas", "City of Chicago Data Portal"),
    "imported.x7ac85649d954": ("imported.ibge.cnefe-2022-sao-paulo", "IBGE"),
    "imported.x8fed58a0f5f2": ("imported.overture.places-sao-paulo-2026-08-19", "Overture Maps"),
    "imported.x90a0aac51bcf": ("imported.sptrans.gtfs-sao-paulo-stop-times", "SPTrans"),
    "imported.xb43db0d13ab5": ("imported.sptrans.gtfs-sao-paulo-routes", "SPTrans"),
    "imported.xb84a111ab174": ("imported.ghsl.chicago-height-volume-rasters", "European Commission JRC"),
    "imported.xbe909a4dfb70": ("imported.cta.gtfs-chicago-routes", "CTA"),
    "imported.xccd77d2c89be": ("imported.sptrans.gtfs-sao-paulo-stops", "SPTrans"),
    "imported.xcd6a7eec205a": ("imported.ghsl.sao-paulo-height-volume-rasters", "European Commission JRC"),
    "imported.xce9da0dc95a3": ("imported.overture.road-segments-chicago-2026-08-19", "Overture Maps"),
    "imported.xd58951d22222": ("imported.cta.gtfs-chicago-trips", "CTA"),
    "imported.xd98c8039891a": ("imported.sptrans.gtfs-sao-paulo-trips", "SPTrans"),
    "imported.xde1e6da51ead": ("imported.geosampa.sao-paulo-districts", "GeoSampa"),
}


def prepare(curio_root: Path):
    user_root = curio_root / ".curio" / "users" / USER_KEY
    store = user_root / "datasets"
    spec_path = user_root / "projects" / PROJECT_ID / "spec.trill.json"
    spec_bytes = spec_path.read_bytes()
    spec_text = spec_bytes.decode("utf-8")
    spec = json.loads(spec_text)
    if spec["dataflow"].get("name") != PROJECT_NAME:
        raise RuntimeError("The saved project name changed; refusing to migrate")
    refs = {ref["datasetId"] for ref in spec["dataflow"].get("datasets", [])}
    if refs & RENAMES.keys() != RENAMES.keys():
        raise RuntimeError(f"Expected all 19 old IDs in the saved project; missing {sorted(RENAMES.keys() - refs)}")
    if len({new for new, _ in RENAMES.values()}) != len(RENAMES):
        raise RuntimeError("New dataset IDs are not unique")

    prepared = []
    for old, (new, source_label) in RENAMES.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,62}(?:\.[a-z][a-z0-9-]{0,62}){1,5}", new):
            raise RuntimeError(f"Invalid Curio dataset ID: {new}")
        source = store / f"{old}@1"
        target = store / f"{new}@1"
        if not source.is_dir() or target.exists():
            raise RuntimeError(f"Missing source or occupied target: {source} -> {target}")
        manifest_path = source / "manifest.json"
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        if manifest.get("id") != old:
            raise RuntimeError(f"Manifest ID differs from its folder: {source}")
        manifest["id"] = new
        manifest["sourceLabel"] = source_label
        prepared.append((source, target, manifest_bytes, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"))

    updated_text = spec_text
    for old, (new, _) in RENAMES.items():
        updated_text = updated_text.replace(old, new)
    updated_spec = json.loads(updated_text)
    updated_refs = {ref["datasetId"] for ref in updated_spec["dataflow"]["datasets"]}
    if any(old in updated_text for old in RENAMES):
        raise RuntimeError("Old IDs remain in transformed project spec")
    if {new for new, _ in RENAMES.values()} - updated_refs:
        raise RuntimeError("New IDs are missing from transformed project refs")
    return spec_path, spec_bytes, updated_text.encode("utf-8"), prepared


def apply(spec_path, spec_bytes, new_spec_bytes, prepared):
    backup = Path(tempfile.mkdtemp(prefix="curio-source-id-rename-"))
    (backup / "spec.trill.json").write_bytes(spec_bytes)
    (backup / "mapping.json").write_text(
        json.dumps(RENAMES, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for source, _, manifest_bytes, _ in prepared:
        (backup / f"{source.name}.manifest.json").write_bytes(manifest_bytes)
    moved = []
    spec_written = False
    try:
        for source, target, _, new_manifest in prepared:
            stage = source / "manifest.json.source-id-rename"
            stage.write_text(new_manifest, encoding="utf-8")
            source.rename(target)
            moved.append((source, target))
            os.replace(target / stage.name, target / "manifest.json")

        # Abort if Curio saved a newer version while the directories moved.
        if hashlib.sha256(spec_path.read_bytes()).digest() != hashlib.sha256(spec_bytes).digest():
            raise RuntimeError("Curio saved the project during migration; no project edit applied")
        staged_spec = spec_path.with_name("spec.trill.json.source-id-rename")
        staged_spec.write_bytes(new_spec_bytes)
        os.replace(staged_spec, spec_path)
        spec_written = True
        print(f"Renamed {len(moved)} datasets; backup: {backup}")
    except Exception:
        if spec_written:
            spec_path.write_bytes(spec_bytes)
        for source, target in reversed(moved):
            if target.exists():
                target.rename(source)
                old_manifest = backup / f"{source.name}.manifest.json"
                (source / "manifest.json").write_bytes(old_manifest.read_bytes())
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("curio_root", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    spec_path, spec_bytes, new_spec_bytes, prepared = prepare(args.curio_root.resolve())
    for source, target, _, _ in prepared:
        print(f"{source.name} -> {target.name}")
    if args.apply:
        apply(spec_path, spec_bytes, new_spec_bytes, prepared)
    else:
        print("Dry run: no files changed")


if __name__ == "__main__":
    main()

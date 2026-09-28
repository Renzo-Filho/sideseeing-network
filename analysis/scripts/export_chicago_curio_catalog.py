"""Export Chicago model inputs into a local Curio Data Catalog.

This script adds missing datasets only. It deliberately excludes DuPage parcel
records, whose publisher terms restrict redistribution through a shared catalog.
Run with --catalog /path/to/curio/datasets. Existing catalog IDs are never
overwritten; --repair-microsoft fixes the pre-existing unsupported GeoJSONL item.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
CHI = ROOT / "analysis/data/Chicago"
CAD = CHI / "chicago_cadastral_2026_09_18"
PREP = ROOT / "analysis/work/prepared/Chicago/chi_functional_2026_09_16_v2"


def metadata(dataset_id, name, fmt, filename, publisher, description, tags, license_text, source):
    return {
        "id": dataset_id,
        "name": name,
        "version": "1.0.0",
        "compatibility": {"curioRuntime": ">=0.5.0", "major": 1},
        "format": fmt,
        "dataFile": f"data/{filename}",
        "description": description,
        "publisher": publisher,
        "sourceLabel": publisher,
        "license": license_text,
        "tags": ["chicago", "sideseeing", *tags],
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sourcePath": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
    }


def register(catalog, spec):
    dataset_id, name, source, kind, publisher, description, tags, license_text = spec
    folder = catalog / f"{dataset_id}@1"
    if (folder / "manifest.json").exists():
        print(f"SKIP existing {dataset_id}", flush=True)
        return
    target_dir = folder / "data"
    target_dir.mkdir(parents=True, exist_ok=True)
    if kind == "parquet_parts":
        filename = f"{dataset_id.rsplit('.', 1)[-1]}.parquet"
        target = target_dir / filename
        dataset = ds.dataset(sorted(source.glob("part_*.parquet")), format="parquet")
        writer = pq.ParquetWriter(target, dataset.schema, compression="zstd")
        count = 0
        try:
            for batch in dataset.to_batches(batch_size=25000):
                writer.write_batch(batch)
                count += batch.num_rows
        finally:
            writer.close()
        fmt = "parquet"
    elif kind == "gtfs_parquet":
        import duckdb

        filename = source.stem + ".parquet"
        target = target_dir / filename
        con = duckdb.connect()
        try:
            con.read_csv(str(source), all_varchar=True, header=True).write_parquet(
                str(target), compression="zstd"
            )
        finally:
            con.close()
        fmt = "parquet"
        count = pq.ParquetFile(target).metadata.num_rows
    elif kind == "workbook_jsonl":
        filename = "commercial-workbook-details.parquet"
        target = target_dir / filename
        schema = pa.schema([
            ("source_url", pa.string()), ("source_file", pa.string()),
            ("sheet", pa.string()), ("source_markdown_line", pa.int64()),
            ("keypin", pa.string()), ("chicago_matched_pins_json", pa.string()),
            ("has_related_pin_without_chicago_geometry", pa.bool_()),
            ("fields_json", pa.string()),
        ])
        writer = pq.ParquetWriter(target, schema, compression="zstd")
        count = 0
        rows = []
        try:
            with source.open() as stream:
                for line in stream:
                    raw = json.loads(line)
                    rows.append({
                        "source_url": raw.get("source_url"), "source_file": raw.get("source_file"),
                        "sheet": raw.get("sheet"), "source_markdown_line": raw.get("source_markdown_line"),
                        "keypin": raw.get("keypin"),
                        "chicago_matched_pins_json": json.dumps(raw.get("chicago_matched_pins")),
                        "has_related_pin_without_chicago_geometry": raw.get("has_related_pin_without_chicago_geometry"),
                        "fields_json": json.dumps(raw.get("fields")),
                    })
                    if len(rows) >= 10000:
                        writer.write_table(pa.Table.from_pylist(rows, schema=schema))
                        count += len(rows)
                        rows.clear()
            if rows:
                writer.write_table(pa.Table.from_pylist(rows, schema=schema))
                count += len(rows)
        finally:
            writer.close()
        fmt = "parquet"
    elif kind == "link":
        filename = source.name
        target = target_dir / filename
        shutil.copy2(source, target)
        fmt = {".geojson": "geojson", ".csv": "csv", ".parquet": "parquet", ".tif": "geotiff"}[source.suffix]
        count = pq.ParquetFile(target).metadata.num_rows if fmt == "parquet" else None
    else:
        raise ValueError(kind)
    manifest = metadata(dataset_id, name, fmt, filename, publisher, description, tags, license_text, source)
    if count is not None:
        manifest["featureCount" if "geometry" in pq.ParquetFile(target).schema_arrow.names else "rowCount"] = count
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"ADD {dataset_id}: {target.stat().st_size:,} bytes", flush=True)


def repair_microsoft(catalog):
    """Replace an unsupported, directory-pointing GeoJSONL manifest with GeoParquet."""
    folder = catalog / "data.microsoft.building-footprints-chicago@1"
    manifest_file = folder / "manifest.json"
    if not manifest_file.exists():
        return
    manifest = json.loads(manifest_file.read_text())
    if manifest.get("format") == "parquet" and (folder / manifest["dataFile"]).is_file():
        print("SKIP valid Microsoft GeoParquet", flush=True)
        return
    from pyproj import CRS
    from shapely.geometry import shape
    from shapely import to_wkb

    target = folder / "data/building-footprints-chicago.parquet"
    schema = pa.schema([
        pa.field("height", pa.float64()),
        pa.field("confidence", pa.float64()),
        pa.field("geometry", pa.binary()),
    ])
    geo = {
        "version": "1.1.0",
        "primary_column": "geometry",
        "columns": {"geometry": {"encoding": "WKB", "geometry_types": ["Polygon", "MultiPolygon"],
                                "crs": CRS.from_epsg(4326).to_json_dict()}},
    }
    schema = schema.with_metadata({b"geo": json.dumps(geo).encode()})
    writer = pq.ParquetWriter(target, schema, compression="zstd")
    heights, confidences, geometries = [], [], []
    count = 0
    try:
        for source in sorted((CHI / "microsoft_buildings_2026_08_13/raw_tiles").glob("*.geojsonl.gz")):
            with gzip.open(source, "rt") as stream:
                for line in stream:
                    feature = json.loads(line)
                    props = feature.get("properties") or {}
                    heights.append(props.get("height"))
                    confidences.append(props.get("confidence"))
                    geometries.append(to_wkb(shape(feature["geometry"])))
                    if len(geometries) >= 25000:
                        writer.write_table(pa.Table.from_arrays([
                            pa.array(heights, type=pa.float64()), pa.array(confidences, type=pa.float64()),
                            pa.array(geometries, type=pa.binary()),
                        ], schema=schema))
                        count += len(geometries)
                        heights, confidences, geometries = [], [], []
            print(f"CONVERT Microsoft tile {source.name}", flush=True)
        if geometries:
            writer.write_table(pa.Table.from_arrays([
                pa.array(heights, type=pa.float64()), pa.array(confidences, type=pa.float64()),
                pa.array(geometries, type=pa.binary()),
            ], schema=schema))
            count += len(geometries)
    finally:
        writer.close()
    # The source tiles remain in sideseeing; remove only the redundant Curio copies.
    for old in (folder / "data").glob("*.geojsonl.gz"):
        old.unlink()
    manifest.update(format="parquet", dataFile="data/building-footprints-chicago.parquet",
                    featureCount=count, publisher="Microsoft", sourceLabel="Microsoft",
                    description="Microsoft Chicago ML footprints converted from three source GeoJSONL tiles; height is metres, not floors. Tiles include a buffer outside city limits.")
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"REPAIR Microsoft: {count:,} geometries", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--repair-microsoft", action="store_true")
    args = ap.parse_args()
    c = args.catalog
    common = [
        ("data.cityofchicago.hydrography-sideseeing", "Chicago Hydrography", CHI / "Hydro_20260916.geojson", "link", "City of Chicago", "Municipal water polygons for Community Area land denominators and block-boundary review.", ["water", "boundaries"], "Chicago open data; verify publisher terms"),
        ("data.dupage.chicago-addison-township-intersection", "Chicago Addison Township Intersection", CHI / "dupage_characteristics_2026_09_21/chicago_township_intersections.parquet", "link", "DuPage County GIS", "Chicago-clipped Addison Township geometry for scoping the DuPage cadastral gap. Contains no restricted parcel real-estate records.", ["boundaries", "cadastral"], "Verify DuPage township-layer terms"),
        ("data.overture.transportation-segments-chicago", "Overture Chicago Road Segments", CHI / "overture_2026_08_19/segment/part_0000.parquet", "link", "Overture Maps", "Overture 2026-08-19 transport segments for street density, class composition and topology review.", ["streets", "network"], "See Overture Maps source terms"),
        ("data.overture.transportation-connectors-chicago", "Overture Chicago Road Connectors", CHI / "overture_2026_08_19/connector/part_0000.parquet", "link", "Overture Maps", "Overture 2026-08-19 connectors; candidate topology, not verified physical junctions.", ["junctions", "network"], "See Overture Maps source terms"),
        ("data.census.chicago-blocks-pop20-lodes-2022", "Chicago Intersecting Census Blocks", PREP / "blocks.parquet", "link", "US Census Bureau / Sideseeing", "39,498 Chicago-intersecting 2020 Census blocks, projected geometry, POP20 and validated LODES WAC join. Includes border blocks; allocation is a separate step.", ["population", "employment", "blocks"], "US Census public data; see LODES terms"),
        ("data.census.illinois-lodes-wac-2022", "Illinois LODES Workplace Jobs 2022", CHI / "il_wac_S000_JT00_2022.csv", "link", "US Census Bureau", "WAC S000 JT00 workplace block counts; use C000 as total jobs and spatially join to Census blocks.", ["employment", "jobs"], "US Census public data; see LODES terms"),
        ("data.sideseeing.chicago-acs-community-areas", "Chicago Community Area ACS Aggregate", CHI / "chicago_acs_community_areas.csv", "link", "Sideseeing / source provenance unresolved", "Supplied 77-area population aggregate labeled 2023. For U3 period sensitivity only; source period, method and margins of error remain unresolved.", ["population", "acs", "diagnostic"], "Source provenance and reuse terms unresolved"),
    ]
    for name, title, publisher in [
        ("cook_parcels_2024", "Cook Chicago Parcels 2024", "Cook County GIS"),
        ("cook_universe_2024", "Cook Chicago Assessor Universe 2024", "Cook County Assessor"),
        ("cook_residential_2024", "Cook Chicago Residential Characteristics 2024", "Cook County Assessor"),
        ("cook_condo_2024", "Cook Chicago Condominium Characteristics 2024", "Cook County Assessor"),
        ("cook_commercial_2024", "Cook Chicago Commercial Valuation 2024", "Cook County Assessor"),
        ("cook_buildings_2022", "Cook Chicago Building Footprints 2022", "Cook County GIS"),
        ("benchmarking_2023", "Chicago Energy Benchmarking 2023", "City of Chicago"),
        ("benchmarking_covered_current", "Chicago Benchmarking Coverage Register", "City of Chicago"),
    ]:
        common.append(("data.sideseeing." + name.replace("_", "-"), title, CAD / name,
                       "parquet_parts", publisher,
                       "Chicago-filtered source records. Analytical candidate only: records do not establish unique buildings or all-stock constructed floor area. See sideseeing cadastral audit.",
                       ["cadastral", "buildings"], "Consult source publisher terms before redistribution"))
    common.append(("data.sideseeing.cook-commercial-workbook-details-2024",
                   "Cook Chicago Commercial Workbook Details 2024",
                   CHI / "chicago_workbooks_2026_09_19/chicago_detail_records.jsonl",
                   "workbook_jsonl", "Cook County Assessor",
                   "Parsed text from eight commercial valuation workbooks. The original workbook binaries were not validated. fields_json preserves displayed values; no exact stories or gross-area field was found.",
                   ["cadastral", "commercial", "workbooks"],
                   "Consult Cook County Assessor source terms before redistribution"))
    for name in ["stops", "routes", "trips", "stop_times", "calendar", "calendar_dates", "agency"]:
        common.append(("data.cta.gtfs-chicago-" + name.replace("_", "-"), "CTA GTFS " + name.replace("_", " ").title(),
                       CHI / "google_transit" / (name + ".txt"), "gtfs_parquet", "Chicago Transit Authority",
                       "CTA static GTFS feed table. Combine by GTFS keys and apply service calendars; bus routes only for U4.",
                       ["transit", "gtfs", name.replace("_", "-")],
                       "CTA Developer License Agreement: limited purpose; review before redistribution"))
    for code, title in [("H_ANBH_E2018", "GHSL Chicago Net Building Height 2018"),
                        ("H_AGBH_E2018", "GHSL Chicago Gross Building Height 2018"),
                        ("V_E2020", "GHSL Chicago Built Volume 2020")]:
        source = next((CHI / "ghsl_public_2026_09_21").glob(f"GHS_BUILT_{code}*.tif"))
        common.append(("data.ghsl.chicago-" + code.lower().replace("_", "-"), title, source, "link", "European Commission JRC",
                       "Chicago raster clip for supplemental vertical-form analysis. Not reported floors or constructed floor area.",
                       ["building-height", "raster"], "See GHSL open data terms"))
    for spec in common:
        register(c, spec)
    if args.repair_microsoft:
        repair_microsoft(c)


if __name__ == "__main__":
    main()

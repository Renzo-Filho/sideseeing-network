"""Check only public Cook parcel-service metadata and seven saved M7 keys.

Raw service JSON is cached in ignored analysis/work. Results publish metadata
availability and per-key counts, not restricted parcel records or geometry.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
WORK = A / "work/chicago_m_holdout_2026_09_25/cook_parent_publication"
OUT = A / "results/Chicago/chicago_m_holdout_2026_09_25"
PARCEL = "https://gis.cookcountyil.gov/traditional/rest/services/parcelHistorical/MapServer"
HOSTED_2022 = "https://gis.cookcountyil.gov/hosting/rest/services/Hosted/Parcel_2022/FeatureServer"
KEYS = ["1308208021", "1308311047", "1716238028", "1710400048",
        "1710318058", "1709419111", "1903201036"]


def fetch(label: str, url: str, params: dict):
    query_url = requests.Request("GET", url, params=params).prepare().url
    cache = WORK / f"{label}.json"
    if cache.exists():
        content = cache.read_bytes()
    else:
        response = requests.get(query_url, timeout=50, headers={"User-Agent": "sideseeing-network bounded academic parcel-source audit"})
        response.raise_for_status()
        content = response.content
        assert len(content) < 2_000_000
        cache.write_bytes(content)
    data = json.loads(content)
    assert "error" not in data, data.get("error")
    return data, {"url": query_url, "sha256": hashlib.sha256(content).hexdigest(),
                  "cached_path": str(cache.relative_to(ROOT))}


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    service, service_receipt = fetch("parcel_2024_service", PARCEL, {"f": "json"})
    layer, layer_receipt = fetch("parcel_2024_layer", PARCEL + "/2024", {"f": "json"})
    hosted, hosted_receipt = fetch("hosted_2022_service", HOSTED_2022, {"f": "json"})
    where = "PIN10 IN (" + ",".join(f"'{x}'" for x in KEYS) + ")"
    remote, remote_receipt = fetch("parcel_2024_seven_keys", PARCEL + "/2024/query", {
        "where": where, "outFields": "OBJECTID,Name,PIN10,PARCELTYPE",
        "returnGeometry": "false", "f": "json"})
    assert not remote.get("exceededTransferLimit")
    features = [x["attributes"] for x in remote["features"]]
    remote_df = pd.DataFrame(features)
    assert set(remote_df.PIN10.astype(str)).issubset(KEYS)
    con = duckdb.connect()
    con.register("sample_keys", pd.DataFrame({"pin10": KEYS}))
    local_df = con.execute(
        "SELECT p.PIN10, p.OBJECTID, p.Name, p.PARCELTYPE "
        "FROM read_parquet(?) p JOIN sample_keys k ON p.PIN10=k.pin10",
        [str(A / "data/Chicago/chicago_cadastral_2026_09_18/cook_parcels_2024/part_*.parquet")],
    ).df()
    rows = []
    for key in KEYS:
        a = local_df.loc[local_df.PIN10.eq(key)]
        b = remote_df.loc[remote_df.PIN10.eq(key)]
        rows.append({"pin10": key, "installed_polygon_rows": len(a), "public_2024_rows": len(b),
                     "objectids_match": set(a.OBJECTID.astype(int)) == set(b.OBJECTID.astype(int)),
                     "installed_distinct_name_values": a.Name.nunique(),
                     "public_distinct_name_values": b.Name.nunique(),
                     "public_null_parceltype_rows": int(b.PARCELTYPE.isna().sum())})
    pd.DataFrame(rows).to_csv(OUT / "cook_public_key_reconciliation.csv", index=False)
    fields = {x["name"] for x in layer.get("fields", [])}
    availability = {
        "official_source_notes": "Public service metadata and seven PIN10 attributes only. Published description mentions underlying PIN/Ref_PIN/condo tables; this inspection checks what these REST services actually expose.",
        "parcel_2024_service_tables": [x.get("name") for x in service.get("tables", [])],
        "parcel_2024_layer_relationships": layer.get("relationships", []),
        "parcel_2024_layer_has_ref_pin": "REF_PIN" in fields,
        "parcel_2024_layer_has_polytype": "POLYTYPE" in fields,
        "parcel_2024_layer_has_pin10": "PIN10" in fields,
        "parcel_2024_layer_has_name_pin14": "Name" in fields,
        "hosted_2022_service_tables": [x.get("name") for x in hosted.get("tables", [])],
        "public_query_count": len(features),
        "receipts": {"parcel_2024_service": service_receipt, "parcel_2024_layer": layer_receipt,
                     "hosted_2022_service": hosted_receipt, "parcel_2024_seven_keys": remote_receipt},
    }
    (OUT / "cook_parent_publication.json").write_text(json.dumps(availability, indent=2) + "\n")
    print(json.dumps({k: v for k, v in availability.items() if k != "receipts"}, indent=2))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()

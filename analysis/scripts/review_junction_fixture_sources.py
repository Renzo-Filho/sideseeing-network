"""Preserve raw Overture street/level evidence for two paired M2 fixtures."""

import json
from pathlib import Path

import geopandas as gpd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2"
RUN = A / "work/runs/sp_chicago_harmonization_2026_09_22/roads"
PAIRS = [
    ("Chicago", "CHI:32", "loop_stacked_roads",
     "22240ae1-e54d-4fc2-9ffb-97558fadd02e", "5a317b77-497f-41f6-8c64-dbf3ab41df38"),
    ("SP", "SP:10", "bras_short_same_street_link",
     "0956a567-99f7-43ee-8861-b331010b8bb1", "9a85f3e4-da15-4163-9099-8626fa6c9d8c"),
]


def main():
    evidence = []
    for city, unit_id, label, first, second in PAIRS:
        points = gpd.read_parquet(RUN / f"{city}_connector_candidates.parquet")
        selected = points.loc[points.id.isin((first, second))]
        if len(selected) != 2:
            raise ValueError(f"Fixture connector absent: {label}")
        p = {row.id: [row.geometry.x, row.geometry.y] for row in selected.itertuples()}
        segments = []
        source = A / "data" / city / "overture_2026_08_19/segment/part_0000.parquet"
        for batch in pq.ParquetFile(source).iter_batches(
            columns=["id", "names", "class", "subclass", "connectors", "level_rules", "road_flags"],
            batch_size=30000,
        ):
            for row in batch.to_pylist():
                hits = [{"connector_id": x["connector_id"], "at": x["at"]}
                        for x in row["connectors"] or [] if x["connector_id"] in (first, second)]
                if hits:
                    segments.append({"id": row["id"], "primary_name": (row["names"] or {}).get("primary"),
                                     "class": row["class"], "subclass": row["subclass"],
                                     "level_rules": row["level_rules"], "road_flags": row["road_flags"],
                                     "fixture_connectors": hits})
        evidence.append({"city": city, "unit_id": unit_id, "label": label,
                         "connector_ids": [first, second], "coordinates_metric": p,
                         "segments": sorted(segments, key=lambda x: x["id"])})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fixture_source_evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    for row in evidence:
        print(row["label"], len(row["segments"]), "source segments")


if __name__ == "__main__":
    main()

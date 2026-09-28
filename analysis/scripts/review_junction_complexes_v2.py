"""Paired M2 pilot: compare nearby connector pairs with short source-road links."""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from harmonization.junctions_v2 import linked_components, short_connector_links


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2"
WORK = A / "work/runs/sp_chicago_harmonization_2026_09_22/roads"
PILOTS = {
    "Chicago": ("CHI", ["24", "28", "30", "32", "76"],
                "Chicago/chi_local_2026_09_16_v1/districts.parquet"),
    "SP": ("SP", ["10", "30", "35"],
           "SP/sp_prep_2026_09_10_v3/N02/districts.parquet"),
}


def main():
    summaries, groups, links_out = [], [], []
    for city, (prefix, ids, district_path) in PILOTS.items():
        roads = gpd.read_parquet(A / "work/prepared" / city / "overture_2026_08_19_review_v1/selected_roads.parquet")
        candidates = gpd.read_parquet(WORK / f"{city}_connector_candidates.parquet")
        districts = gpd.read_parquet(A / "work/prepared" / district_path)
        if city == "SP":
            districts["unit_id"] = "SP:" + districts.district_id.astype(str).str.zfill(2)
        if roads.crs != candidates.crs or roads.crs != districts.crs:
            raise ValueError(f"CRS mismatch in {city}")
        for local_id in ids:
            unit_id = f"{prefix}:{local_id}"
            district = districts.loc[districts.unit_id.eq(unit_id)].geometry.item()
            c = candidates.loc[candidates.unit_id.eq(unit_id)].copy()
            r = roads.iloc[roads.sindex.query(district.buffer(25), predicate="intersects")].copy()
            links = short_connector_links(r, c, max_link_m=20)
            components = linked_components(c, links, max_diameter_m=35)
            points = np.column_stack((c.geometry.x.to_numpy(), c.geometry.y.to_numpy()))
            near = cKDTree(points).query_pairs(10)
            id_values = c.id.to_numpy()
            near_keys = {tuple(sorted((id_values[i], id_values[j]))) for i, j in near}
            linked_keys = {(x["connector_a"], x["connector_b"]) for x in links}
            candidate_groups = [x for x in components if x["within_diameter_cap"]]
            summaries.append({
                "unit_id": unit_id,
                "raw_connector_candidates": len(c),
                "near_pairs_10m": len(near_keys),
                "near_pairs_with_short_source_link": len(near_keys & linked_keys),
                "short_source_links_20m": len(links),
                "linked_components": len(components),
                "components_within_35m_diameter": len(candidate_groups),
                "components_over_35m_diameter": len(components) - len(candidate_groups),
                "candidate_connectors_in_small_components": sum(x["count"] for x in candidate_groups),
                "max_component_size": max((x["count"] for x in components), default=0),
                "status": "diagnostic_only_not_accepted_M2",
            })
            for link in links:
                links_out.append({"unit_id": unit_id, **link,
                                  "within_10m": (link["connector_a"], link["connector_b"]) in near_keys})
            for component in components:
                groups.append({"unit_id": unit_id, **component})
            print(unit_id, "near", len(near_keys), "linked", len(links),
                  "groups", len(components), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summaries).to_csv(OUT / "pilot_summary.csv", index=False)
    pd.DataFrame(links_out).to_csv(OUT / "short_source_links.csv", index=False)
    (OUT / "linked_components.json").write_text(json.dumps(groups, indent=2) + "\n")


if __name__ == "__main__":
    main()

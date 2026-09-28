"""Flag source-road contexts that could invalidate short M2 connector links."""

from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2"


def grade_flagged(flags):
    return any(set(list(rule.get("values")) if rule.get("values") is not None else []) & {"is_bridge", "is_tunnel", "is_covered"}
               for rule in (list(flags) if flags is not None else []))


def main():
    links = pd.read_csv(OUT / "short_source_links.csv")
    links["city_prefix"] = links.unit_id.str.split(":").str[0]
    roads = []
    for city, prefix in (("Chicago", "CHI"), ("SP", "SP")):
        road = gpd.read_parquet(
            A / "work/prepared" / city /
            "overture_2026_08_19_review_v1/selected_roads.parquet"
        )
        subset = pd.DataFrame(road[["id", "subclass", "road_flags"]]).rename(
            columns={"id": "road_id"}
        )
        subset["city_prefix"] = prefix
        roads.append(subset)
    merged = links.merge(pd.concat(roads), on=["city_prefix", "road_id"],
                         how="left", validate="many_to_one", indicator=True)
    if not merged._merge.eq("both").all():
        raise ValueError("Link road absent from selected source roads")
    merged["grade_flagged_anywhere_on_segment"] = merged.road_flags.map(grade_flagged)
    merged["link_subclass"] = merged.subclass.eq("link")
    merged["possible_ramp_or_grade"] = (
        merged.grade_flagged_anywhere_on_segment | merged.link_subclass
    )
    summary = merged.groupby("unit_id").agg(
        short_source_links=("road_id", "size"),
        links_on_possible_ramp_or_grade=("possible_ramp_or_grade", "sum"),
        links_on_link_subclass=("link_subclass", "sum"),
        links_on_grade_flagged_segment=("grade_flagged_anywhere_on_segment", "sum"),
    ).reset_index()
    summary.to_csv(OUT / "road_context_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

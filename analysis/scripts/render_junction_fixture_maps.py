"""Render the two source-topology M2 examples at a common 180 m extent."""

from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/fixture_maps"
RUN = A / "work/runs/sp_chicago_harmonization_2026_09_22/roads"
FIXTURES = [
    ("Chicago", "CHI:32", "loop_close_4arm_pair", 448511.6, 4637139.0),
    ("SP", "SP:10", "bras_close_4arm_pair", 334496.2, 7395335.1),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for city, unit, name, x, y in FIXTURES:
        road = gpd.read_parquet(A / "work/prepared" / city / "overture_2026_08_19_review_v1/selected_roads.parquet")
        connectors = gpd.read_parquet(RUN / f"{city}_connector_candidates.parquet")
        enclosures = gpd.read_parquet(RUN / f"{city}_enclosure_candidates.parquet")
        extent = box(x - 90, y - 90, x + 90, y + 90)
        road = road.iloc[road.sindex.query(extent, predicate="intersects")]
        connectors = connectors.iloc[connectors.sindex.query(extent, predicate="intersects")]
        enclosures = enclosures.iloc[enclosures.sindex.query(extent, predicate="intersects")]
        figure, axis = plt.subplots(figsize=(8, 8))
        if len(enclosures):
            enclosures.plot(ax=axis, facecolor="#e2eef1", edgecolor="#92a7af", linewidth=.5)
        if len(road):
            road.plot(ax=axis, color="#334a5b", linewidth=1.2)
        if len(connectors):
            connectors.plot(ax=axis, color="#cc2737", markersize=35)
            for row in connectors.itertuples():
                axis.annotate(str(row.arms), (row.geometry.x, row.geometry.y), fontsize=7, color="#8e0714")
        axis.plot([x], [y], marker="x", color="#0065bb", markersize=12)
        axis.set_xlim(x - 90, x + 90)
        axis.set_ylim(y - 90, y + 90)
        axis.set_aspect("equal")
        axis.set_title(f"{unit} {name} — source lines / connector arm counts")
        figure.savefig(OUT / f"{name}.png", dpi=180, bbox_inches="tight")
        plt.close(figure)


if __name__ == "__main__":
    main()

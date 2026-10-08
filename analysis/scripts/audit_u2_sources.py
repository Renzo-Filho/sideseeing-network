"""U2 source audit: São Paulo RAIS 2022 district shares (area_first allocation) vs Metrô OD 2023 work trips attracted."""
import unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/u2_source_audit_2026_10_05"
norm = lambda s: unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper().strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    x = pd.read_excel(A / "data/shared/jobs_docs/od2023_atracao_viagens_motivo_destino.xlsx", header=None).iloc[7:, [0, 1, 2, 3]]
    x.columns = ["name", "industry", "commerce", "services"]
    x = x.dropna(subset=["industry"])
    x["od_work_trips"] = x[["industry", "commerce", "services"]].astype(float).sum(axis=1)
    x["key"] = x.name.map(norm)
    city = x.iloc[0].od_work_trips
    x = x.iloc[1:]
    r = pd.read_csv(A / "work/evidence/job_allocation_experiments/district_sensitivity.csv", dtype={"district_id": str})
    r["key"] = r.nm_distrito_municipal.map(norm)
    # A subprefeitura and a district can share a name; the district row follows the subprefeitura row.
    x["n"] = x.groupby("key").cumcount()
    od = x[(x.key.map(x.key.value_counts()) == 1) | (x.n == 1)]
    od = od[od.key.isin(r.key)].set_index("key")[["od_work_trips"]]
    assert len(od) == 96 and abs(od.od_work_trips.sum() / city - 1) < 1e-9
    m = r.set_index("key")[["district_id", "nm_distrito_municipal", "area_first", "scenario_min", "scenario_max"]].join(od)
    m["rais_share"] = m.area_first / m.area_first.sum()
    m["od_share"] = m.od_work_trips / m.od_work_trips.sum()
    m["rais_over_od"] = m.rais_share / m.od_share
    m.reset_index(drop=True).assign(unit_id=lambda d: "SP:" + d.district_id).to_csv(OUT / "sp_rais_vs_od_work_trips.csv", index=False)
    print("OD 2023 work trips attracted to the municipality:", round(city))
    print("Spearman RAIS area_first vs OD work trips:", round(m.area_first.corr(m.od_work_trips, method="spearman"), 3))
    print("rais_over_od quantiles:", m.rais_over_od.quantile([.1, .25, .5, .75, .9]).round(2).to_dict())
    print("districts beyond 2x either way:", int(((m.rais_over_od > 2) | (m.rais_over_od < .5)).sum()))
    print(m.sort_values("rais_over_od")[["nm_distrito_municipal", "rais_over_od"]].round(2).to_string())


if __name__ == "__main__":
    main()

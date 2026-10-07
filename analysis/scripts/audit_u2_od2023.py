"""U2 source audit: Metrô OD 2023 jobs by workplace zone (microdata) vs RAIS 2022 by district, São Paulo."""
import re, subprocess
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
B = A / "data/SP/od2023_metro/Site_190225"
OUT = A / "results/SP_CHI/u2_source_audit_2026_10_05"
# VINC codes (layout): 1 employee with signed card, 3 public servant -> the universe RAIS registers.
RAIS_LIKE = {1, 3}
INFORMAL = {2, 6, 8, 9}          # employee without card, self-employed without CNPJ, family business owner, family worker
OTHER = {4, 5, 7}                # liberal professional, self-employed with CNPJ, employer: outside RAIS, not informal


def city_series():
    """Prefeitura district RAIS series 2011-2024; values placed by column position (blank cells exist)."""
    txt = subprocess.run(["pdftotext", "-layout", str(A / "data/shared/jobs_docs/msp_empregos_distrito_2011_2024.pdf"), "-"],
                         capture_output=True, text=True, check=True).stdout.split("\n")
    hdr = next(l for l in txt if "Unidades Territoriais" in l)
    cols = [(m.end(), int(m.group())) for m in re.finditer(r"20\d\d", hdr)]
    rows = {}
    for l in txt:
        m = re.match(r"^\s*(\D+?)\s{2,}(\d.*)$", l)
        if not m:
            continue
        nums = [(n.end(), int(n.group())) for n in re.finditer(r"\d+", l)]
        # Right-aligned numbers: assign each to the year whose header end is nearest, scaled to the line's own layout.
        scale = max(e for e, _ in nums) / cols[-1][0] if len(nums) < len(cols) else None
        vals = {}
        for k, (e, v) in enumerate(nums):
            year = cols[k][1] if scale is None else min(cols, key=lambda c: abs(c[0] * scale - e))[1]
            vals[year] = v
        rows[m.group(1).strip()] = vals
    return pd.DataFrame(rows).T


def main():
    zones = gpd.read_file(B / "002_Site Metro Mapas_190225/Shape/Zonas_2023.shp")
    sp_zone = zones.loc[zones.NumeroMuni == 36].set_index("NumeroZona").NumDistrit
    p = pyogrio.read_dataframe(B / "Banco2023_divulgacao_190225.dbf", read_geometry=False,
                               columns=["F_PESS", "FE_PESS", "ZONATRA1", "TRAB1_RE", "VINC1", "ZONATRA2", "TRAB2_RE", "VINC2"])
    p = p[p.F_PESS == 1]
    jobs = pd.concat([p[["FE_PESS", f"ZONATRA{k}", f"TRAB{k}_RE", f"VINC{k}"]].set_axis(["w", "zone", "where", "vinc"], axis=1).assign(job=k)
                      for k in (1, 2)], ignore_index=True)
    jobs = jobs[jobs.zone.isin(sp_zone.index)]
    jobs["od_district"] = jobs.zone.map(sp_zone)
    # Table 14 reproduction: 'where' 2 = fixed address outside home, 1 = at home, 3 = no fixed address.
    t14 = pd.read_excel(B / "Tabelas_Site_OD2023_REV_190225.xlsx", sheet_name="Tab14", header=None).iloc[9:, :5]
    t14.columns = ["zone", "fixed_out", "home", "no_fixed", "total"]
    t14 = t14[pd.to_numeric(t14.zone, errors="coerce").notna()].astype(float)
    t14 = t14[t14.zone.astype(int).isin(sp_zone.index)]
    micro = jobs.groupby("where").w.sum()
    print("Table 14 vs microdata, SP municipality:",
          {"fixed_out": (round(t14.fixed_out.sum()), round(micro.get(2, 0))), "home": (round(t14.home.sum()), round(micro.get(1, 0))),
           "no_fixed": (round(t14.no_fixed.sum()), round(micro.get(3, 0)))})
    fixed = jobs[jobs["where"] == 2].copy()
    fixed["universe"] = np.select([fixed.vinc.isin(RAIS_LIKE), fixed.vinc.isin(INFORMAL), fixed.vinc.isin(OTHER)], ["rais_like", "informal", "other"], "unknown")
    share = fixed.groupby("universe").w.sum() / fixed.w.sum()
    print("Fixed-workplace jobs in SP by universe (weighted share):", share.round(4).to_dict())
    allj = jobs.assign(universe=np.select([jobs.vinc.isin(RAIS_LIKE), jobs.vinc.isin(INFORMAL), jobs.vinc.isin(OTHER)], ["rais_like", "informal", "other"], "unknown"))
    print("All OD jobs in SP (any location) by universe:", (allj.groupby("universe").w.sum() / allj.w.sum()).round(4).to_dict(),
          "| RAIS-like total:", round(allj.loc[allj.universe == "rais_like", "w"].sum()))

    # District table. OD district numbers are Metrô's; join to project districts by name.
    names = zones.drop_duplicates("NumDistrit").set_index("NumDistrit").NomeDistri
    d = fixed.groupby(["od_district", "universe"]).w.sum().unstack(fill_value=0)
    d["fixed_all"] = d.sum(axis=1)
    d["sample_first_job_fixed"] = fixed[fixed.job == 1].groupby("od_district").size()
    d["sample_rais_like"] = fixed[fixed.universe == "rais_like"].groupby("od_district").size()
    d = d.fillna(0)
    d["informal_share"] = d.informal / d.fixed_all
    d["name"] = names.reindex(d.index)
    import unicodedata
    norm = lambda s: unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper().strip()
    r = pd.read_csv(A / "work/evidence/job_allocation_experiments/district_sensitivity.csv", dtype={"district_id": str})
    r["key"] = r.nm_distrito_municipal.map(norm)
    d["key"] = d.name.map(norm)
    m = d.merge(r[["key", "district_id", "area_first"]], on="key", how="left", validate="one_to_one")
    assert m.district_id.notna().all() and len(m) == 96, m.loc[m.district_id.isna(), "name"].tolist()
    m["unit_id"] = "SP:" + m.district_id
    for c in ("area_first", "rais_like", "fixed_all"):
        m[c + "_share"] = m[c] / m[c].sum()
    m["rais_over_od_rais_like"] = m.area_first_share / m.rais_like_share
    m["rais_over_od_all_fixed"] = m.area_first_share / m.fixed_all_share
    cs = city_series()
    cs.index = cs.index.map(norm)
    assert cs.loc["INVALIDOS", 2022] == 10381 and cs.loc["NAO LOCALIZADOS", 2022] == 36021 and cs.loc["BRAS", 2022] == 420022
    for y in (2022, 2023, 2024):
        m[f"city_rais_{y}"] = m.key.map(cs[y])
    assert m.city_rais_2022.notna().all()
    print("City series 2022 invalid + not located:", int(cs.loc["INVALIDOS", 2022] + cs.loc["NAO LOCALIZADOS", 2022]))
    for y in (2022, 2023):
        print(f"Spearman city RAIS {y} vs OD RAIS-like:", round(m[f"city_rais_{y}"].corr(m.rais_like, method="spearman"), 3),
              f"| vs project CEP RAIS 2022:", round(m[f"city_rais_{y}"].corr(m.area_first, method="spearman"), 3))
    print(m.loc[m.key.isin(["BRAS", "SE", "PARI", "JAGUARE"]), ["name", "area_first", "city_rais_2022", "city_rais_2023", "city_rais_2024", "rais_like", "fixed_all", "sample_rais_like"]].round(0).to_string(index=False))
    m.to_csv(OUT / "sp_od2023_fixed_jobs_by_district.csv", index=False)
    print("First-job fixed-workplace sample per district: min", int(m.sample_first_job_fixed.min()), "median", int(m.sample_first_job_fixed.median()),
          "max", int(m.sample_first_job_fixed.max()), "| districts under 50:", int((m.sample_first_job_fixed < 50).sum()))
    print("RAIS-like sample per district: min", int(m.sample_rais_like.min()), "median", int(m.sample_rais_like.median()),
          "| districts under 50:", int((m.sample_rais_like < 50).sum()))
    print("Spearman RAIS area_first vs OD RAIS-like:", round(m.area_first.corr(m.rais_like, method="spearman"), 3),
          "| vs OD all fixed:", round(m.area_first.corr(m.fixed_all, method="spearman"), 3))
    print("Spearman district informal share vs RAIS/OD-all ratio:", round(m.informal_share.corr(m.rais_over_od_all_fixed, method="spearman"), 3))
    cols = ["name", "area_first", "rais_like", "fixed_all", "informal_share", "rais_over_od_rais_like", "rais_over_od_all_fixed", "sample_rais_like"]
    pd.set_option("display.width", 250)
    print(m.sort_values("rais_over_od_rais_like", ascending=False)[cols].head(8).round(2).to_string(index=False))
    print(m.sort_values("rais_over_od_rais_like")[cols].head(8).round(2).to_string(index=False))


if __name__ == "__main__":
    main()

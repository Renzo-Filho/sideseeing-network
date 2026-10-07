"""Post-hoc diagnostic for S7-5 (São Paulo): CNEFE 2022 addresses collapsed to one point per building (street + number + block),
share of buildings with at least one establishment, vs IPTU commerce share of occupied land."""
import pandas as pd
import evaluate_b1_step4 as b1

A = b1.A
OUT = A / "results/SP_CHI/u1_step7_2026_10_06"


def main():
    cols = ["COD_DISTRITO", "COD_SETOR", "NUM_QUADRA", "NOM_TIPO_SEGLOGR", "NOM_TITULO_SEGLOGR", "NOM_SEGLOGR", "NUM_ENDERECO", "COD_ESPECIE"]
    cn = pd.read_csv(b1.D / "SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv", sep=";", usecols=cols, dtype=str).fillna("")
    xw = pd.read_csv(A / "results/SP_CHI/simple_index_source_audit_2026_10_01/tables/cnefe_district_crosswalk.csv", dtype=str)
    cn["unit_id"] = cn.COD_DISTRITO.map(dict(zip(xw.cod, xw.modal_unit_id)))
    cn["building"] = cn[["COD_SETOR", "NUM_QUADRA", "NOM_TIPO_SEGLOGR", "NOM_TITULO_SEGLOGR", "NOM_SEGLOGR", "NUM_ENDERECO"]].agg("|".join, axis=1)
    cn["est"] = cn.COD_ESPECIE.isin(["4", "5", "6", "8"])
    b = cn.groupby(["unit_id", "building"]).est.any().reset_index()
    ref = b.groupby("unit_id").est.mean().rename("ref_establishment_building_share")
    t = pd.read_csv(OUT / "u1_by_unit.csv").set_index("unit_id")
    s = t[t.city == "SP"].join(ref)
    print(f"addresses {len(cn):,}; buildings {len(b):,}")
    for col in ("ref_establishment_address_share", "ref_establishment_building_share"):
        print(f"IPTU commerce share vs {col}: Spearman {s.p_commerce.corr(s[col], method='spearman'):.3f}")
    s[["p_commerce", "ref_establishment_address_share", "ref_establishment_building_share"]].to_csv(OUT / "sp_reference_diagnostic.csv")


if __name__ == "__main__":
    main()

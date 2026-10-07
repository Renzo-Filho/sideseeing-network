"""Download 2022 RAIS establishment microdata for the municipality of São Paulo from Base dos Dados, one row per establishment,
all columns (needs GOOGLE_CLOUD_PROJECT). Reference for the U6 D7b-3 test (MODEL_PLAN Step 7b, RT-1)."""
import os
import basedosdados as bd

OUT = "analysis/data/SP/rais_2022_estab/rais_estab_sp_2022.parquet"
query = """
    SELECT *
    FROM `basedosdados.br_me_rais.microdados_estabelecimentos`
    WHERE ano = 2022 AND sigla_uf = 'SP' AND id_municipio = '3550308'
"""
df = bd.read_sql(query, billing_project_id=os.environ["GOOGLE_CLOUD_PROJECT"])
df.to_parquet(OUT, index=False)
print(f"Saved {len(df)} establishments to {OUT}; columns: {list(df.columns)}")

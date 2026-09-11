import os
import basedosdados as bd

# Authenticate locally; supply your own billing project without storing credentials.
PROJECT_ID = os.environ['GOOGLE_CLOUD_PROJECT']

print("Querying RAIS 2022 data for São Paulo...")

# This query gets all establishments in SP, their CEP (for spatial mapping),
# and the number of active jobs (quantidade_vinculos_ativos).
query = """
    SELECT
        cep,
        quantidade_vinculos_ativos AS empregos
    FROM `basedosdados.br_me_rais.microdados_estabelecimentos`
    WHERE ano = 2022
      AND id_municipio = '3550308' -- Código IBGE de São Paulo
      AND quantidade_vinculos_ativos > 0
"""

# Download the data directly to a Pandas DataFrame
df = bd.read_sql(query, billing_project_id=PROJECT_ID)

# Aggregate jobs by CEP so the file isn't unnecessarily huge
df_grouped = df.groupby(['cep'])['empregos'].sum().reset_index()

# Save it to the Socioeconomico folder
output_path = 'analysis/data/SP/Socioeconomico/rais_empregos_sp_2022.csv'
df_grouped.to_csv(output_path, index=False)

print(f"Success! Saved {len(df_grouped)} CEP records to {output_path}")

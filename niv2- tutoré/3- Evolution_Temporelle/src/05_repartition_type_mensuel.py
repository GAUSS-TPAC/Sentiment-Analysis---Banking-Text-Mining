"""
Repartition mensuelle par type de reclamation, sur la periode operationnelle.

Objectif : verifier si la tendance et les pics observes (scripts 02 et 03,
tous deux domines par le type "SARA") sont un phenomene general ou concentres
sur un type de reclamation particulier.

Sorties :
- resultats/tables/05_repartition_type_mensuel.csv
- resultats/figures/05_repartition_type_mensuel.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from utils_temporel import load_data, sauvegarder_table, chemin_figure

DEBUT_PERIODE_OPERATIONNELLE = "2025-11-01"
TOP_N_TYPES = 4

df = load_data()
df_operationnel = df[df["created_at"] >= DEBUT_PERIODE_OPERATIONNELLE].copy()

top_types = df_operationnel["ticket_type_name"].value_counts().head(TOP_N_TYPES).index.tolist()
df_operationnel["type_regroupe"] = df_operationnel["ticket_type_name"].where(
    df_operationnel["ticket_type_name"].isin(top_types), "AUTRES"
)

table = (
    df_operationnel.groupby([df_operationnel["created_at"].dt.to_period("M"), "type_regroupe"])
    .size()
    .unstack(fill_value=0)
)
ordre_colonnes = top_types + ["AUTRES"]
table = table[ordre_colonnes]

chemin_table = sauvegarder_table(table.reset_index().assign(created_at=lambda d: d["created_at"].astype(str)), "05_repartition_type_mensuel.csv")

print(f"Top {TOP_N_TYPES} types sur la periode operationnelle : {top_types}")
print()
print(table.to_string())
print()
print(f"Table enregistree dans : {chemin_table}")

fig, ax = plt.subplots(figsize=(12, 5))
ax.stackplot(table.index.astype(str), [table[c] for c in table.columns], labels=table.columns)
ax.set_title("Repartition mensuelle des reclamations par type — periode operationnelle")
ax.set_xlabel("Mois")
ax.set_ylabel("Nombre de reclamations")
ax.tick_params(axis="x", rotation=90)
ax.legend(loc="upper left")
fig.tight_layout()
chemin_fig = chemin_figure("05_repartition_type_mensuel.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

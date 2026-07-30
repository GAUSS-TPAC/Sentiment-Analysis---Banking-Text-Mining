"""
Zoom sur les 3 familles d'anomalies du champ Montant en XAF, pour aider a
choisir entre les 3 hypotheses (erreur de saisie / montant en centimes /
fraude a montant reellement eleve) :

1. Valeurs negatives (20) : par type de reclamation -> tres concentrees sur
   un seul type, ce qui plaide pour un usage volontaire ("montant a
   regulariser / rembourser") plutot qu'une erreur aleatoire.
2. Valeurs a zero (178) : par type de reclamation.
3. Valeurs extremes (>10M) : leur distribution precise -- un cluster de 44
   valeurs toutes comprises entre 690M et 700M XAF, un seul cas isole a
   50 milliards. Un cluster aussi resserre juste sous 700M (au lieu d'etre
   eparpille) ressemble plus a un artefact technique (plafond/generateur)
   qu'a 44 fraudes reelles de montant quasi identique.

Sorties :
- resultats/tables/03_anomalies_extremes.csv
- resultats/figures/03_anomalies_par_categorie.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from utils_montant import load_data, sauvegarder_table, chemin_figure

df = load_data()

negatifs = df[df["montant"] < 0]
zeros = df[df["montant"] == 0]
extremes = df[df["montant"] > 10_000_000].sort_values("montant", ascending=False)

chemin_table = sauvegarder_table(
    extremes[["created_at", "ticket_type_name", "montant", "ticket_attributes_Agence"]],
    "03_anomalies_extremes.csv",
)
print(f"Negatifs : {len(negatifs)}  |  Zeros : {len(zeros)}  |  Extremes (>10M) : {len(extremes)}")
cluster = extremes[(extremes["montant"] >= 690_000_000) & (extremes["montant"] < 700_000_000)]
print(f"  dont cluster resserre 690M-700M : {len(cluster)} valeurs")
print(f"  dont valeur isolee a 50 milliards : {(extremes['montant'] >= 1_000_000_000).sum()}")
print(f"Table detaillee enregistree dans : {chemin_table}")

fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

negatifs["ticket_type_name"].value_counts().plot(kind="bar", ax=axes[0], color="#c0392b")
axes[0].set_title(f"Valeurs NEGATIVES par type (n={len(negatifs)})")
axes[0].set_ylabel("Nombre de tickets")
axes[0].tick_params(axis="x", rotation=30)

zeros["ticket_type_name"].value_counts().plot(kind="bar", ax=axes[1], color="#e0a800")
axes[1].set_title(f"Valeurs a ZERO par type (n={len(zeros)})")
axes[1].tick_params(axis="x", rotation=30)

extremes_hors_cas_isole = extremes[extremes["montant"] < 1_000_000_000]
axes[2].hist(extremes_hors_cas_isole["montant"] / 1_000_000, bins=40, color="#1f5c8b", edgecolor="white")
axes[2].set_title(f"Valeurs EXTREMES > 10M XAF (n={len(extremes)})\ncluster resserre = 44 valeurs entre 690M et 700M")
axes[2].set_xlabel("Montant (millions XAF)\n(1 valeur isolee a 50 000M exclue du graphique pour la lisibilite)")
axes[2].set_ylabel("Nombre de tickets")

fig.suptitle("Montant en XAF : les 3 familles d'anomalies, par categorie -- a trancher avec le metier", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.93])
chemin_fig = chemin_figure("03_anomalies_par_categorie.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

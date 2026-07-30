"""
Distribution du champ Montant en XAF, malgre les anomalies deja identifiees
dans la statistique descriptive (valeurs negatives, zeros, valeurs extremes).
L'objectif ici n'est pas de "nettoyer" le champ mais de VISUALISER sa forme
pour eclairer les 3 hypotheses a trancher avec le metier (erreur de saisie,
montant en centimes, fraude a montant reellement eleve).

Sorties :
- resultats/tables/01_distribution_montant.csv (statistiques par tranche)
- resultats/figures/01_distribution_montant.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils_montant import load_data, sauvegarder_table, chemin_figure

df = load_data()
montant = df["montant"].dropna()

nb_negatifs = (montant < 0).sum()
nb_zeros = (montant == 0).sum()
positifs = montant[montant > 0]

print(f"Montant renseigne sur {len(montant)} tickets ({100*len(montant)/len(df):.1f}% du dataset)")
print(f"  dont negatifs : {nb_negatifs}  |  zeros : {nb_zeros}  |  strictement positifs : {len(positifs)}")
print()

# Statistiques par tranche de montant (positifs uniquement, echelle log)
tranches = [0, 1_000, 10_000, 50_000, 100_000, 500_000, 1_000_000, 10_000_000, 100_000_000, np.inf]
labels = ["<1k", "1k-10k", "10k-50k", "50k-100k", "100k-500k", "500k-1M", "1M-10M", "10M-100M", ">100M"]
repartition = pd.cut(positifs, bins=tranches, labels=labels).value_counts().sort_index()
table = repartition.rename("nb_tickets").reset_index().rename(columns={"index": "tranche_xaf"})
chemin_table = sauvegarder_table(table, "01_distribution_montant.csv")
print(table.to_string(index=False))
print(f"\nTable enregistree dans : {chemin_table}")

top_types = df["ticket_type_name"].value_counts().head(6).index.tolist()
donnees_boxplot = [df.loc[(df["ticket_type_name"] == t) & (df["montant"] > 0), "montant"] for t in top_types]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

ax1.hist(np.log10(positifs), bins=40, color="#1f5c8b", edgecolor="white")
ax1.set_title(f"Distribution des montants > 0 (echelle log10)\n({nb_negatifs} negatifs + {nb_zeros} zeros non representes ici)")
ax1.set_xlabel("log10(Montant en XAF)")
ax1.set_ylabel("Nombre de tickets")
ticks = [3, 4, 5, 6, 7, 8, 9, 10]
ax1.set_xticks(ticks)
ax1.set_xticklabels([f"{10**t:,.0f}" for t in ticks], rotation=30)

ax2.boxplot(donnees_boxplot, tick_labels=top_types, showfliers=True)
ax2.set_yscale("log")
ax2.set_title("Montant (> 0) par type de reclamation (echelle log)")
ax2.set_ylabel("Montant en XAF (log)")
ax2.tick_params(axis="x", rotation=30)

fig.tight_layout()
chemin_fig = chemin_figure("01_distribution_montant.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

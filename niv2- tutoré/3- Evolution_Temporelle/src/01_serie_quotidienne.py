"""
Volume quotidien de reclamations, base sur created_at.

- reconstruit une serie continue (un jour sans ticket compte pour 0, pas pour
  une absence de donnee) sur toute la periode couverte par le dataset
- calcule une moyenne mobile sur 7 jours pour lisser l'effet week-end
- exporte la table et un graphique

Sorties :
- resultats/tables/01_serie_quotidienne.csv
- resultats/figures/01_volume_quotidien.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from utils_temporel import load_data, sauvegarder_table, chemin_figure

df = load_data()

comptes_par_jour = df.groupby(df["created_at"].dt.date).size()
comptes_par_jour.index = pd.to_datetime(comptes_par_jour.index)

# Serie continue : un index journalier complet du premier au dernier jour, 0 si aucun ticket ce jour-la
index_complet = pd.date_range(comptes_par_jour.index.min(), comptes_par_jour.index.max(), freq="D")
serie = comptes_par_jour.reindex(index_complet, fill_value=0)
serie.index.name = "date"
serie.name = "nb_reclamations"

moyenne_mobile_7j = serie.rolling(window=7, center=True).mean()

table = pd.DataFrame({"nb_reclamations": serie, "moyenne_mobile_7j": moyenne_mobile_7j.round(1)})
chemin_table = sauvegarder_table(table.reset_index().rename(columns={"index": "date"}), "01_serie_quotidienne.csv")

print(f"Periode couverte : {serie.index.min().date()} -> {serie.index.max().date()} ({len(serie)} jours)")
print(f"Total reclamations : {serie.sum()}")
print(f"Moyenne par jour : {serie.mean():.1f}  (ecart-type : {serie.std():.1f})")
print(f"Jour avec le plus de reclamations : {serie.idxmax().date()} ({serie.max()} reclamations)")
print(f"Nb de jours a 0 reclamation : {(serie == 0).sum()}")
print(f"Table enregistree dans : {chemin_table}")

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(serie.index, serie.values, color="#9fb4c7", linewidth=0.8, label="Volume quotidien")
ax.plot(moyenne_mobile_7j.index, moyenne_mobile_7j.values, color="#1f5c8b", linewidth=2, label="Moyenne mobile 7 jours")
ax.set_title("Volume quotidien de reclamations")
ax.set_xlabel("Date")
ax.set_ylabel("Nombre de reclamations")
ax.legend()
fig.tight_layout()
chemin_fig = chemin_figure("01_volume_quotidien.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

"""
Detection des pics (jours anormalement charges) dans la periode operationnelle.

Methode : bornes IQR (Q1 - 1.5*IQR, Q3 + 1.5*IQR) calculees sur les comptages
quotidiens de la periode operationnelle uniquement (>= 2025-11-01, cf. script
02 qui a determine ce debut de periode). Melanger avec la phase pilote
fausserait les bornes (ecart-type tire vers le bas par des mois a ~0 ticket).

Pour chaque pic detecte, on regarde la repartition par type de reclamation ce
jour-la, pour formuler une hypothese de cause (incident technique, etc.) a
verifier avec le metier.

Sorties :
- resultats/tables/03_pics_anomalies.csv
- resultats/figures/03_pics_quotidiens.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from utils_temporel import load_data, sauvegarder_table, chemin_figure

DEBUT_PERIODE_OPERATIONNELLE = "2025-11-01"

df = load_data()
df_operationnel = df[df["created_at"] >= DEBUT_PERIODE_OPERATIONNELLE].copy()

comptes_par_jour = df_operationnel.groupby(df_operationnel["created_at"].dt.date).size()
comptes_par_jour.index = pd.to_datetime(comptes_par_jour.index)
index_complet = pd.date_range(comptes_par_jour.index.min(), comptes_par_jour.index.max(), freq="D")
serie = comptes_par_jour.reindex(index_complet, fill_value=0)

q1, q3 = serie.quantile([0.25, 0.75])
iqr = q3 - q1
borne_haute = q3 + 1.5 * iqr

pics = serie[serie > borne_haute].sort_values(ascending=False)
print(f"Borne haute IQR (periode operationnelle) : {borne_haute:.0f} reclamations/jour")
print(f"{len(pics)} jours au-dela de cette borne sur {len(serie)} jours ({100*len(pics)/len(serie):.1f}%)")
print()

lignes = []
for date_pic, effectif in pics.items():
    jour = df_operationnel[df_operationnel["created_at"].dt.date == date_pic.date()]
    top_type = jour["ticket_type_name"].value_counts().idxmax()
    part_top_type = jour["ticket_type_name"].value_counts(normalize=True).max()
    lignes.append(
        {
            "date": date_pic.date(),
            "nb_reclamations": int(effectif),
            "type_dominant": top_type,
            "pct_type_dominant": round(100 * part_top_type, 1),
        }
    )

table_pics = pd.DataFrame(lignes)
chemin_table = sauvegarder_table(table_pics, "03_pics_anomalies.csv")
print(table_pics.to_string(index=False))
print()
print(f"Table enregistree dans : {chemin_table}")

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(serie.index, serie.values, color="#1f5c8b", linewidth=1)
ax.scatter(pics.index, pics.values, color="#c0392b", zorder=5, label=f"Pics (> {borne_haute:.0f}/jour, methode IQR)")
ax.axhline(borne_haute, color="#c0392b", linestyle="--", linewidth=1)
ax.set_title("Pics de reclamations quotidiennes — periode operationnelle")
ax.set_xlabel("Date")
ax.set_ylabel("Nombre de reclamations")
ax.legend()
fig.tight_layout()
chemin_fig = chemin_figure("03_pics_quotidiens.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

"""
Agregation mensuelle des reclamations + tendance.

Deux points d'attention traites explicitement ici (visibles des le premier
coup d'oeil sur les comptes mensuels bruts) :

1. Le systeme n'a un volume significatif de reclamations qu'a partir d'un
   certain mois ("periode operationnelle") : les mois anterieurs ont un
   volume marginal (1 a 23 tickets/mois), probablement une phase pilote ou
   des tickets de test. Melanger cette phase avec la periode operationnelle
   fausserait completement la lecture de la tendance ("explosion" artificielle).
2. Le dernier mois de la periode est partiel (extraction faite le
   20/07/2026) : le comparer tel quel a un mois complet donnerait l'illusion
   d'une baisse. On calcule donc aussi un taux "par jour" pour comparer des
   mois de longueurs differentes.

Sorties :
- resultats/tables/02_serie_mensuelle.csv
- resultats/figures/02_volume_mensuel.png
"""

import calendar

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils_temporel import load_data, sauvegarder_table, chemin_figure

SEUIL_DEBUT_PERIODE_OPERATIONNELLE = 100  # nb de tickets/mois au-dela duquel on considere l'activite "reelle"

df = load_data()
date_max_globale = df["created_at"].max()

comptes = df.groupby(df["created_at"].dt.to_period("M")).size().rename("nb_reclamations")
table = comptes.to_frame()
table.index.name = "mois"

# Jours reellement couverts par le mois (le dernier mois de la serie peut etre partiel)
def jours_couverts(periode) -> int:
    debut = periode.start_time
    fin_calendaire = periode.end_time
    fin_reelle = min(fin_calendaire, date_max_globale)
    return (fin_reelle.normalize() - debut.normalize()).days + 1

table["jours_couverts"] = [jours_couverts(p) for p in table.index]
table["jours_dans_le_mois"] = [calendar.monthrange(p.year, p.month)[1] for p in table.index]
table["mois_complet"] = table["jours_couverts"] == table["jours_dans_le_mois"]
table["moyenne_par_jour"] = (table["nb_reclamations"] / table["jours_couverts"]).round(1)
table["variation_pct_vs_mois_precedent"] = table["nb_reclamations"].pct_change().mul(100).round(1)
table["periode"] = np.where(table["nb_reclamations"] >= SEUIL_DEBUT_PERIODE_OPERATIONNELLE, "operationnelle", "avant_lancement")

chemin_table = sauvegarder_table(table.reset_index().assign(mois=lambda d: d["mois"].astype(str)), "02_serie_mensuelle.csv")

debut_operationnel = table[table["periode"] == "operationnelle"].index.min()
print(f"Debut de la periode operationnelle detectee : {debut_operationnel} (seuil : {SEUIL_DEBUT_PERIODE_OPERATIONNELLE} tickets/mois)")
print(f"Volume avant cette date : {table.loc[table['periode'] == 'avant_lancement', 'nb_reclamations'].sum()} tickets sur "
      f"{(table['periode'] == 'avant_lancement').sum()} mois (marginal, probable phase pilote / tickets de test)")
print()

# Tendance : regression lineaire sur les mois COMPLETS de la periode operationnelle uniquement
periode_op = table[(table["periode"] == "operationnelle") & (table["mois_complet"])].copy()
x = np.arange(len(periode_op))
pente, ordonnee = np.polyfit(x, periode_op["nb_reclamations"], 1)
previsions = pente * x + ordonnee
r2 = 1 - np.sum((periode_op["nb_reclamations"] - previsions) ** 2) / np.sum((periode_op["nb_reclamations"] - periode_op["nb_reclamations"].mean()) ** 2)

tendance = "hausse" if pente > 0 else "baisse"
print(f"Tendance sur les {len(periode_op)} mois complets de la periode operationnelle ({periode_op.index.min()} -> {periode_op.index.max()}) :")
print(f"  pente = {pente:+.0f} reclamations/mois ({tendance}), R2 = {r2:.2f}")
print()
print(table.to_string())
print()
print(f"Table enregistree dans : {chemin_table}")

fig, ax = plt.subplots(figsize=(12, 5))
couleurs = ["#c9c9c9" if p == "avant_lancement" else ("#f0a35c" if not c else "#1f5c8b") for p, c in zip(table["periode"], table["mois_complet"])]
ax.bar(table.index.astype(str), table["nb_reclamations"], color=couleurs)
ax.plot(periode_op.index.astype(str), previsions, color="#8b1f2f", linewidth=2, linestyle="--", label="Tendance (regression lineaire)")
ax.set_title("Volume mensuel de reclamations (gris = phase pilote, orange = mois partiel)")
ax.set_xlabel("Mois")
ax.set_ylabel("Nombre de reclamations")
ax.tick_params(axis="x", rotation=90)
ax.legend()
fig.tight_layout()
chemin_fig = chemin_figure("02_volume_mensuel.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

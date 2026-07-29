"""
Delai de traitement des reclamations : created_at -> updated_at.

Restreint aux tickets dont ticket_state_category == 'resolved' : pour les
tickets encore 'submitted', updated_at ne represente pas une resolution mais
la derniere modification (souvent proche de created_at), ce qui biaiserait le
delai vers le bas si on les incluait tous.

Sorties :
- resultats/tables/04_delai_traitement_mensuel.csv
- resultats/figures/04_delai_traitement.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from utils_temporel import load_data, sauvegarder_table, chemin_figure

df = load_data()
resolus = df[df["ticket_state_category"] == "resolved"].copy()
resolus["delai_heures"] = (resolus["updated_at"] - resolus["created_at"]).dt.total_seconds() / 3600

print(f"Tickets resolus : {len(resolus)} sur {len(df)} ({100*len(resolus)/len(df):.1f}%)")
print(f"Delai moyen : {resolus['delai_heures'].mean():.1f} h  |  median : {resolus['delai_heures'].median():.1f} h")
print(f"Delai min/max : {resolus['delai_heures'].min():.1f} h / {resolus['delai_heures'].max():.1f} h")
print()

par_mois = resolus.groupby(resolus["created_at"].dt.to_period("M"))["delai_heures"].agg(
    nb_tickets_resolus="count", delai_moyen_h="mean", delai_median_h="median"
).round(1)
par_mois = par_mois[par_mois["nb_tickets_resolus"] >= 5]  # mois avec trop peu de tickets resolus = non significatif

chemin_table = sauvegarder_table(par_mois.reset_index().assign(created_at=lambda d: d["created_at"].astype(str)), "04_delai_traitement_mensuel.csv")
print(par_mois.to_string())
print()
print(f"Table enregistree dans : {chemin_table}")

# Le mois pilote (2024-05, 13 tickets) a un delai ~30x plus grand que les autres :
# on l'exclut du graphique pour garder une echelle lisible sur la periode operationnelle.
par_mois_graphique = par_mois[par_mois.index >= pd.Period("2025-11", freq="M")]

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(par_mois_graphique.index.astype(str), par_mois_graphique["delai_median_h"], marker="o", color="#1f5c8b", label="Delai median (h)")
ax.plot(par_mois_graphique.index.astype(str), par_mois_graphique["delai_moyen_h"], marker="o", color="#c0392b", linestyle="--", label="Delai moyen (h)")
ax.set_title("Delai de traitement des reclamations resolues, par mois de creation")
ax.set_xlabel("Mois de creation du ticket")
ax.set_ylabel("Delai (heures)")
ax.tick_params(axis="x", rotation=90)
ax.legend()
fig.tight_layout()
chemin_fig = chemin_figure("04_delai_traitement.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

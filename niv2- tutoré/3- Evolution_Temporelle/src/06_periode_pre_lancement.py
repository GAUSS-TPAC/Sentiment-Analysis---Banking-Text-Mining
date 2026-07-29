"""
Zoom sur la periode "quasi nulle" (fevrier 2024 -> octobre 2025).

Objectif : visualiser POURQUOI le volume y est negligeable, en distinguant
2 groupes parmi les 38 tickets de cette periode :
- "cluster_config_test" : 25 tickets crees entre le 18/04/2024 et le
  29/05/2024, avec des types generiques Intercom (Support Request, Internal
  task, Bug report, Feature request, Card issue) et des categories
  Tracker/Back-office -> tickets de configuration/test du workspace, pas de
  vraies reclamations clients.
- "organique_isole" : 13 tickets isoles (1 tous les 1-2 mois) arrivant par
  Facebook/Messenger/email/iOS/Android, avant le lancement du canal principal.

On y ajoute une comparaison de la repartition par canal avant/après le debut
de la periode operationnelle (01/11/2025) : le canal android (dominant a
65,7% ensuite) et whatsapp (12,7% ensuite, absent avant) confirment qu'un
nouveau canal a ete deploye a cette date.

Sorties :
- resultats/tables/06_tickets_avant_lancement.csv
- resultats/figures/06_periode_pre_lancement.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from utils_temporel import load_data, sauvegarder_table, chemin_figure

DEBUT_PERIODE_OPERATIONNELLE = pd.Timestamp("2025-11-01")
DEBUT_CLUSTER_CONFIG = pd.Timestamp("2024-04-18")
FIN_CLUSTER_CONFIG = pd.Timestamp("2024-05-29 23:59:59")

df = load_data()
avant = df[df["created_at"] < DEBUT_PERIODE_OPERATIONNELLE].copy()

avant["groupe"] = "organique_isole"
masque_cluster = avant["created_at"].between(DEBUT_CLUSTER_CONFIG, FIN_CLUSTER_CONFIG)
avant.loc[masque_cluster, "groupe"] = "cluster_config_test"

table = avant[["created_at", "channel", "ticket_type_name", "category", "ticket_state_category", "groupe"]].sort_values("created_at")
chemin_table = sauvegarder_table(table.assign(created_at=lambda d: d["created_at"].astype(str)), "06_tickets_avant_lancement.csv")

print(f"{len(avant)} tickets avant le {DEBUT_PERIODE_OPERATIONNELLE.date()} :")
print(avant["groupe"].value_counts().to_string())
print()
print(f"Table detaillee enregistree dans : {chemin_table}")

# Repartition par canal avant / apres, pour les canaux principaux
canaux_principaux = ["android", "ios", "whatsapp", "facebook", "messenger"]
apres = df[df["created_at"] >= DEBUT_PERIODE_OPERATIONNELLE]
part_avant = avant["channel"].value_counts(normalize=True).reindex(canaux_principaux, fill_value=0) * 100
part_apres = apres["channel"].value_counts(normalize=True).reindex(canaux_principaux, fill_value=0) * 100

# --- Figure a 2 volets ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5), gridspec_kw={"width_ratios": [1.5, 1]})

couleurs_groupe = {"cluster_config_test": "#c0392b", "organique_isole": "#1f5c8b"}
for groupe, sous_df in avant.groupby("groupe"):
    ax1.scatter(sous_df["created_at"], sous_df["channel"], color=couleurs_groupe[groupe], label=groupe, s=55, alpha=0.85)
ax1.axvline(DEBUT_PERIODE_OPERATIONNELLE, color="black", linestyle="--", linewidth=1)
ax1.set_xlim(avant["created_at"].min() - pd.Timedelta(days=10), DEBUT_PERIODE_OPERATIONNELLE + pd.Timedelta(days=45))
ax1.text(DEBUT_PERIODE_OPERATIONNELLE + pd.Timedelta(days=5), -0.55, "debut periode\noperationnelle", fontsize=8, ha="left", va="top")
ax1.set_title("Les 38 tickets crees avant novembre 2025, par canal")
ax1.set_xlabel("Date de creation")
ax1.set_ylabel("Canal")
ax1.legend(loc="upper left")

x = range(len(canaux_principaux))
largeur = 0.35
ax2.bar([i - largeur / 2 for i in x], part_avant.values, width=largeur, label="Avant nov. 2025", color="#9fb4c7")
ax2.bar([i + largeur / 2 for i in x], part_apres.values, width=largeur, label="Depuis nov. 2025", color="#1f5c8b")
ax2.set_xticks(list(x))
ax2.set_xticklabels(canaux_principaux, rotation=30)
ax2.set_ylabel("% des tickets de la periode")
ax2.set_title("Repartition par canal : avant vs apres")
ax2.legend()

fig.suptitle(
    "Pourquoi le volume est quasi nul avant novembre 2025 : tickets de configuration/test\n"
    "(rouge, avr-mai 2024) + quelques reclamations isolees (bleu) sur des canaux qui seront ensuite marginaux",
    fontsize=10,
)
fig.tight_layout(rect=[0, 0, 1, 0.90])
chemin_fig = chemin_figure("06_periode_pre_lancement.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

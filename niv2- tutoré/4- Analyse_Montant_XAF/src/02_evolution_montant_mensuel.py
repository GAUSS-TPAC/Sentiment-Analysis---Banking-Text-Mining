"""
Evolution mensuelle du montant reclame, EN BRUT et EN VERSION "ASSAINIE".

Demande explicite : produire quand meme la courbe malgre les anomalies
identifiees (negatifs, zeros, valeurs extremes) -- ces valeurs peuvent etre
volontaires cote metier (ex. montant negatif = regularisation/remboursement).
On affiche donc les deux versions cote a cote plutot que de choisir a la
place du metier :
- "brut"    : toutes les valeurs renseignees, y compris negatifs/zeros/extremes
- "assaini" : on retire les negatifs, les zeros, et les valeurs au-dela de la
              borne haute IQR (meme methode que la statistique descriptive)
              -> utile pour voir la tendance "hors bruit", a titre indicatif
              uniquement, PAS comme un chiffre officiel.

Sorties :
- resultats/tables/02_evolution_montant_mensuel.csv
- resultats/figures/02_evolution_montant_mensuel.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from utils_montant import load_data, sauvegarder_table, chemin_figure

df = load_data()
positifs = df.loc[df["montant"] > 0, "montant"]
q1, q3 = positifs.quantile([0.25, 0.75])
borne_haute = q3 + 1.5 * (q3 - q1)
print(f"Borne haute IQR (sur les montants > 0) : {borne_haute:,.0f} XAF")

df["montant_assaini"] = df["montant"].where((df["montant"] > 0) & (df["montant"] <= borne_haute))

par_mois = df.groupby(df["created_at"].dt.to_period("M")).agg(
    nb_montants_brut=("montant", "count"),
    moyenne_brute=("montant", "mean"),
    mediane_brute=("montant", "median"),
    nb_montants_assainis=("montant_assaini", "count"),
    moyenne_assainie=("montant_assaini", "mean"),
    mediane_assainie=("montant_assaini", "median"),
).round(0)
par_mois = par_mois[par_mois["nb_montants_brut"] >= 5]

chemin_table = sauvegarder_table(par_mois.reset_index().assign(created_at=lambda d: d["created_at"].astype(str)), "02_evolution_montant_mensuel.csv")
print(par_mois.to_string())
print(f"\nTable enregistree dans : {chemin_table}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5), sharex=True)

ax1.plot(par_mois.index.astype(str), par_mois["moyenne_brute"], marker="o", color="#c0392b", label="Moyenne (brut)")
ax1.plot(par_mois.index.astype(str), par_mois["moyenne_assainie"], marker="o", color="#1f5c8b", label="Moyenne (assainie)")
ax1.set_title("Montant moyen par mois -- brut vs assaini")
ax1.set_ylabel("Montant moyen (XAF)")
ax1.tick_params(axis="x", rotation=90)
ax1.legend()

ax2.plot(par_mois.index.astype(str), par_mois["mediane_brute"], marker="o", color="#c0392b", label="Mediane (brut)")
ax2.plot(par_mois.index.astype(str), par_mois["mediane_assainie"], marker="o", color="#1f5c8b", label="Mediane (assainie)")
ax2.set_title("Montant median par mois -- brut vs assaini")
ax2.set_ylabel("Montant median (XAF)")
ax2.tick_params(axis="x", rotation=90)
ax2.legend()

fig.suptitle("Evolution mensuelle du montant reclame -- la moyenne brute est tres instable (sensible aux valeurs extremes), la mediane l'est beaucoup moins", fontsize=10)
fig.tight_layout(rect=[0, 0, 1, 0.94])
chemin_fig = chemin_figure("02_evolution_montant_mensuel.png")
fig.savefig(chemin_fig, dpi=150)
print(f"Graphique enregistre dans : {chemin_fig}")

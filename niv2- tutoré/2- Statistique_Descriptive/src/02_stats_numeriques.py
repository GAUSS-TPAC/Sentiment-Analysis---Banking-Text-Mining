"""
Statistique descriptive des variables numeriques.

Pour chaque colonne classee "numerique" par utils.classifier_colonne, on calcule :
count, % manquant, moyenne, ecart-type, min, quartiles, max, nb de zeros,
nb de valeurs negatives, nb de valeurs aberrantes (methode IQR).

Point d'attention methodologique : certaines colonnes sont numeriques dans
leur FORME (uniquement des chiffres) mais sont en realite des CODES et non des
quantites : un numero de telephone, les 4 derniers chiffres d'une carte, un
numero de compte ou un "order number". Calculer une moyenne sur un numero de
telephone n'a aucun sens metier. On distingue donc explicitement les deux cas
ci-dessous, sur la base de la connaissance metier (pas d'heuristique automatique
fiable pour cette distinction).

Sortie : resultats/tables/02_stats_numeriques.csv
"""

import numpy as np
import pandas as pd

from utils import load_data, vue_ensemble_colonnes, sauvegarder

# Colonnes numeriques qui representent une vraie quantite (moyenne/ecart-type ont un sens)
QUANTITES_REELLES = {
    "ticket_attributes_Montant en XAF",
    "ticket_attributes_Montant",
    "ticket_parts_total_count",
    "linked_objects_total_count",
}


def stats_colonne_numerique(nom: str, serie_num: pd.Series, n_total: int) -> dict:
    non_nulles = serie_num.dropna()
    q1, q2, q3 = non_nulles.quantile([0.25, 0.5, 0.75]) if len(non_nulles) else (np.nan, np.nan, np.nan)
    iqr = q3 - q1 if len(non_nulles) else np.nan
    borne_basse, borne_haute = q1 - 1.5 * iqr, q3 + 1.5 * iqr if len(non_nulles) else (np.nan, np.nan)
    nb_aberrants = ((non_nulles < borne_basse) | (non_nulles > borne_haute)).sum() if len(non_nulles) else 0

    return {
        "colonne": nom,
        "nature": "quantite" if nom in QUANTITES_REELLES else "code_numerique",
        "count": len(non_nulles),
        "pct_manquant": round(100 * (1 - len(non_nulles) / n_total), 2),
        "moyenne": round(non_nulles.mean(), 2) if len(non_nulles) else np.nan,
        "ecart_type": round(non_nulles.std(), 2) if len(non_nulles) else np.nan,
        "min": non_nulles.min() if len(non_nulles) else np.nan,
        "q1": q1,
        "mediane": q2,
        "q3": q3,
        "max": non_nulles.max() if len(non_nulles) else np.nan,
        "nb_zeros": int((non_nulles == 0).sum()),
        "nb_negatifs": int((non_nulles < 0).sum()),
        "nb_valeurs_aberrantes_iqr": int(nb_aberrants),
    }


df = load_data()
vue = vue_ensemble_colonnes(df)
colonnes_numeriques = vue.loc[vue["categorie_detectee"] == "numerique", "colonne"].tolist()

resultats = []
for nom in colonnes_numeriques:
    serie_num = pd.to_numeric(df[nom], errors="coerce")
    resultats.append(stats_colonne_numerique(nom, serie_num, len(df)))

stats = pd.DataFrame(resultats)
chemin = sauvegarder(stats, "02_stats_numeriques.csv")

print(f"{len(colonnes_numeriques)} colonnes numeriques analysees.")
print()
print(stats.to_string(index=False))
print()
print(f"Tableau enregistre dans : {chemin}")

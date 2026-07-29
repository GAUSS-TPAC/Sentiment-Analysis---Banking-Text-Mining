"""
Statistique descriptive des variables de type date.

Pour chaque colonne classee "date" : date min, date max, etendue en jours,
taux de parsing reussi (certaines dates saisies a la main restent illisibles
meme apres normalisation, cf. utils.parser_dates_flexible).

Sortie : resultats/tables/04_stats_dates.csv
"""

import pandas as pd

from utils import load_data, vue_ensemble_colonnes, parser_dates_flexible, sauvegarder


def stats_colonne_date(nom: str, dates: pd.Series, n_total: int) -> dict:
    valides = dates.dropna()
    return {
        "colonne": nom,
        "count_parse_ok": len(valides),
        "pct_manquant_ou_non_parsable": round(100 * (1 - len(valides) / n_total), 2),
        "date_min": valides.min() if len(valides) else pd.NaT,
        "date_max": valides.max() if len(valides) else pd.NaT,
        "etendue_jours": (valides.max() - valides.min()).days if len(valides) else None,
    }


df = load_data()
vue = vue_ensemble_colonnes(df)
colonnes_dates = vue.loc[vue["categorie_detectee"] == "date", "colonne"].tolist()

resultats = []
for nom in colonnes_dates:
    dates = parser_dates_flexible(df[nom])
    resultats.append(stats_colonne_date(nom, dates, len(df)))

stats = pd.DataFrame(resultats)
chemin = sauvegarder(stats, "04_stats_dates.csv")

print(f"{len(colonnes_dates)} colonnes date analysees.")
print()
print(stats.to_string(index=False))
print()
print(f"Tableau enregistre dans : {chemin}")

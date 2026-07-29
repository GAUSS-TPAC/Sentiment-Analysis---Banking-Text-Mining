"""
Statistique descriptive des variables categorielles et booleennes.

Pour chaque colonne categorielle : tableau des frequences (top 10 modalites +
une ligne "AUTRES" qui regroupe le reste), avec effectif et pourcentage.
Pour chaque colonne booleenne : repartition TRUE / FALSE / manquant.

Sorties :
- resultats/tables/03_stats_categorielles.csv (format long : 1 ligne par modalite)
- resultats/tables/03_stats_booleennes.csv
"""

import pandas as pd

from utils import load_data, vue_ensemble_colonnes, sauvegarder

TOP_N = 10


def frequences_colonne(nom: str, serie: pd.Series) -> list[dict]:
    n_total = len(serie)
    comptes = serie.value_counts(dropna=True)
    lignes = []
    for modalite, effectif in comptes.head(TOP_N).items():
        lignes.append(
            {
                "colonne": nom,
                "modalite": modalite,
                "effectif": int(effectif),
                "pourcentage": round(100 * effectif / n_total, 2),
            }
        )
    reste = comptes.iloc[TOP_N:].sum()
    if reste > 0:
        lignes.append(
            {
                "colonne": nom,
                "modalite": f"AUTRES ({len(comptes) - TOP_N} modalites)",
                "effectif": int(reste),
                "pourcentage": round(100 * reste / n_total, 2),
            }
        )
    nb_manquants = serie.isna().sum()
    if nb_manquants > 0:
        lignes.append(
            {
                "colonne": nom,
                "modalite": "(manquant)",
                "effectif": int(nb_manquants),
                "pourcentage": round(100 * nb_manquants / n_total, 2),
            }
        )
    return lignes


def repartition_booleenne(nom: str, serie: pd.Series) -> dict:
    n_total = len(serie)
    normalise = serie.str.upper()
    nb_true = (normalise == "TRUE").sum()
    nb_false = (normalise == "FALSE").sum()
    nb_manquant = serie.isna().sum()
    return {
        "colonne": nom,
        "nb_true": nb_true,
        "pct_true": round(100 * nb_true / n_total, 2),
        "nb_false": nb_false,
        "pct_false": round(100 * nb_false / n_total, 2),
        "nb_manquant": nb_manquant,
        "pct_manquant": round(100 * nb_manquant / n_total, 2),
    }


df = load_data()
vue = vue_ensemble_colonnes(df)

colonnes_categorielles = vue.loc[vue["categorie_detectee"] == "categorielle", "colonne"].tolist()
colonnes_booleennes = vue.loc[vue["categorie_detectee"] == "booleenne", "colonne"].tolist()

lignes_categorielles = []
for nom in colonnes_categorielles:
    lignes_categorielles.extend(frequences_colonne(nom, df[nom]))
stats_categorielles = pd.DataFrame(lignes_categorielles)
chemin_cat = sauvegarder(stats_categorielles, "03_stats_categorielles.csv")

stats_booleennes = pd.DataFrame([repartition_booleenne(nom, df[nom]) for nom in colonnes_booleennes])
chemin_bool = sauvegarder(stats_booleennes, "03_stats_booleennes.csv")

print(f"{len(colonnes_categorielles)} colonnes categorielles -> {chemin_cat}")
print(f"{len(colonnes_booleennes)} colonnes booleennes -> {chemin_bool}")
print()
print("Apercu booleennes :")
print(stats_booleennes.to_string(index=False))

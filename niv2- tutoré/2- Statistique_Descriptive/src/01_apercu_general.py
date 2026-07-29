"""
Etape 0 du cours : profilage general du dataset.

Ce script repond aux questions :
- combien de lignes / colonnes ?
- quel type detecte pour chaque colonne (identifiant, numerique, categorielle,
  booleenne, date, texte libre, json imbrique) ?
- quel taux de valeurs manquantes et quelle cardinalite par colonne ?

Sortie : resultats/tables/01_vue_ensemble_colonnes.csv
"""

from utils import load_data, vue_ensemble_colonnes, sauvegarder

df = load_data()

print(f"Dimensions du dataset : {df.shape[0]} lignes x {df.shape[1]} colonnes")
print()

vue = vue_ensemble_colonnes(df)
chemin = sauvegarder(vue, "01_vue_ensemble_colonnes.csv")

print("Repartition des colonnes par categorie detectee :")
print(vue["categorie_detectee"].value_counts().to_string())
print()
print(f"Tableau complet enregistre dans : {chemin}")

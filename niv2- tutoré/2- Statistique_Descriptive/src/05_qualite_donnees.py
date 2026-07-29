"""
Controles de qualite des donnees, transversaux a tout le dataset :
- doublons (lignes completes, et doublons sur les cles metier id / ticket_id)
- colonnes constantes (une seule valeur -> aucune information, candidates a l'exclusion)
- colonnes les plus creuses (beaucoup de valeurs manquantes)
- coherence temporelle (created_at doit etre <= updated_at)

Sortie : resultats/tables/05_qualite_donnees.csv (indicateurs cle-valeur)
         + impression du detail dans la console pour documentation du rapport
"""

import pandas as pd

from utils import load_data, vue_ensemble_colonnes, parser_dates_flexible, sauvegarder

df = load_data()
vue = vue_ensemble_colonnes(df)

indicateurs = {}

# 1. Doublons
indicateurs["nb_lignes"] = len(df)
indicateurs["nb_doublons_lignes_completes"] = int(df.duplicated().sum())
indicateurs["nb_doublons_sur_id"] = int(df["id"].duplicated().sum())
indicateurs["nb_doublons_sur_ticket_id"] = int(df["ticket_id"].duplicated().sum())

# 2. Colonnes constantes (nunique == 1) : aucune information, candidates a exclure des analyses suivantes
colonnes_constantes = vue.loc[vue["nb_uniques"] == 1, "colonne"].tolist()
indicateurs["nb_colonnes_constantes"] = len(colonnes_constantes)

# 3. Colonnes les plus creuses (>= 99% manquant)
colonnes_tres_creuses = vue.loc[vue["pct_manquant"] >= 99, "colonne"].tolist()
indicateurs["nb_colonnes_pct_manquant_geq_99"] = len(colonnes_tres_creuses)

# 4. Coherence temporelle : created_at <= updated_at
created = parser_dates_flexible(df["created_at"])
updated = parser_dates_flexible(df["updated_at"])
incoherentes = (created.notna() & updated.notna() & (created > updated)).sum()
indicateurs["nb_lignes_created_at_apres_updated_at"] = int(incoherentes)

resume = pd.DataFrame(list(indicateurs.items()), columns=["indicateur", "valeur"])
chemin = sauvegarder(resume, "05_qualite_donnees.csv")

print("Indicateurs de qualite :")
print(resume.to_string(index=False))
print()
print(f"Colonnes constantes ({len(colonnes_constantes)}) :")
print(", ".join(colonnes_constantes))
print()
print(f"Colonnes >= 99% manquantes ({len(colonnes_tres_creuses)}) :")
print(", ".join(colonnes_tres_creuses))
print()
print(f"Tableau enregistre dans : {chemin}")

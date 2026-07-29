"""
Fonctions communes utilisees par tous les scripts de statistique descriptive :
- chargement du fichier source
- classification automatique de chaque colonne (identifiant, numerique,
  categorielle, booleenne, date, texte libre, json imbrique)

Toutes les statistiques sont calculees a partir de ces deux fonctions, afin que
chaque script (02_..., 03_..., ...) reste court et ne fasse qu'une seule chose.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Racine du projet = 2 niveaux au-dessus de ce fichier (src/ -> 2- Statistique_Descriptive/ -> niv2- tutoré/ -> racine)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_CSV = PROJECT_ROOT / "SRC_Intercom_Reclamation_202607201846.csv"
RESULTATS_DIR = Path(__file__).resolve().parents[1] / "resultats"
TABLES_DIR = RESULTATS_DIR / "tables"
FIGURES_DIR = RESULTATS_DIR / "figures"

# Colonnes traitees comme des identifiants techniques (non pertinentes en stat descriptive classique)
COLONNES_IDENTIFIANTS = {
    "id",
    "ticket_id",
    "ticket_state_id",
    "ticket_type_id",
    "admin_assignee_id",
    "team_assignee_id",
}

# Mois en toutes lettres (francais) rencontres dans certaines dates saisies a la main,
# ex: "26 juin 2026" -> convertis en "26 06 2026" avant le parsing.
MOIS_FR = {
    "janvier": "01", "février": "02", "fevrier": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08", "aout": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12", "decembre": "12",
}


def load_data() -> pd.DataFrame:
    """Charge le CSV source en gardant tout en texte brut (dtype=str).

    On charge tout en texte a ce stade : la conversion en nombre / date / booleen
    est faite plus tard, colonne par colonne, une fois son type identifie.
    Cela evite les avertissements de pandas sur les types mixtes et garde le
    controle total sur le parsing (formats de date heterogenes, etc.).
    """
    df = pd.read_csv(SRC_CSV, dtype=str, low_memory=False)
    return df


def parser_dates_flexible(serie: pd.Series) -> pd.Series:
    """Parse une colonne de dates en tolerant plusieurs formats rencontres dans
    l'export Intercom : ISO ('2026-07-16 13:57:25'), JJ.MM.AAAA, JJ/MM/AAAA,
    dates en toutes lettres ('26 juin 2026') et timestamps unix en secondes
    ('1782475560'). Renvoie une Series de dates (NaT si non reconnu).
    """
    brut = serie.astype(str).str.strip()

    texte_normalise = brut.str.lower()
    for mois, num in MOIS_FR.items():
        texte_normalise = texte_normalise.str.replace(mois, num, regex=False)

    dates = pd.to_datetime(texte_normalise, errors="coerce", dayfirst=True, format="mixed")

    # Repechage des timestamps unix en secondes : exactement 10 chiffres (les
    # numeros de telephone camerounais font 9 chiffres, on evite donc de les
    # confondre avec un timestamp en ne ciblant que 10 chiffres).
    manquantes = dates.isna() & brut.str.fullmatch(r"\d{10}")
    if manquantes.any():
        candidats = pd.to_datetime(brut[manquantes].astype("int64"), unit="s", errors="coerce")
        # On ne garde que les dates plausibles pour ecarter les faux positifs
        candidats = candidats.where((candidats.dt.year >= 2015) & (candidats.dt.year <= 2035))
        dates.loc[manquantes] = candidats

    return dates


def _taux_conversion(serie: pd.Series, fonction_conversion) -> float:
    """Renvoie la proportion de valeurs non nulles convertibles avec succes."""
    non_nulles = serie.dropna()
    if len(non_nulles) == 0:
        return 0.0
    converties = fonction_conversion(non_nulles)
    return converties.notna().mean()


def classifier_colonne(nom: str, serie: pd.Series) -> str:
    """Classe une colonne dans une des categories definies dans le cours :
    identifiant / booleenne / date / numerique / json_imbrique / categorielle / texte_libre

    L'ordre des tests compte : on ecarte d'abord les cas "faciles" (booleen,
    date, numerique, json) avant de trancher entre texte libre / identifiant /
    categorielle sur la base de la longueur et de la cardinalite, pour eviter
    qu'une colonne de date ou de texte long ne soit prise a tort pour un
    identifiant simplement parce qu'elle a beaucoup de valeurs uniques.
    """
    n = len(serie)
    non_nulles = serie.dropna()
    nunique = non_nulles.nunique()

    if n == 0 or len(non_nulles) == 0:
        return "vide"

    if nom in COLONNES_IDENTIFIANTS:
        return "identifiant"

    valeurs_uniques = set(non_nulles.unique())
    if valeurs_uniques <= {"TRUE", "FALSE", "True", "False", "true", "false"}:
        return "booleenne"

    taux_date = _taux_conversion(non_nulles, parser_dates_flexible)
    if taux_date > 0.85:
        return "date"

    taux_numerique = _taux_conversion(non_nulles, lambda s: pd.to_numeric(s, errors="coerce"))
    if taux_numerique > 0.9:
        return "numerique"

    echantillon = non_nulles.astype(str).str.strip().str.slice(0, 1)
    if (echantillon.isin(["[", "{"])).mean() > 0.9:
        return "json_imbrique"

    textes = non_nulles.astype(str)
    longueur_moyenne = textes.str.len().mean()
    mots_moyens = textes.str.split().str.len().mean()
    if longueur_moyenne > 60 or mots_moyens > 2.5:
        return "texte_libre"

    ratio_cardinalite = nunique / len(non_nulles)
    if ratio_cardinalite > 0.7 and nunique > 100:
        return "identifiant"

    if nunique <= 50 or ratio_cardinalite < 0.05:
        return "categorielle"

    return "texte_libre"


def vue_ensemble_colonnes(df: pd.DataFrame) -> pd.DataFrame:
    """Construit le tableau de synthese : 1 ligne par colonne avec son type
    detecte, son taux de valeurs manquantes et sa cardinalite.
    """
    lignes = []
    for nom in df.columns:
        serie = df[nom]
        n = len(serie)
        nb_manquants = serie.isna().sum()
        lignes.append(
            {
                "colonne": nom,
                "categorie_detectee": classifier_colonne(nom, serie),
                "pct_manquant": round(100 * nb_manquants / n, 2),
                "nb_uniques": serie.nunique(dropna=True),
                "dtype_brut": str(serie.dtype),
            }
        )
    return pd.DataFrame(lignes)


def sauvegarder(df: pd.DataFrame, nom_fichier: str) -> Path:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    chemin = TABLES_DIR / nom_fichier
    df.to_csv(chemin, index=False)
    return chemin

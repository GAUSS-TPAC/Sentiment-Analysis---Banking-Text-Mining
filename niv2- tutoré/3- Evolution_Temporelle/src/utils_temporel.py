"""
Fonctions communes aux scripts d'evolution temporelle.

On s'appuie exclusivement sur `created_at` comme date de reference d'une
reclamation : c'est une colonne systeme Intercom, remplie a 100%, dans un
format unique (ISO), contrairement a `ticket_attributes_Date de la
transaction` qui est saisie a la main et s'est revelee peu fiable lors de la
statistique descriptive (cf. dossier "2- Statistique_Descriptive").
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_CSV = PROJECT_ROOT / "SRC_Intercom_Reclamation_202607201846.csv"
RESULTATS_DIR = Path(__file__).resolve().parents[1] / "resultats"
TABLES_DIR = RESULTATS_DIR / "tables"
FIGURES_DIR = RESULTATS_DIR / "figures"


def load_data() -> pd.DataFrame:
    """Charge le CSV source avec created_at/updated_at deja convertis en dates."""
    df = pd.read_csv(SRC_CSV, dtype=str, low_memory=False)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    return df


def sauvegarder_table(df: pd.DataFrame, nom_fichier: str) -> Path:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    chemin = TABLES_DIR / nom_fichier
    df.to_csv(chemin, index=False)
    return chemin


def chemin_figure(nom_fichier: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURES_DIR / nom_fichier

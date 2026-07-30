"""Fonctions communes aux scripts d'analyse du champ ticket_attributes_Montant en XAF."""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_CSV = PROJECT_ROOT / "SRC_Intercom_Reclamation_202607201846.csv"
RESULTATS_DIR = Path(__file__).resolve().parents[1] / "resultats"
TABLES_DIR = RESULTATS_DIR / "tables"
FIGURES_DIR = RESULTATS_DIR / "figures"

COLONNE_MONTANT = "ticket_attributes_Montant en XAF"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(SRC_CSV, dtype=str, low_memory=False)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["montant"] = pd.to_numeric(df[COLONNE_MONTANT], errors="coerce")
    return df


def sauvegarder_table(df: pd.DataFrame, nom_fichier: str) -> Path:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    chemin = TABLES_DIR / nom_fichier
    df.to_csv(chemin, index=False)
    return chemin


def chemin_figure(nom_fichier: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURES_DIR / nom_fichier

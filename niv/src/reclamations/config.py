"""
Chemins et constantes de périmètre.

Toutes les dates de coupure utilisées dans l'analyse sont définies ici, avec la
justification de leur valeur et le notebook qui l'établit. Aucune date de coupure
ne doit être écrite en dur dans un notebook : si un seuil bouge, il bouge ici et
l'ensemble de la chaîne reste cohérente.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Chemins
# --------------------------------------------------------------------------- #

#: Racine du projet (dossier contenant `src/`, `notebooks/`, `resultats/`).
RACINE = Path(__file__).resolve().parents[2]

DOSSIER_RESULTATS = RACINE / "resultats"
DOSSIER_FIGURES = DOSSIER_RESULTATS / "figures"
DOSSIER_TABLES = DOSSIER_RESULTATS / "tables"

#: Emplacements où chercher l'export Intercom, par ordre de préférence.
#:
#: Le fichier est volumineux (~11 Mo) et n'a pas vocation à être versionné : il
#: n'est donc pas supposé vivre à un emplacement fixe. On accepte aussi bien
#: `data/raw/` (convention du projet) que la racine, et **le dossier parent** —
#: ce dernier cas couvre la situation où le projet est déposé dans un
#: sous-dossier à côté duquel l'export a été laissé.
_CANDIDATS_DONNEES = (
    RACINE / "data" / "raw",
    RACINE,
    RACINE.parent / "data" / "raw",
    RACINE.parent,
)

#: Motif de nom de l'export brut Intercom.
MOTIF_EXPORT = "SRC_Intercom_Reclamation_*.csv"


def chemin_donnees() -> Path:
    """Localise l'export Intercom le plus récent.

    Cherche dans `data/raw/` puis à la racine du projet. Si plusieurs exports
    sont présents, retourne le plus récent par nom (les noms sont horodatés :
    `SRC_Intercom_Reclamation_YYYYMMDDHHMM.csv`).

    Raises
    ------
    FileNotFoundError
        Si aucun export n'est trouvé, avec la liste des dossiers inspectés.
    """
    trouves: list[Path] = []
    for dossier in _CANDIDATS_DONNEES:
        if dossier.is_dir():
            trouves.extend(sorted(dossier.glob(MOTIF_EXPORT)))
    if not trouves:
        inspectes = "\n  - ".join(str(d) for d in _CANDIDATS_DONNEES)
        raise FileNotFoundError(
            f"Aucun fichier '{MOTIF_EXPORT}' trouvé.\nDossiers inspectés :\n  - {inspectes}"
        )
    return trouves[-1]


def creer_dossiers_sortie() -> None:
    """Crée `resultats/figures` et `resultats/tables` s'ils n'existent pas."""
    DOSSIER_FIGURES.mkdir(parents=True, exist_ok=True)
    DOSSIER_TABLES.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Constantes de périmètre temporel
# --------------------------------------------------------------------------- #

#: Bascule pilote -> opérationnel.
#:
#: Avant cette date, l'export ne contient que 38 tickets sur 21 mois, dont un
#: cluster de tests de configuration du workspace Intercom (avril-mai 2024). La
#: répartition par canal bascule complètement de part et d'autre de cette date
#: (messenger 42 % -> 0,1 % ; android 13 % -> 66 % ; whatsapp 0 % -> 12,7 %),
#: ce qui confirme un changement de dispositif et non une montée en charge.
#: Établi dans : notebooks/02_rupture_de_collecte.ipynb
DEBUT_PERIODE_OPERATIONNELLE = pd.Timestamp("2025-11-01")

#: Date de rupture de la collecte des attributs de ticket.
#:
#: Le 13/03/2026, la part de tickets sans titre ni description passe de <10 % à
#: 80 %, puis 96 % le 14 et 100 % le 15. `Montant en XAF`, `Agence` et
#: `Date de la transaction` s'effondrent simultanément et reviennent ensemble
#: mi-mai. Un incident produit n'efface pas les champs d'un formulaire : la
#: signature est celle d'une mise en production côté application / flux Intercom.
#: Établi dans : notebooks/02_rupture_de_collecte.ipynb
DATE_RUPTURE_COLLECTE = pd.Timestamp("2026-03-13")

#: Mois exclus du périmètre d'analyse causale (collecte dégradée).
#:
#: La couverture texte y est de 16 %, 3 % et 28 % respectivement. Surtout, les
#: tickets qui ont survécu à la panne ne sont pas représentatifs de ceux qui
#: n'en ont pas (cf. test de représentativité, notebook 03) : ils sur-représentent
#: BENEFICIAIRE ERRONE (14,8 % vs 0,3 %) et sous-représentent whatsapp
#: (2,1 % vs 19,7 %). Ce sous-ensemble est trié par le bug lui-même.
#: Établi dans : notebooks/03_perimetre_et_representativite.ipynb
MOIS_COLLECTE_DEGRADEE = (
    pd.Period("2026-03", freq="M"),
    pd.Period("2026-04", freq="M"),
    pd.Period("2026-05", freq="M"),
)

#: Dernier mois de l'export, partiel (extraction faite le 20/07/2026).
#: À ne jamais comparer tel quel à un mois complet.
MOIS_PARTIEL = pd.Period("2026-07", freq="M")

# --------------------------------------------------------------------------- #
# Seuils d'analyse
# --------------------------------------------------------------------------- #

#: Longueur minimale (caractères) d'un texte titre+description pour être classé.
#: En dessous, le texte est du bruit ("Woro Tsoh", "Compte employé") et fausserait
#: la mesure de couverture de la taxonomie.
LONGUEUR_TEXTE_MIN = 25

#: Fenêtre (jours) en deçà de laquelle une seconde réclamation du même client
#: sur le même motif est considérée comme un re-dépôt et non une demande nouvelle.
#: Choix justifié dans le notebook 05 : le taux de « même motif » est de 81 % à
#: moins de 3 jours et décroît régulièrement au-delà (68 % à 7-30 j, 58 % au-delà).
FENETRE_REDEPOT_JOURS = 7

#: Borne haute de plausibilité sur `Montant en XAF`, en XAF.
#: Au-delà, la distribution présente un amas artificiel de 44 valeurs entre 690 M
#: et 700 M et un cas isolé à 50 milliards : agrégats financiers non fiables.
#: Ce seuil ne sert qu'à produire des ordres de grandeur, jamais un chiffre officiel.
MONTANT_PLAFOND_PLAUSIBLE = 10_000_000

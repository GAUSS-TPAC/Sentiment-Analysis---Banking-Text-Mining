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

#: Sorties de travail contenant du texte client, **jamais versionnées**.
#:
#: Placé sous `data/`, couvert par la règle `data/` du `.gitignore`. Tout fichier
#: portant du texte de réclamation va ici et nulle part ailleurs : `resultats/tables/`
#: est versionné et diffusé, il est réservé aux agrégats.
DOSSIER_AUDIT = RACINE / "data" / "audit"

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

# --------------------------------------------------------------------------- #
# Confidentialité
# --------------------------------------------------------------------------- #

#: Fragments de noms de colonnes dont aucune valeur ne doit sortir dans une table.
#:
#: L'export contient des données nominatives en clair : noms, numéros de téléphone,
#: numéros de compte, et le texte libre des réclamations, qui cite couramment des
#: références de transaction. Une table de résultats est destinée à être versionnée
#: et diffusée ; elle ne doit donc jamais porter d'exemple de valeur pour ces champs.
#:
#: Le masquage s'applique **à l'écriture** et non à la relecture : une donnée qui
#: n'a jamais été écrite en clair ne peut pas fuiter.
FRAGMENTS_COLONNES_SENSIBLES = (
    "nom",
    "numero",
    "compte",
    "_default_title_",
    "_default_description_",
    "reference",
    "contacts",
    "rib",
)

#: Noms de colonnes exactement sensibles, en complément des fragments ci-dessus.
COLONNES_SENSIBLES = ("id", "ticket_id")

#: Valeur émise à la place d'un exemple de valeur sensible.
MARQUEUR_MASQUE = "[masqué]"

#: Longueur maximale d'une cellule dans une table de `resultats/tables/`.
#:
#: Sépare un agrégat d'un texte client. Le libellé de famille le plus long du
#: projet (« Débité sans que le bénéficiaire soit crédité ») fait 43 caractères,
#: le nom de colonne le plus long 45, et l'exemple du dictionnaire est tronqué à
#: 60. La médiane d'une description client est de 117 caractères. Le seuil de 200
#: laisse donc passer tous les agrégats existants et arrête toute réclamation
#: autre que la plus laconique.
LONGUEUR_CELLULE_MAX = 200


def est_colonne_sensible(nom: str) -> bool:
    """Indique si une colonne porte des données à caractère personnel.

    Le test est fait sur le **nom** de la colonne, en minuscules, par recherche de
    fragments. Un test par liste exhaustive serait plus précis mais céderait au
    premier attribut ajouté côté outil de support : les noms d'attributs suivent
    une nomenclature métier stable (`Nom du client`, `Numero de compte`,
    `Reference de la transaction`), et c'est elle qu'on filtre.
    """
    minuscule = nom.lower()
    if minuscule in COLONNES_SENSIBLES:
        return True
    return any(fragment in minuscule for fragment in FRAGMENTS_COLONNES_SENSIBLES)


# --------------------------------------------------------------------------- #
# Seuils d'analyse (suite)
# --------------------------------------------------------------------------- #

#: Borne haute de plausibilité sur `Montant en XAF`, en XAF.
#: Au-delà, la distribution présente un amas artificiel de 44 valeurs entre 690 M
#: et 700 M et un cas isolé à 50 milliards : agrégats financiers non fiables.
#: Ce seuil ne sert qu'à produire des ordres de grandeur, jamais un chiffre officiel.
MONTANT_PLAFOND_PLAUSIBLE = 10_000_000

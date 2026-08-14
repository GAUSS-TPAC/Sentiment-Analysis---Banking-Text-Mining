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
    RACINE.parent / "dataset",
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
# Source complémentaire — messages d'ouverture (export conversations Intercom)
# --------------------------------------------------------------------------- #

#: Emplacements où chercher l'export complémentaire des conversations Intercom.
#:
#: Ce fichier porte, pour une partie des tickets, le message d'ouverture réel
#: (`source_body`), non tronqué contrairement au CSV plat (§2.4 du protocole).
#: Mêmes règles de recherche que :func:`chemin_donnees` : volumineux (~19 Mo),
#: pas d'emplacement fixe imposé.
_CANDIDATS_CONVERSATIONS = (
    RACINE / "data" / "raw" / "Interc",
    RACINE.parent / "dataset" / "Interc",
    RACINE.parent / "dataset",
)

#: Motif de nom de l'export conversations Intercom.
MOTIF_CONVERSATIONS = "conversations_*.xlsx"

#: Auteurs dont le message compte comme un message **client** (par opposition
#: à un agent ou une équipe interne). Vérifié sur l'export : `user` et `lead`
#: couvrent 96,8 % des lignes de conversation liées à un ticket ; `admin` et
#: `team` (les 3,2 % restants) sont des tickets ouverts par un agent pour le
#: compte d'un client — leur premier message n'est pas la plainte du client.
AUTEURS_CLIENT = ("user", "lead")


def chemin_conversations() -> Path | None:
    """Localise l'export conversations Intercom le plus récent, si présent.

    Contrairement à :func:`chemin_donnees`, l'absence de ce fichier n'est pas
    une erreur : c'est une source complémentaire, optionnelle, qui enrichit le
    texte quand elle est disponible. Retourne ``None`` si rien n'est trouvé —
    à l'appelant de décider si c'est bloquant.
    """
    trouves: list[Path] = []
    for dossier in _CANDIDATS_CONVERSATIONS:
        if dossier.is_dir():
            trouves.extend(sorted(dossier.glob(MOTIF_CONVERSATIONS)))
    return trouves[-1] if trouves else None


# --------------------------------------------------------------------------- #
# Système B — second outil de gestion de réclamations (non-Intercom)
# --------------------------------------------------------------------------- #

#: Dossiers où chercher les fichiers du Système B, par ordre de préférence.
#:
#: Le dossier réel s'appelle `Nouveau dossier 1/Nouveau dossier` (nom
#: d'extraction non renommé) : plutôt que de coder ce chemin en dur, la
#: recherche est **récursive** (`rglob`) sous chacun de ces dossiers, ce qui
#: survit à un renommage ou un déplacement du sous-dossier. Chaque fichier du
#: Système B a un nom stable et prévisible (`tickets_first.xlsx`,
#: `categories.xlsx`...), peu de risque de collision.
_CANDIDATS_SYSTEME_B = (
    RACINE / "data" / "raw",
    RACINE.parent / "dataset",
    RACINE.parent,
)

#: Fichiers attendus du Système B, tels que vérifiés lors de l'exploration.
FICHIERS_SYSTEME_B = (
    "tickets_first.xlsx",
    "categories.xlsx",
    "groups.xlsx",
    "users.xlsx",
    "ticket_assigned_users.xlsx",
    "custom_fields.xlsx",
    "custom_field_values.xlsx",
    "ticket_conversations.xlsx",
)


def chemin_systeme_b(nom_fichier: str) -> Path | None:
    """Localise un fichier du Système B par son nom exact, si présent.

    Recherche récursive sous :data:`_CANDIDATS_SYSTEME_B` (voir sa docstring).
    Comme :func:`chemin_conversations`, l'absence n'est pas une erreur : à
    l'appelant de décider — mais `systeme_b.py` traite en pratique ces 8
    fichiers comme un tout (un système incomplet n'est pas exploitable).
    """
    for dossier in _CANDIDATS_SYSTEME_B:
        if not dossier.is_dir():
            continue
        trouves = sorted(dossier.rglob(nom_fichier))
        if trouves:
            return trouves[-1]
    return None


#: Fenêtre (jours, ± autour de la date) retenue pour l'appariement A↔B par
#: (téléphone, montant, date). Justifiée par le taux d'appariement mesuré sur
#: le seul téléphone : 19,4 % à ±3 j, 23,3 % à ±7 j, 26,0 % à ±14 j — le signal
#: continue de croître au-delà de 3 j (la ressaisie manuelle est parfois
#: différée), mais ±3 j est le point où l'écart au bruit de fond
#: (`consolidation.bruit_de_fond`) est déjà net sans élargir inutilement le
#: risque de faux appariement. À revérifier, pas à recopier tel quel — le
#: notebook 09 doit reproduire ce calcul sur les données réelles.
#: Établi dans : notebooks/09_deduplication_a_b.ipynb
FENETRE_APPARIEMENT_JOURS = 3

#: Seuil de représentativité pour le test de bruit de fond par permutation
#: (`consolidation.bruit_de_fond`) : un taux d'appariement observé est jugé
#: significatif s'il dépasse ce multiple du taux obtenu par permutation
#: aléatoire des clés. Repère conservateur, pas une loi statistique — c'est
#: l'écart d'ordre de grandeur qui porte la décision (même logique que le
#: seuil de V de Cramér, §4.4 du protocole).
SEUIL_SIGNAL_SUR_BRUIT = 3.0

#: Borne haute de plausibilité sur `montant_xaf` (Système B), en XAF.
#:
#: Valeur provisoire, reprise du seuil équivalent côté Système A
#: (:data:`MONTANT_PLAFOND_PLAUSIBLE`) — **à revérifier dans le notebook 08**
#: contre la distribution réelle de `montant_xaf` avant d'être considérée
#: comme retenue : l'exploration préalable signale un maximum à 698 136 765,
#: très supérieur à celui de A, dont la forme (amas artificiel ou queue
#: continue) n'a pas encore été caractérisée sur les données chargées par ce
#: projet.
#: Établi dans : notebooks/08_systeme_b_chargement_qualite.ipynb
MONTANT_PLAFOND_PLAUSIBLE_B = 10_000_000


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

#: Mois où la collecte des attributs de ticket a été dégradée (repère descriptif).
#:
#: La couverture texte y est de 16 %, 3 % et 28 % respectivement (avant
#: enrichissement, cf. ci-dessous). **N'est plus le critère d'exclusion** du
#: périmètre d'analyse causale depuis l'intégration de l'export conversations
#: (:data:`SEUIL_COUVERTURE_JOURNALIERE`) — conservé comme repère pour les
#: figures et les commentaires du notebook 02, qui datent l'incident lui-même.
#: Établi dans : notebooks/02_rupture_de_collecte.ipynb
MOIS_COLLECTE_DEGRADEE = (
    pd.Period("2026-03", freq="M"),
    pd.Period("2026-04", freq="M"),
    pd.Period("2026-05", freq="M"),
)

#: Seuil de couverture texte **journalière** en-dessous duquel une journée est
#: exclue du périmètre d'analyse causale (`chargement.perimetre_analyse`).
#:
#: Remplace l'exclusion par mois entier (:data:`MOIS_COLLECTE_DEGRADEE`) :
#: protocole §3.4 — sur les 247 journées de la période opérationnelle, 59 sont
#: à 0-10 % de couverture et 184 à 70-100 % ; seules quelques journées se
#: situent entre les deux, ce qui fait de 50 % un seuil qui ne tranche presque
#: rien. La couverture est calculée sur le texte **enrichi**
#: (`chargement.construire_texte_enrichi`, titre + description + message
#: d'ouverture récupéré dans l'export conversations Intercom quand disponible)
#: — appliquer ce seuil au texte enrichi plutôt qu'au CSV seul fait passer le
#: périmètre de 7 563 à 9 161 tickets, validé par le même test de
#: représentativité (V de Cramér ≤ 0,20, notebook 03) que la version non
#: enrichie.
#: Établi dans : notebooks/03_perimetre_et_representativite.ipynb
SEUIL_COUVERTURE_JOURNALIERE = 0.50

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
# Audit manuel du reliquat non classé (notebook 04)
# --------------------------------------------------------------------------- #

#: Décompte de l'audit manuel du reliquat non classé — 20 textes, graine 3,
#: périmètre à 8 348 textes (notebooks 03+04, texte enrichi + balises HTML
#: retirées). Centralisé ici, plutôt que dupliqué dans chaque notebook qui
#: l'utilise (04, 06), pour qu'une ré-lecture de l'audit (nouvel export,
#: nouvelle graine) ne se corrige qu'à un seul endroit — écart déjà rencontré
#: une fois (protocole, écart A3). Toutes les familles observées dans l'audit
#: sont représentées (règle d'intégralité, protocole §5.1) ;
#: `AUDIT_MANUEL_HORS_TAXONOMIE` couvre celles qu'aucune règle de
#: `texte.FAMILLES` ne code encore (§4.2, écart A2). `erreur_client` et
#: `carte` n'apparaissent pas dans ce tirage de 20 textes (absentes, pas à
#: zéro par choix) : rien à en redistribuer cette fois.
AUDIT_MANUEL_TAILLE = 20
AUDIT_MANUEL = {
    "debit_non_credit": 12,
    "debit_injustifie": 2,
    "acces_otp": 1,
    "demande_info": 1,
}
AUDIT_MANUEL_HORS_TAXONOMIE = {"dysfonctionnement_application / hors taxonomie (§4.2)": 4}

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
    # Ajoutés pour le Système B (colonnes en anglais ou vocabulaire différent) :
    "matricule",
    "carte",
    "name",
    "mail",
    "creator",
    "subject",
    "detail",
    "solution",
    "body_text",
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

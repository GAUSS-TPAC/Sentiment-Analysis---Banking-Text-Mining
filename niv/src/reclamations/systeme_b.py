"""
Chargement et qualité du Système B — second outil de gestion de réclamations,
distinct d'Intercom. Le rapprochement des deux systèmes vit dans
`consolidation.py`, pas ici : ce module ne connaît que le Système B.

Structure relationnelle (vérifiée par exploration préalable, intégrité
référentielle à 100 % sur les 7 clés testées, aucune ligne orpheline) ::

    groups ──< categories ──< tickets_first >── users
                                │  ├─ group_id / source_group_id → groups
                                │  └─ user_id → users
                                ├──< ticket_assigned_users >── users
                                ├──< custom_field_values >── custom_fields
                                └──< ticket_conversations

Pièges vérifiés avant d'écrire ce module — ne pas les redécouvrir :

1. Les colonnes `opened_by`, `in_progress_by`, `resolved_by`, `closed_by`,
   `transferred_by` de `tickets_first` sont des **noms de personnes**
   (`users.display_name`), pas des identifiants (0 % de correspondance sur
   `users.id`, 100 % sur `users.display_name`). `closed_by` vaut la chaîne
   littérale `'auto'` sur 1 309 des ~1 400 clôtures explicites.
2. Le délai `created_at -> closed_on` est un **artefact de clôture
   automatique** (~61 jours après résolution, `closed_on == updated_at` sur
   la majorité des clôtures) : ne jamais l'utiliser comme indicateur de délai
   de traitement. Utiliser `created_at -> resolved_on` (:func:`delai_resolution`).
3. `first_response_at` cesse d'être alimenté après le 11/03/2026 (passe de
   100 % à 0 % de remplissage sur les mois suivants) : toute série construite
   dessus s'arrête là, ce n'est pas une dégradation progressive.
4. `type_reclamation`, `is_reclamation_fondee`, `customer_id` sont **vides à
   100 %** ; `domaine_reclamation` n'a qu'une seule modalité
   (`RECLAMATION_CLIENT`, 72 % de remplissage) ; `creator_type` est constant
   (`EMPLOYEE`) ; `priority` est à 97,5 % `MOYENNE` (valeur par défaut jamais
   modifiée). Aucun de ces champs n'est discriminant — à écarter
   explicitement (:func:`controles_qualite_b`), pas silencieusement.
5. La qualification fine du motif ne vient pas de `tickets_first` mais des 3
   champs DROPDOWN de `custom_field_values` (:func:`sous_motifs_b`) — un
   quatrième dropdown (« Selectionnez un probleme ») n'a que 24 valeurs
   renseignées, statistiquement inexploitable, volontairement écarté.
"""

from __future__ import annotations

import unicodedata

import pandas as pd

from . import config

# --------------------------------------------------------------------------- #
# Chargement des 8 tables
# --------------------------------------------------------------------------- #


def _charger(nom_fichier: str) -> pd.DataFrame:
    """Charge un fichier du Système B par son nom, ou lève une erreur claire."""
    chemin = config.chemin_systeme_b(nom_fichier)
    if chemin is None:
        raise FileNotFoundError(
            f"'{nom_fichier}' introuvable sous {config._CANDIDATS_SYSTEME_B}. "
            "Le Système B est traité comme un tout : les 8 fichiers doivent être présents."
        )
    return pd.read_excel(chemin)


def charger_tickets() -> pd.DataFrame:
    """Charge `tickets_first.xlsx`, avec les colonnes de dates typées.

    Les identifiants (`id`, `category_id`, `group_id`, `user_id`,
    `source_group_id`) sont laissés en texte (UUID) : aucune inférence
    numérique ne les concerne, contrairement au CSV Intercom.
    """
    df = _charger("tickets_first.xlsx")
    for col in ("created_at", "updated_at", "first_response_at", "resolved_on", "closed_on"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["mois"] = df["created_at"].dt.to_period("M")
    return df


def charger_categories() -> pd.DataFrame:
    """Charge `categories.xlsx` — 17 catégories, `audience` constante (`EMPLOYEE`)."""
    return _charger("categories.xlsx")


def charger_groups() -> pd.DataFrame:
    """Charge `groups.xlsx` — groupes traitants (`group_id`) et origines (`source_group_id`)."""
    return _charger("groups.xlsx")


def charger_users() -> pd.DataFrame:
    """Charge `users.xlsx` — 791 agents, données personnelles internes (nom, email)."""
    return _charger("users.xlsx")


def charger_assignations() -> pd.DataFrame:
    """Charge `ticket_assigned_users.xlsx` — relation n-n ticket <-> agent."""
    return _charger("ticket_assigned_users.xlsx")


def charger_champs_personnalises() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge `custom_fields.xlsx` (dictionnaire, 19 champs) et
    `custom_field_values.xlsx` (50 874 valeurs, `incident_id` toujours vide —
    le seul lien exploité est `ticket_id`).
    """
    champs = _charger("custom_fields.xlsx")
    valeurs = _charger("custom_field_values.xlsx")
    return champs, valeurs


def charger_conversations() -> pd.DataFrame:
    """Charge `ticket_conversations.xlsx` — notes internes de traitement.

    `creator_type` et `visible_to_customer` sont **constants** sur cet export
    (`EMPLOYEE`, `0`) : ce sont des notes d'agent à agent, jamais des messages
    au client. Contient des données personnelles d'agents
    (`creator_display_name`, `creator_email`) — à ne jamais verser dans
    `resultats/tables/`.
    """
    df = _charger("ticket_conversations.xlsx")
    df["created_on"] = pd.to_datetime(df["created_on"], errors="coerce")
    return df


# --------------------------------------------------------------------------- #
# Sous-motifs — les 3 dropdowns exploitables de custom_field_values
# --------------------------------------------------------------------------- #

#: Nom des 3 champs DROPDOWN retenus comme qualification de motif. Le 4e
#: dropdown de l'export (« Selectionnez un probleme ») n'a que 24 valeurs
#: renseignées sur 7 788 tickets porteurs de champs personnalisés :
#: statistiquement inexploitable, volontairement exclu.
CHAMPS_SOUS_MOTIF = (
    "Sous domaine Sara transactionnel",
    "Sous domaine Monetique",
    "Sous domaine Operations bancaire",
)

#: Corrections de casse constatées dans les valeurs de dropdown (une seule à
#: ce jour : « Opération contestée », 1 occurrence sur 124, à fusionner avec
#: « Opération Contestée »). Ajouter ici plutôt que dans un notebook, pour que
#: toute table qui relit ce champ voie la version corrigée.
_CORRECTIONS_CASSE_SOUS_MOTIF = {"Opération contestée": "Opération Contestée"}


def sous_motifs(champs: pd.DataFrame, valeurs: pd.DataFrame) -> pd.DataFrame:
    """Pivote les 3 dropdowns de motif en une ligne par ticket qualifié.

    Vérifié à l'exploration : un ticket ne porte jamais plus d'un des 3
    champs à la fois, et jamais deux valeurs contradictoires pour un même
    champ — la jointure est donc une simple sélection, pas une agrégation à
    arbitrer.

    Returns
    -------
    DataFrame
        Indexé par `ticket_id`, colonnes `domaine` (nom du champ, ex. « Sous
        domaine Sara transactionnel ») et `sous_motif` (valeur, casse
        normalisée). Un ticket sans dropdown renseigné n'apparaît pas :
        utiliser un `join` à gauche pour le faire apparaître avec des `NaN`.
    """
    fusion = valeurs.merge(
        champs[["id", "name"]], left_on="custom_field_id", right_on="id", suffixes=("", "_champ")
    )
    motifs = fusion[fusion["name"].isin(CHAMPS_SOUS_MOTIF) & fusion["value"].notna()].copy()
    motifs["value"] = motifs["value"].str.strip()
    motifs["value"] = motifs["value"].replace(_CORRECTIONS_CASSE_SOUS_MOTIF)
    motifs = motifs[motifs["value"] != ""]
    motifs = motifs.rename(columns={"name": "domaine", "value": "sous_motif"})
    return motifs.set_index("ticket_id")[["domaine", "sous_motif"]]


def valeurs_champ(champs: pd.DataFrame, valeurs: pd.DataFrame, nom_champ: str) -> pd.Series:
    """Extrait la valeur brute (texte) d'un champ personnalisé nommé
    `nom_champ`, indexée par `ticket_id`.

    Aucune conversion de type : à l'appelant de convertir selon le besoin —
    :func:`montants` et :func:`dates_transaction` le font pour les deux
    champs les plus utilisés dans ce projet ;
    `consolidation.py` s'en sert directement pour le téléphone et la
    référence de transaction, qui restent des identifiants texte.

    Raises
    ------
    KeyError
        Si `nom_champ` ne correspond à aucune ligne de `custom_fields` — un
        nom de champ mal orthographié échoue bruyamment plutôt que de
        retourner une série vide silencieuse.

    Notes
    -----
    La comparaison normalise l'Unicode (NFC) avant de comparer : les noms de
    champs accentués de cet export sont encodés en forme décomposée (NFD, un
    « é » stocké comme deux caractères), invisible à l'affichage mais qui fait
    échouer une comparaison `==` avec un littéral Python écrit normalement
    (NFC). Piège vérifié après un premier échec silencieux sur ce champ précis.
    """
    noms_normalises = champs["name"].map(lambda s: unicodedata.normalize("NFC", s))
    correspondances = champs.loc[noms_normalises == unicodedata.normalize("NFC", nom_champ), "id"]
    if correspondances.empty:
        raise KeyError(f"Aucun champ personnalisé nommé {nom_champ!r} dans custom_fields.")
    id_champ = correspondances.iloc[0]
    return valeurs.loc[valeurs["custom_field_id"] == id_champ].set_index("ticket_id")["value"]


def telephone_client(champs: pd.DataFrame, valeurs: pd.DataFrame) -> pd.Series:
    """Numéro de téléphone du client, valeur brute (texte, non normalisée).

    Voir `consolidation.normaliser_telephone` pour la mise en forme comparable
    au téléphone du Système A avant tout appariement.
    """
    return valeurs_champ(champs, valeurs, "Numéro de téléphone du client")


def reference_transaction(champs: pd.DataFrame, valeurs: pd.DataFrame) -> pd.Series:
    """Référence de transaction, valeur brute (texte)."""
    return valeurs_champ(champs, valeurs, "Référence de la transaction")


def montants(champs: pd.DataFrame, valeurs: pd.DataFrame) -> pd.Series:
    """Extrait le champ `Montant en XAF` de `custom_field_values`, converti en numérique.

    Non filtré : contient des valeurs négatives et nulles (voir
    :func:`montants_plausibles` pour un sous-ensemble exploitable), comme le
    champ homologue côté Système A (`chargement.typer`).
    """
    return pd.to_numeric(valeurs_champ(champs, valeurs, "Montant en XAF"), errors="coerce")


def montants_plausibles(champs: pd.DataFrame, valeurs: pd.DataFrame) -> pd.Series:
    """Sous-ensemble exploitable de :func:`montants` : strictement positif et
    sous :data:`config.MONTANT_PLAFOND_PLAUSIBLE_B`.

    Même réserve que côté Système A
    (`chargement.montants_plausibles`) : sert à hiérarchiser les motifs entre
    eux, jamais un chiffre officiel.
    """
    m = montants(champs, valeurs)
    return m[(m > 0) & (m < config.MONTANT_PLAFOND_PLAUSIBLE_B)]


def dates_transaction(champs: pd.DataFrame, valeurs: pd.DataFrame) -> pd.Series:
    """Extrait le champ `Date de la transaction`, converti en datetime.

    Formats hétérogènes constatés : ISO `AAAA-MM-JJ` (majoritaire),
    `JJ/MM/AAAA`, `JJ-MM-AAAA`, et des dates en toutes lettres (« JJ mois
    AAAA ») que `pandas` ne convertit pas — elles deviennent `NaT`, ce qui
    sous-estime le remplissage réel plutôt que de le sur-estimer par un
    mauvais parsing. Des dates aberrantes (jusqu'en 2029) subsistent ensuite :
    non filtrées ici, à exclure explicitement à l'usage (comparaison à
    `pd.Timestamp.now()` ou à la date d'extraction).
    """
    d = valeurs_champ(champs, valeurs, "Date de la transaction")
    return pd.to_datetime(d, errors="coerce", dayfirst=True)


# --------------------------------------------------------------------------- #
# Délais — ne jamais utiliser created_at -> closed_on (artefact, voir module)
# --------------------------------------------------------------------------- #


def delai_resolution(tickets: pd.DataFrame) -> pd.Series:
    """Délai `created_at -> resolved_on`, en heures. **Seul délai fiable** :
    voir l'avertissement en tête de module sur `closed_on`.
    """
    return (tickets["resolved_on"] - tickets["created_at"]).dt.total_seconds() / 3600


# --------------------------------------------------------------------------- #
# Contrôles qualité
# --------------------------------------------------------------------------- #

#: Colonnes de `tickets_first` vérifiées vides, constantes, ou sans pouvoir
#: discriminant — à afficher explicitement comme écartées (même logique que
#: `chargement.controles_qualite` / notebook 01 côté Système A), jamais
#: silencieusement absentes des tables de contrôle.
COLONNES_INEXPLOITABLES = {
    "type_reclamation": "vide à 100 %",
    "is_reclamation_fondee": "vide à 100 %",
    "customer_id": "vide à 100 % — aucun identifiant client exploitable dans ce système",
    "creator_type": "constante ('EMPLOYEE')",
    "domaine_reclamation": "quasi-constante ('RECLAMATION_CLIENT', 72 % de remplissage)",
    "detail": "remplie à 4,2 % seulement",
    "priority": "à 97,5 % 'MOYENNE' — valeur par défaut jamais modifiée",
}


def controles_qualite(tickets: pd.DataFrame) -> pd.DataFrame:
    """Synthèse des colonnes inexploitables de `tickets_first`, avec taux de
    remplissage mesuré (pas recopié de l'exploration préalable).
    """
    lignes = []
    for col, raison in COLONNES_INEXPLOITABLES.items():
        lignes.append(
            {
                "colonne": col,
                "pct_rempli": round(tickets[col].notna().mean() * 100, 1),
                "nb_uniques": tickets[col].nunique(dropna=True),
                "raison_ecartee": raison,
            }
        )
    return pd.DataFrame(lignes)

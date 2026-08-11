"""
Chargement, typage et contrôles qualité de l'export Intercom.

Principe de chargement : le CSV est lu **intégralement en `str`**. L'inférence de
type de pandas est désactivée volontairement, pour deux raisons :

1. Les colonnes d'identifiants (`id`, `ticket_id`, numéros de téléphone, numéros
   de compte) seraient converties en flottants et perdraient leurs zéros de tête
   ou leur précision.
2. Les champs saisis à la main (`Montant en XAF`, `Date de la transaction`)
   contiennent des formats hétérogènes ; on veut décider explicitement de ce qui
   est converti, de ce qui est écarté, et compter les échecs de conversion.

Chaque conversion est donc faite ensuite, colonne par colonne, avec `errors="coerce"`
et un comptage des valeurs non convertibles.
"""

from __future__ import annotations

import json
from typing import Iterable

import numpy as np
import pandas as pd

from . import config

# --------------------------------------------------------------------------- #
# Chargement
# --------------------------------------------------------------------------- #


def charger_brut(chemin=None) -> pd.DataFrame:
    """Charge l'export Intercom sans aucune inférence de type.

    Parameters
    ----------
    chemin :
        Chemin du CSV. Par défaut, résolu par :func:`config.chemin_donnees`.

    Returns
    -------
    DataFrame
        Toutes les colonnes en `object` (str), valeurs manquantes en `NaN`.

    Notes
    -----
    Le fichier contient des descriptions client sur plusieurs lignes. Le nombre
    de lignes physiques (~23 000) est donc supérieur au nombre de tickets
    (18 094) : c'est normal, le parseur CSV recolle les champs multi-lignes.
    """
    chemin = chemin or config.chemin_donnees()
    return pd.read_csv(chemin, dtype=str, low_memory=False)


def typer(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes dérivées typées utilisées par tous les notebooks.

    Colonnes ajoutées
    -----------------
    ``date_creation``, ``date_maj``
        Horodatages système Intercom (fiables à 100 %, aucun manquant).
    ``mois``, ``jour``
        Périodes dérivées de ``date_creation``, pour les agrégations.
    ``montant``
        ``ticket_attributes_Montant en XAF`` converti en numérique. **Non filtré** :
        contient les valeurs négatives, nulles et aberrantes. Utiliser
        :func:`montants_plausibles` pour un sous-ensemble exploitable.
    ``nb_messages``
        ``ticket_parts_total_count`` : nombre d'échanges dans la conversation.
    ``contact_id``
        Identifiant client extrait du JSON ``contacts_contacts``. C'est la clé
        qui permet de passer d'une analyse par ticket à une analyse par client.
    ``delai_h``
        ``date_maj - date_creation`` en heures. **Proxy imparfait** du délai de
        traitement : Intercom ne fournit pas de date de clôture, et `updated_at`
        bouge à chaque modification du ticket. À n'utiliser que sur les tickets
        `resolved`, et à interpréter comme un ordre de grandeur.
    """
    df = df.copy()
    df["date_creation"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["date_maj"] = pd.to_datetime(df["updated_at"], errors="coerce")
    df["mois"] = df["date_creation"].dt.to_period("M")
    df["jour"] = df["date_creation"].dt.date
    df["montant"] = pd.to_numeric(df["ticket_attributes_Montant en XAF"], errors="coerce")
    df["nb_messages"] = pd.to_numeric(df["ticket_parts_total_count"], errors="coerce")
    df["contact_id"] = df["contacts_contacts"].map(_extraire_contact_id)
    df["delai_h"] = (df["date_maj"] - df["date_creation"]).dt.total_seconds() / 3600
    return df


def _extraire_contact_id(valeur) -> str | None:
    """Extrait l'identifiant du premier contact d'une cellule JSON Intercom.

    Format attendu ::

        [{"type": "contact", "id": "6a2c...", "external_id": "[TEL]"}]

    Retourne ``None`` si la cellule est vide, illisible ou sans contact.
    """
    try:
        contacts = json.loads(valeur)
    except (TypeError, ValueError):
        return None
    if not contacts:
        return None
    return contacts[0].get("id")


# --------------------------------------------------------------------------- #
# Périmètres
# --------------------------------------------------------------------------- #


def perimetre_operationnel(df: pd.DataFrame) -> pd.DataFrame:
    """Restreint à la période opérationnelle (à partir de novembre 2025).

    Écarte les 38 tickets de la phase pilote (février 2024 - octobre 2025), qui
    mélangent des tickets de test de configuration du workspace et un filet
    résiduel de réclamations. Voir :data:`config.DEBUT_PERIODE_OPERATIONNELLE`.
    """
    return df[df["date_creation"] >= config.DEBUT_PERIODE_OPERATIONNELLE].copy()


def perimetre_analyse(df: pd.DataFrame) -> pd.DataFrame:
    """Restreint au périmètre d'analyse causale : opérationnel **moins** mars-mai 2026.

    C'est le périmètre sur lequel les conclusions de motifs sont valides. Il couvre
    six mois de fonctionnement normal (nov. 2025 - fév. 2026, juin - juil. 2026)
    et représente 6 867 tickets, avec 95,5 % de couverture texte.

    Le passage par cette fonction, plutôt que par un filtre écrit à la main dans
    chaque notebook, garantit que tous les chiffres publiés portent sur la même base.
    """
    op = perimetre_operationnel(df)
    return op[~op["mois"].isin(config.MOIS_COLLECTE_DEGRADEE)].copy()


def montants_plausibles(df: pd.DataFrame) -> pd.DataFrame:
    """Sous-ensemble des tickets dont le montant est exploitable.

    Filtre : montant strictement positif et inférieur à
    :data:`config.MONTANT_PLAFOND_PLAUSIBLE`.

    Warning
    -------
    Ce filtre produit des **ordres de grandeur**, pas des chiffres officiels.
    Les valeurs écartées ne sont pas du bruit : les 20 montants négatifs sont
    concentrés à 90 % sur le type COMPTE (probable régularisation volontaire),
    et les 178 zéros à 83 % sur SARA (transfert non abouti). Elles portent du
    sens métier et doivent être qualifiées avec le métier, pas supprimées.
    """
    m = df["montant"]
    return df[(m > 0) & (m < config.MONTANT_PLAFOND_PLAUSIBLE)].copy()


# --------------------------------------------------------------------------- #
# Contrôles qualité
# --------------------------------------------------------------------------- #


def dictionnaire_colonnes(df: pd.DataFrame) -> pd.DataFrame:
    """Dictionnaire de données : type, taux de manquants, cardinalité, longueur max.

    La colonne ``longueur_max`` est le contrôle qui révèle les champs **tronqués
    à l'export** : une colonne JSON dont la longueur maximale est de 4 caractères
    (`[{"t`) n'est pas une colonne constante, c'est une colonne dont le contenu
    a été perdu à l'extraction.
    """
    lignes = []
    for col in df.columns:
        s = df[col]
        non_nul = s.dropna()
        lignes.append(
            {
                "colonne": col,
                "pct_manquant": round(s.isna().mean() * 100, 2),
                "nb_uniques": s.nunique(dropna=True),
                "longueur_max": int(non_nul.str.len().max()) if len(non_nul) else 0,
                "exemple": non_nul.iloc[0][:60] if len(non_nul) else "",
            }
        )
    return pd.DataFrame(lignes).sort_values("pct_manquant").reset_index(drop=True)


def colonnes_tronquees(df: pd.DataFrame, longueur_suspecte: int = 8) -> list[str]:
    """Colonnes dont le contenu a été tronqué à l'export.

    Détecte les colonnes qui ressemblent à du JSON (commencent par ``[`` ou ``{``)
    mais dont **aucune** valeur ne dépasse `longueur_suspecte` caractères : le
    contenu a été coupé à l'extraction.

    C'est un contrôle à part entière, distinct de « colonne constante » : une
    colonne constante n'apporte pas d'information, une colonne tronquée en
    apportait et l'a perdue. La distinction change la conclusion — dans le premier
    cas on écarte la colonne, dans le second on redemande l'export.
    """
    suspectes = []
    for col in df.columns:
        non_nul = df[col].dropna()
        if non_nul.empty:
            continue
        longueurs = non_nul.str.len()
        ressemble_json = non_nul.str.startswith(("[", "{")).mean() > 0.9
        if ressemble_json and longueurs.max() <= longueur_suspecte:
            suspectes.append(col)
    return suspectes


def controles_qualite(df: pd.DataFrame) -> pd.DataFrame:
    """Tableau de synthèse des contrôles transversaux.

    Contrôles appliqués : volumétrie, doublons (ligne complète et sur clés),
    colonnes constantes, colonnes quasi vides, colonnes tronquées, et cohérence
    temporelle `created_at <= updated_at`.
    """
    dico = dictionnaire_colonnes(df)
    constantes = dico.loc[dico["nb_uniques"] <= 1, "colonne"].tolist()
    quasi_vides = dico.loc[
        (dico["pct_manquant"] >= 99) & (dico["nb_uniques"] > 1), "colonne"
    ].tolist()
    tronquees = colonnes_tronquees(df)

    dates_ok = pd.to_datetime(df["created_at"], errors="coerce") <= pd.to_datetime(
        df["updated_at"], errors="coerce"
    )

    controles = [
        ("Tickets chargés", len(df)),
        ("Colonnes", df.shape[1]),
        ("Doublons (ligne complète)", int(df.duplicated().sum())),
        ("Doublons sur id", int(df["id"].duplicated().sum())),
        ("Doublons sur ticket_id", int(df["ticket_id"].duplicated().sum())),
        ("Colonnes constantes", len(constantes)),
        ("Colonnes >= 99% manquantes", len(quasi_vides)),
        ("Colonnes tronquées à l'export", len(tronquees)),
        ("Incohérences created_at > updated_at", int((~dates_ok).sum())),
    ]
    return pd.DataFrame(controles, columns=["controle", "resultat"])


def taux_completude(
    df: pd.DataFrame, colonnes: Iterable[str], par: str = "mois"
) -> pd.DataFrame:
    """Taux de remplissage de plusieurs colonnes, agrégé par période.

    C'est l'outil central du notebook 02 : c'est en regardant la complétude
    **dans le temps** — et non globalement — que la rupture du 13/03/2026 apparaît.
    Un taux de manquants global de 60 % ne dit rien ; le même taux qui passe de
    5 % à 97 % du jour au lendemain désigne un événement système.
    """
    out = df.groupby(par, observed=True).apply(
        lambda g: pd.Series({c: g[c].notna().mean() for c in colonnes}),
        include_groups=False,
    )
    out["nb_tickets"] = df.groupby(par, observed=True).size()
    return out


def indicateur_ticket_vide(df: pd.DataFrame) -> pd.Series:
    """Booléen : le ticket n'a ni titre, ni description exploitable.

    Sert d'indicateur synthétique de la panne de collecte. On teste les deux
    champs plutôt qu'un seul, pour ne pas confondre « l'agent n'a pas mis de
    titre » (courant) avec « aucun contenu n'a été capturé » (la panne).
    """
    sans_titre = df["ticket_attributes__default_title_"].isna()
    desc = df["ticket_attributes__default_description_"].fillna("")
    sans_desc = desc.str.len() <= config.LONGUEUR_TEXTE_MIN
    return sans_titre & sans_desc


def profil_comparatif(
    df: pd.DataFrame, masque: pd.Series, colonnes: Iterable[str]
) -> dict[str, pd.DataFrame]:
    """Compare la distribution de plusieurs variables entre deux sous-groupes.

    Utilisé pour le **test de représentativité** du notebook 03 : si les tickets
    qui ont du texte et ceux qui n'en ont pas ont le même profil sur les variables
    observables (type, canal, statut), alors le sous-ensemble textuel est
    extrapolable. S'ils diffèrent, il ne l'est pas.

    Parameters
    ----------
    masque :
        Booléen définissant le groupe A (``True``) contre le groupe B (``False``).

    Returns
    -------
    dict
        Une table par colonne, avec les deux distributions en % et leur écart
        en points de pourcentage.
    """
    resultats = {}
    for col in colonnes:
        a = df.loc[masque, col].value_counts(normalize=True) * 100
        b = df.loc[~masque, col].value_counts(normalize=True) * 100
        t = pd.DataFrame({"groupe_A_pct": a, "groupe_B_pct": b}).fillna(0)
        t["ecart_pts"] = (t["groupe_A_pct"] - t["groupe_B_pct"]).round(1)
        resultats[col] = t.round(1).sort_values("groupe_A_pct", ascending=False)
    return resultats


def sauver_table(df: pd.DataFrame, nom: str, index: bool = True) -> None:
    """Écrit une table dans `resultats/tables/` en CSV UTF-8 (BOM pour Excel)."""
    config.creer_dossiers_sortie()
    chemin = config.DOSSIER_TABLES / f"{nom}.csv"
    df.to_csv(chemin, index=index, encoding="utf-8-sig")
    print(f"  -> {chemin.relative_to(config.RACINE)}")

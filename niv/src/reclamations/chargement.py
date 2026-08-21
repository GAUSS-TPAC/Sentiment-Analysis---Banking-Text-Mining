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

from . import config, texte

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


def charger_messages_ouverture(chemin=None) -> pd.Series:
    """Charge le message d'ouverture de chaque ticket, depuis l'export
    conversations Intercom complémentaire (`conversations_*.xlsx`).

    Le CSV plat tronque le fil de conversation à 4 caractères (`colonnes_tronquees`,
    §2.4 du protocole). Cet export séparé — une ligne par conversation, pas par
    ticket — porte le contenu réel dans `source_body`, non tronqué.

    Jointure
    --------
    Par la colonne `id` de cet export **contre la colonne `id` du CSV plat**,
    jamais contre `ticket_id` : la colonne `ticket_id` de cet export est
    auto-référente (elle vaut la plupart du temps l'`id` de la même ligne) et
    ne pointe vers aucun ticket. Vérifié manuellement avant d'écrire cette
    fonction — c'est un piège de nommage propre à cet export, pas une
    convention Intercom générale.

    Un ticket a en général plusieurs lignes de conversation associées (sa
    création, les réponses, les réouvertures) ; seule la ligne dont l'`id`
    égale l'`id` du ticket porte son message d'ouverture, donc au plus une
    ligne par ticket survit à cette jointure — pas de déduplication à faire
    sur le fond, `drop_duplicates` ne sert qu'à écarter un doublon accidentel
    d'export.

    Returns
    -------
    Series
        Indexée par `id` (str, comparable à la colonne `id` de :func:`charger_brut`),
        message d'ouverture brut (non normalisé, non masqué). Vide si aucun
        export conversations n'est trouvé — source complémentaire, pas bloquante.
    """
    chemin = chemin or config.chemin_conversations()
    if chemin is None:
        return pd.Series(dtype="object", name="source_body")

    conv = pd.read_excel(chemin, dtype={"id": "int64"})
    conv["id"] = conv["id"].astype(str)
    client = conv[conv["source_author_type"].isin(config.AUTEURS_CLIENT)]
    return client.drop_duplicates("id").set_index("id")["source_body"]


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

        [{"type": "contact", "id": "<24 caractères hexadécimaux>",
          "external_id": "<numéro de téléphone du client>"}]

    L'exemple est volontairement schématique : une docstring est versionnée et
    diffusée, elle ne porte donc jamais de valeur réelle.

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


def regrouper_canal_digital(channel: pd.Series) -> pd.Series:
    """Regroupe les sous-canaux digitaux Intercom (`config.REGROUPEMENT_CANAL_DIGITAL`).

    Android et iOS sont deux OS de la même application SARA, pas deux canaux
    au sens métier : les fondre change la lecture de Q3 (« quel canal génère
    le plus de réclamations ? ») sans changer aucun ticket sous-jacent. Une
    valeur absente du dictionnaire (nouveau sous-canal dans un futur export)
    est conservée telle quelle plutôt que d'être silencieusement classée `Autre`.
    """
    return channel.map(config.REGROUPEMENT_CANAL_DIGITAL).fillna(channel)


def perimetre_operationnel(df: pd.DataFrame) -> pd.DataFrame:
    """Restreint à la période opérationnelle (à partir de novembre 2025).

    Écarte les 38 tickets de la phase pilote (février 2024 - octobre 2025), qui
    mélangent des tickets de test de configuration du workspace et un filet
    résiduel de réclamations. Voir :data:`config.DEBUT_PERIODE_OPERATIONNELLE`.
    """
    return df[df["date_creation"] >= config.DEBUT_PERIODE_OPERATIONNELLE].copy()


def construire_texte_enrichi(df: pd.DataFrame, messages_ouverture: pd.Series | None = None) -> pd.Series:
    """Texte de la réclamation, normalisé, complété par le message d'ouverture
    récupéré dans l'export conversations Intercom quand il est disponible.

    Combine :func:`texte.construire_texte` (titre + description du CSV plat,
    tronqué à l'extraction — §2.4 du protocole) et
    :func:`texte.enrichir_avec_messages_ouverture` (message réel, non tronqué,
    quand l'export complémentaire le porte — §3.4). Le résultat est aligné sur
    l'index de `df`, pas sur `id` : utilisable directement,
    ``df["texte"] = chargement.construire_texte_enrichi(df)``.

    Parameters
    ----------
    messages_ouverture :
        Par défaut, rechargé via :func:`charger_messages_ouverture`. À passer
        explicitement pour éviter de relire le fichier xlsx (~5 s) à chaque
        appel dans une même session — voir l'usage dans `perimetre_analyse`.
    """
    if messages_ouverture is None:
        messages_ouverture = charger_messages_ouverture()
    texte_csv = texte.construire_texte(df)
    par_id = texte_csv.set_axis(df["id"].to_numpy())
    enrichi = texte.enrichir_avec_messages_ouverture(par_id, messages_ouverture)
    return enrichi.set_axis(df.index)


def perimetre_analyse(df: pd.DataFrame, messages_ouverture: pd.Series | None = None) -> pd.DataFrame:
    """Restreint au périmètre d'analyse causale : période opérationnelle,
    restreinte aux journées dont la couverture texte **enrichie** atteint
    :data:`config.SEUIL_COUVERTURE_JOURNALIERE`.

    C'est le périmètre sur lequel les conclusions de motifs sont valides.
    Remplace l'ancienne règle par mois entier (`config.MOIS_COLLECTE_DEGRADEE`)
    par une règle à la journée appliquée au texte enrichi du message
    d'ouverture récupéré dans l'export conversations Intercom
    (:func:`construire_texte_enrichi`) — protocole §3.4. Représente 9 161
    tickets, validé par le test de représentativité du notebook 03 (V de
    Cramér 0,169 sur `ticket_type_name`, 0,121 sur `channel`, tous deux sous
    le seuil de 0,20 — contre 0,261 et 0,206, au-dessus du seuil, si la fenêtre
    dégradée entière est réintégrée sans le filtre journalier).

    Le DataFrame retourné porte deux colonnes ajoutées, `texte` (enrichi,
    normalisé) et `a_texte` (booléen, :func:`texte.a_texte_exploitable`), pour
    qu'aucun notebook consommateur n'ait à les reconstruire séparément — le
    risque, sinon, est d'oublier l'enrichissement dans un notebook et de
    retomber silencieusement sur l'ancien périmètre.

    Le passage par cette fonction, plutôt que par un filtre écrit à la main dans
    chaque notebook, garantit que tous les chiffres publiés portent sur la même base.
    """
    op = perimetre_operationnel(df)
    op["texte"] = construire_texte_enrichi(op, messages_ouverture)
    op["a_texte"] = texte.a_texte_exploitable(op["texte"])
    couverture_jour = op.groupby("jour")["a_texte"].transform("mean")
    return op[couverture_jour >= config.SEUIL_COUVERTURE_JOURNALIERE].copy()


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

    Confidentialité
    ---------------
    La colonne ``exemple`` est **masquée** pour les champs identifiés comme
    sensibles par :func:`config.est_colonne_sensible` — noms, numéros, texte libre.
    Cette table est versionnée et diffusée ; sans ce masquage, elle exposerait le
    nom et le numéro de téléphone d'un client réel, ceux de la première ligne non
    nulle rencontrée.

    Le masquage ne dégrade aucun contrôle : ``longueur_max``, ``nb_uniques`` et
    ``pct_manquant`` sont inchangés, et ce sont eux qui portent la détection de
    troncature et la décision d'écarter une colonne.
    """
    lignes = []
    for col in df.columns:
        s = df[col]
        non_nul = s.dropna()
        if config.est_colonne_sensible(col):
            exemple = config.MARQUEUR_MASQUE
        elif len(non_nul):
            exemple = non_nul.iloc[0][:60]
        else:
            exemple = ""
        lignes.append(
            {
                "colonne": col,
                "pct_manquant": round(s.isna().mean() * 100, 2),
                "nb_uniques": s.nunique(dropna=True),
                "longueur_max": int(non_nul.str.len().max()) if len(non_nul) else 0,
                "exemple": exemple,
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


def cramer_v(groupe: pd.Series, variable: pd.Series) -> float:
    """V de Cramér entre une variable de groupe (2 modalités ou plus) et une
    variable catégorielle observable — mesure synthétique de représentativité
    (protocole §4.4).

    Normalise le χ² par la taille de l'échantillon et le nombre de catégories,
    ce qui permet de comparer des tests portant sur des tables de tailles
    différentes (`ticket_type_name`, 17 catégories, et `channel`, 7). Seuil
    retenu au protocole : 0,20, repère rond et conservateur — ce qui porte la
    décision est l'écart d'un ordre de grandeur entre les résultats comparés,
    pas la position exacte du seuil.

    Nécessite `scipy` (non requis ailleurs dans le projet — import local pour
    ne pas alourdir la dépendance pour les notebooks qui ne calculent pas ce
    test).
    """
    from scipy.stats import chi2_contingency

    table = pd.crosstab(groupe, variable)
    chi2 = chi2_contingency(table)[0]
    n = table.to_numpy().sum()
    degres_liberte = min(table.shape) - 1
    return float(np.sqrt(chi2 / (n * degres_liberte)))


def sauver_table(df: pd.DataFrame, nom: str, index: bool = True) -> None:
    """Écrit une table d'agrégats dans `resultats/tables/`, en CSV UTF-8 (BOM Excel).

    Ce dossier est **versionné et diffusé**. Il est réservé aux agrégats : aucune
    table écrite ici ne doit contenir de texte de réclamation ni d'identifiant
    client. Pour un fichier de travail portant du texte, utiliser
    :func:`sauver_audit`.

    Raises
    ------
    ValueError
        Si une cellule dépasse :data:`config.LONGUEUR_CELLULE_MAX` caractères.
        C'est le garde-fou : un agrégat tient en quelques dizaines de caractères,
        une réclamation non. Plutôt que de compter sur la vigilance à la relecture,
        la fonction **refuse d'écrire** le fichier dangereux. Le message indique
        la colonne fautive et oriente vers :func:`sauver_audit`.
    """
    trop_long = _colonnes_trop_longues(df)
    if trop_long:
        raise ValueError(
            f"Table '{nom}' refusée : les colonnes {trop_long} dépassent "
            f"{config.LONGUEUR_CELLULE_MAX} caractères et ressemblent à du texte client. "
            "`resultats/tables/` est versionné et diffusé. "
            "Utiliser `sauver_audit()` après `texte.masquer_identifiants()`."
        )
    config.creer_dossiers_sortie()
    chemin = config.DOSSIER_TABLES / f"{nom}.csv"
    df.to_csv(chemin, index=index, encoding="utf-8-sig")
    print(f"  -> {chemin.relative_to(config.RACINE)}")


def _colonnes_trop_longues(df: pd.DataFrame) -> list[str]:
    """Colonnes (index compris) dont une valeur dépasse la longueur d'un agrégat."""
    fautives = []
    a_tester = [(str(c), df[c]) for c in df.columns]
    a_tester.append(("<index>", pd.Series(df.index)))
    for nom, serie in a_tester:
        textuel = serie.dropna().astype(str)
        if len(textuel) and textuel.str.len().max() > config.LONGUEUR_CELLULE_MAX:
            fautives.append(nom)
    return fautives


def sauver_audit(df: pd.DataFrame, nom: str, index: bool = True) -> None:
    """Écrit un fichier de travail contenant du texte client, **hors dépôt**.

    Destination : `data/audit/`, couvert par la règle `data/` du `.gitignore`.

    L'audit manuel du reliquat suppose de lire de vraies réclamations ; ces textes
    ne peuvent donc pas être supprimés. Ils sont en revanche masqués à l'écriture
    (:func:`texte.masquer_identifiants`, appelé par l'appelant) et n'entrent jamais
    dans `resultats/tables/`.
    """
    config.DOSSIER_AUDIT.mkdir(parents=True, exist_ok=True)
    chemin = config.DOSSIER_AUDIT / f"{nom}.csv"
    df.to_csv(chemin, index=index, encoding="utf-8-sig")
    print(f"  -> {chemin.relative_to(config.RACINE)}  (hors dépôt, non versionné)")

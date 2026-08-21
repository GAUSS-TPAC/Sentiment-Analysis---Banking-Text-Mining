"""
Rapprochement du Système A (Intercom) et de First Copilot (`systeme_b.py`).

Ce module ne contient aucune logique de chargement propre à l'un ou l'autre
système — seulement ce qui sert à les comparer. Établi après une exploration
préalable qui a montré que les deux systèmes **ne sont pas indépendants** :
une partie des tickets `canal = INTERCOM` de First Copilot sont des ressaisies
manuelles de tickets déjà présents dans le Système A, quelques heures après
leur création côté A (voir notebook 09).

Principe retenu — **appariement fin par paires**, pas une exclusion en bloc
d'un canal entier : on construit une table de correspondance ticket_id_a ↔
ticket_id_b sur des clés qui ne devraient coïncider par hasard que très
rarement (téléphone + montant + date proche, ou référence de transaction
commune), on la valide contre un bruit de fond mesuré par permutation
(:func:`bruit_de_fond` — même exigence méthodologique que
`chargement.cramer_v` pour la représentativité), et on n'exclut que les
tickets B effectivement appariés.

Aucune des deux clés n'est parfaite : le téléphone/montant est vulnérable aux
coïncidences (plusieurs clients, même montant rond, même jour), la référence
de transaction est plus rare mais moins souvent renseignée. Utiliser les deux
et publier le bruit de fond de chacune, plutôt que de choisir une seule clé et
taire son taux de faux positifs.
"""

from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from . import config

# --------------------------------------------------------------------------- #
# Normalisation — rendre comparables deux champs saisis dans deux systèmes
# --------------------------------------------------------------------------- #

#: Un numéro de téléphone plausible n'est fait que de chiffres et de
#: séparateurs de mise en forme (espace, +, parenthèses, tiret), sur une
#: longueur raisonnable. Sert de **garde avant** extraction des chiffres —
#: indispensable pour le côté Système A, où `contacts_contacts.external_id`
#: (§ `_extraire_telephone_json`) contient tantôt un téléphone, tantôt un
#: email, tantôt un identifiant hexadécimal (UUID) : un email ou un UUID
#: contiennent eux aussi, une fois les caractères non numériques retirés,
#: suffisamment de chiffres pour franchir un simple seuil de longueur — un
#: UUID est ~37 % de caractères `0-9` par construction (chiffres hexadécimaux
#: `0-9` sur 16 valeurs possibles `0-9a-f`). Ce piège a été détecté après un
#: premier appariement dont le taux dépassait tout ce qui était plausible.
_MOTIF_TELEPHONE_PLAUSIBLE = re.compile(r"^[\d\s+().-]{7,17}$")


def normaliser_telephone(serie: pd.Series) -> pd.Series:
    """Normalise un numéro de téléphone pour comparaison inter-systèmes.

    Rejette d'abord toute valeur qui ne *ressemble* pas à un téléphone
    (:data:`_MOTIF_TELEPHONE_PLAUSIBLE`), puis retire tout ce qui n'est pas
    un chiffre, l'indicatif pays (`237`) en tête, et ne garde que les 9
    derniers chiffres (format local camerounais). En dessous de 8 chiffres
    restants, le résultat est mis à `None` plutôt que de risquer un
    appariement sur un numéro tronqué.
    """
    brut = serie.astype("string")
    plausible = brut.str.match(_MOTIF_TELEPHONE_PLAUSIBLE, na=False)
    chiffres = brut.where(plausible).str.replace(r"\D", "", regex=True)
    chiffres = chiffres.str.replace(r"^237", "", regex=True, n=1)
    normalise = chiffres.str[-9:]
    return normalise.where(chiffres.str.len() >= 8)


def normaliser_reference(serie: pd.Series) -> pd.Series:
    """Normalise une référence de transaction : espaces retirés, majuscules.

    Une chaîne vide après nettoyage est mise à `None` — sinon deux tickets
    sans référence renseignée s'apparieraient l'un à l'autre sur une chaîne
    vide commune, un faux positif garanti.
    """
    propre = serie.astype("string").str.strip().str.upper()
    return propre.where(propre.str.len() > 0)


def _extraire_telephone_json(contacts_contacts: pd.Series) -> pd.Series:
    """Extrait `external_id` (numéro de téléphone) du premier contact du JSON
    `contacts_contacts` du Système A — même format que `chargement.
    _extraire_contact_id`, qui extrait `id` du même JSON pour un autre usage.
    """

    def extraire(valeur):
        try:
            contacts = json.loads(valeur)
        except (TypeError, ValueError):
            return None
        if not contacts:
            return None
        return contacts[0].get("external_id")

    return contacts_contacts.map(extraire)


def telephone_client_a(tickets_a: pd.DataFrame) -> pd.Series:
    """Meilleur numéro de téléphone disponible côté Système A, non normalisé.

    Priorité à `ticket_attributes_Numero_tel_client` (rempli sur 42,7 % des
    tickets), complété par `external_id` du JSON `contacts_contacts` quand
    l'attribut est vide (porte la couverture à 85,5 %). Les deux sources
    concordent à 86,2 % quand toutes deux sont présentes — vérifié à
    l'exploration, pas supposé.
    """
    attribut = tickets_a["ticket_attributes_Numero_tel_client"]
    depuis_json = _extraire_telephone_json(tickets_a["contacts_contacts"])
    return attribut.fillna(depuis_json)


# --------------------------------------------------------------------------- #
# Tables de clés — un format commun aux deux systèmes
# --------------------------------------------------------------------------- #


def cles_a(tickets_a: pd.DataFrame) -> pd.DataFrame:
    """Table de clés d'appariement pour le Système A, indexée par `id`
    (identifiant canonique du ticket dans ce projet — voir
    `chargement.construire_texte_enrichi` pour le même choix).

    Colonnes : `telephone` (normalisé), `montant` (arrondi à l'entier XAF le
    plus proche), `date` (`date_creation` du ticket), `reference` (normalisée).

    Attention à l'ordre des opérations : chaque colonne est calculée **avant**
    de changer l'index, puis alignée par position (`.to_numpy()`) — construire
    directement un `DataFrame(..., index=...)` à partir de Series qui portent
    encore l'index d'origine les réaligne silencieusement par label sur le
    nouvel index et vide la table (piège rencontré en écrivant cette fonction).
    """
    df = pd.DataFrame(
        {
            "telephone": normaliser_telephone(telephone_client_a(tickets_a)).to_numpy(),
            "montant": tickets_a["montant"].round(0).to_numpy(),
            "date": tickets_a["date_creation"].to_numpy(),
            "reference": normaliser_reference(
                tickets_a["ticket_attributes_Reference de la transaction"]
            ).to_numpy(),
        },
        index=pd.Index(tickets_a["id"].to_numpy(), name="ticket_id_a"),
    )
    return df


def cles_b(tickets_b: pd.DataFrame, champs: pd.DataFrame, valeurs: pd.DataFrame) -> pd.DataFrame:
    """Table de clés d'appariement pour First Copilot, même format que :func:`cles_a`.

    Le téléphone et la référence viennent de `custom_field_values`
    (`systeme_b.telephone_client` / `systeme_b.reference_transaction`), le
    montant de `systeme_b.montants`, la date de création de `tickets_b`
    elle-même (`created_at`, toujours alimentée côté B).
    """
    from . import systeme_b  # import local : évite une dépendance circulaire au chargement du paquet

    # `montants`/`telephone_client`/`reference_transaction` sont indexées par
    # ticket_id (elles viennent de `custom_field_values`, une ligne par champ
    # renseigné, pas une ligne par ticket) : le `.reindex` aligne correctement
    # sur l'ensemble complet des tickets B, y compris ceux sans aucun champ
    # personnalisé (NaN). C'est ce même alignement par label, fait
    # explicitement ici, dont `cles_a` s'est passée par erreur (voir sa
    # docstring) : la différence est que `df.index` et l'index de
    # `montant`/`telephone`/`reference` sont déjà le même espace de valeurs
    # (les `id` de tickets), pas une correspondance positionnelle à imposer.
    montant = systeme_b.montants(champs, valeurs)
    telephone = systeme_b.telephone_client(champs, valeurs)
    reference = systeme_b.reference_transaction(champs, valeurs)

    df = tickets_b.set_index("id")
    resultat = pd.DataFrame(
        {
            "telephone": normaliser_telephone(telephone.reindex(df.index)).to_numpy(),
            "montant": montant.reindex(df.index).round(0).to_numpy(),
            "date": df["created_at"].to_numpy(),
            "reference": normaliser_reference(reference.reindex(df.index)).to_numpy(),
        },
        index=df.index.rename("ticket_id_b"),
    )
    return resultat


# --------------------------------------------------------------------------- #
# Appariement
# --------------------------------------------------------------------------- #


def apparier_telephone_montant_date(
    cles_a_: pd.DataFrame, cles_b_: pd.DataFrame, fenetre_jours: float | None = None
) -> pd.DataFrame:
    """Apparie sur (téléphone, montant) exacts, puis filtre sur l'écart de
    date en jours (`abs(date_b - date_a) <= fenetre_jours`).

    Ne considère que les lignes où téléphone **et** montant sont renseignés
    des deux côtés — un `NaN` ne doit jamais être une clé de jointure.
    """
    fenetre_jours = config.FENETRE_APPARIEMENT_JOURS if fenetre_jours is None else fenetre_jours
    a = cles_a_.dropna(subset=["telephone", "montant"]).reset_index()
    b = cles_b_.dropna(subset=["telephone", "montant"]).reset_index()
    fusion = a.merge(b, on=["telephone", "montant"], suffixes=("_a", "_b"))
    fusion["ecart_jours"] = (fusion["date_b"] - fusion["date_a"]).dt.total_seconds() / 86400
    retenues = fusion[fusion["ecart_jours"].abs() <= fenetre_jours].copy()
    retenues["methode"] = "telephone_montant_date"
    return retenues[["ticket_id_a", "ticket_id_b", "ecart_jours", "methode"]]


def apparier_reference(cles_a_: pd.DataFrame, cles_b_: pd.DataFrame) -> pd.DataFrame:
    """Apparie sur référence de transaction commune (exacte, normalisée)."""
    a = cles_a_.dropna(subset=["reference"]).reset_index()
    b = cles_b_.dropna(subset=["reference"]).reset_index()
    fusion = a.merge(b, on="reference", suffixes=("_a", "_b"))
    fusion["ecart_jours"] = (fusion["date_b"] - fusion["date_a"]).dt.total_seconds() / 86400
    fusion["methode"] = "reference"
    return fusion[["ticket_id_a", "ticket_id_b", "ecart_jours", "methode"]]


def apparier(
    cles_a_: pd.DataFrame, cles_b_: pd.DataFrame, fenetre_jours: float | None = None
) -> pd.DataFrame:
    """Union des deux méthodes d'appariement.

    Une paire trouvée par les deux méthodes à la fois porte `methode =
    "telephone_montant_date+reference"` — c'est le niveau de confiance le
    plus élevé disponible dans ce projet.
    """
    par_tmd = apparier_telephone_montant_date(cles_a_, cles_b_, fenetre_jours)
    par_ref = apparier_reference(cles_a_, cles_b_)

    fusion = par_tmd.merge(
        par_ref, on=["ticket_id_a", "ticket_id_b"], how="outer", suffixes=("_tmd", "_ref")
    )
    a_les_deux = fusion["methode_tmd"].notna() & fusion["methode_ref"].notna()
    fusion["methode"] = np.select(
        [a_les_deux, fusion["methode_tmd"].notna()],
        ["telephone_montant_date+reference", "telephone_montant_date"],
        default="reference",
    )
    fusion["ecart_jours"] = fusion["ecart_jours_tmd"].fillna(fusion["ecart_jours_ref"])
    return fusion[["ticket_id_a", "ticket_id_b", "ecart_jours", "methode"]]


# --------------------------------------------------------------------------- #
# Validation — bruit de fond par permutation
# --------------------------------------------------------------------------- #


def bruit_de_fond(
    cles_a_: pd.DataFrame,
    cles_b_: pd.DataFrame,
    methode: str = "telephone_montant_date",
    fenetre_jours: float | None = None,
    n_permutations: int = 200,
    graine: int = 0,
) -> dict:
    """Taux d'appariement attendu **par hasard**, pour juger si un taux observé
    est un signal ou du bruit — même logique que `chargement.cramer_v` pour
    la représentativité : un nombre seul ne veut rien dire sans un repère de
    ce à quoi ressemblerait l'absence de relation.

    Méthode : mélange **seulement le téléphone** du côté B, en le
    redistribuant aléatoirement entre les tickets — (montant, date) restent
    attachés tels qu'observés. C'est la seule des deux options qui teste
    quelque chose : mélanger (téléphone, montant, date) **conjointement**
    revient à ne permuter que l'étiquette `ticket_id`, sans toucher au
    multi-ensemble des triplets présents dans B — le nombre de coïncidences
    avec A serait alors rigoureusement identique à chaque permutation,
    identique aux données réelles (piège rencontré en écrivant cette
    fonction : `ecart_type` valait 0 sur 100 permutations, signe que rien
    n'était réellement testé). Casser le lien entre téléphone et
    (montant, date) est la seule façon de simuler « ce client-ci n'a pas fait
    cette transaction-là », l'hypothèse nulle qu'on veut chiffrer. Pour la clé
    par référence, on mélange la seule colonne `reference`, pour la même
    raison (une seule colonne à casser).

    Returns
    -------
    dict
        `{"moyenne": float, "ecart_type": float, "n_permutations": int}` du
        nombre de paires trouvées sous permutation.
    """
    rng = np.random.default_rng(graine)
    fonction = apparier_telephone_montant_date if methode == "telephone_montant_date" else apparier_reference
    colonne_a_melanger = "telephone" if methode == "telephone_montant_date" else "reference"

    tailles = []
    for _ in range(n_permutations):
        permute = cles_b_.copy()
        ordre = rng.permutation(len(permute))
        permute[colonne_a_melanger] = cles_b_[colonne_a_melanger].to_numpy()[ordre]
        if methode == "telephone_montant_date":
            paires = fonction(cles_a_, permute, fenetre_jours)
        else:
            paires = fonction(cles_a_, permute)
        tailles.append(len(paires))

    return {
        "moyenne": float(np.mean(tailles)),
        "ecart_type": float(np.std(tailles)),
        "n_permutations": n_permutations,
    }


# --------------------------------------------------------------------------- #
# Périmètre consolidé
# --------------------------------------------------------------------------- #


def tickets_b_non_apparies(tickets_b: pd.DataFrame, paires: pd.DataFrame) -> pd.DataFrame:
    """Sous-ensemble de `tickets_b` dont l'`id` n'apparaît dans aucune paire
    de `paires` (sortie de :func:`apparier`) — la partie de B qui n'est pas
    un doublon détecté du Système A.
    """
    apparies = set(paires["ticket_id_b"])
    return tickets_b[~tickets_b["id"].isin(apparies)].copy()

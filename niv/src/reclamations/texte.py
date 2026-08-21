"""
Normalisation du texte client et taxonomie des motifs de réclamation.

Ce module répond à la question « **pourquoi** les clients se plaignent ». Les
colonnes structurées (`ticket_type_name`) disent seulement *dans quelle catégorie*
le ticket a été rangé — SARA, COMPTE — ce qui est une nomenclature de produit, pas
une cause. Seul le texte écrit par le client dit ce qui s'est réellement passé.

Limite assumée de l'approche par mots-clés
------------------------------------------
La classification implémentée ici est **à base de règles**, et une part du corpus
lui échappe par construction : les clients décrivent le même incident de vingt
façons, en français et en anglais (« n'a pas abouti », « non dénoué », « non
comptabilisé », « inachevé », « it indicated that it went through but... »).

Cette part a été réduite en fouillant le vocabulaire réel du reliquat plutôt
qu'en devinant des formulations : n-grammes sur-représentés chez les non-classés
par rapport aux classés, retenus quand ils couvraient assez de tickets, puis
**vérifiés par lecture d'échantillons** avant d'être codés. Le non-classé passe
ainsi de **46,0 % à 36,0 %** de la base opérationnelle (1 032 tickets), sans
qu'aucune famille ne change de définition — ce sont les mêmes causes, dites
autrement. La grille cherchait `pas arrive` mais pas `jamais arrive`, et
connaissait `login` / `connexion` / `can't access` sans connaître le mot
français **`acceder`** : ces deux oublis expliquaient l'essentiel de l'écart.

Quatre itérations, à rendement franchement décroissant (636, 190, 130, puis
79 tickets) :

1. n-grammes sur-représentés, familles `debit_non_credit` et `acces_otp` ;
2. deuxième passe sur le reliquat restant (`erreur_client`, doubles débits) ;
3. et 4. formulations relevées **en lisant l'échantillon d'audit** lui-même
   (« déficit », « à deux reprises », « compte erroné », « échec d'opération »).

La méthode marche, mais elle a un plancher, et l'audit le montre directement :
sur les 20 textes tirés du reliquat (:func:`echantillon_non_classes`), **5 ne
portent aucune cause exprimée** (« bonjour », « bsr », « compte courant ») —
aucune règle ni aucun modèle ne les classera jamais. Extrapolé, ce quart du
reliquat est un plancher structurel, pas un défaut de réglage. C'est lui que
mesure la ligne :data:`NON_CLASSE`.

Ce plafond est donc **un résultat de l'analyse, pas un préalable technique** : il
constitue l'argument chiffré en faveur d'une classification apprise (NLP) plutôt
que de règles. Pour que cet argument tienne, il faut :

1. mesurer la couverture explicitement -> :func:`couverture` ;
2. auditer manuellement ce qui échappe aux règles -> :func:`echantillon_non_classes`.

Les deux sont faits dans le notebook 04. Toute conclusion tirée des pourcentages
de :func:`classer` doit être présentée comme un **plancher**, jamais comme une
estimation de la vraie répartition.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from . import config

# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #


def normaliser(valeur) -> str:
    """Normalise un texte client pour la mise en correspondance par motifs.

    Opérations : suppression des balises HTML, passage en minuscules,
    suppression des accents (décomposition NFKD puis filtrage ASCII), et
    normalisation des espaces.

    La suppression des accents est indispensable ici : l'export est encodé de
    façon instable (on trouve « effectué », « effectuÃ© » et « effectue » dans le
    même fichier), et les clients écrivent majoritairement sans accents depuis
    un clavier mobile. Sans cette étape, un motif ``débité`` manque la majorité
    des occurrences réelles.

    La suppression des balises HTML (``<p>``, ``<br>``...) est nécessaire depuis
    l'intégration du message d'ouverture récupéré dans l'export conversations
    (`chargement.charger_messages_ouverture`) : ce texte-là, contrairement au
    titre/description du CSV plat, est parfois du HTML enrichi. Sans ce
    nettoyage, ``<br>`` survit à la suppression des accents et pollue le
    vocabulaire du topic modeling (notebook 07) comme un terme « br » à part
    entière — repéré en audit, corrigé ici plutôt que dans chaque appelant.
    """
    if not isinstance(valeur, str):
        return ""
    sans_balises = re.sub(r"<[^>]+>", " ", valeur)
    sans_accent = (
        unicodedata.normalize("NFKD", sans_balises).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"\s+", " ", sans_accent).strip().lower()


#: Motifs d'identifiants à masquer dans le texte client, et leur jeton de remplacement.
#:
#: L'ordre compte : le numéro de compte, de la forme `NNNNN-NNNNN-NNNNNNNNNNN-NN`,
#: doit être reconnu avant les suites de chiffres isolées, sinon il serait découpé
#: en morceaux. Aucun exemple réel n'est cité ici : ce fichier est versionné.
MOTIFS_IDENTIFIANTS: tuple[tuple[str, str], ...] = (
    (r"\b\d{4,5}(?:[-\s]\d{2,}){2,}\b", "[COMPTE]"),
    (r"\b[wW]\d{10,}\b", "[REF]"),
    (r"(?:\+?237[\s-]?)?\b6\d{8}\b", "[TEL]"),
    (r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", "[EMAIL]"),
    (r"\b\d{9,}\b", "[NUM]"),
)


def masquer_identifiants(valeur: str) -> str:
    """Remplace les identifiants d'un texte client par des jetons stables.

    Applique :data:`MOTIFS_IDENTIFIANTS` : numéros de compte, références de
    transaction, numéros de téléphone camerounais, adresses électroniques, puis
    toute suite d'au moins neuf chiffres restante.

    Le sens de la plainte est intégralement préservé — « débité mais [TEL] n'a
    rien reçu » se classe exactement comme l'original. Ce sont les montants qui
    portent l'information analytique, et ils sont à quatre ou cinq chiffres :
    le seuil de neuf chiffres du dernier motif les laisse intacts.

    Warning
    -------
    Cette fonction ne masque **pas les noms de personnes**, qu'aucun motif
    régulier ne reconnaît de façon fiable dans un texte libre. Un texte masqué
    n'est donc pas anonyme : il reste à diffusion restreinte, et n'a pas
    vocation à être versionné.
    """
    if not isinstance(valeur, str):
        return ""
    for motif, jeton in MOTIFS_IDENTIFIANTS:
        valeur = re.sub(motif, jeton, valeur)
    return valeur


def construire_texte(df: pd.DataFrame) -> pd.Series:
    """Concatène titre et description en un texte normalisé unique.

    Les deux champs sont fusionnés car ils sont **complémentaires et non
    redondants** : 70 % des tickets n'ont pas de titre, 54 % pas de description,
    mais seulement 55 % n'ont ni l'un ni l'autre. Certains tickets ne portent
    l'information que dans le titre (« TRANSFERT NON ABOUTI »), d'autres que dans
    la description.
    """
    titre = df["ticket_attributes__default_title_"].fillna("")
    description = df["ticket_attributes__default_description_"].fillna("")
    return (titre + " " + description).map(normaliser)


def enrichir_avec_messages_ouverture(texte_csv: pd.Series, messages: pd.Series) -> pd.Series:
    """Complète le texte construit à partir du CSV plat avec le message
    d'ouverture récupéré dans l'export conversations Intercom, quand il existe.

    Le CSV plat tronque le fil de conversation à l'extraction (§2.4 du
    protocole) ; l'export complémentaire (:func:`chargement.charger_messages_ouverture`)
    porte, pour une partie des tickets, le message réel. Cette fonction
    concatène les deux plutôt que de remplacer l'un par l'autre : le titre et
    la description du CSV restent utiles même quand un message d'ouverture est
    retrouvé, exactement comme titre et description sont déjà complémentaires
    entre eux (:func:`construire_texte`).

    Parameters
    ----------
    texte_csv :
        Sortie de :func:`construire_texte` — déjà normalisée.
    messages :
        Sortie de `chargement.charger_messages_ouverture` — indexée par `id`,
        **pas encore normalisée**. Réindexée sur `texte_csv` ; les tickets sans
        message correspondant reçoivent une chaîne vide.

    Returns
    -------
    Series
        Texte enrichi, normalisé, espaces multiples réduits.
    """
    ajout = messages.reindex(texte_csv.index).fillna("").map(normaliser)
    fusion = (texte_csv + " " + ajout).str.strip()
    return fusion.str.replace(r"\s+", " ", regex=True)


def a_texte_exploitable(texte: pd.Series) -> pd.Series:
    """Booléen : le texte dépasse :data:`config.LONGUEUR_TEXTE_MIN` caractères.

    Le seuil écarte les contenus qui ne portent aucune information sur la cause
    (« Woro Tsoh », « Compte employé », « RECLAMATION »). Sans lui, la couverture
    de la taxonomie est artificiellement dégradée par des textes qu'aucune méthode,
    règles ou NLP, ne pourrait classer.
    """
    return texte.str.len() > config.LONGUEUR_TEXTE_MIN


# --------------------------------------------------------------------------- #
# Taxonomie des motifs
# --------------------------------------------------------------------------- #

#: Familles causales, **dans l'ordre de priorité d'application**.
#:
#: L'ordre compte : les familles sont exclusives et la première qui correspond
#: gagne. `erreur_client` passe avant `debit_non_credit` parce qu'un client qui
#: s'est trompé de numéro décrit *aussi* de l'argent parti sans arriver — l'aveu
#: explicite d'erreur (« au lieu du », « je me suis trompé ») est le signal
#: discriminant, et il doit être testé en premier sous peine d'être absorbé par
#: la famille dominante.
#:
#: Colonne `responsable` : c'est elle qui rend la taxonomie actionnable. Deux
#: familles de même volume mais de responsables différents appellent des
#: corrections différentes — un correctif technique côté passerelle, ou une
#: refonte d'écran côté application.
FAMILLES: tuple[tuple[str, str, str, str], ...] = (
    (
        "erreur_client",
        "Erreur de saisie du client (mauvais bénéficiaire)",
        r"(erreur de (numero|beneficiaire|destinataire|saisie)"
        r"|mauvais (numero|beneficiaire|destinataire)"
        r"|numero (erron|inactif)|beneficiaire ?(erron|eronn?e?|erone)"
        r"|wrongly (made|sent|transfer)|(compte|destinataire) ?erron"
        r"|erreur de benefici|au lieu j|confondu"
        r"|au lieu d[ue]|je me suis tromp|je suis tromp|par erreur"
        r"|erreur de (transaction|transfert|operation)"
        r"|(envoye|transfere) .{0,30}(numero|compte) inconnu"
        r"|wrong (number|recipient)|mistakenly)",
        "UX de l'application",
    ),
    (
        "debit_non_credit",
        "Débité sans que le bénéficiaire soit crédité",
        r"(debit\w+ (mais|et|sans)|debite sans"
        r"|(n.?a |n.?est |pas |jamais )?(pas |jamais )?(ete )?(recu|percu)"
        r"|non (abouti|credit|denoue|comptabilis|finalis|recu)"
        r"|pas abouti|n.?aboutit pas|inacheve"
        r"|n.?a pas (ete )?(approvisionn|credit|verse)"
        r"|argent (n.?est pas|pas) arriv|pas arrive"
        r"|sorti\w* de mon compte|transaction echou|echec (de|du) (transfert|transaction)"
        r"|toujours pas|n.?a rien recu"
        r"|jamais (ete )?(arriv|recu|credit|percu|parvenu)"
        r"|pas encore (ete )?(arriv|recu|credit|parvenu|depos)"
        r"|non (pris en compte|execut|depos)"
        r"|(argent|montant|somme|fonds?) .{0,25}(disparu|volatilis|evapor|manqu)"
        r"|disparu de mon compte"
        r"|(has|have)n.?t received|not received|didn.?t (receive|go through)"
        r"|(was|been|is) debited|debited (but|and|without)"
        r"|not (credited|gone through)|no credit"
        r"|has not been (deposited|credited|received)|\bmissing\b"
        r"|echec d.?(operation|transaction)|operation echou|statut initiated)",
        "Système (banque <-> opérateur)",
    ),
    (
        "acces_otp",
        "Accès bloqué / OTP / authentification",
        r"(\botp\b|code (de )?(verification|confirmation)"
        r"|connexion|connecter|login|log in|mot de passe|password"
        r"|compte (bloqu|desactiv|verrouill)|verrouill"
        r"|reinitialis|can.?t (log|open|access)|deactivat"
        r"|(pas|impossible d.|arrive pas a|parviens pas a) ?acced"
        r"|acces (a|refuse|impossible)|acceder (a )?mon"
        r"|(pas|impossible d.|arrive pas a) ?ouvrir|(appli\w*|compte) ne s.ouvre"
        r"|(arrive|parviens) pas a consulter|plus consulter"
        r"|dispositif de confiance)",
        "Système (authentification)",
    ),
    (
        "debit_injustifie",
        "Débit injustifié, doublé, ou frais contestés",
        r"(sans (aucune )?raison|debit (abusif|inexplique|double)"
        r"|extourne|agios|frais|prelev|retranch"
        r"|solde (incorrect|errone)|deducted|without any reason"
        r"|solde .{0,30}(pas le bon|ne correspond|errone|incorrect|inexact|inferieur)"
        r"|balance .{0,20}(not correct|is wrong)|negative balance"
        r"|(debit|preleve|retir|deduct)\w* .{0,20}deux fois|double deduction"
        r"|(montants?|solde) negatif|retire de mon compte sans"
        r"|solde .{0,25}negatif|compte .{0,15}negatif"
        r"|\bdeficit\b|(money|argent|somme) .{0,15}(was )?(lost|perdu)|il (me )?manque"
        r"|debit\w* (injuste|non justifi|illegal)|injustement (debit|preleve)"
        r"|(debit|preleve|retir|deduct|credit|transaction|recharge|versement)\w*"
        r".{0,40}(deux|2) (fois|reprises)"
        r"|(deux|2) (fois|reprises).{0,40}(debit|preleve|retir|deduct|credit)"
        r"|a tor[dt]|transaction double|sans explication"
        r"|dont je n.?ai pas sollicit)",
        "Système (banque)",
    ),
    (
        "carte",
        "Carte bancaire / distributeur",
        r"(\bcarte\b|\bgab\b|\bdab\b|distributeur|\batm\b)",
        "Système (monétique)",
    ),
    (
        "demande_info",
        "Demande d'information (pas une réclamation)",
        r"(comment (faire|puis|je)|je (voudrais|souhaite) (savoir|connaitre)"
        r"|renseignement|c.?est quoi|how (do|can) i"
        r"|(voir|obtenir|avoir) (mon )?releve|demande de releve"
        r"|releve (du|de) compte|releve bancaire)",
        "Hors périmètre réclamation",
    ),
)

#: Code affecté aux tickets qu'aucune règle ne reconnaît.
NON_CLASSE = "non_classe"


def classer(texte: pd.Series) -> pd.Series:
    """Affecte chaque texte à une famille causale exclusive.

    Applique les motifs de :data:`FAMILLES` dans l'ordre : le premier qui
    correspond fixe la famille, les suivants ne sont testés que sur le reliquat.

    Returns
    -------
    Series
        Code de famille, ou :data:`NON_CLASSE`.
    """
    familles = pd.Series(NON_CLASSE, index=texte.index, dtype="object")
    for code, _libelle, motif, _responsable in FAMILLES:
        reste = familles == NON_CLASSE
        correspond = texte.str.contains(motif, regex=True, na=False)
        familles[reste & correspond] = code
    return familles


def libelles() -> dict[str, str]:
    """Correspondance code de famille -> libellé lisible."""
    d = {code: libelle for code, libelle, _, _ in FAMILLES}
    d[NON_CLASSE] = "Non classé par les règles"
    return d


def responsables() -> dict[str, str]:
    """Correspondance code de famille -> entité responsable de la correction."""
    d = {code: resp for code, _, _, resp in FAMILLES}
    d[NON_CLASSE] = "Indéterminé"
    return d


def couverture(familles: pd.Series) -> pd.DataFrame:
    """Répartition des familles, avec le taux de couverture des règles.

    La ligne :data:`NON_CLASSE` est **volontairement conservée** dans la table.
    La masquer donnerait une répartition apparemment complète alors qu'elle ne
    porte que sur une partie des textes (62 % après l'enrichissement de la
    grille, contre 54 % avant) : c'est précisément l'erreur de lecture que ce
    module cherche à empêcher.
    """
    n = len(familles)
    t = familles.value_counts().rename("effectif").to_frame()
    t["pct"] = (t["effectif"] / n * 100).round(1)
    t["libelle"] = t.index.map(libelles())
    t["responsable"] = t.index.map(responsables())
    return t[["libelle", "responsable", "effectif", "pct"]]


def estimation_corrigee(couverture_par_famille: pd.DataFrame) -> pd.DataFrame:
    """Extrapole l'audit manuel du reliquat (`config.AUDIT_MANUEL`) sur
    l'ensemble des textes non classés.

    Implémente la règle d'intégralité du protocole (§5.1) : chaque famille
    observée dans l'audit — y compris celles qui n'ont qu'un seul texte, et le
    dysfonctionnement hors taxonomie (`config.AUDIT_MANUEL_HORS_TAXONOMIE`) —
    est redistribuée sur le reliquat, aucune n'est écartée. Centralisé ici
    pour qu'un seul calcul serve le notebook qui établit l'audit (04) et tout
    notebook qui en reprend les chiffres clés (06) — les deux dérivaient
    auparavant la même correction séparément, avec un risque de désaccord
    silencieux entre les deux.

    **Les textes sans cause exprimée ne sont pas redistribués.**
    `config.AUDIT_MANUEL_SANS_CAUSE` compte les textes de l'audit qui ne disent
    rien de leur cause (« bonjour », « compte courant ») : les répartir entre
    les familles reviendrait à leur inventer une cause. Ils sortent donc du
    dénominateur, et la part du reliquat qu'ils représentent reste explicitement
    non attribuée — c'est la ligne `pct_reliquat` manquante, assumée.

    Parameters
    ----------
    couverture_par_famille :
        Sortie de :func:`couverture` — colonne `pct`, indexée par code de
        famille, incluant la ligne :data:`NON_CLASSE`.

    Returns
    -------
    DataFrame
        Une ligne par famille de `config.AUDIT_MANUEL`, plus une ligne pour
        `config.AUDIT_MANUEL_HORS_TAXONOMIE`, plus une ligne finale
        « sans cause exprimée » qui porte la part non attribuée :
        `pct_regles`, `pct_reliquat`, `pct_corrige`.
    """
    part_non_classe = couverture_par_famille.loc[NON_CLASSE, "pct"]
    # Dénominateur = seuls les textes de l'audit qui portent une cause. Diviser
    # par la taille totale du tirage diluerait les proportions observées avec
    # des textes dont on sait qu'ils n'ont rien à dire.
    n_avec_cause = config.AUDIT_MANUEL_TAILLE - config.AUDIT_MANUEL_SANS_CAUSE
    part_attribuable = part_non_classe * (n_avec_cause / config.AUDIT_MANUEL_TAILLE)
    lignes = []
    for code, n in config.AUDIT_MANUEL.items():
        regle = couverture_par_famille.loc[code, "pct"]
        part_reliquat = part_attribuable * (n / n_avec_cause)
        lignes.append(
            {
                "famille": libelles()[code],
                "pct_regles": regle,
                "pct_reliquat": round(part_reliquat, 1),
                "pct_corrige": round(regle + part_reliquat, 1),
            }
        )
    for libelle, n in config.AUDIT_MANUEL_HORS_TAXONOMIE.items():
        part_reliquat = part_attribuable * (n / n_avec_cause)
        lignes.append(
            {
                "famille": libelle,
                "pct_regles": 0.0,
                "pct_reliquat": round(part_reliquat, 1),
                "pct_corrige": round(part_reliquat, 1),
            }
        )
    # Ligne explicite plutôt qu'un reliquat silencieux : le lecteur doit voir
    # que la correction ne couvre pas tout le non-classé, et de combien.
    lignes.append(
        {
            "famille": "Sans cause exprimée (non attribuable)",
            "pct_regles": 0.0,
            "pct_reliquat": round(part_non_classe - part_attribuable, 1),
            "pct_corrige": round(part_non_classe - part_attribuable, 1),
        }
    )
    return pd.DataFrame(lignes).set_index("famille")


def echantillon_non_classes(
    texte: pd.Series, familles: pd.Series, n: int = 20, graine: int = 3
) -> pd.Series:
    """Échantillon aléatoire reproductible de textes non classés, pour audit manuel.

    L'audit manuel n'est pas une formalité : c'est lui qui permet de dire si le
    reliquat est *une autre famille* (auquel cas la taxonomie est incomplète) ou
    *la même famille formulée autrement* (auquel cas les règles sous-estiment une
    famille connue). Les deux diagnostics mènent à des suites opposées.

    La graine est fixée pour que l'échantillon audité soit le même à chaque
    exécution du notebook, et donc que le décompte manuel reporté dans le
    commentaire reste vérifiable.
    """
    reste = texte[familles == NON_CLASSE]
    return reste.sample(min(n, len(reste)), random_state=graine)


# --------------------------------------------------------------------------- #
# Extraction d'entités
# --------------------------------------------------------------------------- #

#: Opérateurs de mobile money cités dans le texte.
OPERATEURS = {
    "Orange Money": r"(orange|\bom\b)",
    "MTN MoMo": r"(\bmtn\b|momo)",
    "Autre banque": r"(ecobank|\buba\b|bicec|sgc|virement bancaire)",
}

#: Sens du flux financier décrit par le client.
SENS_FLUX = {
    "Sortant (SARA -> mobile money)": r"(de mon compte sara|depuis (mon compte )?sara"
    r"|sara (money )?(vers|a un|au)|transfert vers (orange|mtn|om)"
    r"|from my sara (money )?account)",
    "Entrant (banque/MoMo -> SARA)": r"(vers mon compte sara|vers (mon compte )?sara money"
    r"|approvisionn\w* mon compte sara|recharge de mon compte"
    r"|to my sara (money )?account)",
}


def detecter(texte: pd.Series, motifs: dict[str, str]) -> pd.DataFrame:
    """Compte les occurrences d'un dictionnaire de motifs dans une série de textes.

    Les motifs ne sont **pas exclusifs** : un même texte peut citer deux
    opérateurs. Le tableau retourné compte donc des mentions, pas des tickets
    répartis, et les pourcentages ne somment pas à 100.

    Warning
    -------
    Un décompte de mentions ne se lit pas comme un taux de défaillance. Si
    Orange Money est cité quatre fois plus que MTN, cela peut refléter un
    problème quatre fois plus fréquent — ou simplement une base de clients
    quatre fois plus large. Sans le volume de transactions par opérateur
    (absent de cet export), l'écart est une **piste**, pas une conclusion.
    """
    n = len(texte)
    lignes = []
    for nom, motif in motifs.items():
        m = texte.str.contains(motif, regex=True, na=False)
        lignes.append({"motif": nom, "mentions": int(m.sum()), "pct": round(m.mean() * 100, 1)})
    return pd.DataFrame(lignes).set_index("motif").assign(base=n)

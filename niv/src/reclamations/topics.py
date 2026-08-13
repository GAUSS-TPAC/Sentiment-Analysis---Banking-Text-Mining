"""
Reconstruction de sous-motifs par topic modeling (TF-IDF + NMF), catégorie par
catégorie.

Complémentaire de :mod:`texte` (classification causale par règles, notebook 04),
pas un remplacement. Les deux méthodes répondent à des questions différentes :

- :mod:`texte` applique une taxonomie **conçue à la main** pour un problème
  précis (l'argent qui quitte SARA sans arriver), sur l'ensemble du périmètre —
  elle est auditable ligne à ligne mais plafonne en rappel (§4.2 du protocole).
- ce module ne présuppose **aucune** taxonomie : il laisse les mots qui
  reviennent ensemble, catégorie par catégorie (``ticket_type_name``), former
  des groupes. Il couvre 100 % des textes par construction (NMF affecte
  toujours un ticket au topic le plus proche), mais le prix de cette
  couverture est qu'un topic n'a pas de sens *a priori* — un humain doit lire
  ses mots-clés et, idéalement, quelques tickets, pour lui donner un nom. C'est
  la même logique d'audit que le reliquat non classé du notebook 04, appliquée
  ici à chaque topic plutôt qu'au seul reliquat.

Choix technique : scikit-learn (TF-IDF + NMF), pas d'embeddings de phrases ni de
modèle à télécharger — cohérent avec le reste du projet (pas de dépendance
lourde, rien qui ne tourne pas de façon identique hors ligne) et suffisant sur
des tickets courts, à vocabulaire métier restreint.

Confidentialité : le corpus vectorisé doit être **masqué au préalable**
(:func:`texte.masquer_identifiants`) — sans cela, un numéro de compte ou de
téléphone peu fréquent peut devenir un terme du vocabulaire TF-IDF et
apparaître en clair dans une liste de mots-clés versionnée. Les fonctions de ce
module ne le font pas elles-mêmes : c'est à l'appelant de masquer avant
d'appeler :func:`topics_par_categorie`, exactement comme le notebook 04 masque
avant d'afficher ou d'écrire le moindre texte.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

# --------------------------------------------------------------------------- #
# Paramètres
# --------------------------------------------------------------------------- #

#: Règle empirique de calibration du nombre de topics : ~1 topic pour 40
#: tickets, borné à [NB_TOPICS_MIN, NB_TOPICS_MAX]. Reprise de l'approche déjà
#: éprouvée dans `niv1/pipeline/phase3_topics.py`.
TICKETS_PAR_TOPIC = 40
NB_TOPICS_MIN = 2
NB_TOPICS_MAX = 8

#: En dessous de ce volume, une catégorie n'a pas assez de texte pour qu'un
#: topic soit autre chose que du bruit ; elle est laissée à `non_modelise`.
TICKETS_MIN_CATEGORIE = 30

#: Nombre de mots-clés retenus pour décrire chaque topic.
TOP_MOTS_PAR_TOPIC = 10

#: Graine de NMF (initialisation + solveur). Fixée pour que les topics soient
#: identiques à chaque exécution, à corpus identique.
GRAINE_NMF = 42

#: Code affecté aux tickets d'une catégorie trop petite pour être modélisée.
NON_MODELISE = -1

#: Mots vides : mots grammaticaux (français) + formules de politesse
#: récurrentes dans une réclamation, qui n'apportent aucune information sur le
#: motif + la liste anglaise de scikit-learn (le corpus est bilingue,
#: cf. protocole §2.4). Les termes métier (sara, orange, mtn, momo, carte...)
#: sont volontairement **conservés** : ce sont eux qui distinguent les topics.
MOTS_VIDES_FR = frozenset(
    """
    a au aux avec ce ces dans de des du elle en et eux il je la le leur lui ma
    mais me même mes moi mon ne nos notre nous on ou par pas pour qu que qui sa
    se ses son sur ta te tes toi ton tu un une vos votre vous c d j l m n s t y
    été étée étées étés étant suis es est sommes êtes sont serai seras sera
    serons serez seront serais serait serions seriez seraient étais était
    étions étiez étaient fus fut fûmes fûtes furent sois soit soyons soyez
    soient fusse fusses fût fussions fussiez fussent ayant eu eue eues eus ai
    as avons avez ont aurai auras aura aurons aurez auront aurais aurait
    aurions auriez auraient avais avait avions aviez avaient eut eûmes eûtes
    eurent aie aies ait ayons ayez aient eusse eusses eût eussions eussiez
    eussent ceci cela cet cette ici ne o soi meme
    ces mon ton son leurs quel quelle quels quelles
    bonjour bonsoir cordialement madame monsieur mademoiselle svp
    veuillez vouloir merci svp prie priere afin cordialement
    """.split()
)
MOTS_VIDES = frozenset(MOTS_VIDES_FR) | frozenset(ENGLISH_STOP_WORDS)


# --------------------------------------------------------------------------- #
# Calibration et ajustement
# --------------------------------------------------------------------------- #


def nombre_topics(n_tickets: int) -> int:
    """Nombre de topics à ajuster pour une catégorie de `n_tickets`.

    Formule bornée : ``n_tickets // TICKETS_PAR_TOPIC``, entre
    :data:`NB_TOPICS_MIN` et :data:`NB_TOPICS_MAX`.
    """
    return max(NB_TOPICS_MIN, min(NB_TOPICS_MAX, n_tickets // TICKETS_PAR_TOPIC))


def ajuster_topics(
    textes: pd.Series, n_topics: int | None = None, top_mots: int = TOP_MOTS_PAR_TOPIC
) -> tuple[pd.Series, list[str]]:
    """Ajuste TF-IDF + NMF sur une série de textes déjà masqués et normalisés.

    Parameters
    ----------
    textes :
        Textes d'une seule catégorie, masqués (:func:`texte.masquer_identifiants`).
    n_topics :
        Nombre de topics. Par défaut, calculé par :func:`nombre_topics`.

    Returns
    -------
    (topic_ids, mots_cles)
        `topic_ids` : topic dominant par ticket (même index que `textes`), ou
        :data:`NON_MODELISE` si le ticket n'a produit aucun terme retenu par le
        vectoriseur (texte réduit à des mots vides ou des termes trop rares).
        `mots_cles` : une chaîne de mots-clés par topic, du plus au moins
        caractéristique.
    """
    if n_topics is None:
        n_topics = nombre_topics(len(textes))

    vectoriseur = TfidfVectorizer(
        min_df=3,
        max_df=0.6,
        ngram_range=(1, 2),
        stop_words=list(MOTS_VIDES),
    )
    X = vectoriseur.fit_transform(textes)
    vocabulaire = np.array(vectoriseur.get_feature_names_out())

    modele = NMF(n_components=n_topics, init="nndsvda", random_state=GRAINE_NMF, max_iter=400)
    poids_tickets = modele.fit_transform(X)  # (n_tickets, n_topics)
    poids_mots = modele.components_  # (n_topics, n_vocabulaire)

    mots_cles = [
        ", ".join(vocabulaire[np.argsort(poids_mots[t])[::-1][:top_mots]])
        for t in range(n_topics)
    ]

    dominant = np.argmax(poids_tickets, axis=1)
    # Un ticket dont le texte ne contient aucun terme retenu produit une ligne
    # nulle dans X : argmax retournerait 0 par défaut, ce qui l'attribuerait à
    # tort au premier topic. On l'exclut explicitement plutôt que de le laisser
    # gonfler silencieusement un topic.
    ligne_nulle = np.asarray(X.sum(axis=1)).ravel() == 0
    ids = pd.Series(dominant, index=textes.index)
    ids[ligne_nulle] = NON_MODELISE
    return ids, mots_cles


def topics_par_categorie(
    df: pd.DataFrame,
    colonne_texte: str,
    colonne_categorie: str,
    min_tickets: int = TICKETS_MIN_CATEGORIE,
) -> tuple[pd.Series, pd.DataFrame]:
    """Ajuste un modèle de topics indépendant par valeur de `colonne_categorie`.

    Chaque catégorie reçoit son propre vocabulaire et son propre nombre de
    topics (:func:`nombre_topics`) : les mots caractéristiques de COMPTE n'ont
    aucune raison d'être ceux de CARTE, et les mélanger diluerait les deux.

    Returns
    -------
    (topic_ids, resume)
        `topic_ids` : Series alignée sur `df.index`, valant
        ``f"{categorie}#{topic_id}"`` pour un ticket modélisé, ou
        ``"non_modelise"`` si la catégorie est sous :data:`TICKETS_MIN_CATEGORIE`
        ou si le ticket n'a produit aucun terme retenu.
        `resume` : une ligne par topic — catégorie, sous-motif (identifiant),
        effectif, part de la catégorie, mots-clés. Prête pour
        `chargement.sauver_table` (aucune cellule ne porte de texte client).
    """
    topic_ids = pd.Series("non_modelise", index=df.index, dtype="object")
    lignes_resume = []

    effectifs = df[colonne_categorie].value_counts()
    for categorie, n_tickets in effectifs.items():
        masque_categorie = df[colonne_categorie] == categorie
        if n_tickets < min_tickets:
            continue

        ids_locaux, mots_cles = ajuster_topics(df.loc[masque_categorie, colonne_texte])
        for t, mc in enumerate(mots_cles):
            effectif = int((ids_locaux == t).sum())
            lignes_resume.append(
                {
                    "categorie": categorie,
                    "sous_motif": f"{categorie}#{t}",
                    "effectif": effectif,
                    "pct_categorie": round(effectif / n_tickets * 100, 1),
                    "mots_cles": mc,
                }
            )
        non_modelises_ici = int((ids_locaux == NON_MODELISE).sum())
        if non_modelises_ici:
            lignes_resume.append(
                {
                    "categorie": categorie,
                    "sous_motif": f"{categorie}#non_modelise",
                    "effectif": non_modelises_ici,
                    "pct_categorie": round(non_modelises_ici / n_tickets * 100, 1),
                    "mots_cles": "(texte sans terme retenu par le vectoriseur)",
                }
            )

        etiquette = ids_locaux.map(
            lambda t: f"{categorie}#{t}" if t != NON_MODELISE else "non_modelise"
        )
        topic_ids.loc[masque_categorie] = etiquette

    resume = pd.DataFrame(lignes_resume).sort_values(
        ["categorie", "effectif"], ascending=[True, False]
    )
    return topic_ids, resume.reset_index(drop=True)

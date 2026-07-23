"""
Phase 3 - Extraction des parametres utiles a la banque : topic modeling.

Objectif : reconstruire ce que le champ `ticket_attributes_Root cause` aurait
du contenir (rempli a 0,02% dans le fichier source) en decouvrant les
sous-thematiques recurrentes A L'INTERIEUR de chaque categorie deja connue
(`ticket_type_name`), a partir du texte lemmatise.

Methode : TF-IDF + NMF (Non-negative Matrix Factorization), categorie par
categorie. On reste volontairement sur scikit-learn (deja courant, aucun
modele a telecharger) plutot que BERTopic : plus robuste ici vu l'instabilite
reseau constatee en Phase 2, et suffisant sur des categories avec un
vocabulaire metier restreint et deja nettoye/lemmatise.

Entree : reclamations_phase2.csv (sortie de la Phase 2, contient deja le
sentiment). Fonctionne aussi sur reclamations_phase1.csv si la Phase 2 n'a
pas encore tourne (le sentiment sera simplement absent des colonnes en sortie).

Sortie :
  - reclamations_phase3.csv : donnees enrichies de topic_id / topic_keywords
  - topics_summary.csv : un topic par ligne, avec ses mots-cles et son volume
"""

import sys

import numpy as np
import pandas as pd

INPUT_CANDIDATES = ["reclamations_phase2.csv", "reclamations_phase1.csv"]
OUTPUT_CSV = "reclamations_phase3.csv"
TOPICS_SUMMARY_CSV = "topics_summary.csv"

MIN_TICKETS_FOR_TOPICS = 30   # en dessous, pas assez de volume pour des topics fiables
MAX_TOPICS = 8
TICKETS_PER_TOPIC = 40        # regle empirique : ~1 topic pour 40 tickets, plafonne a MAX_TOPICS
TOP_WORDS_PER_TOPIC = 8


def load_input() -> pd.DataFrame:
    for path in INPUT_CANDIDATES:
        try:
            df = pd.read_csv(path, low_memory=False)
            print(f"Lecture de {path} ({len(df)} lignes).")
            return df
        except FileNotFoundError:
            continue
    print(f"[!] Aucun fichier d'entree trouve parmi {INPUT_CANDIDATES}.", file=sys.stderr)
    sys.exit(1)


def n_topics_for(n_tickets: int) -> int:
    return max(2, min(MAX_TOPICS, n_tickets // TICKETS_PER_TOPIC))


def topic_model_category(texts: pd.Series):
    """
    Ajuste TF-IDF + NMF sur les textes d'une categorie.
    Retourne (topic_ids par ligne, liste des mots-cles par topic).
    """
    from sklearn.decomposition import NMF
    from sklearn.feature_extraction.text import TfidfVectorizer

    non_empty = texts.fillna("").str.strip() != ""
    if non_empty.sum() < MIN_TICKETS_FOR_TOPICS:
        return pd.Series(-1, index=texts.index), []

    vectorizer = TfidfVectorizer(
        min_df=3,          # ignore les mots presents dans moins de 3 tickets (bruit/typos)
        max_df=0.6,        # ignore les mots presents dans plus de 60% des tickets (trop generiques)
        ngram_range=(1, 2),  # capte aussi des bigrammes ("beneficiaire errone", "compte bloque")
    )
    X = vectorizer.fit_transform(texts.loc[non_empty])
    vocab = np.array(vectorizer.get_feature_names_out())

    k = n_topics_for(non_empty.sum())
    nmf = NMF(n_components=k, init="nndsvda", random_state=42, max_iter=400)
    W = nmf.fit_transform(X)   # (n_tickets, k) : poids de chaque topic par ticket
    H = nmf.components_        # (k, n_vocab)   : poids de chaque mot par topic

    topic_keywords = [
        ", ".join(vocab[np.argsort(H[t])[::-1][:TOP_WORDS_PER_TOPIC]])
        for t in range(k)
    ]

    dominant_topic = np.argmax(W, axis=1)
    result = pd.Series(-1, index=texts.index)
    result.loc[non_empty] = dominant_topic
    return result, topic_keywords


def main():
    df = load_input()

    if "texte_lemmatise" not in df.columns:
        print("[!] Colonne texte_lemmatise absente : la Phase 1 doit avoir tourne "
              "avec spaCy installe.", file=sys.stderr)
        sys.exit(1)

    df["topic_id"] = -1
    df["topic_keywords"] = ""
    summary_rows = []

    categories = df["ticket_type_name"].value_counts()
    for category, n_tickets in categories.items():
        mask = df["ticket_type_name"] == category
        topic_ids, keywords = topic_model_category(df.loc[mask, "texte_lemmatise"])

        if not keywords:
            print(f"  - {category:<28} ({n_tickets:>5} tickets) : trop peu de texte, ignore")
            continue

        df.loc[mask, "topic_id"] = topic_ids
        df.loc[mask, "topic_keywords"] = topic_ids.map(
            lambda t: keywords[t] if t >= 0 else ""
        )

        k = len(keywords)
        print(f"  - {category:<28} ({n_tickets:>5} tickets) : {k} topics")
        for t, kw in enumerate(keywords):
            count = int((topic_ids == t).sum())
            summary_rows.append({
                "categorie": category,
                "topic_id": t,
                "nb_tickets": count,
                "mots_cles": kw,
            })

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nEcrit : {OUTPUT_CSV} ({len(df)} lignes, {len(df.columns)} colonnes)")

    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["categorie", "nb_tickets"], ascending=[True, False]
    )
    summary_df.to_csv(TOPICS_SUMMARY_CSV, index=False)
    print(f"Ecrit : {TOPICS_SUMMARY_CSV} ({len(summary_df)} topics au total)")


if __name__ == "__main__":
    main()

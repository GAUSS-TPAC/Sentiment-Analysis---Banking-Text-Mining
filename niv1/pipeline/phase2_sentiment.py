"""
Phase 2 - Analyse de sentiment des reclamations.

Modele : cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual
  - multilingue (couvre FR/EN, pas besoin de router par langue)
  - entraine sur du texte social informel -> registre proche des reclamations
  - 3 classes : negative / neutral / positive
  - utilise en inference directe (zero-shot), aucune donnee labellisee n'existe
    dans ce jeu de donnees pour entrainer un modele supervise

Important : le modele est applique sur `texte_masque` (nettoye, PII masquee,
non lemmatise) et non sur `texte_lemmatise`. Un modele transformer s'appuie sur
l'ordre des mots et la syntaxe : lemmatiser detruirait ce signal (utile
seulement pour le TF-IDF / topic modeling de la Phase 3).

Sortie : reclamations_phase2.csv = reclamations_phase1.csv + sentiment_label,
sentiment_score (confiance de la classe predite), sentiment_scores_detail
(distribution des 3 classes).
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = ROOT / "data" / "processed" / "reclamations_phase1.csv"
OUTPUT_CSV = ROOT / "data" / "processed" / "reclamations_phase2.csv"
MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"
BATCH_SIZE = 16
MAX_LENGTH = 256  # les reclamations sont courtes ; suffisant et plus rapide que 512


def load_pipeline():
    try:
        import torch
        from transformers import pipeline
    except ImportError as exc:
        print(f"[!] Dependance manquante : {exc}. "
              f"Installer via requirements_phase2.txt + requirements_phase1.txt (torch CPU).",
              file=sys.stderr)
        sys.exit(1)

    device = 0 if torch.cuda.is_available() else -1
    return pipeline(
        "sentiment-analysis",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        device=device,
        truncation=True,
        max_length=MAX_LENGTH,
        top_k=None,  # renvoie les scores des 3 classes, pas juste la meilleure
        # revision="main" fixee explicitement : sans ca, transformers resout
        # vers la revision refs/pr/5 (PR du bot de conversion safetensors) qui
        # retelecharge inutilement ~1 Go de poids deja presents sous main.
        revision="main",
        model_kwargs={"use_safetensors": False},
    )


def run_sentiment(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    clf = load_pipeline()

    texts = df[text_col].fillna("").tolist()
    # textes vides -> pas d'inference, on les marquera a part
    non_empty_idx = [i for i, t in enumerate(texts) if t.strip()]
    non_empty_texts = [texts[i] for i in non_empty_idx]

    print(f"Inference sur {len(non_empty_texts)} textes (batch_size={BATCH_SIZE}) ...")
    results = clf(non_empty_texts, batch_size=BATCH_SIZE)

    labels = [""] * len(df)
    scores = [None] * len(df)
    details = [""] * len(df)

    for pos, res in zip(non_empty_idx, results):
        # res = liste de dicts {label, score} pour les 3 classes
        best = max(res, key=lambda d: d["score"])
        labels[pos] = best["label"]
        scores[pos] = round(best["score"], 4)
        details[pos] = ";".join(f"{d['label']}:{round(d['score'], 4)}" for d in res)

    df = df.copy()
    df["sentiment_label"] = labels
    df["sentiment_score"] = scores
    df["sentiment_scores_detail"] = details
    return df


def main():
    print(f"Lecture de {INPUT_CSV} ...")
    df = pd.read_csv(INPUT_CSV, low_memory=False)

    df = run_sentiment(df, text_col="texte_masque")

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Ecrit : {OUTPUT_CSV} ({len(df)} lignes, {len(df.columns)} colonnes)")

    print("\nDistribution globale du sentiment :")
    print(df["sentiment_label"].value_counts())

    print("\nSentiment par categorie (ticket_type_name) :")
    print(
        df.groupby("ticket_type_name")["sentiment_label"]
        .value_counts(normalize=True)
        .unstack()
        .round(3)
    )


if __name__ == "__main__":
    main()

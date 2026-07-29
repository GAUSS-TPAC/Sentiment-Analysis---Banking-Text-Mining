"""
Phase 4 - Restitution : KPIs croisant categorie x sentiment x canal x periode x topic,
+ montants en jeu (objectif A + objectif B reunis).

Entree : reclamations_phase3.csv (sortie de la Phase 3, qui contient deja
sentiment_label de la Phase 2 et topic_id/topic_keywords de la Phase 3).

Sorties (CSV, exploitables directement dans Excel/PowerBI ou pour un futur
dashboard) :
  - kpi_sentiment_categorie.csv   : % negatif/neutre/positif par categorie
  - kpi_sentiment_mensuel.csv     : evolution mensuelle du sentiment
  - kpi_sentiment_canal.csv       : % negatif/neutre/positif par canal
  - kpi_montants.csv              : montant moyen/median/total par categorie
  - kpi_topics_sentiment.csv      : pour chaque topic (sous-motif), volume +
                                     % negatif -> les "points de douleur" les
                                     plus precis et les plus frequents
"""

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
_processed = ROOT / "data" / "processed"
INPUT_CSV = _processed / "reclamations_phase3.csv"


def parse_montant(value) -> float:
    """Nettoie ticket_attributes_Montant en XAF (espaces, virgules, texte) -> float ou NaN."""
    if pd.isna(value):
        return float("nan")
    digits = re.sub(r"[^\d]", "", str(value))
    return float(digits) if digits else float("nan")


def main():
    print(f"Lecture de {INPUT_CSV} ...")
    df = pd.read_csv(INPUT_CSV, low_memory=False)

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["mois"] = df["created_at"].dt.to_period("M").astype(str)
    df["montant_xaf"] = df["ticket_attributes_Montant en XAF"].map(parse_montant)

    has_sentiment = "sentiment_label" in df.columns
    has_topics = "topic_id" in df.columns

    if not has_sentiment:
        print("[!] Pas de colonne sentiment_label : lancer phase2_sentiment.py d'abord "
              "pour des KPIs complets. Les KPIs de volume/montant sont generes quand meme.")

    # --- 1. sentiment par categorie -----------------------------------------
    if has_sentiment:
        kpi_cat = (
            df.groupby("ticket_type_name")["sentiment_label"]
            .value_counts(normalize=True)
            .unstack()
            .fillna(0)
            .round(3)
        )
        kpi_cat["nb_tickets"] = df.groupby("ticket_type_name").size()
        kpi_cat = kpi_cat.sort_values("nb_tickets", ascending=False)
        kpi_cat.to_csv(_processed / "kpi_sentiment_categorie.csv")
        print("\n=== Sentiment par categorie ===")
        print(kpi_cat.to_string())

        # --- 2. sentiment mensuel -------------------------------------------
        kpi_mois = (
            df.groupby("mois")["sentiment_label"]
            .value_counts(normalize=True)
            .unstack()
            .fillna(0)
            .round(3)
        )
        kpi_mois["nb_tickets"] = df.groupby("mois").size()
        kpi_mois.to_csv(_processed / "kpi_sentiment_mensuel.csv")

        # --- 3. sentiment par canal -------------------------------------------
        kpi_canal = (
            df.groupby("channel")["sentiment_label"]
            .value_counts(normalize=True)
            .unstack()
            .fillna(0)
            .round(3)
        )
        kpi_canal["nb_tickets"] = df.groupby("channel").size()
        kpi_canal = kpi_canal.sort_values("nb_tickets", ascending=False)
        kpi_canal.to_csv(_processed / "kpi_sentiment_canal.csv")
        print("\n=== Sentiment par canal ===")
        print(kpi_canal.to_string())

    # --- 4. montants par categorie -------------------------------------------
    kpi_montant = (
        df.groupby("ticket_type_name")["montant_xaf"]
        .agg(montant_moyen="mean", montant_median="median", montant_total="sum",
             nb_valeurs="count")
        .round(0)
        .sort_values("montant_total", ascending=False)
    )
    kpi_montant.to_csv(_processed / "kpi_montants.csv")
    print("\n=== Montants (XAF) par categorie ===")
    print(kpi_montant.to_string())

    # --- 5. topics x sentiment : les points de douleur precis ----------------
    if has_topics and has_sentiment:
        topic_mask = df["topic_id"] >= 0
        kpi_topics = (
            df.loc[topic_mask]
            .groupby(["ticket_type_name", "topic_id", "topic_keywords"])
            .agg(
                nb_tickets=("sentiment_label", "size"),
                pct_negatif=("sentiment_label", lambda s: round((s == "negative").mean(), 3)),
            )
            .reset_index()
            .sort_values(["nb_tickets", "pct_negatif"], ascending=[False, False])
        )
        kpi_topics.to_csv(_processed / "kpi_topics_sentiment.csv", index=False)

        print("\n=== Top 10 points de douleur (volume x %negatif) ===")
        top_pain = kpi_topics[kpi_topics["nb_tickets"] >= 15].sort_values(
            "pct_negatif", ascending=False
        ).head(10)
        print(top_pain.to_string(index=False))
    elif has_topics:
        print("[!] topic_id present mais sentiment_label absent : "
              "kpi_topics_sentiment.csv non genere (necessite les deux).")
    else:
        print("[!] Pas de colonne topic_id : lancer phase3_topics.py d'abord "
              "pour le detail par sous-motif.")

    print(f"\nKPI files written to {_processed}")


if __name__ == "__main__":
    main()

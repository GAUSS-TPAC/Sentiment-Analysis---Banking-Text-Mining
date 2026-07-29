# Sentiment Analysis & Text Mining — Banking Customer Complaints

NLP pipeline applied to customer complaint tickets exported from Intercom.
Four sequential phases (cleaning → sentiment → topic modeling → reporting) feed a Streamlit dashboard for business teams.

---

## Background

Customer complaints flow through multiple channels (web, mobile, branch) and are tracked in Intercom. The `Root cause` field was filled in less than **0.02 %** of tickets. This project automatically reconstructs complaint sub-themes and qualifies the sentiment of each ticket to produce actionable KPIs — without any labeled training data.

---

## Pipeline overview

```
data/raw/SRC_Intercom_Reclamation_*.csv
        │
        ▼
┌──────────────────────────────┐
│  Phase 1 — Cleaning          │  pipeline/phase1_cleaning.py
│  · Encoding fix (0x1A → ')   │
│  · PII extraction & masking  │  → <TEL> <MONTANT> <REF> <DATE>
│  · Language detection        │  fr / en / other
│  · Lemmatisation (spaCy)     │
└────────────┬─────────────────┘
             │ data/processed/reclamations_phase1.csv
             ▼
┌──────────────────────────────┐
│  Phase 2 — Sentiment         │  pipeline/phase2_sentiment.py
│  · XLM-RoBERTa multilingual  │  cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual
│  · Zero-shot inference       │  negative / neutral / positive
│  · Confidence score          │
└────────────┬─────────────────┘
             │ data/processed/reclamations_phase2.csv
             ▼
┌──────────────────────────────┐
│  Phase 3 — Topic Modeling    │  pipeline/phase3_topics.py
│  · TF-IDF + NMF              │  per complaint category
│  · Auto-calibrated topics    │  ~1 topic / 40 tickets, max 8
│  · Bigrams enabled           │  "compte bloqué", "virement erroné"…
└────────────┬─────────────────┘
             │ data/processed/reclamations_phase3.csv
             │ data/processed/topics_summary.csv
             ▼
┌──────────────────────────────┐
│  Phase 4 — KPI Reporting     │  pipeline/phase4_reporting.py
│  · Sentiment × category      │
│  · Monthly trend             │
│  · Sentiment × channel       │
│  · Amounts (XAF) by category │
│  · Topics × sentiment        │  → pain points
└──────────────────────────────┘
             │ data/processed/kpi_*.csv
             ▼
┌──────────────────────────────┐
│  Streamlit Dashboard         │  app.py
│  · Auto column profiler      │  works with any similar CSV/Excel
│  · Business dashboards       │
│  · PDF guide export          │
└──────────────────────────────┘
```

---

## Phase details

### Phase 1 — Cleaning & preprocessing

| Step | Detail |
|---|---|
| Encoding fix | `0x1A` (SUB char) systematically replaces French apostrophes in Intercom exports |
| PII masking | Phone numbers, amounts, transaction refs, dates replaced by neutral tokens |
| Language detection | `langdetect` on the masked text → `fr` / `en` / `other` |
| Lemmatisation | spaCy (`fr_core_news_sm` / `en_core_web_sm`) — business terms protected (`sara`, `orange`, `momo`, `mtn`…) |

### Phase 2 — Sentiment analysis

- **Model**: [`cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`](https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual)
- Applied on `texte_masque` (not lemmatised — transformers rely on word order and syntax)
- GPU auto-detected; falls back to CPU
- Outputs: `sentiment_label` + `sentiment_score` (confidence) + per-class score breakdown

### Phase 3 — Topic modeling

- **TF-IDF + NMF** (scikit-learn), fitted independently per complaint category
- Number of topics: `max(2, min(8, n_tickets // 40))`
- Bigrams enabled to capture business phrases
- `topic_id = -1` for tickets with insufficient text

### Phase 4 — KPI reporting

| Output file | Content |
|---|---|
| `kpi_sentiment_categorie.csv` | % negative / neutral / positive per complaint type |
| `kpi_sentiment_mensuel.csv` | Monthly sentiment trend |
| `kpi_sentiment_canal.csv` | Sentiment by channel (web, mobile, branch…) |
| `kpi_montants.csv` | Mean / median / total amount (XAF) per category |
| `kpi_topics_sentiment.csv` | % negative per topic — ranked pain points |

---

## Dashboard (`app.py`)

```bash
streamlit run app.py
```

Loads the richest available processed file (`reclamations_phase3.csv` first), or accepts any similar CSV/Excel via the sidebar.

| Tab | Content |
|---|---|
| Overview | Fill rate per column, global metrics |
| Column profiler | Auto-adapted chart per column type (bar, boxplot, timeline…) |
| Business dashboards | Sentiment global + by category + by channel, monthly trend, heatmap, resolution rate, amounts, topics |

> **Visualisation rule**: no category is ever truncated — no "Top N", no "Other" bucket, even for categories below 0.1 %.

---

## Project structure

```
.
├── README.md
├── .gitignore
├── requirements.txt
├── app.py                          # Streamlit dashboard
│
├── pipeline/
│   ├── phase1_cleaning.py          # Encoding, PII, language, lemmatisation
│   ├── phase2_sentiment.py         # Sentiment (XLM-RoBERTa)
│   ├── phase3_topics.py            # Topic modeling (TF-IDF + NMF)
│   └── phase4_reporting.py         # KPI generation
│
├── notebooks/
│   ├── 01_exploration_toutes_colonnes.ipynb
│   ├── 02_nettoyage.ipynb
│   ├── 03_sentiment.ipynb
│   ├── 04_topics.ipynb
│   ├── 05_reporting.ipynb
│   └── viz_utils.py                # Shared visualisation helpers
│
├── docs/
│   ├── rapport_analyse_sentiment.md
│   └── presentations/
│       ├── 00_catalogue_colonnes.md
│       ├── 01_exploration.md
│       ├── 02_nettoyage.md
│       ├── 03_sentiment.md
│       ├── 04_topics.md
│       └── 05_reporting.md
│
└── data/                           # gitignored — never committed
    ├── raw/                        # Original Intercom exports
    └── processed/                  # Pipeline outputs (phase1-3 CSV, KPIs)
```

---

## Installation

```bash
pip install -r requirements.txt

# spaCy language models (Phase 1)
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
```

---

## Usage

Place the Intercom export in `data/raw/`, then run the phases in order:

```bash
python pipeline/phase1_cleaning.py
python pipeline/phase2_sentiment.py
python pipeline/phase3_topics.py
python pipeline/phase4_reporting.py

# Launch the dashboard
streamlit run app.py
```

---

## Tech stack

| Layer | Tools |
|---|---|
| Preprocessing | `pandas`, `spaCy`, `langdetect` |
| Sentiment | `transformers` (HuggingFace), `torch` |
| Topic modeling | `scikit-learn` (TF-IDF + NMF) |
| Dashboard | `streamlit`, `matplotlib` |
| PDF export | `reportlab` |

---

## Notes

- **Sensitive data**: CSV files contain customer PII (names, phone numbers, amounts). They are excluded from version control via `.gitignore`.
- **PII handling**: masked in the NLP pipeline; raw values preserved in dedicated columns (`pii_telephones`, `pii_montants`…) for audit purposes.
- **Zero-shot model**: sentiment is inferred without fine-tuning on banking data. Results should be validated against a manually annotated sample before production use.

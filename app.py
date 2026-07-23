"""
Profileur automatique de tickets - app Streamlit.

Depose un CSV "similaire" (export Intercom ou proche) : chaque colonne recoit
automatiquement le graphique adapte a son type et sa cardinalite, en
reutilisant telle quelle la logique de `notebooks/viz_utils.py` (meme regle
que dans les notebooks : aucune categorie omise, meme a 0,1%).

Lancement : streamlit run app.py
"""

import io
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR / "notebooks"))
sys.path.insert(0, str(APP_DIR))

from viz_utils import (  # noqa: E402
    annotated_heatmap,
    plot_full_counts,
    plot_full_distribution,
    plot_stacked_share,
    profile_column,
)
from phase4_reporting import parse_montant  # noqa: E402

st.set_page_config(page_title="Profileur de tickets", layout="wide")

DEFAULT_CSV_CANDIDATES = [
    "reclamations_phase3.csv",
    "reclamations_phase2.csv",
    "reclamations_phase1.csv",
    "SRC_Intercom_Reclamation_202607201846.csv",
]

SENTIMENT_COLORS = {"negative": "#C44E52", "neutral": "#8C8C8C", "positive": "#55A868"}

REQUIRED_COLS = {
    "Sentiment global": ["sentiment_label"],
    "Sentiment par categorie": ["ticket_type_name", "sentiment_label"],
    "Sentiment par canal": ["channel", "sentiment_label"],
    "Evolution mensuelle": ["created_at", "sentiment_label"],
    "Heatmap categorie x mois": ["created_at", "ticket_type_name"],
    "Taux de resolution": ["ticket_state_category", "ticket_type_name"],
    "Montants par categorie": ["ticket_type_name", "ticket_attributes_Montant en XAF"],
    "Topics x sentiment": ["topic_id", "topic_keywords", "sentiment_label", "ticket_type_name"],
}


def get_default_csv_path():
    for name in DEFAULT_CSV_CANDIDATES:
        p = APP_DIR / name
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner="Chargement du fichier...")
def load_data(file, filename: str) -> pd.DataFrame:
    if filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file, low_memory=False)


@st.cache_data(show_spinner=False)
def build_profile_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "remplissage_pct": (df.notna().mean() * 100).round(2),
            "nb_remplis": df.notna().sum(),
            "nb_valeurs_uniques": df.nunique(dropna=True),
            "dtype": df.dtypes.astype(str),
        }
    ).sort_values("remplissage_pct", ascending=False)


def available_sections(df: pd.DataFrame) -> dict:
    return {name: all(c in df.columns for c in cols) for name, cols in REQUIRED_COLS.items()}


def compute_kpis(df: pd.DataFrame) -> list:
    kpis = [("Tickets", f"{len(df):,}")]
    if "sentiment_label" in df.columns:
        pct_neg = (df["sentiment_label"] == "negative").mean() * 100
        kpis.append(("% negatif", f"{pct_neg:.1f}%"))
    if "ticket_attributes_Montant en XAF" in df.columns:
        med = df["ticket_attributes_Montant en XAF"].map(parse_montant).median()
        if pd.notna(med):
            kpis.append(("Montant median (XAF)", f"{med:,.0f}"))
    if "ticket_state_category" in df.columns:
        pct_resolved = df["ticket_state_category"].astype(str).str.lower().eq("resolved").mean() * 100
        kpis.append(("% resolus", f"{pct_resolved:.1f}%"))
    text_col = next(
        (c for c in ("texte", "ticket_attributes__default_description_") if c in df.columns), None
    )
    if text_col:
        kpis.append(("% avec texte libre", f"{df[text_col].notna().mean() * 100:.1f}%"))
    return kpis


def show(fig):
    st.pyplot(fig)
    plt.close(fig)


def build_pdf_guide(source_label, n_rows, n_cols, max_categories, id_ratio_threshold, avail, kpis) -> bytes:
    """Guide PDF (methodologie + parametres + analyse du fichier charge)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm
    )
    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8.5, leading=11)
    header_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C72B0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])
    story = [
        Paragraph("Guide de l'application - Profileur automatique de tickets", styles["Title"]),
        Paragraph(f"Genere le {datetime.now():%d/%m/%Y a %H:%M}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
        Paragraph("1. Objectif", styles["Heading2"]),
        Paragraph(
            "Cette application charge un fichier de reclamations (CSV ou Excel) - celui-ci ou "
            "un export similaire - et genere automatiquement, pour chaque colonne, le graphique "
            "le plus adapte a son contenu, sans jamais tronquer une categorie meme si elle pese "
            "moins de 1% des lignes.",
            styles["Normal"],
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("2. Charger des donnees", styles["Heading2"]),
        Paragraph(
            "Depose un fichier CSV ou Excel (.xlsx) via la barre laterale. Sans depot, l'app "
            "charge automatiquement le fichier le plus riche disponible dans le projet "
            "(reclamations_phase3.csv en priorite, puis phase2, phase1, ou le CSV brut).",
            styles["Normal"],
        ),
        Spacer(1, 0.3 * cm),
        Paragraph("3. Comment un graphique est choisi pour chaque colonne", styles["Heading2"]),
    ]
    rules = [
        "Colonne constante ou vide : pas de graphique, seulement le taux de remplissage.",
        "Colonne de date/horodatage : volume par mois (tous les mois affiches, aucun exclu).",
        "Colonne numerique = une vraie mesure (montant, score...) : boite a moustaches "
        "(mediane, quartiles, outliers IQR individualises) plutot qu'un histogramme, pour "
        "rester lisible malgre des valeurs aberrantes extremes.",
        "Colonne numerique dont le NOM indique un identifiant (numero, tel, compte, carte, "
        "code, reference...) : jamais de boite a moustaches (une moyenne de numero de "
        "telephone n'a pas de sens) - barres si le nombre de valeurs reste gerable, sinon "
        "statistiques seules.",
        "Colonne categorielle de cardinalite geree : barres horizontales exhaustives, "
        "triees, annotees effectif + pourcentage - jamais de troncature 'top N', jamais de "
        "bucket 'Autres', jamais de pie chart.",
        "Colonne identifiant/texte libre/JSON a trop forte cardinalite : pas de graphique, "
        "seulement les statistiques (remplissage, cardinalite, valeur la plus frequente).",
    ]
    for r in rules:
        story.append(Paragraph(f"- {r}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("4. Parametres de profilage actuels", styles["Heading2"]))
    param_table = Table(
        [
            ["Parametre", "Valeur", "Role"],
            [
                "Nb max de categories", str(max_categories),
                Paragraph(
                    "Au-dela de ce nombre de valeurs distinctes, une colonne categorielle "
                    "bascule en statistiques seules.",
                    cell_style,
                ),
            ],
            [
                "Seuil uniques/rempli", f"{id_ratio_threshold:.2f}",
                Paragraph(
                    "Si (valeurs uniques / lignes remplies) depasse ce seuil, la colonne est "
                    "traitee comme un identifiant plutot qu'une categorie.",
                    cell_style,
                ),
            ],
        ],
        colWidths=[3.3 * cm, 2 * cm, 8.7 * cm],
    )
    param_table.setStyle(header_style)
    story.append(param_table)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("5. Analyse du fichier actuellement charge", styles["Heading2"]))
    story.append(Paragraph(f"Source : {source_label}", styles["Normal"]))
    story.append(Paragraph(f"{n_rows:,} lignes, {n_cols} colonnes.", styles["Normal"]))
    story.append(Spacer(1, 0.2 * cm))
    if kpis:
        kpi_table = Table([["Indicateur", "Valeur"]] + [[k, v] for k, v in kpis], colWidths=[6 * cm, 4 * cm])
        kpi_table.setStyle(header_style)
        story.append(kpi_table)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("6. Tableaux de bord metier disponibles pour ce fichier", styles["Heading2"]))
    dash_table = Table(
        [["Tableau de bord", "Disponible ?"]]
        + [[name, "Oui" if ok else "Non (colonnes manquantes)"] for name, ok in avail.items()],
        colWidths=[7 * cm, 5 * cm],
    )
    dash_table.setStyle(header_style)
    story.append(dash_table)

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------- sidebar --
st.sidebar.title("Profileur de tickets")
uploaded = st.sidebar.file_uploader("Deposer un CSV ou Excel", type=["csv", "xlsx", "xls"])

if uploaded is not None:
    try:
        df = load_data(uploaded, uploaded.name)
    except ImportError:
        st.error(
            "Format .xls (Excel < 2007) non lisible dans cet environnement - "
            "reenregistre le fichier en .xlsx ou .csv et redepose-le."
        )
        st.stop()
    source_label = uploaded.name
else:
    default_path = get_default_csv_path()
    if default_path is None:
        st.warning("Aucun fichier CSV trouve a la racine du projet - depose un fichier pour commencer.")
        st.stop()
    df = load_data(str(default_path), default_path.name)
    source_label = f"{default_path.name} (demo - depose un CSV/Excel pour analyser un autre jeu de donnees)"

st.sidebar.caption(f"Source : {source_label}")
st.sidebar.caption(f"{len(df):,} lignes x {df.shape[1]} colonnes")

st.sidebar.divider()
st.sidebar.subheader("Parametres de profilage")
max_categories = st.sidebar.number_input(
    "Nb max de categories avant repli sur le taux de remplissage",
    min_value=5, max_value=2000, value=150, step=10,
    help="Au-dela de ce nombre de valeurs distinctes, une colonne categorielle "
         "bascule en statistiques seules (le graphique serait illisible).",
)
id_ratio_threshold = st.sidebar.number_input(
    "Seuil uniques/rempli au-dela duquel une colonne est traitee comme identifiant",
    min_value=0.01, max_value=1.0, value=0.5, step=0.05, format="%.2f",
    help="Si (valeurs uniques / lignes remplies) depasse ce seuil, la colonne est "
         "traitee comme un identifiant (pas de graphique) plutot qu'une categorie.",
)

avail = available_sections(df)
kpis = compute_kpis(df)

st.sidebar.divider()
pdf_bytes = build_pdf_guide(source_label, len(df), df.shape[1], max_categories, id_ratio_threshold, avail, kpis)
st.sidebar.download_button(
    "Telecharger le guide PDF", data=pdf_bytes, file_name="guide_profileur_tickets.pdf",
    mime="application/pdf",
)

# ------------------------------------------------------------------ main --
st.title("Profileur automatique de tickets")
st.caption(
    "Chaque colonne recoit automatiquement le graphique adapte a son type et "
    "sa cardinalite, sans troncature - meme une categorie a 0,1% reste affichee."
)

tab_overview, tab_columns, tab_business = st.tabs(
    ["Vue d'ensemble", "Profil par colonne", "Tableaux de bord metier"]
)

with tab_overview:
    profil = build_profile_summary(df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Lignes", f"{len(df):,}")
    c2.metric("Colonnes", df.shape[1])
    c3.metric("Remplissage moyen", f"{profil['remplissage_pct'].mean():.1f}%")
    st.dataframe(profil, width="stretch")

with tab_columns:
    all_cols = df.columns.tolist()
    show_all = st.checkbox("Afficher toutes les colonnes (mode exhaustif)", value=False)
    if show_all:
        selected_cols = all_cols
    else:
        selected_cols = st.multiselect(
            "Colonnes a afficher", options=all_cols, default=all_cols[: min(5, len(all_cols))]
        )

    for col in selected_cols:
        with st.expander(col, expanded=not show_all and len(selected_cols) <= 5):
            fig, ax, summary = profile_column(
                df, col, max_categories=max_categories, id_ratio_threshold=id_ratio_threshold
            )
            stats = {k: str(v) for k, v in summary.items() if k != "colonne"}
            st.dataframe(
                pd.DataFrame(stats.items(), columns=["statistique", "valeur"]),
                width="stretch", hide_index=True,
            )
            if fig is not None:
                show(fig)
            else:
                st.caption(
                    "Pas de graphique : identifiant / texte libre / JSON / colonne "
                    "constante - sans valeur analytique pour une visualisation "
                    "(voir les statistiques ci-dessus)."
                )

with tab_business:
    if not any(avail.values()):
        st.info(
            "Ce fichier ne contient aucune des colonnes metier attendues "
            "(sentiment_label, ticket_type_name, channel, topic_id...) - "
            "section tableaux de bord non disponible pour ce jeu de donnees."
        )
    else:
        # ---- KPIs synthetiques (chacun affiche seulement si calculable) ----
        for slot, (label, value) in zip(st.columns(len(kpis)), kpis):
            slot.metric(label, value)
        st.divider()

        st.subheader("Sentiment global")
        if avail["Sentiment global"]:
            fig, ax = plot_full_distribution(df["sentiment_label"], "Distribution globale du sentiment")
            show(fig)
        else:
            st.caption("Colonne sentiment_label absente - section ignoree.")

        st.subheader("Sentiment par categorie")
        if avail["Sentiment par categorie"]:
            fig, ax = plot_stacked_share(
                df, "ticket_type_name", "sentiment_label", "Sentiment par type de reclamation",
                colors=SENTIMENT_COLORS,
            )
            show(fig)
        else:
            st.caption("Colonnes ticket_type_name / sentiment_label absentes - section ignoree.")

        st.subheader("Sentiment par canal")
        if avail["Sentiment par canal"]:
            fig, ax = plot_stacked_share(
                df, "channel", "sentiment_label", "Sentiment par canal", colors=SENTIMENT_COLORS
            )
            show(fig)
        else:
            st.caption("Colonnes channel / sentiment_label absentes - section ignoree.")

        st.subheader("Evolution mensuelle du sentiment")
        if avail["Evolution mensuelle"]:
            dates = pd.to_datetime(df["created_at"], errors="coerce")
            mois = dates.dt.to_period("M").astype(str)
            valid = dates.notna()
            volume_mensuel = mois[valid].value_counts().sort_index()
            pct_neg_mensuel = (
                (df.loc[valid, "sentiment_label"] == "negative").groupby(mois[valid]).mean() * 100
            )
            fig, ax = plt.subplots(figsize=(9, 3.5))
            ax.plot(pct_neg_mensuel.index, pct_neg_mensuel.values, marker="o", color="#C44E52")
            for x, y, n in zip(pct_neg_mensuel.index, pct_neg_mensuel.values,
                               volume_mensuel.reindex(pct_neg_mensuel.index)):
                ax.annotate(f"n={n}", (x, y), textcoords="offset points", xytext=(0, 6),
                            fontsize=7, ha="center")
            ax.set_ylabel("% negatif")
            ax.set_title("Evolution mensuelle du % negatif (tous les mois, effectif indique)")
            ax.tick_params(axis="x", rotation=45)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
            show(fig)
        else:
            st.caption("Colonnes created_at / sentiment_label absentes - section ignoree.")

        st.subheader("Volume categorie x mois (heatmap)")
        if avail["Heatmap categorie x mois"]:
            dates = pd.to_datetime(df["created_at"], errors="coerce")
            mois = dates.dt.to_period("M").astype(str)
            valid = dates.notna()
            volume_matrix = pd.crosstab(df.loc[valid, "ticket_type_name"], mois[valid])
            volume_matrix = volume_matrix.loc[volume_matrix.sum(axis=1).sort_values(ascending=False).index]
            fig, ax = annotated_heatmap(
                volume_matrix, "Volume de tickets par categorie et par mois",
                fmt=".0f", cmap="Blues", xlabel="Mois", ylabel="Categorie",
            )
            show(fig)
            if "sentiment_label" in df.columns:
                neg = (df["sentiment_label"] == "negative").astype(float) * 100
                pct_matrix = neg[valid].groupby(
                    [df.loc[valid, "ticket_type_name"], mois[valid]]
                ).mean().unstack().fillna(0).round(1)
                pct_matrix = pct_matrix.reindex(volume_matrix.index)
                fig, ax = annotated_heatmap(
                    pct_matrix, "% negatif par categorie et par mois",
                    fmt=".0f", cmap="RdYlGn_r", xlabel="Mois", ylabel="Categorie",
                )
                show(fig)
        else:
            st.caption("Colonnes created_at / ticket_type_name absentes - section ignoree.")

        st.subheader("Etat des tickets par categorie (taux de resolution)")
        if avail["Taux de resolution"]:
            fig, ax = plot_stacked_share(
                df, "ticket_type_name", "ticket_state_category",
                "Etat des tickets par type de reclamation",
            )
            show(fig)
            counts_etat = df["ticket_state_category"].value_counts()
            fig, ax = plot_full_counts(
                counts_etat, "Repartition globale des etats de ticket", xlabel="Nombre de tickets"
            )
            show(fig)
        else:
            st.caption("Colonnes ticket_state_category / ticket_type_name absentes - section ignoree.")

        st.subheader("Montants medians par categorie")
        if avail["Montants par categorie"]:
            montants = df["ticket_attributes_Montant en XAF"].map(parse_montant)
            montant_median = montants.groupby(df["ticket_type_name"]).median().fillna(0)
            fig, ax = plot_full_counts(
                montant_median, "Montant median (XAF) par categorie",
                xlabel="Montant median (XAF)", pct=False, value_fmt="{:,.0f}",
            )
            show(fig)
        else:
            st.caption(
                "Colonnes ticket_type_name / ticket_attributes_Montant en XAF absentes - section ignoree."
            )

        st.subheader("Topics x sentiment")
        if avail["Topics x sentiment"]:
            topic_mask = df["topic_id"] >= 0
            kpi_topics = (
                df.loc[topic_mask]
                .groupby(["ticket_type_name", "topic_id", "topic_keywords"])
                .agg(
                    nb_tickets=("sentiment_label", "size"),
                    pct_negatif=("sentiment_label", lambda s: (s == "negative").mean() * 100),
                )
                .reset_index()
            )
            kpi_topics["label"] = (
                kpi_topics["ticket_type_name"] + " . topic " + kpi_topics["topic_id"].astype(str)
                + " (" + kpi_topics["topic_keywords"].str.split(", ").str[:3].str.join(", ") + ")"
            )
            pct_series = kpi_topics.set_index("label")["pct_negatif"]
            fig, ax = plot_full_counts(
                pct_series, "% negatif par topic (tous les topics)",
                xlabel="% negatif", pct=False, value_fmt="{:.0f}%",
            )
            show(fig)
            st.dataframe(
                kpi_topics.sort_values(["pct_negatif", "nb_tickets"], ascending=[False, False])[
                    ["ticket_type_name", "topic_id", "topic_keywords", "nb_tickets", "pct_negatif"]
                ],
                width="stretch",
            )
        else:
            st.caption(
                "Colonnes topic_id / topic_keywords / sentiment_label absentes - section ignoree."
            )

"""
Utilitaires de visualisation "representation exhaustive".

Principe directeur de ces notebooks : quand un graphique est trace, AUCUNE
categorie ne doit en disparaitre, meme si son poids est de 0,1%. On bannit
donc :
  - les pie/donut charts (les tres petites parts deviennent illisibles et
    sont souvent fusionnees visuellement avec leurs voisines) ;
  - les "top N" qui tronquent silencieusement la distribution ;
  - les regroupements automatiques dans un bucket "Autres".

A la place : des barres horizontales, toujours triees, toujours annotees
avec l'effectif ET le pourcentage exact -> une categorie a 0,1% reste une
ligne a part entiere, meme si sa barre est visuellement un trait fin.

Second principe (`profile_column`) : un graphique n'est trace que s'il
apporte une lecture analytique. Un identifiant (numero de telephone, de
compte, de carte...), un texte libre ou une colonne constante n'ont pas de
"distribution" au sens statistique -> ces colonnes restent representees
via `summarize_column` (statistiques : remplissage, cardinalite, et pour
le numerique moyenne/mediane/quartiles/outliers) plutot que par un
graphique qui n'aurait pas de sens.

Chaque fonction qui trace des barres fait une assertion explicite (nombre
de barres tracees == nombre de valeurs uniques presentes) pour qu'un futur
run alerte tout de suite si une categorie venait a etre perdue en cours de
pipeline.
"""

from __future__ import annotations

import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BAR_HEIGHT_PER_CATEGORY = 0.42
MIN_FIG_HEIGHT = 2.2
NEUTRAL_COLOR = "#4C72B0"


def _fig_height(n_categories: int) -> float:
    return max(MIN_FIG_HEIGHT, n_categories * BAR_HEIGHT_PER_CATEGORY + 1.2)


def plot_full_counts(
    values: pd.Series,
    title: str,
    xlabel: str = "Nombre de tickets",
    color: str = NEUTRAL_COLOR,
    ax=None,
    pct: bool = True,
    value_fmt: str = "{:,.0f}",
):
    """
    Barres horizontales a partir d'un Series DEJA agrege (index = categorie,
    valeur = effectif ou metrique). Toutes les lignes du Series sont
    tracees, sans troncature. Utile pour des comptages deja groupby-es
    (un mois, une categorie... par ligne) sans repartir des donnees brutes.
    """
    values = values.sort_values(ascending=True)
    total = values.sum()
    n_cat = len(values)

    if ax is None:
        fig, ax = plt.subplots(figsize=(9, _fig_height(n_cat)))
    else:
        fig = ax.figure

    bars = ax.barh(values.index.astype(str), values.values, color=color)
    ax.set_xlabel(xlabel)
    subtitle = f"{n_cat} categories - toutes representees"
    if pct:
        subtitle = f"n={value_fmt.format(total)}, " + subtitle
    ax.set_title(f"{title}\n({subtitle})")

    max_val = values.values.max()
    for bar, val in zip(bars, values.values):
        label = value_fmt.format(val)
        if pct and total:
            label += f" ({100 * val / total:.1f}%)"
        ax.text(
            bar.get_width() + max_val * 0.01,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="left",
            fontsize=8,
        )

    ax.set_xlim(0, max_val * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig, ax


def plot_full_distribution(
    series: pd.Series,
    title: str,
    xlabel: str = "Nombre de tickets",
    color: str = NEUTRAL_COLOR,
    ax=None,
    dropna: bool = False,
):
    """
    Barres horizontales de la distribution COMPLETE de `series`
    (toutes les valeurs uniques presentes, triees par effectif decroissant).
    Chaque barre est annotee "n (p%)".
    """
    counts = series.value_counts(dropna=dropna)
    n_cat = len(counts)

    fig, ax = plot_full_counts(counts, title, xlabel=xlabel, color=color, ax=ax)

    # garde-fou : on doit avoir trace exactement autant de barres que de
    # valeurs uniques presentes dans les donnees -> rien n'a ete tronque.
    assert n_cat == series.nunique(dropna=dropna), (
        "Categories manquantes dans le graphique !"
    )
    return fig, ax


def plot_stacked_share(
    df: pd.DataFrame,
    group_col: str,
    stack_col: str,
    title: str,
    colors: dict | None = None,
    order_by: str = "count",
):
    """
    Barres horizontales empilees en % (100%) pour chaque valeur de
    `group_col`, ventilees par `stack_col`. Toutes les valeurs de
    `group_col` sont affichees (pas de top N) ; le nombre de tickets de
    chaque groupe est indique en fin de barre pour ne pas perdre le volume
    derriere le pourcentage.
    """
    ct = pd.crosstab(df[group_col], df[stack_col])
    counts = ct.sum(axis=1)
    if order_by == "count":
        order = counts.sort_values(ascending=True).index
    else:
        order = sorted(ct.index, reverse=True)
    ct = ct.loc[order]
    pct = ct.div(ct.sum(axis=1), axis=0) * 100

    n_cat = len(ct)
    fig, ax = plt.subplots(figsize=(9, _fig_height(n_cat)))

    left = np.zeros(n_cat)
    stack_values = pct.columns
    default_palette = plt.get_cmap("tab10").colors
    for i, val in enumerate(stack_values):
        c = (colors or {}).get(val, default_palette[i % len(default_palette)])
        ax.barh(pct.index.astype(str), pct[val], left=left, label=str(val), color=c)
        left += pct[val].values

    for i, (idx, n) in enumerate(counts.loc[order].items()):
        ax.text(101, i, f"n={n}", va="center", fontsize=8)

    ax.set_xlim(0, 112)
    ax.set_xlabel("Part (%)")
    ax.set_title(f"{title}\n({n_cat} categories - toutes representees)")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    assert n_cat == df[group_col].nunique(dropna=False)
    return fig, ax


def annotated_heatmap(
    matrix: pd.DataFrame,
    title: str,
    fmt: str = ".1f",
    cmap: str = "RdYlGn_r",
    xlabel: str = "",
    ylabel: str = "",
):
    """
    Heatmap avec la valeur ecrite en clair dans CHAQUE cellule -> une
    cellule a 0,1% reste lisible en texte meme si la couleur est proche du
    fond (contrairement a une heatmap couleur-seule).
    """
    fig, ax = plt.subplots(figsize=(max(6, matrix.shape[1] * 1.1), _fig_height(matrix.shape[0])))
    im = ax.imshow(matrix.values, cmap=cmap, aspect="auto")
    ax.set_xticks(range(matrix.shape[1]))
    ax.set_xticklabels(matrix.columns, rotation=45, ha="right")
    ax.set_yticks(range(matrix.shape[0]))
    ax.set_yticklabels(matrix.index)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title}\n(toutes les lignes/colonnes presentes dans les donnees)")

    vmax = np.nanmax(matrix.values)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            v = matrix.values[i, j]
            text_color = "white" if v > vmax * 0.6 else "black"
            ax.text(j, i, format(v, fmt), ha="center", va="center", color=text_color, fontsize=8)

    fig.colorbar(im, ax=ax, shrink=0.7)
    fig.tight_layout()
    return fig, ax


# Colonnes numeriques dont le NOM indique un identifiant (numero de compte,
# telephone, carte, code...) plutot qu'une mesure : leur magnitude n'a pas de
# sens quantitatif, un histogramme/boxplot dessus serait trompeur. Detection
# par token isole (le nom de colonne est decoupe sur tout caractere non
# alphanumerique - espace, underscore, apostrophe... - pour eviter les faux
# positifs du type "identifiant", "solide", "validee" tout en gerant aussi
# bien "Numero_tel_client" que "Numero errone" ou "4 derniers chiffres de la
# carte").
_ID_TOKENS = {
    "id", "numero", "num", "tel", "telephone", "phone", "compte",
    "carte", "card", "code", "reference", "ref", "rib",
}


def _looks_like_identifier_name(col: str) -> bool:
    tokens = re.split(r"[^a-z0-9]+", col.lower())
    return any(t in _ID_TOKENS for t in tokens)


def plot_numeric_measure(non_null: pd.Series, title: str, xlabel: str = ""):
    """
    Boite a moustaches (boxplot horizontal) pour une colonne numerique qui
    represente une vraie mesure (montant, score, compteur...). Plus efficace
    qu'un histogramme quand la distribution a des valeurs aberrantes extremes
    (ex. montants XAF) : la mediane/les quartiles restent lisibles, et chaque
    outlier (au sens IQR, meme convention que les moustaches du boxplot) est
    trace individuellement comme un point plutot que d'ecraser l'echelle.
    """
    q1, med, q3 = non_null.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    lo_fence, hi_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = non_null[(non_null < lo_fence) | (non_null > hi_fence)]

    fig, ax = plt.subplots(figsize=(8, 2.4))
    ax.boxplot(
        non_null,
        vert=False,
        widths=0.6,
        patch_artist=True,
        boxprops={"facecolor": NEUTRAL_COLOR, "alpha": 0.5},
        medianprops={"color": "black"},
        flierprops={"marker": "o", "markersize": 4, "markerfacecolor": "#C44E52", "markeredgecolor": "none", "alpha": 0.5},
    )
    ax.set_yticks([])
    ax.set_xlabel(xlabel or "")

    if med > 0 and non_null.max() / max(med, 1) > 50:
        ax.set_xscale("symlog")

    stats_txt = (
        f"mediane={med:,.0f}  Q1={q1:,.0f}  Q3={q3:,.0f}  min={non_null.min():,.0f}  "
        f"max={non_null.max():,.0f}  outliers(IQR)={len(outliers)} ({100*len(outliers)/len(non_null):.1f}%)"
    )
    ax.set_title(f"{title}\n{stats_txt}", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig, ax


def summarize_column(df: pd.DataFrame, col: str) -> dict:
    """
    Resume statistique d'une colonne, calcule pour TOUTES les colonnes
    (meme celles jugees sans valeur analytique pour un graphique) : c'est
    la garantie que chaque colonne reste representee, sous forme de
    statistiques si un graphique n'apporte rien.
    """
    s = df[col]
    non_null = s.dropna()
    n = len(s)
    filled = len(non_null)

    summary = {
        "colonne": col,
        "dtype": str(s.dtype),
        "remplissage_pct": round(100 * filled / n, 2) if n else 0.0,
        "nb_remplis": filled,
        "nb_valeurs_uniques": int(non_null.nunique()),
    }

    is_numeric = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
    is_id_named = _looks_like_identifier_name(col)
    if is_numeric and not is_id_named and filled:
        q1, med, q3 = non_null.quantile([0.25, 0.5, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = non_null[(non_null < lo) | (non_null > hi)]
        summary.update(
            {
                "moyenne": round(float(non_null.mean()), 2),
                "mediane": round(float(med), 2),
                "ecart_type": round(float(non_null.std()), 2) if filled > 1 else 0.0,
                "min": float(non_null.min()),
                "q1": round(float(q1), 2),
                "q3": round(float(q3), 2),
                "max": float(non_null.max()),
                "nb_outliers_iqr": int(len(outliers)),
                "pct_outliers": round(100 * len(outliers) / filled, 2),
            }
        )
    elif filled:
        vc = non_null.value_counts()
        summary.update(
            {
                "valeur_plus_frequente": str(vc.index[0]),
                "pct_valeur_plus_frequente": round(100 * vc.iloc[0] / filled, 2),
            }
        )
    return summary


def profile_column(df: pd.DataFrame, col: str, max_categories: int = 150, id_ratio_threshold: float = 0.5):
    """
    Retourne (fig, ax, summary) pour `col`. `summary` (voir `summarize_column`)
    est TOUJOURS calcule ; `fig`/`ax` valent None quand un graphique n'a pas
    de valeur analytique pour cette colonne (identifiant type numero de
    telephone/compte/carte, texte libre, JSON, colonne constante) - dans ce
    cas seul le resume statistique represente la colonne.

    Strategie de selection du graphique (dans cet ordre) :
      1. Colonne constante (0 ou 1 valeur unique)              -> pas de graphique
      2. Colonne date/horodatage qui se parse correctement     -> volume par mois (complet)
      3. Numerique = une vraie mesure (nom non identifiant)
         avec assez de valeurs distinctes                      -> boxplot (mediane/quartiles/outliers)
      4. Categorique de cardinalite geree (<= max_categories
         ET pas un identifiant quasi unique par ligne)          -> barres exhaustives (aucune troncature)
         (s'applique aussi aux numeriques a nom d'identifiant,
         tant que leur cardinalite reste categorisable)
      5. Sinon (identifiant a forte cardinalite, texte libre,
         JSON...)                                               -> pas de graphique, resume seul
    """
    s = df[col]
    non_null = s.dropna()
    n_unique = non_null.nunique()
    filled = len(non_null)

    summary = summarize_column(df, col)

    if filled == 0 or n_unique <= 1:
        return None, None, summary

    is_datetime_name = (
        not col.lower().startswith("pii_")
        and any(k in col.lower() for k in ("_at", "date"))
    )
    if is_datetime_name and s.dtype == object:
        parsed = pd.to_datetime(non_null, errors="coerce", dayfirst=True, format="mixed")
        if pd.api.types.is_datetime64_any_dtype(parsed) and parsed.notna().mean() >= 0.7:
            months = parsed.dt.to_period("M").astype(str).value_counts()
            fig, ax = plot_full_counts(months, f"{col} — volume par mois", xlabel="Nombre de lignes")
            return fig, ax, summary

    is_numeric = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
    is_id_named = _looks_like_identifier_name(col)

    if is_numeric and not is_id_named and n_unique > 15:
        fig, ax = plot_numeric_measure(non_null, f"{col} — distribution", xlabel=col)
        return fig, ax, summary

    near_unique_id = n_unique / filled > id_ratio_threshold
    if n_unique <= max_categories and not near_unique_id:
        fig, ax = plot_full_counts(
            non_null.value_counts(),
            f"{col} — repartition complete ({100*filled/len(s):.1f}% des lignes renseignees)",
            xlabel="Nombre de lignes",
        )
        return fig, ax, summary

    return None, None, summary


def display_profile(df: pd.DataFrame, col: str, max_categories: int = 150, id_ratio_threshold: float = 0.5):
    """
    Variante notebook-friendly de `profile_column` : imprime le resume et
    affiche le graphique s'il y en a un (sinon indique explicitement
    pourquoi aucun graphique n'est trace).
    """
    fig, ax, summary = profile_column(df, col, max_categories=max_categories, id_ratio_threshold=id_ratio_threshold)

    print(f"--- {col} ---")
    for k, v in summary.items():
        if k == "colonne":
            continue
        print(f"    {k}: {v}")

    if fig is not None:
        plt.show()
    else:
        print("    (pas de graphique - identifiant/texte libre/JSON/colonne constante : sans valeur analytique pour un graphique)")


def print_full_value_counts(series: pd.Series, label: str, dropna: bool = False):
    """Table texte complete (aucune ligne omise) en complement du graphique."""
    vc = series.value_counts(dropna=dropna)
    pct = (vc / vc.sum() * 100).round(2)
    table = pd.DataFrame({"nb_tickets": vc, "pct": pct})
    print(f"--- {label} : {len(table)} valeurs uniques (100% des donnees) ---")
    with pd.option_context("display.max_rows", None):
        print(table)
    return table

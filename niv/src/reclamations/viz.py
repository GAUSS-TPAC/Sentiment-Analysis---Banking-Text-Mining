"""
Charte graphique commune aux notebooks.

Les figures de ce projet sont destinées à un rapport interne : elles doivent être
lisibles imprimées en noir et blanc, et rester correctes pour un lecteur
daltonien. Les couleurs suivent une palette catégorielle validée (séparation
suffisante en vision normale et sous simulation de déficience colorée), utilisée
**dans un ordre fixe** : la série 1 prend toujours le bleu, la série 2 toujours
l'orange, etc. Une couleur n'est jamais réattribuée en fonction du rang d'une
série, sans quoi un même acteur change de couleur d'un graphique à l'autre.

Deux règles structurantes appliquées ici :

- **Jamais de double axe des ordonnées.** Superposer un volume et un taux sur
  deux échelles permet de faire dire n'importe quoi à deux courbes. Quand il faut
  montrer les deux, on empile deux panneaux qui partagent l'axe du temps
  (:func:`panneaux_temporels`) : la lecture reste honnête et la comparaison
  visuelle intacte.
- **Le texte ne porte jamais la couleur de la série.** Titres, valeurs et
  étiquettes restent en encre neutre ; c'est la marque colorée à côté qui porte
  l'identité. Cela évite qu'une information dépende uniquement de la couleur.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

from . import config

# --------------------------------------------------------------------------- #
# Palette
# --------------------------------------------------------------------------- #

#: Palette catégorielle, ordre fixe. Ne pas réordonner : l'ordre est le mécanisme
#: qui garantit la séparation des couleurs adjacentes en vision déficiente.
SERIES = [
    "#2a78d6",  # 1 bleu
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 jaune
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 vert
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 rouge
]

#: Encre et chrome. Le gris de grille est volontairement très clair : la grille
#: sert de repère, pas d'élément graphique.
ENCRE = {
    "surface": "#fcfcfb",
    "primaire": "#0b0b0b",
    "secondaire": "#52514e",
    "muet": "#898781",
    "grille": "#e1e0d9",
    "axe": "#c3c2b7",
}

#: Couleurs de statut, réservées. Jamais utilisées comme couleur de série :
#: le rouge « critique » doit vouloir dire « anomalie », pas « série 8 ».
STATUT = {
    "bon": "#0ca30c",
    "attention": "#fab219",
    "serieux": "#ec835a",
    "critique": "#d03b3b",
}

#: Couleur dédiée à la fenêtre de collecte dégradée (mars-mai 2026). Une zone
#: grisée signale « données non fiables ici » sans concurrencer les séries.
ZONE_INVALIDE = "#e8e7e2"


def appliquer_charte() -> None:
    """Applique la charte aux paramètres matplotlib globaux.

    À appeler une fois en début de notebook. Après cet appel, un `plot` par défaut
    est déjà conforme : pas besoin de repasser des couleurs à chaque tracé.
    """
    mpl.rcParams.update(
        {
            "figure.facecolor": ENCRE["surface"],
            "axes.facecolor": ENCRE["surface"],
            "savefig.facecolor": ENCRE["surface"],
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "figure.figsize": (9, 4.5),
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "sans-serif"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "semibold",
            "axes.titlecolor": ENCRE["primaire"],
            "axes.titlelocation": "left",
            "axes.titlepad": 12,
            "axes.labelsize": 9,
            "axes.labelcolor": ENCRE["secondaire"],
            "axes.edgecolor": ENCRE["axe"],
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.prop_cycle": mpl.cycler(color=SERIES),
            "grid.color": ENCRE["grille"],
            "grid.linewidth": 0.8,
            "xtick.color": ENCRE["muet"],
            "ytick.color": ENCRE["muet"],
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "legend.frameon": False,
            "legend.fontsize": 9,
            "lines.linewidth": 2.0,
            "lines.markersize": 5,
        }
    )


def sauver(fig, nom: str) -> Path:
    """Enregistre une figure dans `resultats/figures/` et retourne son chemin."""
    config.creer_dossiers_sortie()
    chemin = config.DOSSIER_FIGURES / f"{nom}.png"
    fig.savefig(chemin)
    print(f"  -> {chemin.relative_to(config.RACINE)}")
    return chemin


# --------------------------------------------------------------------------- #
# Formes
# --------------------------------------------------------------------------- #


def barres_horizontales(
    series: pd.Series,
    titre: str,
    unite: str = "",
    couleur: str | list[str] = SERIES[0],
    ax=None,
    format_valeur: str = "{:,.0f}",
):
    """Barres horizontales triées, avec étiquette de valeur en bout de barre.

    Forme retenue pour toute comparaison de magnitude entre catégories nommées :
    les libellés métier (« Débité sans que le bénéficiaire soit crédité ») sont
    longs, et l'horizontale les rend lisibles sans rotation.

    L'étiquette de valeur en bout de barre remplace l'axe des abscisses : le
    lecteur lit le chiffre exact plutôt que de l'estimer sur une graduation.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9, max(2.4, 0.42 * len(series) + 1.2)))
    ordre = series.sort_values()
    ax.barh(
        [str(i) for i in ordre.index],
        ordre.to_numpy(),
        color=couleur,
        height=0.68,  # < 1 : laisse une respiration entre les barres
    )
    marge = ordre.max() * 0.015 if ordre.max() else 0.1
    for y, v in enumerate(ordre.to_numpy()):
        ax.text(
            v + marge,
            y,
            format_valeur.format(v) + unite,
            va="center",
            fontsize=9,
            color=ENCRE["secondaire"],  # encre neutre, jamais la couleur de la barre
        )
    ax.set_title(titre)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, ordre.max() * 1.18 if ordre.max() else 1)
    ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.spines["bottom"].set_visible(False)
    return ax


def panneaux_temporels(
    index,
    panneaux: list[dict],
    titre: str,
    zone_grisee: tuple | None = None,
    ligne_verticale=None,
    etiquette_ligne: str = "",
):
    """Plusieurs mesures dans le temps, en panneaux empilés partageant l'axe des x.

    **Remplace explicitement le double axe des ordonnées.** Un volume (en tickets)
    et un taux (en %) n'ont pas la même unité ; les superposer sur deux échelles
    laisse le choix des échelles décider de la conclusion. Empilés, les deux
    signaux restent alignés dans le temps — ce qui est la seule comparaison qui
    nous intéresse ici — sans qu'aucune échelle ne soit arbitraire.

    Parameters
    ----------
    panneaux :
        Un dict par panneau : ``{"valeurs": Series, "libelle": str,
        "couleur": str, "type": "ligne"|"barres", "pct": bool}``.
    zone_grisee :
        ``(debut, fin)`` d'une plage temporelle à signaler comme non fiable.
    ligne_verticale :
        Date d'un événement à matérialiser sur tous les panneaux.
    """
    n = len(panneaux)
    fig, axes = plt.subplots(
        n, 1, figsize=(9, 2.6 * n), sharex=True, constrained_layout=True
    )
    axes = [axes] if n == 1 else list(axes)

    for ax, p in zip(axes, panneaux):
        couleur = p.get("couleur", SERIES[0])
        if p.get("type", "ligne") == "barres":
            ax.bar(index, p["valeurs"], color=couleur, width=p.get("largeur", 20))
        else:
            ax.plot(index, p["valeurs"], color=couleur, linewidth=2.0)
        ax.set_ylabel(p["libelle"], fontsize=9, color=ENCRE["secondaire"])
        ax.grid(axis="x", visible=False)
        if p.get("pct"):
            ax.set_ylim(0, 1)
            ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(xmax=1, decimals=0))

        if zone_grisee is not None:
            ax.axvspan(*zone_grisee, color=ZONE_INVALIDE, zorder=0)
        if ligne_verticale is not None:
            ax.axvline(
                ligne_verticale, color=STATUT["critique"], linewidth=1.4, linestyle="--"
            )

    if ligne_verticale is not None and etiquette_ligne:
        axes[0].annotate(
            etiquette_ligne,
            xy=(ligne_verticale, axes[0].get_ylim()[1]),
            xytext=(6, -12),
            textcoords="offset points",
            fontsize=9,
            color=STATUT["critique"],
            fontweight="semibold",
        )
    axes[0].set_title(titre)
    return fig, axes


def annoter_source(fig, texte: str) -> None:
    """Ajoute une note de source/périmètre en pied de figure.

    Systématique dans ce projet : la plupart des chiffres ne valent que sur un
    périmètre précis (période, base textuelle). Une figure qui circule sans son
    périmètre finit par être citée hors contexte.
    """
    fig.text(
        0.0,
        -0.02,
        texte,
        fontsize=8,
        color=ENCRE["muet"],
        va="top",
        ha="left",
        transform=fig.transFigure,
    )

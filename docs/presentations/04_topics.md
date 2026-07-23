# Discours — Notebook 4 : Extraction des sous-motifs / topic modeling (Phase 3)

*Support : `notebooks/04_topics.ipynb` (équivalent notebook de `phase3_topics.py`)*

---

## Introduction

Savoir qu'une réclamation est négative ne dit pas *pourquoi* elle l'est. La catégorie (`ticket_type_name`) donne un premier niveau de lecture — "Transaction", "Compte", "Carte"... — mais reste large. Ce notebook va plus loin : il découvre automatiquement les sous-thématiques récurrentes à l'intérieur de chaque catégorie, à partir du texte des réclamations elles-mêmes.

## Pourquoi ce travail est nécessaire

Le champ `Root cause` (cause racine), qui aurait dû documenter précisément cette information dans le système Intercom, n'est rempli que sur 0,02 % des tickets — un champ quasiment jamais utilisé par les agents. Ce notebook reconstruit, par analyse automatique du texte, ce que ce champ manuel aurait dû contenir : des sous-motifs concrets ("carte bloquée", "bénéficiaire erroné", "compte bloqué"...) au lieu d'une catégorie générique.

## Comment le modèle fonctionne

La méthode retenue est **TF-IDF + NMF** (Non-negative Matrix Factorization), appliquée catégorie par catégorie sur le texte lemmatisé (celui produit dans le notebook 2, dont l'ordre des mots n'a pas d'importance ici).

Le choix de scikit-learn plutôt qu'une approche plus moderne type BERTopic est délibéré : il ne nécessite aucun téléchargement de modèle supplémentaire (contrairement au modèle de sentiment de la Phase 2, où une instabilité réseau a déjà été rencontrée), et il est suffisant sur un vocabulaire métier restreint, déjà nettoyé et lemmatisé — un contexte où la robustesse et la simplicité priment sur la sophistication.

Concrètement, pour chaque catégorie :
1. Un **TF-IDF** vectorise les textes, en ignorant les mots trop rares (présents dans moins de 3 tickets — probablement du bruit ou des fautes de frappe) et les mots trop fréquents (présents dans plus de 60 % des tickets — trop génériques pour être discriminants). Les bigrammes sont inclus en plus des mots seuls, ce qui permet de capter des expressions comme "bénéficiaire erroné" ou "compte bloqué" plutôt que leurs mots pris isolément.
2. Une **NMF** factorise cette matrice en un nombre de topics *k*, déterminé par une règle empirique : environ un topic pour 40 tickets, plafonné à 8 topics maximum et 2 minimum par catégorie. Chaque topic est ensuite décrit par ses 8 mots les plus caractéristiques, et chaque ticket se voit assigner le topic dominant parmi ceux détectés dans sa catégorie.

Un seuil minimal de 30 tickets avec texte est requis par catégorie pour qu'un topic modeling soit jugé fiable ; en dessous, la catégorie est exclue de cette étape — mais reste visible dans les graphiques de volume, pour que cette exclusion soit explicite plutôt que silencieuse.

Comme dans les notebooks précédents, un cache (`reclamations_phase3.csv` et `topics_summary.csv`) évite de relancer le calcul NMF catégorie par catégorie à chaque exécution.

## Ce que montrent les graphiques

- **Volume de texte par catégorie**, avec une ligne verticale marquant le seuil des 30 tickets requis pour le topic modeling — permet de voir immédiatement quelles catégories seront concernées.
- **Catégories exclues du topic modeling**, listées explicitement avec leur effectif, plutôt que de disparaître sans explication.
- **Tous les topics découverts, par volume** — 34 topics au total dans le run actuel, représentés sans troncature. L'ancien rapport ne montrait que les 10 sous-motifs jugés les plus "critiques" (volume × % négatif) ; ici, l'intégralité des topics découverts est visible, le croisement avec le sentiment étant réservé au notebook de reporting suivant.

## Ce qu'il faut retenir

Ce notebook transforme une catégorie générique en sous-motifs concrets et actionnables, directement dérivés du langage des clients eux-mêmes plutôt que d'une nomenclature imposée a priori. C'est la brique qui permettra, dans le notebook suivant, de répondre à la question "quels sont précisément les points de friction les plus fréquents et les plus mal vécus ?"

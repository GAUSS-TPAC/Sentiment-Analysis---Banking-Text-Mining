# Discours — Notebook 5 : Restitution, KPIs et visualisations (Phase 4)

*Support : `notebooks/05_reporting.ipynb` (remplace `phase4_reporting.py` et `rapport_analyse_sentiment.md`)*

---

## Introduction

Ce dernier notebook rassemble tout le travail des quatre précédents — nettoyage, sentiment, topics — en une restitution destinée à la lecture métier : quels sont les grands équilibres, comment évoluent-ils dans le temps, où se concentrent les points de friction. Il remplace à la fois le script `phase4_reporting.py` et le rapport texte `rapport_analyse_sentiment.md`, dont certains tableaux tronquaient silencieusement les catégories ou canaux les plus rares.

**Le principe directeur reste le même que dans les quatre notebooks précédents : chaque graphique représente 100 % des valeurs présentes dans les données, sans exception ni seuil de significativité caché.**

## Comment les données sont préparées

Le notebook part de `reclamations_phase3.csv`, la sortie complète du pipeline (texte nettoyé, sentiment, topics). Deux transformations légères sont ajoutées à ce stade :
- la date de création est convertie en période mensuelle (`mois`), pour permettre l'analyse de tendance ;
- le montant en XAF, stocké comme texte libre dans la donnée source, est reconverti en valeur numérique par extraction des chiffres (les séparateurs de milliers et symboles sont retirés).

## Ce que montrent les graphiques, et pourquoi chaque choix a été fait

**1. Sentiment global.** Le point de départ : la répartition négative / neutre / positive sur l'ensemble du corpus.

**2. Sentiment par catégorie — toutes les catégories.** L'ancien rapport (`rapport_analyse_sentiment.md`, section 4.2) n'affichait que 10 catégories sur 15. Ici, les 15 sont visibles, y compris celles à très faible volume (`Feature request`, `Card issue`, `Internal task`, `Bug report`, `Support Request` — 2 à 17 tickets). Ces catégories rares ne doivent pas pour autant être ignorées : elles peuvent signaler un usage émergent ou un problème encore marginal mais réel.

**3. Sentiment par canal — tous les canaux.** Même logique : l'ancien rapport (section 4.3) s'arrêtait à 5 canaux sur 7, laissant disparaître `instagram` et `email` malgré 1 à 2 tickets chacun.

**4. Évolution mensuelle du pourcentage de négatif.** L'ancien rapport (section 4.4) excluait de la lecture de tendance les mois comptant moins de 25 tickets, jugés non significatifs. Ici, tous les mois restent affichés, mais chaque point est annoté avec son effectif exact (`n=...`) directement sur le graphique — un choix qui déplace la décision de significativité vers le lecteur, qui peut juger lui-même, plutôt que de la figer silencieusement en amont.

**5. Montants en jeu, par catégorie — médiane plutôt que moyenne.** Le montant moyen est faussé par des valeurs aberrantes extrêmes, jusqu'à 500 milliards XAF sur un seul ticket (identifié dans le notebook 1, section 6). La médiane, moins sensible aux valeurs extrêmes, est utilisée systématiquement, pour toutes les catégories y compris celles avec très peu de montants valides — avec, en complément, un graphique du nombre de montants valides disponibles par catégorie pour contextualiser la fiabilité de chaque médiane.

**6. Topics croisés avec le sentiment — tous les topics.** L'ancien rapport (section 4.6) ne montrait que les 10 sous-motifs jugés les plus "critiques", sélectionnés par volume × % négatif. Ici, les 34 topics découverts en Phase 3 sont tous représentés, triés par pourcentage de négatif, avec leur volume en annotation — la sélection des sujets prioritaires reste possible en aval, mais elle n'est plus faite silencieusement en amont par le graphique lui-même.

**7. Vérification de couverture face à l'ancien rapport.** La dernière section chiffre explicitement l'écart : nombre de catégories, de canaux, de topics et de mois représentés ici, comparé aux volumes de l'ancien rapport. C'est la preuve, mesurable, que la nouvelle approche ne perd plus d'information en route.

## Ce qu'il faut retenir

Ce notebook n'apporte pas de nouvelle méthode d'analyse par rapport aux précédents : sa valeur est dans l'exhaustivité et la traçabilité de la restitution. Chaque chiffre présenté peut être confronté directement à l'ancien rapport, et chaque choix de représentation (médiane plutôt que moyenne, effectif annoté plutôt que seuil caché) est justifié explicitement plutôt que laissé implicite. C'est la version du reporting sur laquelle une décision métier peut s'appuyer en toute confiance.

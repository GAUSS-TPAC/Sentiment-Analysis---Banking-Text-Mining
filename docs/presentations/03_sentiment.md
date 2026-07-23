# Discours — Notebook 3 : Analyse de sentiment (Phase 2)

*Support : `notebooks/03_sentiment.ipynb` (équivalent notebook de `phase2_sentiment.py`)*

---

## Introduction

Une fois le texte nettoyé et masqué, la question centrale devient : ce client est-il satisfait, neutre, ou mécontent ? Ce notebook attribue à chaque réclamation une étiquette de sentiment — négatif, neutre ou positif — accompagnée d'un score de confiance.

## Pourquoi ce modèle et pas un autre

Aucune donnée labellisée n'existe dans ce jeu de données : personne n'a annoté manuellement un échantillon de tickets avec leur sentiment réel. Entraîner un modèle supervisé n'est donc pas une option ici. Le choix s'est porté sur un modèle pré-entraîné utilisé directement en inférence (« zero-shot ») : `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`.

Trois raisons à ce choix précis :
- **Multilingue** : le modèle couvre le français et l'anglais, les deux langues détectées dans le notebook précédent, sans avoir besoin de router vers un modèle différent selon la langue.
- **Registre adapté** : entraîné sur des messages de réseaux sociaux — un langage informel, direct, parfois familier — ce qui se rapproche davantage du ton des réclamations clients que ne le ferait un modèle entraîné sur de la presse ou de la littérature.
- **3 classes** (négatif / neutre / positif), suffisant pour l'objectif métier : identifier les points de friction, pas nuancer une intensité émotionnelle.

## Comment l'inférence est appliquée

Point technique important : le modèle est appliqué sur `texte_masque` — le texte nettoyé et anonymisé, mais **non lemmatisé** — et non sur `texte_lemmatise` utilisé pour les topics. La raison est structurelle : un modèle transformer comme celui-ci construit sa compréhension du texte à partir de l'ordre des mots et de la syntaxe. Lemmatiser (réduire chaque mot à sa forme canonique, en écartant les mots vides) détruirait une partie de ce signal grammatical dont le modèle a besoin. À l'inverse, cette destruction de l'ordre des mots ne pose aucun problème pour le TF-IDF de la Phase 3, qui ne raisonne que sur des sacs de mots.

Concrètement, le pipeline `transformers` est chargé avec `top_k=None` pour récupérer le score des 3 classes (et pas seulement la classe gagnante), ce qui permet de connaître la répartition complète des probabilités par ticket, en plus de la classe retenue. La revision du modèle est fixée explicitement (`revision="main"`) pour éviter un téléchargement inutile de ~1 Go de poids liés à une révision alternative gérée par un bot.

Comme pour le nettoyage, un mécanisme de cache évite de relancer l'inférence — plusieurs minutes sur CPU pour l'ensemble du corpus — à chaque ouverture du notebook : si `reclamations_phase2.csv` existe déjà, il est chargé directement.

## Ce que montrent les graphiques

- **Distribution globale du sentiment** sur l'ensemble du corpus.
- **Sentiment par catégorie de réclamation, sans exception.** L'ancien rapport texte n'affichait que 10 catégories sur 15 ; les catégories à très faible volume (`Feature request`, `Card issue`, 2 tickets chacune) disparaissaient silencieusement. Ici, les 15 catégories sont représentées, avec leur volume réel — une catégorie à 2 tickets reste visible, même si son pourcentage de négatif doit être lu avec prudence vu le faible effectif.
- **Sentiment par canal, sans exception.** Même logique : l'ancien rapport s'arrêtait à 5 canaux sur 7, laissant de côté `instagram` et `email` malgré 1 à 2 tickets chacun.
- **Score de confiance du modèle** — la distribution des scores associés à la classe prédite, avec sa médiane. Cet indicateur permet de juger la fiabilité globale des prédictions plutôt que de les prendre pour argent comptant.

## Ce qu'il faut retenir

Ce notebook ne se contente pas de produire une étiquette par ticket : il documente aussi explicitement ses limites — absence de données labellisées, donc pas de mesure de précision au sens strict, et un score de confiance qui doit accompagner chaque lecture des résultats. La discipline de représentation exhaustive (aucune catégorie ni canal omis) se poursuit ici exactement comme dans les notebooks précédents.

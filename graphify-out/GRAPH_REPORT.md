# Graph Report - analyse des reclamation clients  (2026-08-14)

## Corpus Check
- 57 files · ~79,108 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 536 nodes · 847 edges · 28 communities
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 66 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Gouvernance et anomalies du protocole
- chargement.py (Système A)
- systeme_b.py
- Périmètre à la journée
- Catalogue des colonnes
- Statistique descriptive
- Sentiment analysis (Phase 2)
- config.py
- texte.py — taxonomie causale
- Qualité des données
- consolidation.py
- viz_utils.py
- Évolution temporelle — scripts
- Dashboard Streamlit
- Phase 1 — nettoyage
- Analyse montant XAF — scripts
- Période pré-lancement et canaux
- Anomalies montant XAF par catégorie
- topics.py — topic modeling
- Phase 3 — topic modeling
- Répartition mensuelle par type
- Évolution montant mensuel
- Phase 2 — script sentiment
- Volume mensuel des réclamations
- Pics quotidiens de réclamations
- Délai de traitement
- Distribution des montants XAF
- Volume quotidien et pic 2026

## God Nodes (most connected - your core abstractions)
1. `Protocole d'étude — analyse des réclamations clients Intercom` - 32 edges
2. `Catalogue des colonnes (discours)` - 12 edges
3. `_charger()` - 11 edges
4. `Rapport Evolution Temporelle` - 11 edges
5. `Notebook 5 — Restitution, KPIs et visualisations (Phase 4)` - 11 edges
6. `Phase 2 — Sentiment Analysis` - 10 edges
7. `Rapport d'analyse des réclamations clients` - 10 edges
8. `vue_ensemble_colonnes()` - 9 edges
9. `load_data()` - 9 edges
10. `sauvegarder_table()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Colonnes sensibles (Nom du client, Numero de compte)` --references--> `protocole_etude.md`  [EXTRACTED]
  ecarts_rapport_inventaire.md → ecarts_protocole_etude.md
- `config.py` --semantically_similar_to--> `config.py`  [EXTRACTED] [semantically similar]
  niv/README.md → ecarts_protocole_etude.md
- `chargement.py` --semantically_similar_to--> `chargement.py`  [EXTRACTED] [semantically similar]
  niv/README.md → ecarts_protocole_etude.md
- `texte.py` --semantically_similar_to--> `texte.py`  [EXTRACTED] [semantically similar]
  niv/README.md → ecarts_protocole_etude.md
- `Périmètre de référence 8 284 tickets` --conceptually_related_to--> `Règle de périmètre à la journée (9 381/8 348)`  [EXTRACTED]
  ecarts_rapport_inventaire.md → ecarts_protocole_etude.md

## Import Cycles
- None detected.

## Communities (28 total, 0 thin omitted)

### Community 0 - "Gouvernance et anomalies du protocole"
Cohesion: 0.07
Nodes (45): Protocole d'étude — analyse des réclamations clients Intercom, Afriland First Bank, Alan TCHAPDA, Anomalie 3 — définitions concurrentes de réclamation sans contenu, Anomalie 2 — montants aberrants sur Montant en XAF, Anomalie 1 — rupture de collecte du 13 mars 2026, Biais méthodologiques identifiés (§6.2), Cédric Donfack (+37 more)

### Community 1 - "chargement.py (Système A)"
Cohesion: 0.08
Nodes (39): charger_brut(), charger_messages_ouverture(), colonnes_tronquees(), _colonnes_trop_longues(), construire_texte_enrichi(), controles_qualite(), cramer_v(), dictionnaire_colonnes() (+31 more)

### Community 2 - "systeme_b.py"
Cohesion: 0.10
Nodes (37): _charger(), charger_assignations(), charger_categories(), charger_champs_personnalises(), charger_conversations(), charger_groups(), charger_tickets(), charger_users() (+29 more)

### Community 3 - "Périmètre à la journée"
Cohesion: 0.09
Nodes (34): chargement.py, config.py, conversations_*.xlsx (source complémentaire), Notebook 04 — analyse_causale (AUDIT), Règle de périmètre à la journée (9 381/8 348), protocole_etude.md, Règle d'intégralité de l'extrapolation (AUDIT corrigé), 7e famille causale absente (dysfonctionnement applicatif) (+26 more)

### Community 4 - "Catalogue des colonnes"
Cohesion: 0.09
Nodes (33): Column: category, Column: channel, Column: created_at, Catalogue des colonnes (discours), Column: ticket_attributes_Montant en XAF, Column: ticket_attributes_Root cause, Columns: sentiment_label / sentiment_score / sentiment_scores_detail, Column: texte_lemmatise (+25 more)

### Community 5 - "Statistique descriptive"
Cohesion: 0.11
Nodes (27): Etape 0 du cours : profilage general du dataset. Ce script repond aux questions…, Series, Statistique descriptive des variables numeriques. Pour chaque colonne classee…, stats_colonne_numerique(), frequences_colonne(), Series, Statistique descriptive des variables categorielles et booleennes. Pour chaque…, repartition_booleenne() (+19 more)

### Community 6 - "Sentiment analysis (Phase 2)"
Cohesion: 0.11
Nodes (31): Notebook 3 — Analyse de sentiment (Phase 2), cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual, Rationale : choix du modèle cardiffnlp (multilingue, registre réseaux sociaux, 3 classes), Score de confiance du modèle de sentiment, texte_lemmatise (champ texte lemmatisé), texte_masque (champ texte nettoyé non lemmatisé), Inférence zero-shot, Notebook 4 — Extraction des sous-motifs / Topic Modeling (Phase 3) (+23 more)

### Community 7 - "config.py"
Cohesion: 0.08
Nodes (26): chemin_conversations(), chemin_donnees(), chemin_systeme_b(), creer_dossiers_sortie(), est_colonne_sensible(), Path, Chemins et constantes de périmètre. Toutes les dates de coupure utilisées dans…, Localise l'export conversations Intercom le plus récent, si présent.… (+18 more)

### Community 8 - "texte.py — taxonomie causale"
Cohesion: 0.11
Nodes (27): a_texte_exploitable(), classer(), construire_texte(), couverture(), detecter(), echantillon_non_classes(), enrichir_avec_messages_ouverture(), estimation_corrigee() (+19 more)

### Community 9 - "Qualité des données"
Cohesion: 0.12
Nodes (26): Classification automatique des colonnes, Recommandation: utiliser created_at, Synthese qualite des donnees, Date de la transaction anomaly, Rapport Statistique Descriptive, Montant en XAF anomalies, Numero_tel_client anomaly, SRC_Intercom_Reclamation dataset (+18 more)

### Community 10 - "consolidation.py"
Cohesion: 0.13
Nodes (25): apparier(), apparier_reference(), apparier_telephone_montant_date(), bruit_de_fond(), cles_a(), cles_b(), _extraire_telephone_json(), normaliser_reference() (+17 more)

### Community 11 - "viz_utils.py"
Cohesion: 0.14
Nodes (23): annotated_heatmap(), display_profile(), _fig_height(), _looks_like_identifier_name(), plot_full_counts(), plot_full_distribution(), plot_numeric_measure(), plot_stacked_share() (+15 more)

### Community 12 - "Évolution temporelle — scripts"
Cohesion: 0.19
Nodes (13): Volume quotidien de reclamations, base sur created_at. - reconstruit une serie…, Agregation mensuelle des reclamations + tendance. Deux points d'attention…, Detection des pics (jours anormalement charges) dans la periode operationnelle.…, Delai de traitement des reclamations : created_at -> updated_at. Restreint aux…, Repartition mensuelle par type de reclamation, sur la periode operationnelle.…, Zoom sur la periode "quasi nulle" (fevrier 2024 -> octobre 2025). Objectif :…, chemin_figure(), load_data() (+5 more)

### Community 13 - "Dashboard Streamlit"
Cohesion: 0.16
Nodes (13): cache_data, available_sections(), build_pdf_guide(), build_profile_summary(), compute_kpis(), load_data(), DataFrame, Profileur automatique de tickets - app Streamlit. Depose un CSV "similaire"… (+5 more)

### Community 14 - "Phase 1 — nettoyage"
Cohesion: 0.21
Nodes (13): detect_language(), extract_and_mask(), fix_encoding(), lemmatize_by_language(), _lemmatize_doc(), load_spacy_pipelines(), main(), DataFrame (+5 more)

### Community 15 - "Analyse montant XAF — scripts"
Cohesion: 0.29
Nodes (9): Distribution du champ Montant en XAF, malgre les anomalies deja identifiees…, Evolution mensuelle du montant reclame, EN BRUT et EN VERSION "ASSAINIE".…, Zoom sur les 3 familles d'anomalies du champ Montant en XAF, pour aider a…, chemin_figure(), load_data(), DataFrame, Path, Fonctions communes aux scripts d'analyse du champ ticket_attributes_Montant en… (+1 more)

### Community 16 - "Période pré-lancement et canaux"
Cohesion: 0.35
Nodes (11): Figure: Periode pre-lancement (avant nov. 2025), Canal Android, Cluster config/test (avr-mai 2024), Debut de la periode operationnelle (nov. 2025), Canal Email, Canal Facebook, Canal iOS, Canal Messenger (+3 more)

### Community 17 - "Anomalies montant XAF par catégorie"
Cohesion: 0.33
Nodes (10): Anomalie : valeurs extremes > 10M XAF (n=79), Anomalie : valeurs negatives (n=20), Anomalie : valeurs a zero (n=178), Analyse du Montant en XAF, Anomalies Montant XAF par Categorie (figure), Type de ticket : CARTE, Type de ticket : COMPTE, Type de ticket : CREDIT (+2 more)

### Community 18 - "topics.py — topic modeling"
Cohesion: 0.27
Nodes (9): ajuster_topics(), nombre_topics(), DataFrame, Series, Reconstruction de sous-motifs par topic modeling (TF-IDF + NMF), catégorie par…, Ajuste TF-IDF + NMF sur une série de textes déjà masqués et normalisés.…, Ajuste un modèle de topics indépendant par valeur de `colonne_categorie`.…, Nombre de topics à ajuster pour une catégorie de `n_tickets`. Formule bornée :… (+1 more)

### Community 19 - "Phase 3 — topic modeling"
Cohesion: 0.31
Nodes (8): load_input(), main(), n_topics_for(), DataFrame, Series, Phase 3 - Extraction des parametres utiles a la banque : topic modeling.…, Ajuste TF-IDF + NMF sur les textes d'une categorie. Retourne (topic_ids par…, topic_model_category()

### Community 20 - "Répartition mensuelle par type"
Cohesion: 0.32
Nodes (8): Repartition mensuelle des reclamations par type (graphique), Analyse d'evolution temporelle des reclamations, Pic operationnel des reclamations (mars-avril 2026), Type de reclamation AUTRES, Type de reclamation BENEFICIAIRE ERRONE, Type de reclamation CARTE, Type de reclamation COMPTE, Type de reclamation SARA

### Community 21 - "Évolution montant mensuel"
Cohesion: 0.52
Nodes (7): Montant median mensuel (assaini), Montant median mensuel (brut), Montant moyen mensuel (assaini), Montant moyen mensuel (brut), Montant reclame (XAF), La moyenne brute est tres instable (sensible aux valeurs extremes), la mediane l'est beaucoup moins, Evolution mensuelle du montant reclame (brut vs assaini)

### Community 22 - "Phase 2 — script sentiment"
Cohesion: 0.47
Nodes (5): load_pipeline(), main(), DataFrame, Phase 2 - Analyse de sentiment des reclamations. Modele : cardiffnlp/twitter-…, run_sentiment()

### Community 23 - "Volume mensuel des réclamations"
Cohesion: 0.60
Nodes (6): Partial Month (July 2026, color-coded orange), Pilot Phase (color-coded in gray), Peak Volume in April 2026 (~5200 reclamations), Linear Regression Trend Line, Monthly Reclamation Volume Chart, Monthly Reclamation Volume Metric

### Community 24 - "Pics quotidiens de réclamations"
Cohesion: 0.70
Nodes (5): Evolution temporelle des reclamations, Methode IQR de detection des pics (seuil > 201/jour), Pics quotidiens de reclamations, Pics de reclamations quotidiennes (figure), Rationale: pics concentres sur periode operationnelle janvier-mai 2026

### Community 25 - "Délai de traitement"
Cohesion: 0.50
Nodes (5): Analyse Evolution Temporelle des reclamations, Amelioration continue du delai de traitement (nov 2025 a juin 2026), Delai de traitement (median / moyen, en heures), Donnees des reclamations resolues (tickets, dates de creation/resolution), Delai de traitement des reclamations resolues, par mois de creation (figure)

### Community 26 - "Distribution des montants XAF"
Cohesion: 0.67
Nodes (4): Montant des Reclamations (XAF), Distribution des Montants XAF (figure), Insight: distribution des montants et ecarts par type, Type de Reclamation (SARA, COMPTE, CARTE, BENEFICIAIRE ERRONE, CREDIT, ACCUEIL)

### Community 27 - "Volume quotidien et pic 2026"
Cohesion: 0.67
Nodes (3): Moyenne mobile 7 jours (smoothing method), Pic de reclamations debut 2026 (surge insight), Volume quotidien de reclamations (chart)

## Ambiguous Edges - Review These
- `Reclamations organiques isolees (pre-lancement)` → `Canal Email`  [AMBIGUOUS]
  niv2- tutoré/3- Evolution_Temporelle/resultats/figures/06_periode_pre_lancement.png · relation: references
- `Rapport_Inventaire_Colonnes_Intercom.docx` → `Problématique causale SARA (angle retenu)`  [AMBIGUOUS]
  ecarts_rapport_inventaire.md · relation: conceptually_related_to
- `Sept familles causales exclusives (§4.2)` → `config.py`  [AMBIGUOUS]
  protocole_etude.md · relation: implements

## Knowledge Gaps
- **53 isolated node(s):** `Pic de reclamations debut 2026 (surge insight)`, `Moyenne mobile 7 jours (smoothing method)`, `Donnees des reclamations resolues (tickets, dates de creation/resolution)`, `Analyse Evolution Temporelle des reclamations`, `Type de reclamation CARTE` (+48 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Reclamations organiques isolees (pre-lancement)` and `Canal Email`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Rapport_Inventaire_Colonnes_Intercom.docx` and `Problématique causale SARA (angle retenu)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Sept familles causales exclusives (§4.2)` and `config.py`?**
  _Edge tagged AMBIGUOUS (relation: implements) - confidence is low._
- **Why does `creer_dossiers_sortie()` connect `config.py` to `chargement.py (Système A)`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **Why does `construire_texte_enrichi()` connect `chargement.py (Système A)` to `texte.py — taxonomie causale`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Catalogue des colonnes (discours)` (e.g. with `Sentiment Analysis & Text Mining — Banking Customer Complaints` and `Notebook 1 — Exploration exhaustive du dataset (discours)`) actually correct?**
  _`Catalogue des colonnes (discours)` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Pic de reclamations debut 2026 (surge insight)`, `Moyenne mobile 7 jours (smoothing method)`, `Donnees des reclamations resolues (tickets, dates de creation/resolution)` to the rest of the system?**
  _53 weakly-connected nodes found - possible documentation gaps or missing edges._
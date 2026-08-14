# Protocole d'étude — analyse des réclamations clients Intercom

**Analyse des réclamations clients par text mining** — Afriland First Bank.

| | |
|---|---|
| Auteur / Analyste | Alan TCHAPDA — Direction Recherche & Innovation (DRI) |
| Commanditaire | Cédric Donfack — Direction Recherche & Innovation (DRI) |
| Confidentialité | Ce document ne saurait être divulgué en partie ou en totalité, verbalement ou par écrit — y compris par photocopie — à une tierce personne sans autorisation écrite d'Afriland First Bank. Il est la propriété d'Afriland First Bank et doit lui être retourné à sa demande. |

**Écart assumé avec la commande initiale.** Le document de cadrage remis par le commanditaire
(*« Analyse des réclamations clients par Text mining et Sentiments analysis »*, structuré en 4
phases : conformité et conception d'une procédure, analyse des causes profondes, formulation de
recommandations opérationnelles, évaluation de la responsabilité vis-à-vis des créanciers) demandait
un **dashboard Streamlit** alimenté par sentiment analysis et topic modeling. Ce protocole retient
une méthode différente — classification causale par règles, sans mesure de sentiment, restituée en
notebooks reproductibles plutôt qu'en dashboard — justifiée en § 4.1. Une première itération
conforme à la commande initiale existe (`niv1/`, sentiment XLM-RoBERTa + topic modeling NMF +
dashboard Streamlit) mais n'a pas été retenue comme méthode de référence, pour les raisons du § 4.1.
La correspondance entre les 4 phases de la commande et le contenu réellement livré est faite en
§ 1.6.

---

**Version.** Ce document consolide les résultats des notebooks `niv/notebooks/01` à `06` et fixe la
méthodologie retenue pour la suite de l'étude. Certaines décisions ici présentées comme retenues
sont validées par un calcul reproduit dans ce document mais **pas encore reflétées dans le code**
de `niv/src/reclamations/` : chaque cas est signalé par la mention **[À intégrer au code]**.
Un chiffre sans cette mention est déjà celui que produit le code actuel.

> ⚠️ **Chiffres dépassés depuis le 13/08/2026 — mise à jour de ce document non encore faite.**
> Le code (`niv/src/reclamations/`, notebooks 03-04-06-07) a intégré une source de données
> complémentaire (`conversations_.xlsx`, message d'ouverture réel d'une partie des tickets — voir
> `niv/README.md`) et remplacé la règle d'exclusion par mois entier (§3.4) par la règle à la journée
> déjà décrite ci-dessous comme *retenue* — cette dernière est donc maintenant **implémentée**, pas
> seulement retenue. Conséquence : tous les effectifs de périmètre cités dans ce document (6 867,
> 6 545, 7 950, 7 563...) sont dépassés. Les valeurs actuelles, produites par le code : **périmètre
> d'analyse causale 9 381 tickets, base textuelle 8 348 (89,0 %)**, validées par un test de
> représentativité (V de Cramér 0,17 sur le type de ticket, 0,10 sur le canal — notebook 03, section
> 4). Les pourcentages de familles causales (§4.2, §5.1) et les libellés de topics (notebook 07) ont
> été recalculés sur ce nouveau périmètre et diffèrent également de ceux cités plus bas. Se référer à
> `niv/README.md` et aux notebooks eux-mêmes pour les chiffres à jour tant que ce document n'a pas
> été réécrit dans son ensemble ; le détail des écarts encore ouverts est tenu dans
> `ecarts_protocole_etude.md`.

**Règle de rédaction.** Aucun chiffre n'est estimé pour la forme : tout nombre cité provient d'un
calcul reproduit à la rédaction de ce document, ou d'une sortie de notebook. Une information non
disponible est marquée **[À COMPLÉTER]**, jamais devinée.

---

## 1. Objet et cadre de l'étude

### 1.1 Contexte et commanditaire

L'étude porte sur les réclamations clients d'Afriland First Bank déposées via le canal de support
Intercom, en particulier celles relatives au produit de mobile banking **SARA** et à ses
interfaces avec les opérateurs de mobile money (Orange Money, MTN MoMo).

| | |
|---|---|
| Établissement | Afriland First Bank |
| Cadre du travail | Mémoire tutoré |
| Commanditaire / service porteur | Cédric Donfack — Direction Recherche & Innovation (DRI) |
| Maître de stage / tuteur | **[À COMPLÉTER]** — à confirmer si distinct du commanditaire ci-dessus |

### 1.2 Problématique

> Pourquoi une part significative des transferts entre SARA et les opérateurs de mobile money
> débite le client sans créditer le bénéficiaire — et comment agir à la source pour réduire le
> **taux d'incident par transaction**, plutôt que le seul nombre de plaintes ?

**Le piège de mesure à écarter explicitement.** Si l'indicateur de succès devient *le nombre de
réclamations*, le moyen le plus efficace de réussir est de rendre la réclamation plus difficile à
déposer. Ce n'est pas un risque théorique : la section 3.2 montre qu'un changement du canal de
dépôt en mars 2026 a fait chuter les réclamations documentées, sans qu'aucune réclamation réelle
n'ait été résolue pour autant. Un bon canal de réclamation **augmente** au contraire les
réclamations enregistrées, en révélant une insatisfaction jusque-là silencieuse. C'est pourquoi
l'indicateur cible n'est pas le volume de plaintes, mais un taux rapporté à l'activité — voir 5.3.

### 1.3 Questions de recherche

| # | Question | Sous-question mesurable | Section |
|---|---|---|---|
| 1 | Quelles données sont exploitables ? | Taux de remplissage et de troncature par variable | 2, 3 |
| 2 | Les variations de volume sont-elles un signal métier ? | Complétude de 4 champs indépendants dans le temps, datation à la journée | 3.2 |
| 3 | Sur quelle base les conclusions sur les motifs sont-elles valides ? | Force d'association (V de Cramér) entre disponibilité du texte et variables observables | 4.4 |
| 4 | Que décrivent les clients qui se plaignent ? | Répartition en familles causales, précision et rappel mesurés par famille | 4, 5 |
| 5 | Le nombre de réclamations mesure-t-il la demande réelle ? | Taux de dépôt répété, part de clients récidivistes, charge en messages | 5 |
| 6 | Que peut-on affirmer, et que ne peut-on pas affirmer ? | Section 6 | 6 |

**Questions écartées d'emblée**, faute de la donnée qui les rendrait traitables :

| Question | Donnée manquante |
|---|---|
| À quelle étape technique la transaction échoue | Aucun code d'erreur, aucun statut de passerelle |
| L'argent est-il définitivement perdu ou en suspens | Aucune issue de dossier enregistrée |
| Quel est le taux d'incident rapporté aux transactions | Le volume de transactions réalisées est inconnu |

### 1.4 Périmètre de l'étude

**Inclus**

- Les réclamations déposées sur le canal Intercom (android, iOS, WhatsApp, Facebook, Messenger,
  Instagram, e-mail), du fichier `SRC_Intercom_Reclamation_202607201846.csv`.
- La période opérationnelle du dispositif : 1ᵉʳ novembre 2025 → 17 juillet 2026 (§ 3.4).
- L'analyse causale des motifs de réclamation, la mesure de la récidive client, et l'exposition
  financière en ordre de grandeur.

**Explicitement exclu**

- Toute réclamation déposée par un autre canal que Intercom (agence physique, courrier, appel
  téléphonique non tracé dans l'outil).
- Le calcul d'un taux d'incident rapporté au volume de transactions : le dénominateur n'existe pas
  dans cette source (§ 5.3, § 6.1).
- Le diagnostic technique de la chaîne SARA ↔ opérateurs mobile money : aucune trace technique
  n'est disponible dans l'export (§ 6.1).
- La mesure d'un taux de résolution ou d'un délai de traitement fiable : le statut majoritaire du
  dispositif est ambigu (§ 5.3, § 6.3).
- La phase pilote du dispositif (février 2024 – octobre 2025, 38 réclamations) : dispositif de
  collecte différent, non comparable (§ 3.4).

### 1.5 Public cible du livrable

Ingénieurs data amenés à reprendre ou étendre ce travail, et maître de stage / jury du mémoire
tutoré. Le document se lit sans connaissance préalable de la mise en œuvre : toute notion utilisée
est définie à son premier usage.

### 1.6 Correspondance avec les 4 phases de la commande initiale

Le document de cadrage remis par le commanditaire (§ en tête de ce protocole) structure le travail
en 4 phases. Ce protocole détaille le même travail en 10 sections plus fines (§ 2 à § 10) ; la
table ci-dessous fait la correspondance, phase par phase, en signalant explicitement où le
contenu livré diverge de ce que la commande décrivait.

| Phase (commande initiale) | Ce que la commande décrivait | Ce qui est réellement livré | Section |
|---|---|---|---|
| Phase 1 — Analyse de conformité et conception d'une nouvelle procédure | Audit de l'existant (constat du champ `Root cause` inexploité), conception d'une procédure de préparation des données | Identique sur l'audit (§ 2, § 3.1-3.2) et la procédure de préparation (nettoyage, masquage, normalisation, § 3.3) | § 2, § 3 |
| Phase 2 — Analyse des causes profondes | Sentiment analysis (négatif/neutre/positif) + topic modeling par catégorie, pour nourrir un dashboard | **Diverge** : classification causale par règles (auditable ligne à ligne) en lieu et place du sentiment (justifié § 4.1), complétée par du topic modeling sur les catégories hors du périmètre des règles (notebook 07) | § 4 |
| Phase 3 — Formulation des recommandations opérationnelles | Statistiques et graphes dans un dashboard Streamlit, priorisation des recommandations | **Diverge sur le support** : mêmes statistiques (§ 5), mais restituées en tables et figures versionnées (`resultats/`) au sein de notebooks reproductibles, pas dans un dashboard interactif — voir l'écart assumé en tête de document | § 5, notebook 06 |
| Phase 4 — Évaluation de la responsabilité vis-à-vis des créanciers | Isoler les motifs à dysfonctionnement confirmé, quantifier volume et montants, depuis le dashboard | Identique sur le fond (§ 4.2 rang 2 et 4, § 5.1) — l'exposition financière en ordre de grandeur **est** la lecture de responsabilité vis-à-vis des clients lésés (créanciers de la banque au sens de dépositaires) ; restituée en table plutôt qu'en vue dashboard | § 4.2, § 5.1 |

---

## 2. Sources de données

### 2.1 Description de la source

| | |
|---|---|
| Système d'origine | Outil de support client Intercom |
| Fichier | `SRC_Intercom_Reclamation_202607201846.csv` |
| Mode d'extraction | **[À COMPLÉTER]** — export CSV depuis Intercom, mécanisme exact (API, export manuel, connecteur) non documenté dans le dépôt |
| Date d'extraction | 20/07/2026, d'après l'horodatage porté par le nom du fichier |
| Granularité | Une ligne par réclamation (ticket) |

### 2.2 Volumétrie et période couverte

| | |
|---|---|
| Volumétrie brute | 18 094 réclamations, 67 champs |
| Lignes physiques du fichier | ~23 000 — l'écart vient des descriptions multi-lignes, recollées correctement par le parseur CSV |
| Période totale du fichier | février 2024 → juillet 2026 |
| Période opérationnelle retenue | novembre 2025 → juillet 2026 : 18 056 réclamations sur 9 mois (§ 3.4) |
| Dernier mois | juillet 2026, **partiel** — extraction faite le 20 du mois, exclu de toute comparaison mensuelle |

### 2.3 Dictionnaire des variables retenues

67 champs sont exportés ; 31 sont écartés en 3.4. Les 13 champs ci-dessous portent l'ensemble de
l'analyse.

| Variable | Type | Signification métier | Taux de remplissage |
|---|---|---|---|
| `created_at` | Horodatage système | Date de dépôt de la réclamation | 100,0 % |
| `updated_at` | Horodatage système | Dernière modification du dossier — **pas** une date de clôture | 100,0 % |
| `ticket_type_name` | Catégorie | Produit déclaré au dépôt (SARA, COMPTE, CARTE…), 17 valeurs | 100,0 % |
| `ticket_state_category` | Catégorie | Statut du dossier, 4 valeurs | 100,0 % |
| `channel` | Catégorie | Canal de dépôt, 7 valeurs | 100,0 % |
| `contacts_contacts` | Identifiant (JSON) | Identifiant client, 10 955 valeurs distinctes | 100,0 % |
| `ticket_parts_total_count` | Compteur | Nombre d'échanges dans la conversation — nature exacte non vérifiée (§ 6.3) | 100,0 % |
| `admin_assignee_id` | Identifiant | Agent affecté, 8 valeurs distinctes | 100,0 % |
| `team_assignee_id` | Identifiant | Équipe affectée, 4 valeurs distinctes | 100,0 % |
| `ticket_attributes__default_description_` | Texte libre | Description écrite par le client | 45,66 % (54,34 % manquant) |
| `ticket_attributes_Agence` | Catégorie | Agence concernée, 112 valeurs | 42,12 % (57,88 % manquant) |
| `ticket_attributes_Montant en XAF` | Montant, saisi à la main | Montant en jeu | 39,96 % (60,04 % manquant) |
| `ticket_attributes__default_title_` | Texte libre | Titre écrit par le client ou l'agent | 29,66 % (70,34 % manquant) |

### 2.4 ⚠️ Limites connues de la source à la collecte

1. **Deux champs sont tronqués à l'extraction.** `ticket_parts_ticket_parts` (le fil de
   conversation) et `ticket_type_ticket_type_attributes_data` valent exactement `[{"t` (4
   caractères) sur les 18 094 lignes, sans exception. Deux autres colonnes JSON du même fichier —
   `contacts_contacts` (jusqu'à 193 caractères) et `linked_objects_data` (jusqu'à 239) — ne le sont
   pas : la troncature n'est donc pas uniforme sur les colonnes JSON. Le compteur associé,
   `ticket_parts_total_count`, a bien été exporté ; son minimum est de 5 échanges par ticket, y
   compris pour des tickets sans aucun contenu — indice que ce compteur inclut des événements
   système, pas seulement des messages humains (§ 6.3).
2. **Le mode d'extraction n'est pas documenté** (2.1) : la cause de la troncature — export partiel,
   limitation d'API, choix délibéré — n'est établie nulle part.
3. **La collecte des champs de formulaire s'est interrompue** pendant plusieurs semaines au
   printemps 2026, indépendamment du volume de réclamations reçues (§ 3.2).
4. **La source contient des données à caractère personnel en clair** : noms, numéros de téléphone,
   numéros de compte, et un texte libre qui cite fréquemment montants, dates d'opération et
   références de transaction (§ 7.1).

---

## 3. Qualité et préparation des données

### 3.1 Contrôles de qualité appliqués

| Contrôle | Constat |
|---|---|
| Doublons de ligne complète | 0 |
| Doublons sur `id` | 0 |
| Doublons sur `ticket_id` | 0 |
| Incohérences `created_at > updated_at` | 0 |
| Champs constants (une seule valeur) | 16 |
| Champs vides à 99 % ou plus | 15 |
| Champs tronqués à l'extraction | 2 (§ 2.4) |

La couche système d'Intercom (identifiants, horodatages) est saine sur tous ces contrôles ; le
défaut de qualité est entièrement concentré sur les champs de formulaire saisis à la main.

### 3.2 Anomalies identifiées et traitement retenu

**Anomalie 1 — rupture de la collecte des champs de formulaire, datée au 13 mars 2026.**

Quatre champs indépendants (description, titre, montant, agence) tombent ensemble en 48 heures :

| Jour | Volume | Part de tickets sans contenu |
|---|---|---|
| 12/03/2026 | 19 | 0 % |
| 13/03/2026 | 69 | 81 % |
| 14/03/2026 | 57 | 96 % |
| 15/03/2026 | 54 | 100 % |

Les champs remontent ensemble mi-mai 2026. Quatre champs de nature différente, alimentés à des
moments différents du parcours, ne disparaissent pas ensemble par hasard : un afflux réel de
réclamations n'a aucune raison de vider les formulaires. **Traitement retenu** : l'épisode est
qualifié d'incident de collecte, pas d'incident produit — voir le critère d'exclusion en 3.4.
**[À COMPLÉTER]** — le mécanisme exact (mise en production applicative, modification du
connecteur Intercom) n'est pas confirmé, cf. § 6.3, point 1.

**Anomalie 2 — montants aberrants sur `Montant en XAF`.**

Champ saisi à la main, renseigné sur 39,96 % des réclamations. Il comporte des valeurs négatives
et nulles, concentrées sur des catégories précises, et un amas de valeurs extrêmes au-delà de
10 M XAF. **Traitement retenu** : seules les valeurs strictement positives et inférieures à un
plafond sont conservées pour hiérarchiser les familles entre elles (seuil et justification en
§ 3.4 et § 4.3) ; aucun total n'est communiqué comme chiffre officiel (§ 5.1). Les valeurs
négatives et nulles ne sont pas supprimées de l'analyse descriptive : elles portent probablement du
sens métier (régularisation, opération non aboutie) et restent à qualifier avec le métier (§ 8.4).

**Anomalie 3 — deux définitions concurrentes de « réclamation sans contenu » coexistaient dans le
code source** avant la rédaction de ce protocole (l'une sur les champs bruts non normalisés, l'autre
sur le texte concaténé et normalisé), produisant des effectifs différents selon le notebook.
**Traitement retenu** : une seule définition est admise, fixée en § 3.3.

### 3.3 Règles de nettoyage et de transformation

1. **Chargement sans inférence de type.** Le CSV est lu entièrement en chaînes de caractères.
   Une inférence automatique transformerait les numéros de compte et de téléphone en valeurs
   numériques et en détruirait les zéros de tête. Chaque conversion est ensuite faite
   explicitement, colonne par colonne, avec un comptage des valeurs non convertibles.
2. **Normalisation du texte** — appliquée avant toute classification : suppression des accents
   (l'encodage de l'export est instable — un même mot apparaît accentué, mal encodé et non
   accentué dans le même fichier), réduction des espaces multiples, passage en minuscules.
3. **Construction du texte de la réclamation** — concaténation du titre et de la description,
   champs absents traités comme vides, puis normalisation. Les deux champs sont complémentaires :
   70,3 % des réclamations n'ont pas de titre, 54,3 % pas de description, mais seulement 54,2 %
   n'ont ni l'un ni l'autre.
4. **Masquage des identifiants dans le texte** — avant tout affichage ou écriture d'un texte de
   réclamation : numéros de compte, références de transaction, numéros de téléphone et adresses
   électroniques sont remplacés par des jetons stables (`[COMPTE]`, `[TEL]`, `[REF]`, `[EMAIL]`).
   Les montants (4 à 5 chiffres) sont préservés ; le sens de la plainte reste intact pour la
   classification (§ 4, § 7.3).

### 3.4 ⚠️ Critères d'exclusion

Chaque exclusion porte son seuil chiffré, le critère qui le fixe, et l'endroit du code où il est
défini (`niv/src/reclamations/config.py`, sauf mention contraire).

| # | Exclusion | Seuil | Critère de fixation | Effectif exclu |
|---|---|---|---|---|
| 1 | Phase pilote | avant le 1ᵉʳ novembre 2025 (`DEBUT_PERIODE_OPERATIONNELLE`) | Bascule complète de la répartition par canal de part et d'autre de la date (messenger 42,1 % → 0,0 % ; android 13,2 % → 65,7 % ; whatsapp 0,0 % → 12,7 %) | 38 réclamations sur 21 mois |
| 2 | Réclamation sans texte exploitable | longueur du texte concaténé ≤ 25 caractères (`LONGUEUR_TEXTE_MIN`) | En deçà, le contenu ne porte aucune information causale (titre générique, mot isolé) | dépend du périmètre retenu (voir 3.5) |
| 3 | Journée à collecte dégradée | couverture texte de la journée < 50 % **[À intégrer au code — actuellement une exclusion par mois entier, voir note ci-dessous]** | Décrochage net de la distribution des journées : sur les 247 journées de la période opérationnelle, 59 sont à 0-10 % de couverture et 184 à 70-100 % ; seules 3 journées se situent entre les deux | voir § 3.5 |
| 4 | Montant hors bornes | montant ≤ 0 ou ≥ 10 000 000 XAF (`MONTANT_PLAFOND_PLAUSIBLE`) | Amas de valeurs manifestement artificielles au-delà de ce seuil, sur un champ saisi à la main | dépend de la famille (§ 5.1) |

**Note sur l'exclusion n° 3.** Le code actuel (`config.MOIS_COLLECTE_DEGRADEE`) exclut mars,
avril et mai 2026 **en mois entiers**, ce qui écarte aussi des journées antérieures au 13 mars,
correctement documentées. Ce protocole retient une règle plus fine, à la journée, dont le calcul
et la validation figurent en 4.4. Elle récupère 31 journées et 1 083 réclamations supplémentaires,
sans réintroduire le biais qui a justifié l'exclusion mensuelle (§ 4.4). **Cette règle n'est pas
encore implémentée dans `config.py`** ; le jeu de données de la section 3.5 l'anticipe et le
signale.

### 3.5 Jeu de données final retenu

| Périmètre | Effectif | Base textuelle | Usage |
|---|---|---|---|
| Période opérationnelle complète | 18 056 | — | Analyse par client, récidive, charge (§ 5.2) — n'utilise que des champs système, alimentés pendant la panne |
| Périmètre d'analyse causale — règle par mois *(implémentée)* | 6 867 | 6 545 (95,3 %) | Valeur actuellement produite par le code |
| Périmètre d'analyse causale — règle à la journée *(retenue, § 3.4 note)* | 7 950 | 7 563 (95,1 %) | Valeur cible de ce protocole, +1 083 réclamations |

---

## 4. Méthodologie d'analyse

### 4.1 Approche générale et justification du choix

L'intitulé initial du travail évoque une analyse de sentiment. La méthode retenue est une
**classification causale par règles**, pour trois raisons :

1. La question posée est *pourquoi* le client se plaint, non *avec quelle intensité* : la polarité
   d'un corpus composé à 100 % de réclamations est négative par construction et n'a aucun pouvoir
   discriminant.
2. Une classification par règles est auditable ligne à ligne — exigence d'un usage bancaire où
   chaque affirmation doit être remontée jusqu'au texte qui la fonde.
3. Le taux de couverture des règles est lui-même un résultat de l'étude : il chiffre l'intérêt d'un
   modèle appris pour une itération suivante, au lieu de le postuler.

### 4.2 Méthodes et algorithmes utilisés

- **Classification** : reconnaissance de motifs par expressions régulières sur le texte normalisé
  (§ 3.3). Aucun modèle appris, aucun lexique externe à ce stade. Sept familles **exclusives**,
  appliquées dans un ordre de priorité fixe (la première règle qui correspond fixe la famille) :

| Rang | Famille | Responsable présumé — **non validé, § 8.4** |
|---|---|---|
| 1 | Erreur de saisie du client (mauvais bénéficiaire) | Ergonomie de l'application |
| 2 | Débité sans que le bénéficiaire soit crédité | Chaîne technique banque ↔ opérateur |
| 3 | Accès bloqué, code à usage unique, authentification | Authentification |
| 4 | Débit injustifié, doublé, ou frais contestés | Système bancaire |
| 5 | Carte bancaire ou distributeur | Monétique |
| 6 | Demande d'information (pas une réclamation) | Hors périmètre |
| 7 | Dysfonctionnement de l'application hors flux d'argent **[À intégrer au code]** | Éditeur de l'application |

  Le rang 1 est justifié : un client qui s'est trompé de numéro décrit aussi de l'argent parti sans
  arriver, et son aveu explicite d'erreur doit être testé avant la famille dominante sous peine
  d'en être absorbé. Les rangs suivants ne sont pas justifiés individuellement dans le code ; leur
  effet est mesuré, pas argumenté (§ 4.4, sensibilité à l'ordre).

  La 7ᵉ famille (rang 7) n'existe pas dans le code actuel. Elle est retenue ici parce que l'audit
  manuel (§ 4.5) montre que 2 des 20 textes non classés relèvent d'un dysfonctionnement applicatif
  qu'aucune des six familles existantes ne couvre (« je n'arrive pas à ajouter de bénéficiaire »,
  « mon compte bancaire a disparu dans l'application »).

- **Audit du reliquat non classé** : échantillon aléatoire, relecture manuelle, décision binaire
  par texte — nouvelle famille ou famille existante mal détectée.
- **Extrapolation** : la structure observée dans l'audit redistribue le reliquat non classé sur
  l'ensemble des familles qu'il contient (règle d'intégralité, § 5.1).
- **Extraction d'entités** : dénombrement (non exclusif) des mentions d'opérateur et de sens de
  flux dans les textes de la famille dominante.

### 4.3 Paramètres et seuils retenus

| Paramètre | Valeur | Défini dans |
|---|---|---|
| `DEBUT_PERIODE_OPERATIONNELLE` | 2025-11-01 | `config.py` |
| `LONGUEUR_TEXTE_MIN` | 25 caractères | `config.py` |
| `MOIS_COLLECTE_DEGRADEE` | mars, avril, mai 2026 *(règle en cours de remplacement, § 3.4)* | `config.py` |
| Couverture journalière minimale | 50 % | **[À intégrer au code]** |
| `MONTANT_PLAFOND_PLAUSIBLE` | 10 000 000 XAF | `config.py` |
| `FENETRE_REDEPOT_JOURS` | 7 jours | `config.py` |
| Longueur suspecte pour détecter une troncature | 8 caractères | `chargement.colonnes_tronquees()` |
| Longueur maximale d'une cellule dans `resultats/tables/` | 200 caractères — refus d'écriture au-delà | `config.LONGUEUR_CELLULE_MAX`, appliqué par `sauver_table()` |
| Graine de l'échantillon d'audit | 3 | `texte.echantillon_non_classes()` |
| Taille de l'échantillon d'audit initial | 20 textes | notebook 04 |
| Seuil de force d'association (représentativité) | V de Cramér ≤ 0,20 | § 4.4 |

### 4.4 ⚠️ Test de représentativité

**Mesure retenue : le V de Cramér**, entre l'appartenance au groupe « texte disponible / texte
absent » et une variable observable pour l'ensemble des réclamations (type de produit, canal,
statut). Cette mesure normalise le χ² par la taille de l'échantillon et le nombre de catégories,
ce qui permet de comparer des tests portant sur des tables de tailles différentes — condition
nécessaire ici, puisque les groupes comparés changent de taille d'un test à l'autre.

**Seuil retenu : 0,20.** Le seuil conventionnel exact dépend en toute rigueur du nombre de degrés
de liberté de chaque table (`ticket_type_name` compte 17 catégories, `channel` en compte 7), et
n'est donc pas une valeur universelle. Il est retenu ici comme repère rond et conservateur ; ce qui
porte la décision n'est pas la position exacte du seuil mais l'écart d'un ordre de grandeur entre
les résultats ci-dessous.

| Test | `ticket_type_name` | `channel` | `ticket_state_category` | Décision |
|---|---|---|---|---|
| Hors fenêtre dégradée — texte présent vs absent | **V = 0,204** | V = 0,110 | V = 0,035 | À la limite du seuil sur le type ; le groupe sans texte ne pèse que 4,7 % de ce périmètre, son influence sur la répartition d'ensemble reste marginale |
| Dans la fenêtre dégradée — survivants vs reliquat | **V = 0,379** | V = 0,170 | — | Nettement au-dessus du seuil : les tickets qui ont conservé du texte pendant la panne ne sont pas représentatifs de ceux qui l'ont perdu |
| Journées récupérées (couverture ≥ 50 %) vs mois sains — règle retenue en § 3.4 | V = 0,188 | V = 0,035 | — | Sous le seuil sur les deux variables : ces journées sont admissibles |

Sur ce dernier test, l'écart le plus visible à l'œil — le canal `whatsapp`, à −17,6 points dans la
fenêtre dégradée globale — **tombe à −1,7 point** sur les seules journées récupérées : c'est ce
qui distingue une journée de collecte fonctionnelle d'un jour trié par la panne. Un écart subsiste
sur `BENEFICIAIRE ERRONE` (+12,5 points), plus marqué chez les journées récupérées que chez les
survivants isolés du reliquat (+10,4 points) : l'explication la plus cohérente n'est pas une
sélection par le bug — qui produirait l'effet inverse — mais une hausse réelle de ce motif au
printemps 2026, à investiguer plutôt qu'à exclure (§ 8.4).

### 4.5 Méthode de validation des résultats

| Étape | Taille | Statut |
|---|---|---|
| Audit manuel initial du reliquat non classé | 20 textes, une seule personne, graine fixe (3) | Fait — intervalle de confiance ±21 points, résultat qualifié d'ordre de grandeur |
| Jeu de référence annoté | 300 textes : 150 non classés, 150 classés, stratifiés par famille (minimum 15 par famille) | **[À réaliser]** |
| Double annotation | 100 des 300 textes, par deux personnes indépendantes | **[À réaliser]** — critère d'accord : coefficient kappa ≥ 0,70 |
| Mesure de qualité | Précision, rappel et F1 par famille, matrice de confusion | **[À réaliser]**, dépend du jeu de référence |
| Test de sensibilité à l'ordre des familles | Évaluation, pour chaque texte, de l'ensemble des familles dont les règles correspondent, indépendamment de l'ordre appliqué | **[À réaliser]** |

**Correction de calcul.** Avec 150 textes non classés annotés, la demi-largeur de l'intervalle de
confiance à 95 % sur une proportion proche de 0,5 est de ±8,0 points (1,96 × √(0,25/150)), et non
±6 points comme énoncé dans une version antérieure de ce document — cette dernière valeur
demanderait 267 textes. La cible retenue est ±8 points avec 150 textes.

---

## 5. Indicateurs et variables d'analyse

### 5.1 Définition opérationnelle de chaque indicateur

| Indicateur | Formule | Base |
|---|---|---|
| Taux de couverture des règles | (textes classés dans une famille) / (textes exploitables) | Base textuelle du périmètre causal |
| Répartition par famille causale | effectif de la famille / effectif de la base | idem, `non_classe` toujours affiché |
| Estimation corrigée par famille | pct(famille, règles) + pct(non classé) × (n_famille_dans_l'audit / taille_audit) — **toutes** les familles observées dans l'audit sont redistribuées, aucune n'est écartée | Base textuelle + audit |
| Taux de dépôt répété | réclamations d'un client < 7 jours après une réclamation antérieure de même catégorie / total des réclamations | Période opérationnelle complète, publié en fourchette (borne haute : même catégorie seule ; borne basse : même catégorie **et** identité de l'opération) |
| Part de clients récidivistes | clients ayant déposé ≥ 2 réclamations / clients distincts | idem |
| Exposition financière par famille | médiane des montants plausibles (§ 3.4, exclusion 4) par famille — jamais un total | Réclamations à montant renseigné et plausible |
| Mentions d'opérateur / de sens de flux | comptage non exclusif de motifs dans le texte, rapporté à la base — **pas** un taux de défaillance | Famille dominante uniquement |

### 5.2 Variables de segmentation retenues

Mois, canal de dépôt, type de produit déclaré (`ticket_type_name`), famille causale, responsable
présumé de la correction, identifiant client (pour le passage de l'unité « réclamation » à l'unité
« client »), agence (couverture partielle, 42,1 %).

### 5.3 ⚠️ Indicateurs écartés et pourquoi

| Indicateur envisagé | Pourquoi il est écarté |
|---|---|
| Taux de résolution | Le statut `submitted` (90,3 % des réclamations) est ambigu : il peut désigner une réclamation en attente ou un état terminal de workflow. Aucune conclusion n'est publiable tant que ce point n'est pas tranché avec l'équipe support (§ 6.3, § 8.4) |
| Délai de traitement | `updated_at` n'est pas une date de clôture ; il bouge à chaque modification du dossier. Tout délai qui en serait dérivé n'est qu'un proxy grossier |
| Taux de défaillance par opérateur mobile money | Un décompte de mentions confond le problème réel et la part de marché de l'opérateur dans la base client ; le dénominateur (volume de transactions par opérateur) est absent |
| Taux d'incident par transaction | Retenu comme indicateur **cible** (§ 1.2), mais non calculable : aucun journal de transactions n'est disponible dans cette source (§ 6.1) |
| Charge de traitement en « messages humains » | Le compteur `ticket_parts_total_count` n'est pas vérifié comme comptant exclusivement des messages humains (§ 2.4, § 6.3) ; tout ratio qui en dérive est publié comme conditionnel, jamais comme un fait |

---

## 6. Limites et biais

### 6.1 Limites structurelles — ce que les données ne permettront jamais d'établir

1. **Absence de dénominateur.** L'export recense des réclamations, jamais des transactions. Un
   même effectif de plaintes est compatible avec un taux d'échec critique ou négligeable.
2. **Fil de conversation absent.** Le contenu des échanges agent/client est tronqué à l'extraction
   (§ 2.4) : ce qui a été demandé, répondu, et l'issue du dossier restent hors de portée.
3. **Aucune trace technique.** Ni code d'erreur, ni identifiant de transaction technique, ni statut
   de passerelle : l'endroit où une transaction casse n'est pas observable depuis Intercom.
4. **Population non plaignante hors de portée.** Les clients qui subissent un incident sans se
   plaindre sont absents du fichier par construction.

### 6.2 Biais méthodologiques identifiés

1. **Ordre des familles causales.** L'ordre d'application des règles influe sur le résultat de
   classification ; son effet n'est pas encore mesuré (test prévu en § 4.5).
2. **Taille de l'audit initial.** 20 textes, un seul annotateur, aucune validation croisée —
   traité comme insuffisant et corrigé par le jeu de référence de 300 textes (§ 4.5).
3. **Stratification de l'échantillon de validation non repondérée.** L'échantillonnage par famille
   avec un minimum de 15 textes garantit la représentation des familles rares, mais toute mesure
   de précision globale calculée dessus doit être repondérée par les effectifs réels des familles,
   sous peine de surestimer la qualité sur les familles rares.
4. **Le critère d'identité d'opération**, utilisé pour la borne basse du taux de dépôt répété
   (§ 5.1), repose sur des champs (montant, référence, date d'opération) renseignés à seulement
   3 % en mars-avril 2026 — précisément les mois où le taux de dépôt répété culmine à 24,3 %. La
   borne basse sera donc peu fiable sur cette période.

### 6.3 ⚠️ Hypothèses non vérifiables depuis les données seules

| # | Hypothèse | Ce qui la fonde | Ce qui manque pour la confirmer |
|---|---|---|---|
| 1 | La rupture du 13 mars 2026 est une mise en production, pas un incident produit | Concomitance de quatre champs indépendants qui tombent et reviennent ensemble en 48 heures | Historique des mises en production et des modifications de configuration du workspace Intercom |
| 2 | La famille dominante correspond à un incident technique sur la chaîne SARA ↔ mobile money | Description faite par les clients | Aucune trace technique disponible depuis Intercom |
| 3 | `ticket_parts_total_count` compte des messages humains | — | Le minimum de 5 par ticket, y compris sur des tickets vides, suggère l'inclusion d'événements système ; invérifiable tant que le contenu des parts reste tronqué |
| 4 | Le mapping famille → responsable de la correction est correct | Cohérence métier apparente | Aucune équipe technique ou métier ne l'a validé (§ 8.4) |

### 6.4 Impact de ces limites sur l'interprétation des résultats

Ce que l'étude établit : la **hiérarchie des motifs** entre eux et la structure du problème tel que
les clients le décrivent. Ce qu'elle n'établit pas : la fréquence d'un incident rapportée à
l'activité (6.1-1), le mécanisme technique exact (6.3-2), ni un taux de résolution ou un délai de
traitement (5.3). Toute lecture de ce rapport qui franchirait ces bornes outrepasse ce que la
source permet d'affirmer.

---

## 7. Gouvernance et conformité des données

### 7.1 Nature des données traitées

Données personnelles (noms, numéros de téléphone, numéros de compte), données financières
(montants de transaction), et texte libre à caractère sensible — les réclamations citent
couramment des montants, des dates d'opération et des références de transaction.

### 7.2 Cadre réglementaire applicable

**[À COMPLÉTER — à faire confirmer par le service juridique / conformité de la banque.]** Ce
document ne cite aucun texte réglementaire précis faute de pouvoir en garantir l'exactitude et
l'applicabilité actuelle. Le point à faire trancher : quel cadre régit le traitement de données
client à des fins d'analyse interne (secret bancaire, réglementation de protection des données
personnelles applicable, politique interne de la banque).

### 7.3 Mesures d'anonymisation et de sécurité

Ces mesures ont été renforcées après qu'une exposition réelle a été constatée dans l'historique
du dépôt (deux tables versionnées portaient le nom, le téléphone et des verbatims complets d'un
client réel) ; l'incident a été corrigé par réécriture de l'historique et les mesures suivantes
ont été mises en place pour empêcher sa reproduction :

| Mesure | Mise en œuvre |
|---|---|
| Masquage à l'écriture des champs nominatifs | `config.est_colonne_sensible()` — 35 des 67 champs n'émettent plus d'exemple de valeur dans les tables de contrôle qualité |
| Masquage des identifiants dans le texte libre | `texte.masquer_identifiants()` — comptes, références, téléphones, courriels remplacés par des jetons stables avant tout affichage ou écriture ; les montants sont préservés |
| Garde-fou structurel sur les tables versionnées | `chargement.sauver_table()` **refuse** l'écriture de toute cellule dépassant 200 caractères — une réclamation ne peut pas franchir ce point de sortie |
| Séparation des sorties par sensibilité | Les fichiers portant du texte de réclamation vont dans `data/audit/`, hors dépôt ; `resultats/tables/` est réservé aux agrégats, en liste blanche explicite dans `.gitignore` |
| Fichier source | Jamais versionné ni copié hors de l'environnement de travail |

Le masquage est appliqué **à l'écriture**, jamais à la relecture : une donnée qui n'a jamais été
écrite en clair ne peut pas fuiter par ce chemin.

### 7.4 Restrictions de diffusion des résultats

| Règle | Portée |
|---|---|
| Aucun texte client intégral n'est écrit dans un fichier partagé ou versionné | Toutes les tables produites |
| Un verbatim cité dans le mémoire ou une présentation est masqué et limité à 200 caractères | Rapports et présentations |
| Diffusion interne uniquement, aucun dépôt public | Ensemble des productions |
| Un nouvel export ne remplace jamais silencieusement le précédent | Réexécution complète et comparaison explicite exigées |

---

## 8. Livrables et critères de succès

### 8.1 Liste des livrables attendus

- Mémoire tutoré (document écrit).
- Ce protocole d'étude.
- Pipeline de code reproductible (`niv/src/reclamations/`, notebooks 01-06).
- Tables et figures de `niv/resultats/` (agrégats uniquement, § 7.3).
- **[À COMPLÉTER]** — support de soutenance, s'il est requis.

### 8.2 Format et destinataire de chacun

| Livrable | Format | Destinataire |
|---|---|---|
| Mémoire | Document écrit | Maître de stage, jury |
| Protocole d'étude | Markdown (ce document) | Maître de stage, toute personne reprenant le travail |
| Code | Notebooks Jupyter + package Python | Ingénieurs data |
| Tables et figures | CSV, PNG | Annexes du mémoire, réutilisation par un tiers |

### 8.3 ⚠️ Critères de succès mesurables

| Critère | Seuil |
|---|---|
| Représentativité du périmètre retenu | V de Cramér ≤ 0,20 sur les variables observables (§ 4.4) — **atteint** |
| Fiabilité de l'annotation du jeu de référence | Kappa ≥ 0,70 (§ 4.5) — **à mesurer** |
| Précision de l'estimation du reliquat non classé | ± 8 points sur 150 textes annotés (§ 4.5) — **à réaliser** |
| Robustesse à l'ordre des familles causales | Chevauchements mesurés ; fourchette publiée si non négligeables (§ 4.5) — **à réaliser** |
| Traçabilité des chiffres publiés | Tout chiffre du mémoire relu depuis une table de `resultats/tables/`, jamais recopié à la main |
| Absence de donnée personnelle dans les livrables versionnés | 0 occurrence de nom, téléphone, numéro de compte ou verbatim intégral (§ 7.3) — **atteint** |
| Calendrier | **[À COMPLÉTER]**, dépend de 9.1 |

### 8.4 Points nécessitant une validation métier

| # | Point | Interlocuteur | Ce qui reste bloqué |
|---|---|---|---|
| 1 | Cause de la rupture de collecte du 13 mars 2026 | Équipe applicative / administrateur Intercom | Qualification de l'incident, non-reproduction |
| 2 | Diagnostic technique sur la chaîne SARA ↔ opérateurs | Équipe technique | Toute conclusion technique |
| 3 | Attribution de chaque famille causale à un responsable de correction | Métier et équipes concernées | Toute allocation de charge corrective |
| 4 | Signification du statut `submitted` | Responsable du support | Tout taux de résolution |
| 5 | Nature exacte de `ticket_parts_total_count` | Administrateur Intercom | Tous les indicateurs de charge |
| 6 | Fiabilité du champ montant | Métier | Toute conclusion d'exposition financière |
| 7 | Mode d'extraction et cause de la troncature | Administrateur Intercom | La ré-extraction demandée ci-dessous |
| 8 | Effectif réel affecté au traitement (8 `admin_assignee_id` distincts) | Responsable du support | Tout ratio par agent |
| 9 | Cadre réglementaire applicable (§ 7.2) | Service juridique / conformité | Toute communication externe des résultats |

**Données demandées, par ordre de ce qu'elles débloquent :**

1. **Journal des transactions SARA** (identifiant, montant, opérateur, sens, horodatage, statut
   technique, code d'erreur), rapprochable aux réclamations par montant, numéro et date — lève la
   limite principale de l'étude (§ 6.1-1, § 1.2).
2. **Ré-extraction Intercom avec le fil de conversation complet** — débloque la charge réelle de
   traitement et l'issue des dossiers (§ 6.1-2).
3. **Date de clôture et issue du dossier** (remboursé, rejeté, sans suite) — rend le taux de
   résolution publiable (§ 5.3).

---

## 9. Organisation et calendrier

### 9.1 Phases et jalons

**[À COMPLÉTER]** — le calendrier précis n'est pas fixé dans ce document. La chaîne d'analyse
existante donne la structure de phases suivante, à dater avec le maître de stage :

| Phase | Contenu | Notebook |
|---|---|---|
| 1 | Chargement et qualité de la source | 01 |
| 2 | Datation de la rupture de collecte | 02 |
| 3 | Périmètre et représentativité | 03 |
| 4 | Classification causale | 04 |
| 5 | Récidive et charge de traitement | 05 |
| 6 | Synthèse et énoncé de la problématique | 06 |
| 7 | Constitution du jeu de référence et validation (§ 4.5) | à créer |
| 8 | Rédaction du mémoire | — |

### 9.2 Rôles et responsabilités

**[À COMPLÉTER]**

### 9.3 Points de validation intermédiaires

Les points de la section 8.4 constituent les validations intermédiaires attendues avant que les
conclusions correspondantes puissent être publiées dans le mémoire. Leur calendrier de traitement
est **[À COMPLÉTER]**.

---

## 10. Reproductibilité

### 10.1 Environnement technique

`niv/requirements.txt`, versions minimales testées sur **Python 3.13** :

```
pandas>=2.2      # taux_completude() utilise groupby().apply(include_groups=False), pandas 2.2+
numpy>=1.26
matplotlib>=3.8
jupyterlab>=4.0
ipykernel>=6.29
jupytext>=1.16   # optionnel — conversion notebook <-> script diffable
```

Environnement de rédaction de ce document : pandas 2.3.3.

### 10.2 Organisation du code et des fichiers

```
niv/
├── src/reclamations/          logique partagée entre notebooks
│   ├── config.py              chemins, seuils de périmètre, règles de confidentialité
│   ├── chargement.py          chargement, typage, contrôles qualité, périmètres, sauvegarde
│   ├── texte.py                normalisation, masquage, taxonomie causale
│   └── viz.py                 charte graphique
├── notebooks/                  01 à 06, indépendants — chacun recharge la source
├── data/audit/                 fichiers de travail portant du texte client — non versionné
└── resultats/
    ├── figures/                non versionné
    └── tables/                 versionné — réservé aux agrégats (§ 7.3)
```

### 10.3 Commandes d'exécution de la chaîne complète

```bash
cd niv
pip install -r requirements.txt

# Exécution interactive
jupyter lab notebooks/

# Exécution complète non interactive
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb

# Version diffable des notebooks
jupytext --to py:percent notebooks/*.ipynb
```

Le seul tirage aléatoire de la chaîne (`texte.echantillon_non_classes(graine=3)`) est fixé : à
données d'entrée identiques, la chaîne est reproductible à l'identique.

### 10.4 Traçabilité des versions

- Le CSV source n'est pas versionné (`data/`, `*.csv` dans `.gitignore`). `config.chemin_donnees()`
  résout le fichier le plus récent par nom horodaté dans quatre emplacements candidats ; un nouvel
  export ne remplace jamais silencieusement le précédent (§ 7.4).
- L'historique git du dépôt a été réécrit pour retirer une exposition de données personnelles
  constatée dans un commit antérieur (§ 7.3). Toute personne ayant cloné le dépôt avant cette
  réécriture doit re-cloner plutôt que `git pull`.
- État de ce document au moment de sa rédaction : commit `7533f98` sur `main`.

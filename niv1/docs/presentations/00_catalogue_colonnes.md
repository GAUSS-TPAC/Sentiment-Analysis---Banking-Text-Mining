# Discours — Catalogue des colonnes : à quoi sert chacune dans l'analyse

*Source : `SRC_Intercom_Reclamation_202607201846.csv` (18 094 lignes, 67 colonnes) + colonnes produites par le pipeline (`notebooks/02` à `05`)*

---

## Introduction

Avant de décider quelles colonnes garder, enrichir ou ignorer, il faut avoir sous les yeux l'inventaire complet, avec pour chacune : son taux de remplissage, sa cardinalité (nombre de valeurs distinctes), et surtout — le sujet de ce document — **à quoi elle sert, ou pourrait servir, dans l'analyse**.

Une note d'utilité accompagne chaque colonne :
- **Essentielle** — déjà au cœur du pipeline actuel (sentiment, topics, KPIs).
- **Utile** — exploitée ou exploitable directement, avec un potentiel analytique clair.
- **Marginale** — anecdotique par le volume, mais pas nécessairement sans intérêt (cas rares, signaux faibles).
- **Sans valeur analytique** — constante, doublon technique, ou artefact d'export : ne porte aucune information distinctive.

Ce classement est une proposition de lecture, pas une décision. Il sert de base à l'échange qui suivra sur les colonnes à conserver, enrichir ou abandonner.

---

## 1. Identifiants & état du ticket

| Colonne | Remplissage | Cardinalité | Utilité dans l'analyse |
|---|---|---|---|
| `type` | 100 % | 1 (`ticket`) | **Sans valeur analytique** — constante sur toute la table (toutes les lignes valent `ticket`). |
| `id` | 100 % | 18 094 | **Utile** — identifiant technique unique Intercom. Sert de clé primaire / de dédoublonnage, pas d'insight direct. |
| `ticket_id` | 100 % | 18 094 | **Utile** — identifiant métier du ticket, visible côté agent. Redondant avec `id` (même cardinalité, même rôle de clé). |
| `ticket_state_type` | 100 % | 1 (`ticket_state`) | **Sans valeur analytique** — constante. |
| `ticket_state_id` | 100 % | 4 | **Marginale** — identifiant numérique de l'état, redondant avec `ticket_state_category`. |
| `ticket_state_category` | 100 % | 4 (`submitted`, `in_progress`, `resolved`, `waiting_on_customer`) | **Utile** — statut d'avancement du traitement. Potentiel : croiser avec le sentiment (un ticket resté longtemps "waiting_on_customer" est-il plus souvent négatif ?), ou mesurer le taux de résolution. Non exploité pour l'instant. |
| `ticket_state_internal_label` | 100 % | 4 | **Marginale** — libellé texte de l'état côté agent, redondant avec `ticket_state_category`. |
| `ticket_state_external_label` | 100 % | 4 | **Marginale** — libellé texte de l'état côté client, redondant avec `ticket_state_category`. |
| `open` | 100 % | 2 (bool) | **Utile** — indicateur binaire ouvert/fermé, dérivé de l'état. Pratique pour un KPI simple "% de tickets encore ouverts". |
| `category` | 100 % | 3 (`Customer`, `Back-office`, `Tracker`) | **Essentielle** — distingue les réclamations clients réelles des tickets internes/techniques. Détermine le périmètre pertinent pour l'analyse de sentiment (le "Back-office" et le "Tracker" ne sont pas des réclamations client). |

## 2. Classification — type de réclamation (`ticket_type_*`)

| Colonne | Remplissage | Cardinalité | Utilité dans l'analyse |
|---|---|---|---|
| `ticket_type_type` | 100 % | 1 (`ticket_type`) | **Sans valeur analytique** — constante. |
| `ticket_type_id` | 100 % | 17 | **Marginale** — identifiant technique de la catégorie, redondant avec `ticket_type_name` (clé de jointure uniquement). |
| `ticket_type_name` | 100 % | 17 (`SARA`, `COMPTE`, `CARTE`, `BENEFICIAIRE ERRONE`, `CREDIT`...) | **Essentielle** — c'est l'axe central de tout le pipeline : catégorie de réclamation, utilisée pour le sentiment par catégorie (notebook 3) et comme périmètre du topic modeling (notebook 4). |
| `ticket_type_description` | 0,15 % | 4 | **Sans valeur analytique** — description générique du *type* de ticket (texte de configuration Intercom, ex. "When a customer query can't be instantly resolved..."), pas du contenu client. |
| `ticket_type_icon` | 100 % | 1 (caractère de contrôle illisible) | **Sans valeur analytique** — artefact d'export. |
| `ticket_type_workspace_id` | 100 % | 1 | **Sans valeur analytique** — constante (un seul espace de travail Intercom). |
| `ticket_type_archived` | 100 % | 1 (`False`) | **Sans valeur analytique** — constante. |
| `ticket_type_created_at` / `ticket_type_updated_at` | 100 % | 16 | **Sans valeur analytique** — dates de configuration du *type* de ticket (pas du ticket lui-même). |
| `ticket_type_is_internal` | 100 % | 2 (bool) | **Marginale** — distingue les types internes des types client-facing ; recoupe `category`/`ticket_type_category`. |
| `ticket_type_category` | 100 % | 3 | **Sans valeur analytique** — doublon exact de `category` (vérifié : correspondance parfaite entre les deux colonnes). |
| `ticket_type_ticket_type_attributes_type` / `_data` | 100 % | 1 | **Sans valeur analytique** — métadonnée de schéma Intercom ; `_data` est en réalité **tronquée à l'export** (toutes les valeurs commencent par `[{"t` et s'arrêtent là), donc inexploitable même si on voulait la parser. |

## 3. Contact, canal, assignation

| Colonne | Remplissage | Cardinalité | Utilité dans l'analyse |
|---|---|---|---|
| `contacts_type` | 100 % | 1 | **Sans valeur analytique** — constante. |
| `contacts_contacts` | 100 % | 10 955 | **Utile (potentiel non exploité)** — JSON contenant l'identifiant du contact client. Permettrait, après parsing, d'identifier les clients réclamant plusieurs fois (fidélité négative, clients à risque) — actuellement non exploité par le pipeline. |
| `admin_assignee_id` | 100 % | 8 | **Marginale** — identifiant de l'agent assigné. Utile pour une analyse de charge/traitement par agent, hors du périmètre sentiment actuel. |
| `team_assignee_id` | 100 % | 4 | **Marginale** — équipe assignée. Même potentiel que ci-dessus, à l'échelle de l'équipe. |
| `channel` | 100 % | 7 (`android`, `whatsapp`, `ios`, `facebook`, `instagram`, `messenger`, `email`) | **Essentielle** — déjà exploitée dans le pipeline (sentiment par canal, notebooks 3 et 5). |
| `is_shared` | 100 % | 2 (bool) | **Sans valeur analytique** — indicateur technique de visibilité côté client dans Intercom, pas de signal métier. |

## 4. Horodatage

| Colonne | Remplissage | Cardinalité | Utilité dans l'analyse |
|---|---|---|---|
| `created_at` | 100 % | 18 064 (quasi unique) | **Essentielle** — base de toute l'analyse temporelle (évolution mensuelle, déjà exploitée en Phase 4). |
| `updated_at` | 100 % | 16 964 | **Utile (potentiel non exploité)** — permettrait de calculer un délai de traitement (`updated_at − created_at`) comme proxy du temps de résolution, croisable avec le sentiment (un traitement long est-il associé à plus d'insatisfaction ?). Non exploité pour l'instant. |

## 5. Parties du ticket / objets liés (métadonnées techniques Intercom)

| Colonne | Remplissage | Cardinalité | Utilité dans l'analyse |
|---|---|---|---|
| `ticket_parts_type` | 100 % | 1 | **Sans valeur analytique** — constante. |
| `ticket_parts_ticket_parts` | 100 % | 1 | **Sans valeur analytique** — champ **tronqué à l'export** (toutes les valeurs sont la fraction `[{"t`), donc inutilisable en l'état. |
| `ticket_parts_total_count` | 100 % | 103 | **Marginale** — nombre d'échanges (messages) sur le ticket. Pourrait être un proxy de complexité du dossier, non exploité. |
| `linked_objects_type` | 100 % | 1 | **Sans valeur analytique** — constante. |
| `linked_objects_data` | 100 % | 18 | **Sans valeur analytique** — quasi toujours `[]` (aucun objet lié) ; les rares valeurs non vides restent un JSON peu exploitable en l'état. |
| `linked_objects_total_count` | 100 % | 5 | **Marginale** — nombre d'objets liés (tickets connexes), signal faible et peu interprété sans le détail. |
| `linked_objects_has_more` | 100 % | 1 (`False`) | **Sans valeur analytique** — constante. |

## 6. Attributs métier fréquents (29 % à 46 % de remplissage)

C'est le groupe qui alimente directement le pipeline NLP et les KPI actuels. Repère important : ces taux de remplissage sont calculés sur les **18 094 tickets**, mais une fois qu'on se restreint aux **8 284 tickets ayant du texte libre** (le périmètre réel du pipeline NLP), certains de ces champs deviennent beaucoup plus fiables — ex. `Montant en XAF` passe de 40 % à **87 %**, `Numero_tel_client` de 43 % à **93 %**.

| Colonne | Remplissage (global / sur texte dispo.) | Cardinalité | Utilité dans l'analyse |
|---|---|---|---|
| `ticket_attributes__default_description_` | 45,66 % | 7 988 | **Essentielle** — texte libre, fusionné avec le titre pour former `texte` (base de tout le pipeline NLP). |
| `ticket_attributes__default_title_` | 29,66 % | 3 326 | **Essentielle** — idem, fusionné avec la description. |
| `ticket_attributes_Nom du client` | 42,67 % | 6 125 | **Utile (sensible)** — PII directe (nom). Utile pour identifier les réclamants récurrents, mais volontairement **non exploitée** dans le texte analysé (bon réflexe de protection des données) ; pertinente seulement pour un usage interne strictement contrôlé. |
| `ticket_attributes_Numero_tel_client` | 42,57 % / **92,93 %** | 5 300 | **Utile** — champ structuré, plus fiable que le téléphone extrait par regex du texte libre. Pourrait servir à croiser/valider `pii_telephones`. |
| `ticket_attributes_Date de la transaction` | 42,27 % | 2 713 | **Utile (potentiel non exploité)** — date de l'opération contestée, distincte de `created_at` (date du ticket). Permettrait de mesurer le délai entre l'incident et la réclamation. |
| `ticket_attributes_Agence` | 42,12 % | 112 | **Utile (potentiel non exploité)** — agence bancaire concernée. Fort potentiel pour une analyse géographique/par agence du sentiment, non exploitée à ce stade. |
| `ticket_attributes_Montant en XAF` | 39,96 % / **87,23 %** | 1 460 | **Essentielle** — déjà exploitée en Phase 4 (montant médian par catégorie). Champ clé pour quantifier l'enjeu financier des réclamations. |
| `ticket_attributes_Numero de compte` | 28,24 % | 3 960 | **Utile (très sensible)** — numéro de compte bancaire. Utile pour du rapprochement opérationnel, mais à traiter avec la plus grande prudence ; volontairement absent du texte analysé par les modèles NLP. |
| `ticket_attributes_Reference de la transaction` | 21,49 % | 3 295 | **Utile** — référence structurée, à croiser avec `pii_references` (extraite du texte libre par regex) pour évaluer la cohérence des deux sources. |

## 7. Attributs métier rares (3,2 % à 0,01 % de remplissage)

Vingt champs, presque tous des formulaires ou sous-cas très spécifiques, souvent des doublons partiels de champs du groupe 6 (parfois avec un suffixe `1`, signe d'un champ recréé après coup dans Intercom).

| Colonne | Remplissage | Cardinalité | Utilité dans l'analyse |
|---|---|---|---|
| `ticket_attributes_Montant` | 3,16 % | 217 | **Marginale** — semble être une variante de `Montant en XAF` sur un sous-ensemble de tickets ; à clarifier si c'est un doublon incohérent ou un formulaire distinct avant de choisir de le fusionner ou l'ignorer. |
| `ticket_attributes_Numero errone` | 3,16 % | 461 | **Marginale, utile pour un sous-cas précis** — spécifique aux réclamations "bénéficiaire/numéro erroné" (572 tickets dans `ticket_type_name`). Utile seulement si on isole ce sous-motif. |
| `ticket_attributes_Votre Numero` | 3,09 % | 446 | **Marginale** — lié au champ précédent, même sous-cas. |
| `ticket_attributes_4 derniers chiffres de la carte` | 0,63 % | 101 | **Marginale** — PII carte (partiellement masquée), utile seulement pour les réclamations "carte", volume très faible. |
| `ticket_attributes_Date de depot` | 0,48 % | 75 | **Marginale** — date de dépôt d'un dossier (probablement une pièce justificative physique). |
| `ticket_attributes_Agence concernee` | 0,43 % | 41 | **Marginale** — doublon partiel de `Agence` sur un très petit sous-ensemble. |
| `ticket_attributes_Date de depot du dossier` | 0,09 % | 14 | **Marginale** — quasi identique conceptuellement à `Date de depot`. |
| `ticket_attributes_Reference de la transaction1` | 0,03 % | 5 | **Marginale** — doublon quasi vide de `Reference de la transaction`. |
| `ticket_attributes_Platforms` | 0,03 % | 4 | **Marginale** — plateforme technique concernée, anecdotique. |
| `ticket_attributes_Supporting evidence` | 0,03 % | 2 | **Marginale** — probablement un indicateur de pièce justificative fournie. |
| `ticket_attributes_Nom` | 0,02 % | 4 | **Marginale** — doublon quasi vide de `Nom du client`. |
| `ticket_attributes_Root cause` | 0,02 % | 4 | **Marginale mais symboliquement centrale** — c'est le champ qui, correctement rempli par les agents, aurait rendu inutile tout le travail de topic modeling du notebook 4. Son quasi-abandon opérationnel est en soi une observation utile pour la banque (le champ existe, mais n'est pas utilisé). |
| `ticket_attributes_Numero de compte1` | 0,02 % | 3 | **Sans valeur analytique** — doublon quasi vide de `Numero de compte`. |
| `ticket_attributes_Agence de domiciliation` | 0,02 % | 3 | **Sans valeur analytique** — doublon partiel et quasi vide de `Agence`. |
| `ticket_attributes_Priority` | 0,02 % | 3 | **Marginale, potentiellement intéressante si mieux renseignée** — champ de priorité quasi jamais utilisé malgré son utilité théorique pour le triage. |
| `ticket_attributes_RIB de l'etranger` | 0,02 % | 3 | **Sans valeur analytique** — cas très spécifique (virements internationaux), volume anecdotique. |
| `ticket_attributes_Feature` | 0,01 % | 2 | **Sans valeur analytique** — lié aux 2 tickets `Feature request` seulement. |
| `ticket_attributes_Order number` | 0,01 % | 1 | **Sans valeur analytique** — rempli sur une seule ligne sur 18 094. |
| `ticket_attributes_Amount` | 0,01 % | 1 | **Sans valeur analytique** — doublon anglais de `Montant`, une seule valeur. |
| `ticket_attributes_Reason` | 0,01 % | 1 | **Sans valeur analytique** — une seule valeur sur 18 094. |

## 8. Colonnes produites par le pipeline (notebooks 2 à 4)

Ces colonnes n'existent pas dans le fichier source : elles sont calculées. Elles sont incluses ici car ce sont elles, in fine, qui portent l'essentiel de la valeur analytique du projet.

| Colonne | Produite par | Utilité dans l'analyse |
|---|---|---|
| `texte` | Notebook 2 | **Essentielle** — fusion brute titre + description, avant nettoyage. |
| `texte_masque` | Notebook 2 | **Essentielle** — texte nettoyé, PII masquée ; entrée du modèle de sentiment (notebook 3). |
| `pii_telephones` / `pii_dates` / `pii_references` / `pii_montants` | Notebook 2 | **Utile** — informations personnelles extraites et isolées, exploitables pour du rapprochement opérationnel (ex. retrouver la transaction contestée) sans polluer le texte analysé. |
| `langue` | Notebook 2 | **Utile** — sert à orienter la lemmatisation (fr/en) ; utile aussi comme KPI en soi (répartition linguistique de la clientèle qui réclame). |
| `texte_lemmatise` | Notebook 2 | **Essentielle** — entrée du topic modeling (notebook 4) ; volontairement non utilisée pour le sentiment (notebook 3). |
| `sentiment_label` / `sentiment_score` / `sentiment_scores_detail` | Notebook 3 | **Essentielle** — cœur du projet : classe de sentiment, confiance, et distribution complète des 3 classes. |
| `topic_id` / `topic_keywords` | Notebook 4 | **Essentielle** — sous-motif découvert au sein de chaque catégorie, reconstruit le champ `Root cause` jamais renseigné manuellement. |

---

## Pour la suite

Ce catalogue distingue déjà, à titre indicatif :
- un noyau de colonnes **essentielles**, au cœur du pipeline actuel (`category`, `ticket_type_name`, `channel`, `created_at`, les champs texte, `Montant en XAF`, et toutes les colonnes dérivées) ;
- un ensemble de colonnes **sans valeur analytique** — constantes sur toute la table, doublons exacts, ou champs tronqués à l'export (`ticket_parts_ticket_parts`, `ticket_type_ticket_type_attributes_data`) — candidates naturelles à l'abandon ;
- des colonnes **utiles mais non exploitées** à fort potentiel (`Agence`, `updated_at`, `contacts_contacts`, `Date de la transaction`) qui pourraient enrichir les analyses futures (géographie, délai de traitement, clients récurrents) ;
- une longue traîne de colonnes **marginales**, quasi vides, dont l'intérêt dépend surtout de la question métier posée (garder pour les cas rares, ou ignorer pour simplifier).

À vous de me dire lesquelles vous jugez à conserver, enrichir ou écarter — je peux ensuite ajuster le pipeline et les notebooks en conséquence.

# Rapport — Statistique descriptive du fichier SRC_Intercom_Reclamation

**Source** : `SRC_Intercom_Reclamation_202607201846.csv` (export Intercom des réclamations)
**Auteur** : Analyse Data / Sentiment Analysis — Afriland
**Date du rapport** : 29/07/2026

Ce rapport documente la statistique descriptive de chaque colonne du fichier source, produite par les scripts Python du dossier [`src/`](src/). Chaque script correspond à une étape de la méthodologie et écrit son résultat dans [`resultats/tables/`](resultats/tables/).

---

## 1. Méthodologie appliquée

1. **Chargement** du CSV en texte brut (`dtype=str`), pour garder le contrôle total sur la conversion de chaque colonne (voir `src/utils.py::load_data`).
2. **Classification automatique** de chaque colonne dans une catégorie : `identifiant`, `numerique`, `categorielle`, `booleenne`, `date`, `texte_libre`, `json_imbrique` (`src/utils.py::classifier_colonne`). La règle de décision teste dans l'ordre : nom de colonne connu → booléen → date → numérique → JSON → longueur/nombre de mots (texte libre) → cardinalité (identifiant vs catégorielle).
3. **Statistiques adaptées à chaque type** :
   - numérique → moyenne, écart-type, min/max, quartiles, zéros, négatifs, valeurs aberrantes (méthode IQR)
   - catégorielle/booléenne → tableau de fréquences (top 10 + "AUTRES")
   - date → date min/max, étendue, taux de valeurs réellement exploitables
4. **Contrôle qualité** transversal : doublons, colonnes constantes, colonnes très creuses, cohérence temporelle.

Chaque script est indépendant et peut être relancé seul : `python3 src/0X_....py`.

---

## 2. Vue d'ensemble du dataset

| Indicateur | Valeur |
|---|---|
| Lignes réellement chargées par pandas | **18 094** |
| Colonnes | **67** |
| Doublons (ligne complète) | 0 |
| Doublons sur `id` / `ticket_id` | 0 |

> ⚠️ **Point d'attention** : `wc -l` sur le fichier brut indique ~23 022 lignes, mais pandas n'en charge que 18 094. L'écart s'explique par des champs texte (ex. description de la réclamation) contenant des retours à la ligne à l'intérieur d'un champ entre guillemets — comptés comme plusieurs lignes par `wc -l` mais correctement comme **une seule ligne logique** par le parseur CSV de pandas. Le chiffre à retenir est donc 18 094.

### Répartition des 67 colonnes par type détecté

| Catégorie | Nb colonnes |
|---|---|
| Catégorielle | 25 |
| Numérique | 10 |
| Identifiant | 8 |
| Texte libre | 7 |
| Date | 6 |
| JSON imbriqué | 6 |
| Booléenne | 5 |

Tableau complet colonne par colonne : [`resultats/tables/01_vue_ensemble_colonnes.csv`](resultats/tables/01_vue_ensemble_colonnes.csv).

---

## 3. Statistiques par type de variable

### 3.1 Variables numériques

Détail complet : [`resultats/tables/02_stats_numeriques.csv`](resultats/tables/02_stats_numeriques.csv)

**Point méthodologique important** : parmi les 10 colonnes numériques, seules certaines sont de vraies *quantités* pour lesquelles moyenne/écart-type ont un sens métier ; les autres sont des *codes numériques* (numéro de téléphone, 4 derniers chiffres de carte, numéro de compte, order number) où seule la présence/l'unicité compte, pas la moyenne.

| Colonne | Nature | Count | % manquant | Moyenne | Médiane | Min | Max |
|---|---|---|---|---|---|---|---|
| `ticket_attributes_Montant en XAF` | quantité | 7 230 | 60.0% | 13,77 M | 50 000 | **-368 635** | **5,0e10** |
| `ticket_parts_total_count` | quantité | 18 094 | 0% | 27.8 | 26 | 5 | 171 |
| `linked_objects_total_count` | quantité | 18 094 | 0% | 0.05 | 0 | 0 | 4 |
| `ticket_attributes_Montant` | quantité | 572 | 96.8% | 15,66 M | 30 000 | 0 | 6,99e8 |
| `ticket_attributes_Numero_tel_client` | code | 7 703 | 57.4% | — | — | -652 743 288 | 8,3e12 |
| `ticket_attributes_Numero errone` | code | 572 | 96.8% | — | — | 1 | 1,4e10 |
| `ticket_attributes_Votre Numero` | code | 559 | 96.9% | — | — | 695 | 1,5e10 |
| `ticket_attributes_4 derniers chiffres de la carte` | code | 114 | 99.4% | — | — | 4 | 9 951 |

**Anomalies détectées à investiguer avec le métier** :
- `Montant en XAF` contient **20 valeurs négatives** et **178 zéros**, ainsi que des montants extrêmes (jusqu'à 50 milliards XAF) : 759 valeurs sont hors bornes IQR. À vérifier — erreur de saisie, montant en centimes au lieu de XAF, ou réclamation atypique (fraude de gros montant) ?
- `ticket_attributes_Numero_tel_client` contient des valeurs négatives et des valeurs à 13 chiffres, incompatibles avec un numéro camerounais (9 chiffres) : confirme qu'il s'agit d'un champ de saisie libre mal contrôlé côté formulaire Intercom.

### 3.2 Variables catégorielles (extraits clés)

Détail complet (top 10 modalités par colonne) : [`resultats/tables/03_stats_categorielles.csv`](resultats/tables/03_stats_categorielles.csv)

**Statut du ticket** (`ticket_state_category`) :
| Statut | % |
|---|---|
| submitted | 90.2% |
| resolved | 9.3% |
| in_progress | 0.4% |
| waiting_on_customer | 0.09% |

**Canal** (`channel`) :
| Canal | % |
|---|---|
| android | 65.6% |
| ios | 20.6% |
| whatsapp | 12.7% |
| facebook | 1.0% |
| autres (messenger, instagram, email) | 0.2% |

**Type de réclamation** (`ticket_type_name`, 17 modalités) :
| Type | % |
|---|---|
| SARA | 59.0% |
| COMPTE | 27.2% |
| CARTE | 3.8% |
| BENEFICIAIRE ERRONE | 3.2% |
| CREDIT | 2.1% |
| autres (12 types) | 4.7% |

**Agence** (`ticket_attributes_Agence`, 112 modalités, 57.9% manquant) : top agence = FIRST_BANK_HIPPODROME (4.0%), suivie de BONANJO (2.0%) et BAFOUSSAM (1.8%) ; le reste est très dispersé (102 agences se partagent 25% des tickets).

### 3.3 Variables booléennes

Détail : [`resultats/tables/03_stats_booleennes.csv`](resultats/tables/03_stats_booleennes.csv)

| Colonne | % TRUE | Interprétation |
|---|---|---|
| `open` | 0.27% | quasi tous les tickets sont clôturés/fermés au moment de l'export |
| `is_shared` | 99.93% | quasi tous les tickets sont partagés |
| `ticket_type_is_internal` | 0.07% | quasi aucun ticket interne (cohérent : dataset de réclamations clients) |
| `ticket_type_archived`, `linked_objects_has_more` | 0% | colonnes sans variance → aucune information |

### 3.4 Variables de date

Détail : [`resultats/tables/04_stats_dates.csv`](resultats/tables/04_stats_dates.csv)

| Colonne | Date min | Date max | % non exploitable |
|---|---|---|---|
| `created_at` | 2024-02-01 | 2026-07-17 | 0% |
| `updated_at` | 2024-05-10 | 2026-07-18 | 0% |
| `ticket_type_created_at` / `updated_at` | 2024-04-18 | 2026-02-24 | 0% |
| `ticket_attributes_Date de la transaction` | **1988-11-26** | **2073-12-10** | 61.6% |
| `ticket_attributes_Date de depot du dossier` | 2025-06-02 | 2026-05-27 | 99.9% |

**Anomalie majeure** : `ticket_attributes_Date de la transaction` est un champ **saisi librement** par l'agent, avec au moins 6 formats différents observés (ISO, JJ/MM/AAAA, JJ.MM.AAAA, date en toutes lettres françaises, année sur 2 chiffres, timestamp Unix). Résultat : 61,6% des valeurs ne sont pas exploitables telles quelles, et parmi celles qui le sont, ~48 dates tombent hors de la période plausible (avant 2023 ou après 2027) à cause d'années à 2 chiffres mal interprétées (ex. `10.12.73` → lu comme 2073 au lieu d'une saisie erronée). **Recommandation** : ne pas utiliser cette colonne telle quelle pour l'analyse temporelle ; préférer `created_at` (fiable à 100%, format unique, cohérent avec `updated_at`).

Cohérence vérifiée : **0 ligne** où `created_at` > `updated_at` (bon signe de fiabilité sur les colonnes système).

### 3.5 Identifiants, texte libre, JSON imbriqué

- **Identifiants** (`id`, `ticket_id`, `ticket_state_id`, `ticket_type_id`, `admin_assignee_id`, `team_assignee_id`, `Numero de compte`, `Reference de la transaction`) : unicité vérifiée à 100% sur `id`/`ticket_id` (pas de doublon). `admin_assignee_id` ne prend que 8 valeurs distinctes (8 agents/comptes assignataires), `team_assignee_id` seulement 4 équipes.
- **Texte libre** (`ticket_attributes__default_description_`, `ticket_attributes_Nom du client`, titres...) : pas de statistique de fréquence pertinente à ce stade — utile pour l'étape suivante (analyse de sentiment). Taux de remplissage de la description : 45.7%.
- **JSON imbriqué** (`contacts_contacts`, `linked_objects_data`, `ticket_parts_ticket_parts`...) : champs structurés qui nécessiteraient un parsing dédié pour être exploités (hors périmètre de la stat descriptive classique).

---

## 4. Qualité des données — synthèse

Détail : [`resultats/tables/05_qualite_donnees.csv`](resultats/tables/05_qualite_donnees.csv)

| Contrôle | Résultat |
|---|---|
| Doublons (ligne complète) | 0 |
| Doublons sur `id` / `ticket_id` | 0 |
| Colonnes constantes (1 seule valeur, aucune info) | **16** |
| Colonnes ≥ 99% manquantes | **18** |
| Incohérences `created_at` > `updated_at` | 0 |

Les 16 colonnes constantes et les colonnes quasi-vides (≥99% manquant) sont candidates à l'**exclusion** des analyses futures (elles n'apportent aucune information discriminante). Elles correspondent en grande partie à des attributs propres à un seul type de ticket rare (ex. `ticket_attributes_Priority`, `Root cause`, `Feature`) — probablement des champs Intercom configurés pour d'autres types de tickets que ceux majoritairement utilisés ici (SARA, COMPTE).

---

## 5. Limites et recommandations

- **Montants** (`Montant en XAF`) : présence de valeurs négatives et d'outliers extrêmes → à valider avec le métier avant tout calcul agrégé (somme, moyenne) dans un futur rapport.
- **Dates de transaction saisies à la main** : peu fiables, à ne pas utiliser pour l'analyse temporelle — préférer `created_at`/`updated_at` (colonnes système, 100% fiables).
- **Champs texte libre** (description, nom du client) : nécessaires pour l'analyse de sentiment à venir, non couverts par la stat descriptive classique au-delà du taux de remplissage.
- **60% des colonnes** (identifiants techniques + colonnes constantes + colonnes quasi-vides) n'apportent pas d'information exploitable et pourront être écartées dans les analyses suivantes pour alléger le dataset.

---

## 6. Comment reproduire

```bash
cd "niv2- tutoré/2- Statistique_Descriptive/src"
python3 01_apercu_general.py       # vue d'ensemble + typologie des colonnes
python3 02_stats_numeriques.py     # variables numériques
python3 03_stats_categorielles.py  # variables catégorielles + booléennes
python3 04_stats_dates.py          # variables date
python3 05_qualite_donnees.py      # doublons, colonnes constantes, cohérence
```

Chaque script régénère son fichier dans `resultats/tables/`.

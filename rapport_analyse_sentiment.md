# Analyse des réclamations clients — Text mining & Sentiment Analysis

**Source :** Export Intercom (`SRC_Intercom_Reclamation_202607201846.csv`)
**Période couverte :** février 2024 → juillet 2026
**Volume total :** 18 094 tickets

---

## 1. Contexte et objectifs

L'application (SARA, comptes, cartes...) génère un volume important de réclamations via Intercom. Deux objectifs guident cette analyse :

- **Objectif A — Paramètres utiles à la banque** : identifier les motifs de réclamation récurrents, leur volume, les canaux et montants associés, pour orienter les priorités opérationnelles.
- **Objectif B — Sentiment du client** : mesurer le niveau d'insatisfaction exprimé dans le texte libre des réclamations, et le croiser avec les motifs pour cibler les irritants les plus critiques.

---

## 2. Périmètre et limites des données

| Constat | Donnée | Implication |
|---|---|---|
| Volume total | 18 094 tickets | — |
| Texte libre disponible | 8 284 tickets (46%) — titre et/ou description | Le sentiment analysis ne porte que sur cette sous-population ; le reste est analysé via les champs structurés uniquement |
| `ticket_attributes__default_title_` rempli | 30% | Titre et description ne sont pas toujours renseignés pour les mêmes tickets → fusion nécessaire pour ne perdre aucun signal |
| `ticket_attributes__default_description_` rempli | 46% | idem |
| `ticket_attributes_Root cause` rempli | 0,02% (4 tickets) | Champ quasi inexploitable tel quel → reconstruit par topic modeling (Phase 3) |
| Texte mixte FR/EN | ~84% FR / ~15% EN (mesuré Phase 1) | Pipeline linguistique à deux branches (détection de langue + lemmatiseur dédié) |
| État des tickets | 93% "submitted", peu de "resolved" | Pas de proxy de satisfaction via la résolution — le sentiment doit être déduit du texte |

**Catégories de réclamation (`ticket_type_name`, sur les 18 094 tickets)** : SARA 59%, COMPTE 27%, CARTE 3,8%, BENEFICIAIRE ERRONE 3,2%, CREDIT 2,1%, ACCUEIL 1,5%, OPERATIONS_INTERNATIONALES 1%, MAC 0,9%, CARTE_BLANCHE 0,5%, EFIRST 0,5%, DECOUVERT 0,2%

**Canaux (`channel`)** : Android 66%, iOS 21%, WhatsApp 13%, Facebook/Messenger/Instagram/Email marginal (<1,5% cumulé)

---

## 3. Méthodologie — Stratégie en 4 phases

### Phase 1 — Consolidation & nettoyage ✅ *terminée*
- Fusion titre + description en un champ `texte`
- Correction de l'encodage (apostrophes corrompues, caractères de contrôle)
- Masquage des PII (téléphone/montant/date/référence) par regex → extraction dans des colonnes dédiées plutôt que suppression (utile pour l'objectif A)
- Détection de la langue par ticket (FR/EN)
- Lemmatisation spaCy (`fr_core_news_sm` / `en_core_web_sm` selon la langue), avec préservation des termes de marque (SARA, Orange, Momo...) que le lemmatiseur déformait sinon

### Phase 2 — Sentiment analysis ✅ *terminée*
- Modèle `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` en inférence directe (zero-shot) — pas de données labellisées disponibles pour entraîner un modèle supervisé
- Sortie : classe négatif/neutre/positif + score de confiance, par ticket
- Appliqué sur le texte nettoyé non lemmatisé (`texte_masque`), pour préserver l'ordre des mots dont dépend un modèle transformer

### Phase 3 — Extraction des paramètres utiles ✅ *terminée*
- Topic modeling (TF-IDF + NMF) appliqué catégorie par catégorie sur le texte lemmatisé
- 34 topics découverts sur 8 catégories ayant assez de volume (les 7 catégories restantes, <18 tickets chacune, n'ont pas assez de texte pour un topic modeling fiable)
- Objectif : faire ressortir les sous-causes réelles à l'intérieur de chaque catégorie, pour combler le vide du champ `Root cause`

### Phase 4 — Restitution ✅ *terminée*
- KPIs croisant catégorie × sentiment × canal × mois × montant
- Identification des sous-motifs (topics) au taux de sentiment négatif le plus élevé — les points de douleur les plus précis et les plus fréquents

---

## 4. Résultats

### 4.1 Vue d'ensemble du sentiment

Sur les 8 284 tickets analysés (ceux disposant de texte libre) :

| Sentiment | Volume | % |
|---|---|---|
| Négatif | 4 842 | 58,4% |
| Neutre | 3 340 | 40,3% |
| Positif | 102 | 1,2% |

**Plus d'un ticket sur deux exprime une insatisfaction explicite.** Le sentiment positif est quasi inexistant (1,2%) — cohérent avec la nature du canal (réclamations, pas d'avis satisfaction).

### 4.2 Sentiment par catégorie de réclamation

| Catégorie | % négatif | Volume (texte) |
|---|---|---|
| **BENEFICIAIRE ERRONE** | **81,5%** | 536 |
| ACCUEIL | 67,5% | 77 |
| EFIRST | 66,7% | 9 |
| CARTE_BLANCHE | 60,0% | 15 |
| SARA | 59,3% | 4 532 |
| CARTE | 58,4% | 113 |
| OPERATIONS_INTERNATIONALES | 54,5% | 33 |
| COMPTE | 53,5% | 2 843 |
| CREDIT | 34,4% | 64 |
| DECOUVERT | 31,2% | 32 |

**Lecture business** : BENEFICIAIRE ERRONE cumule le taux d'insatisfaction le plus élevé (81,5%) — logique, l'erreur est souvent irréversible une fois les fonds transférés à un mauvais bénéficiaire. SARA et COMPTE, malgré un sentiment négatif "seulement" autour de 55-59%, pèsent le plus en **volume absolu** (4 532 et 2 843 tickets texte) : ce sont eux qui déterminent la charge de travail du support et l'essentiel de l'insatisfaction globale.

### 4.3 Sentiment par canal

| Canal | % négatif | Volume |
|---|---|---|
| iOS | 59,8% | 2 036 |
| Android | 58,6% | 5 845 |
| WhatsApp | 51,2% | 367 |
| Facebook | 36,4% | 11 |
| Messenger | 27,3% | 22 |

Android et iOS (les canaux applicatifs, 95% du volume texte) affichent un sentiment très proche et légèrement plus négatif que WhatsApp — cohérent avec le fait que l'app mobile est le point d'entrée principal en cas de dysfonctionnement transactionnel direct.

### 4.4 Évolution temporelle

Le volume mensuel n'est statistiquement significatif qu'à partir de **novembre 2025** (< 25 tickets/mois avant cette date). Sur la période exploitable (nov. 2025 → juil. 2026) :

| Mois | % négatif | Volume |
|---|---|---|
| 2025-11 | 51,7% | 594 |
| 2025-12 | 54,0% | 1 605 |
| 2026-01 | 60,2% | 1 464 |
| 2026-02 | 60,7% | 1 365 |
| 2026-03 | 66,1% | 681 |
| 2026-04 | 69,0% | 171 |
| 2026-05 | 63,0% | 568 |
| 2026-06 | 52,8% | 1 319 |
| 2026-07 | 66,5% | 486 |

**Tendance à surveiller** : hausse continue du sentiment négatif de nov. 2025 (51,7%) à avril 2026 (69,0%), avec un répit en juin 2026 (52,8%) suivi d'une remontée en juillet. À confirmer avec plus de recul, mais ce pic mérite une investigation ciblée sur ce qui s'est passé début 2026.

### 4.5 Montants en jeu

⚠️ **Alerte qualité donnée** : le montant *moyen* est faussé par des valeurs aberrantes extrêmes (un ticket COMPTE atteint 500 milliards XAF, manifestement une erreur de saisie/format). **Le montant médian est la mesure fiable ici** :

| Catégorie | Montant médian (XAF) | Nb tickets avec montant |
|---|---|---|
| CREDIT | 6 000 000 | 63 |
| OPERATIONS_INTERNATIONALES | 3 000 000 | 33 |
| CARTE | 1 175 000 | 90 |
| COMPTE | 520 000 | 2 506 |
| SARA | 400 000 | 4 525 |
| EFIRST | 50 000 | 9 |

Les catégories CREDIT et OPERATIONS_INTERNATIONALES, bien que faibles en volume, concentrent les montants unitaires les plus élevés — à prioriser malgré leur volume modeste si l'angle d'analyse est le risque financier plutôt que la charge opérationnelle.

### 4.6 Sous-motifs et points de douleur (topics)

34 topics identifiés sur 8 catégories (SARA et COMPTE : 8 topics chacun ; BENEFICIAIRE ERRONE : 8 topics ; CARTE, ACCUEIL, CREDIT, OPERATIONS_INTERNATIONALES, DECOUVERT : 2 topics chacun). Les 10 points de douleur les plus critiques (volume ≥15 tickets, triés par %négatif) :

| Catégorie | Mots-clés du topic | Volume | % négatif |
|---|---|---|---|
| BENEFICIAIRE ERRONE | erroné, bénéficiaire erroné, annulation transaction | 54 | 100% |
| BENEFICIAIRE ERRONE | destinataire, erreur numéro, téléphone | 51 | 94,1% |
| ACCUEIL | account, money, receive, sara, orange, withdrawal | 28 | 89,3% |
| BENEFICIAIRE ERRONE | erreur bénéficiaire, numéro | 73 | 86,3% |
| BENEFICIAIRE ERRONE | send, wrong number, beneficiary, error | 50 | 86,0% |
| CARTE | card, debit, atm, withdrawal | 19 | 84,2% |
| BENEFICIAIRE ERRONE | transaction, erreur, annulation | 69 | 82,6% |
| BENEFICIAIRE ERRONE | orange money, compte sara | 103 | 80,6% |
| **SARA** | **recevoir, retrait, argent non reçu, dépôt** | **525** | **80,2%** |
| **SARA** | **transfer, receive, momo** | **515** | **73,2%** |

**Insight clé** : tous les sous-motifs de BENEFICIAIRE ERRONE dépassent 80% de négatif — confirme que c'est une catégorie entière à traiter en priorité (process d'annulation/récupération de fonds à fluidifier). Mais les deux topics SARA en fin de liste, malgré un %négatif "seulement" autour de 73-80%, représentent **1 040 tickets à eux seuls** (2× le volume total de BENEFICIAIRE ERRONE) — ce sont eux qui pèsent le plus sur la charge réelle de mécontentement, tous deux liés à des **fonds non reçus après transfert/retrait**, ce qui pointe vers un problème de fiabilité de créditation plutôt que d'erreur utilisateur.

---

## 5. Recommandations pour la banque

1. **Prioriser le sous-motif "fonds non reçus" sur SARA** (2 topics, 1 040 tickets, 73-80% négatif) : investiguer la fiabilité de créditation des transferts/retraits SARA↔Orange Money/MoMo — c'est le plus gros volume d'insatisfaction cumulée du corpus.
2. **Fluidifier le process BENEFICIAIRE ERRONE** (81,5% négatif toutes causes confondues, le taux le plus élevé de toutes les catégories) : les 8 topics de cette catégorie sont tous au-dessus de 80% négatif — envisager un mécanisme d'annulation/récupération de fonds plus rapide ou une confirmation renforcée avant validation du transfert (numéro de bénéficiaire).
3. **Investiguer le pic de sentiment négatif de mars-avril 2026** (66-69%, contre ~52-60% sur le reste de la période) : identifier un incident technique ou opérationnel ponctuel.
4. **Cibler CREDIT et OPERATIONS_INTERNATIONALES pour le risque financier** malgré leur faible volume : montants médians élevés (6M et 3M XAF) — un incident y coûte proportionnellement plus cher qu'un incident SARA.
5. **Nettoyer la saisie du champ Montant** (valeurs aberrantes jusqu'à 500 milliards XAF) avant tout usage dans un reporting financier officiel — ajouter une validation de plage à la saisie.

---

## 6. Limites méthodologiques

- Le sentiment n'est mesuré que sur 46% des tickets (ceux avec texte libre) ; les 54% restants ne sont représentés que par leurs attributs structurés
- Modèle de sentiment utilisé en zero-shot (aucun fine-tuning sur des données bancaires camerounaises) — à valider par un échantillon relu manuellement
- Extraction PII par regex : quelques faux positifs connus (ex. une année dans une date en toutes lettres confondue avec un montant) — sans impact sur les KPIs qui s'appuient sur les colonnes structurées (`Montant en XAF`) plutôt que sur l'extraction regex
- Topic modeling non supervisé (NMF) : les libellés de topics sont des listes de mots-clés, pas des catégories métier validées — une relecture humaine reste recommandée avant diffusion externe
- Champ `Montant en XAF` : contient des valeurs aberrantes extrêmes (jusqu'à 500 milliards XAF sur un seul ticket) qui faussent toute moyenne — utiliser systématiquement la médiane, jamais la moyenne brute, pour ce champ
- Tendance mensuelle : volume non significatif avant novembre 2025 (<25 tickets/mois) — à exclure de toute lecture de tendance

---

## Annexe — Glossaire technique

| Terme | Définition rapide |
|---|---|
| Tokenisation | Découpage du texte en unités (mots) |
| Stop word removal | Suppression des mots à faible valeur informative (articles, prépositions) |
| Lemmatisation | Réduction d'un mot à sa forme canonique (infinitif, singulier) |
| TF-IDF | Pondération d'un mot = fréquence dans le document × rareté dans le corpus |
| Topic modeling (NMF) | Découverte non supervisée de thématiques récurrentes dans un ensemble de textes |
| Zero-shot | Utilisation d'un modèle pré-entraîné sans ré-entraînement sur les données du projet |

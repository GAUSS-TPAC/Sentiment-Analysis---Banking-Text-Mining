# Réclamations clients Intercom — analyse exploratoire et énoncé du problème

Analyse des réclamations déposées sur le canal Intercom, à partir de l'export brut
`SRC_Intercom_Reclamation_202607201846.csv` (18 094 tickets, 68 colonnes, extraction
du 20/07/2026), **complété depuis par un second export Intercom**
(`conversations_*.xlsx`) qui porte le message d'ouverture réel d'une partie des
tickets — le CSV plat tronque le fil de conversation à l'extraction, cet export
séparé ne le tronque pas. Voir notebook 03, section 4.

**Objet du dépôt** — établir, à partir des données seules, *pourquoi* les clients
se plaignent, et délimiter précisément ce que ces données permettent ou non de
conclure. Le livrable final est un **énoncé de problème défendable**, pas un
tableau de bord.

---

## Démarrage

```bash
pip install -r requirements.txt
jupyter lab notebooks/
```

Les notebooks s'exécutent **dans l'ordre 01 → 07**, mais chacun est autonome :
tous rechargent la source et reconstruisent leur périmètre. Aucun état n'est
partagé entre notebooks.

L'export CSV n'est pas versionné (11 Mo). `config.chemin_donnees()` le cherche
dans `data/raw/`, à la racine du projet, dans le dossier parent, puis dans un
dossier `dataset/` à côté du projet — il suffit qu'il soit à l'un de ces
emplacements. L'export complémentaire (`conversations_*.xlsx`, ~19 Mo) est
optionnel : `config.chemin_conversations()` le cherche dans `data/raw/Interc/`
ou `dataset/Interc/` ; son absence n'est pas bloquante, mais réduit le
périmètre d'analyse causale à sa version non enrichie (à recalculer si le
fichier manque — les chiffres de ce document supposent qu'il est présent).

Exécution complète en ligne de commande :

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
```

---

## Structure

```
niv/
├── src/reclamations/          logique partagée entre notebooks
│   ├── config.py              chemins + constantes de périmètre (dates de coupure, seuils, audit)
│   ├── chargement.py          chargement, typage, contrôles qualité, périmètres, texte enrichi
│   ├── texte.py               normalisation + taxonomie causale des motifs
│   ├── topics.py              topic modeling (TF-IDF + NMF) par catégorie
│   └── viz.py                 charte graphique
├── notebooks/                 le raisonnement, un notebook par étape
└── resultats/
    ├── figures/               7 figures PNG
    └── tables/                25 tables CSV
```

**Règle de séparation** — ce qui est utilisé par plus d'un notebook vit dans
`src/` ; le raisonnement et l'interprétation vivent dans les notebooks. Aucune
date de coupure ni aucun décompte d'audit manuel n'est écrit en dur dans un
notebook : ils sont tous dans `config.py`, avec leur justification et le
notebook qui les établit.

---

## Les notebooks

| # | Notebook | Ce qu'il établit |
|---|---|---|
| 01 | `chargement_et_qualite` | La donnée système est fiable ; 39 colonnes sur 67 sont inexploitables ; **le contenu des conversations a été tronqué à l'export** |
| 02 | `rupture_de_collecte` | Le pic de mars-avril 2026 est contemporain d'une **panne de capture des champs**, pas d'un incident produit isolé |
| 03 | `perimetre_et_representativite` | Le périmètre d'analyse valide est de 9 381 tickets (89,0 % de couverture texte), après intégration d'une source complémentaire (`conversations_.xlsx`) et validation par test de représentativité |
| 04 | `analyse_causale` | ~2 réclamations sur 3 décrivent le même incident ; les règles plafonnent à 57 % de rappel |
| 05 | `recidive_et_charge` | 20 % du volume sont des re-dépôts ; le dispositif produit une partie de sa propre charge |
| 06 | `synthese_problematique` | Chiffres clés consolidés, limites, énoncé du problème *(reprend 04 ; n'intègre pas encore les sous-motifs du 07)* |
| 07 | `topics_categories` | Sous-motifs par topic modeling sur le **complémentaire de SARA** (COMPTE, BENEFICIAIRE ERRONE, CARTE, ACCUEIL, CREDIT, OPERATIONS_INTERNATIONALES) — complète le 04, ne le remplace pas |

---

## Chaîne de raisonnement

L'ordre des notebooks n'est pas un plan de rapport, c'est une **chaîne de
dépendances** : chaque étape conditionne la validité de la suivante.

1. **Écarter ce qui n'est pas un signal métier** (02). Sans cette étape, on conclut
   à un « incident produit SARA en mars-avril 2026 » qui est en réalité un artefact
   de collecte. Quatre champs de saisie indépendants s'effondrent ensemble le
   13 mars — de 9 % à 100 % de tickets vides en 48 heures — et reviennent ensemble
   mi-mai. Un incident produit n'efface pas les champs d'un formulaire.
2. **Délimiter le périmètre avant de mesurer** (03). Le manque de texte n'est pas
   diffus : 96,8 % en est concentré sur ces trois mois. La bonne base n'est donc pas
   « 44 % des 18 056 tickets » mais un périmètre construit à la journée : les six
   mois à collecte saine, plus les journées de la fenêtre mars-mai dont la
   couverture texte — une fois enrichie du message d'ouverture récupéré dans
   `conversations_.xlsx` — atteint 50 %. **9 381 tickets**, validés par un test
   de représentativité (V de Cramér 0,17 sur le type de ticket, 0,10 sur le canal,
   sous le seuil de 0,20 retenu) — contre un V de 0,26/0,20, au-dessus du seuil,
   si la fenêtre dégradée est réintégrée en bloc sans ce filtre journalier : le
   fichier complémentaire ne couvre pas les tickets au hasard.
3. **Passer du champ structuré au texte libre** (04). `ticket_type_name` dit dans
   quel produit ranger le dossier, pas ce qui a dysfonctionné.
4. **Changer d'unité d'analyse : du ticket au client** (05). Tant qu'on compte des
   tickets, on voit un volume ; en regroupant par client, on voit des relances.
5. **Mesurer le coût, pas le nombre** (05). 18 000 tickets ne veut rien dire ;
   501 399 messages pour 7 agents, si.

---

## Résultats principaux

| Indicateur | Valeur | Notebook |
|---|---|---|
| Tickets, période opérationnelle (nov. 2025 – juil. 2026) | 18 056 | 02 |
| Périmètre d'analyse causale (règle à la journée, texte enrichi) | 9 381 | 03 |
| Base textuelle exploitable | 8 348 (89,0 %) | 03 |
| Tickets exclus — journées sous le seuil de couverture | 8 675 | 03 |
| Messages perdus par troncature à l'export | 501 399 | 01 |
| « Débité, bénéficiaire jamais crédité » — règles seules | 40,5 % | 04 |
| — estimation corrigée par audit manuel | ~66 % | 04 |
| Argent prélevé à tort ou jamais arrivé (cumul corrigé) | ~74 % | 04 |
| Erreur de saisie du bénéficiaire (évitable par l'interface) | 6,9 % | 04 |
| Statut `resolved` | 9,3 % | 05 |
| Messages par ticket (médiane) | 26 | 05 |
| Messages / agent / mois | 7 959 | 05 |
| Clients ayant déposé ≥ 2 réclamations | 33,8 % (60 % du volume) | 05 |
| Re-dépôts (< 7 j, même motif) | 19,5 % | 05 |

### Précaution de lecture sur les motifs

Les pourcentages de familles causales sont des **planchers**. La classification du
notebook 04 est à base de règles et son rappel plafonne à 57 % : les clients
décrivent le même incident de vingt façons, en français et en anglais. L'audit
manuel de 20 textes non classés (section 4 du notebook) montre que 16 relèvent de
familles déjà définies — la taxonomie est complète, ce sont les règles qui sont
insuffisantes.

L'estimation corrigée qui en découle repose sur ces 20 textes : l'intervalle de
confiance à 95 % est d'environ ±20 points. **C'est un ordre de grandeur, pas une
mesure** — et c'est précisément ce qui justifie une classification apprise comme
étape suivante. Le notebook 07 en est un premier pas, limité aux catégories
autres que SARA.

---

## Ce que ces données ne peuvent pas établir

Section la plus importante du projet : elle délimite ce qui peut être affirmé.

**Intercom est un journal de symptômes. Il contient le numérateur, jamais le
dénominateur.** On sait que ~2 000 clients se sont plaints d'un transfert échoué.
On ignore si c'est sur 20 000 transferts (10 % d'échec — critique) ou sur 2 000 000
(0,1 % — bruit de fond). Le même fichier est compatible avec les deux, et elles
appellent des décisions opposées.

| Question | Pourquoi elle est hors de portée |
|---|---|
| Où la transaction casse-t-elle ? | Aucune trace technique : ni code d'erreur, ni étape, ni statut de passerelle |
| Orange Money est-il plus défaillant que MTN ? | Les mentions sont confondues avec les parts de marché ; pas de volume par opérateur |
| L'argent est-il perdu ou en suspens ? | Aucune issue de dossier n'est enregistrée |
| Combien subissent l'incident sans se plaindre ? | Absents du fichier par construction — et ce sont eux qui partent sans rien dire |
| Le délai de traitement s'améliore-t-il ? | `updated_at` est un proxy, pas une date de clôture ; 90 % des tickets n'ont pas de statut final |

### Données à demander

1. **Journal des transactions SARA** — identifiant, montant, opérateur, sens,
   horodatage, statut technique, code d'erreur. Joignable aux réclamations par
   montant + numéro + date. *C'est cette jointure qui transforme l'étude en diagnostic.*
2. **Ré-extraction Intercom avec `ticket_parts` complet** — 501 399 échanges
   tronqués à 4 caractères (`[{"t`) dans l'export actuel. **Partiellement
   satisfait** depuis l'intégration de `conversations_.xlsx` (notebook 03) :
   le message d'ouverture est récupéré pour une partie des tickets, mais pas
   le fil complet (réponses, échanges suivants).
3. **Date de clôture et issue du dossier** (remboursé / rejeté / sans suite).

---

## Problématique

> **Pourquoi une part significative des transferts entre SARA et les opérateurs de
> mobile money débite le client sans créditer le bénéficiaire — et comment agir à
> la source pour réduire le taux d'incident par transaction, plutôt que le nombre
> de plaintes ?**

**Le piège de mesure à écarter explicitement.** Si l'indicateur de succès devient
*le nombre de réclamations*, le moyen le plus efficace de réussir est de rendre la
réclamation plus difficile. Ce levier n'est pas théorique : le notebook 02 montre
que le canal a changé de comportement en mars 2026 et que le volume en a été
bouleversé, sans qu'aucune réclamation réelle n'ait été résolue. Le mécanisme joue
dans les deux sens — un bon canal de réclamation *augmente* les réclamations
enregistrées, en révélant une insatisfaction jusque-là silencieuse.

L'indicateur retenu est donc le **taux d'incident par transaction**, qui exige le
dénominateur — précisément la donnée à demander.

| # | Question | Faisable avec les données actuelles ? |
|---|---|---|
| 1 | Quelle est la structure réelle des motifs ? | **Oui** — classification apprise sur 8 348 textes, pour passer de 57 % à ~95 % de couverture |
| 2 | Quelle part est un re-dépôt évitable ? | **Oui** — chiffrée à 19,5 %, à industrialiser en détection à l'ouverture |
| 3 | À quelle étape la transaction casse-t-elle ? | **Non** — nécessite le journal des transactions |
| 4 | Quels dossiers vont s'enliser ? | **Non** — pas de date de clôture ni d'issue de dossier |

**Prochaine étape** — la question 1. Elle est le seul point de la problématique
entièrement traitable avec les données disponibles, et elle conditionne la mesure
de tous les autres.

---

## Notes techniques

- **Chargement en `dtype=str`.** L'inférence de type est désactivée volontairement :
  elle transformerait les numéros de compte en flottants et convertirait
  silencieusement des champs de saisie hétérogènes. Chaque conversion est ensuite
  explicite, avec comptage des échecs.
- **Texte enrichi, pas seulement le CSV plat.** Depuis le notebook 03,
  `chargement.construire_texte_enrichi` complète le titre + description du CSV
  avec le message d'ouverture récupéré dans l'export `conversations_*.xlsx`
  (`chargement.charger_messages_ouverture`) quand il existe — jointure sur `id`
  du CSV = `id` de cet export, **pas** `ticket_id`, qui y est un piège de
  nommage (colonne auto-référente). La normalisation (`texte.normaliser`)
  retire aussi les balises HTML que ce message peut porter.
- **Périmètre variable selon la question.** Le notebook 04 travaille sur le
  périmètre d'analyse causale du notebook 03 (il a besoin du texte) ; le
  notebook 05 sur la période opérationnelle complète (il n'utilise que des
  champs système, restés alimentés pendant la panne). Chaque notebook
  explicite le sien.
- **Pas de double axe des ordonnées.** Un volume et un taux ne se superposent pas
  sur deux échelles sans que le choix des échelles décide de la conclusion. Les
  figures concernées empilent deux panneaux partageant l'axe du temps
  (`viz.panneaux_temporels`).
- **Aucun agrégat financier n'est un chiffre officiel.** Le champ `Montant en XAF`
  contient des valeurs négatives, des zéros et un amas artificiel de valeurs
  extrêmes. Seule la médiane est utilisée, et uniquement pour hiérarchiser les
  familles entre elles.
- **Versionner les notebooks.** Pour obtenir une version diffable :
  `jupytext --to py:percent notebooks/*.ipynb`.

---

*Direction Recherche & Innovation — usage interne.*

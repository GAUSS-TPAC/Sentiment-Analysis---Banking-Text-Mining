# Écarts internes au protocole d'étude — état à mettre à jour avant validation

**Document concerné** : `protocole_etude.md` (racine du dépôt).

**Objet de cette note** : le protocole décrit, à plusieurs endroits, une méthode **retenue** qui
n'est pas encore celle que produit le code aujourd'hui (`niv/src/reclamations/`, notebooks 01-06),
et laisse plusieurs informations non renseignées nécessaires à une validation formelle. Chaque
point ci-dessous a été vérifié directement dans le code au moment de la rédaction — ce n'est pas
une relecture du texte, mais un contrôle d'exécution.

Deux catégories, parce qu'elles appellent des actions différentes : (A) le protocole décrit une
méthode que le code ne produit pas encore — corriger l'un ou l'autre avant de publier un chiffre ;
(B) une information est absente et bloque la validation formelle du document — la renseigner.

---

## A. Écarts méthodologiques — méthode décrite vs méthode exécutée

### A1 — ~~Le périmètre final annoncé (§3.5) n'est pas celui que produisent les notebooks aujourd'hui~~ — **corrigé et dépassé le 13/08/2026**

Le protocole affichait deux lignes dans le même tableau :

| Périmètre | Effectif | État |
|---|---|---|
| Règle par mois *(implémentée)* | 6 867 / 6 545 textes | C'était ce que produisait une exécution des notebooks |
| Règle à la journée *(retenue)* | 7 950 / 7 563 textes | Calculée pour le protocole, absente de `config.py` |

**Correction appliquée** : `config.SEUIL_COUVERTURE_JOURNALIERE` (50 %) existe maintenant, et
`chargement.perimetre_analyse` applique la règle à la journée — `config.MOIS_COLLECTE_DEGRADEE`
n'est plus utilisé comme critère d'exclusion, seulement comme repère descriptif pour le notebook 02.

**Ce qui va plus loin que la correction prévue** : au même moment, une source de données
complémentaire a été intégrée (`conversations_.xlsx`, message d'ouverture réel pour une partie des
tickets — `chargement.charger_messages_ouverture`, notebook 03 section 4). La règle à la journée
s'applique donc au **texte enrichi**, pas au CSV seul, ce qui change à nouveau le chiffre : ni 6 867/
6 545, ni 7 950/7 563, mais **9 381 / 8 348**. Vérifié représentatif par le même test que celui déjà
utilisé au protocole (V de Cramér 0,17 / 0,10, sous le seuil de 0,20) — voir aussi le nouveau garde-fou
identifié en cours de route : réintégrer la fenêtre dégradée entière une fois enrichie, **sans** le
filtre journalier, reste biaisé (V = 0,26 / 0,20, au-dessus du seuil) — le fichier complémentaire ne
couvre pas les tickets au hasard, exactement le même phénomène que celui déjà documenté pour le CSV
seul.

**Conséquence** : le protocole (§2-§6) cite encore les anciens effectifs partout — voir l'avertissement
ajouté en tête de `protocole_etude.md`. Une réécriture complète du protocole avec les nouveaux chiffres
reste à faire ; en attendant, `niv/README.md` et les notebooks eux-mêmes font foi.

### A2 — La 7ᵉ famille causale (§4.2) n'existe pas dans le code

Le protocole liste sept familles, la 7ᵉ marquée « Dysfonctionnement de l'application hors flux
d'argent — **[À intégrer au code]** ».

**Vérifié** : `texte.FAMILLES` contient exactement **6** familles ; la 7ᵉ n'y figure pas.

**Conséquence directe** : la table `04_familles_causales.csv` que produirait une nouvelle exécution
ne contiendra toujours pas cette famille — les 2 textes de l'audit qui la justifient (§4.2 du
protocole) resteront classés `non_classe` tant que la règle n'est pas ajoutée à `texte.py`.

**Action** : ajouter la 7ᵉ famille à `texte.FAMILLES` avec son motif de reconnaissance, ou retirer
la ligne du protocole si elle n'est pas retenue pour cette itération.

### A3 — ~~La « règle d'intégralité » de l'extrapolation (§5.1) contredit ce que fait le code~~ — **corrigé le 12/08/2026**

Le protocole énonce, comme règle retenue et sans marqueur d'écart : *« toutes les familles
observées dans l'audit sont redistribuées, aucune n'est écartée »*.

**Vérifié avant correction**, notebook 04 :
```
AUDIT = {"debit_non_credit": 8, "debit_injustifie": 8}
```
Sur les 5 familles réellement observées dans l'audit manuel de 20 textes (§4.5 du protocole :
`debit_non_credit` 8, `debit_injustifie` 8, `erreur_client` 1, `carte` 1, « autre » 2), **seules
deux étaient redistribuées**. Les 4 textes restants ne comptaient dans aucune famille du calcul
final.

**C'était le seul écart de cette section qui n'était pas marqué comme tel dans le protocole** — il
énonçait une règle comme si elle était déjà appliquée.

**Correction appliquée** : le dictionnaire `AUDIT` du notebook 04 couvre maintenant les 4 familles
observées qui existent déjà dans `texte.FAMILLES` (`debit_non_credit`, `debit_injustifie`,
`erreur_client`, `carte`). Les 2 textes « autre » (dysfonctionnement applicatif, sans règle codée —
écart A2, toujours ouvert) sont comptés à part dans `AUDIT_HORS_TAXONOMIE`, à 0 % de base-règles,
plutôt que d'être silencieusement exclus. Un `assert` vérifie désormais que les 20 textes de
l'audit sont intégralement comptés, pour empêcher la régression de cet écart. Le cumul narratif
« argent prélevé à tort ou jamais arrivé » (§4.2, cité dans le mémoire) reste calculé sur les deux
seules familles concernées (`debit_non_credit` + `debit_injustifie`, ~81 %, contre ~81 % avant
correction — **ce chiffre ne change pas**, seule l'intégralité de la table intermédiaire est
corrigée) ; les 4 familles ajoutées apparaissent maintenant dans l'impression détaillée sans entrer
dans ce cumul, ce qui n'était pas le cas auparavant. Notebook réexécuté de bout en bout, aucune
erreur.

**Reste ouvert** : A2 (la 7ᵉ famille n'est toujours pas codée dans `texte.FAMILLES` — les 2 textes
« dysfonctionnement applicatif » sont comptés dans l'extrapolation mais toujours classés
`non_classe` par `texte.classer()`).

---

## B. Informations manquantes — bloquantes pour une validation formelle

Un protocole soumis à validation nomme d'ordinaire qui le porte et qui le valide. Ces champs sont
actuellement vides :

| Section | Champ | Pourquoi il bloque la validation |
|---|---|---|
| §1.1 | Commanditaire / service porteur | Un document validé doit dire au nom de qui il est produit |
| §1.1 | Maître de stage / tuteur | Doit être nommé avant toute signature de validation |
| §2.1 | Mode d'extraction exact du CSV | Point technique cité en limite (§2.4) sans réponse |
| §7.2 | Cadre réglementaire applicable | Section entièrement vide ; conditionne la portée réelle de §7.4 (restrictions de diffusion) — un engagement de diffusion restreinte sans base réglementaire nommée est difficile à faire valider tel quel |
| §8.1 | Support de soutenance | À confirmer si le mémoire tutoré prévoit une soutenance |
| §9.1 | Calendrier des phases | Seule la structure logique (issue des notebooks) est proposée, aucune date |
| §9.2 | Rôles et responsabilités | Section vide |
| §9.3 | Calendrier de traitement des points de validation (§8.4) | Dépend de 9.1 |

---

## C. Étapes de validation elles-mêmes non réalisées (§4.5)

Ce ne sont pas des écarts au sens d'une contradiction, mais des cases du protocole encore ouvertes
et qui déterminent directement les critères de succès (§8.3) :

| Étape prévue | Statut vérifié |
|---|---|
| Jeu de référence annoté, 300 textes stratifiés | N'existe toujours pas — voir cependant le jeu de référence *de fait* ci-dessous (section D) |
| Double annotation (100 textes) + coefficient kappa | Non réalisée |
| Précision, rappel, F1 par famille | **Partiellement fait** le 14/08/2026, notebook 11 : sur 950 tickets appariés au Système B (annotation humaine indépendante), precision 0,93/rappel 0,60/F1 0,73 (`erreur_client`) et precision 0,93/rappel 0,49/F1 0,65 (`debit_non_credit`). Échantillon biaisé (§ D.4), ne remplace pas le jeu stratifié de 300 textes ni le calcul de kappa. |
| Test de sensibilité à l'ordre des familles causales | Non réalisé |

**Conséquence directe sur §8.3** — sur les 6 critères de succès listés, seuls deux sont marqués
« atteint » aujourd'hui (représentativité V ≤ 0,20 ; absence de donnée personnelle dans les
livrables versionnés). Les quatre autres dépendent de ces étapes.

---

## D. Chantier ajouté le 14/08/2026 — intégration du Système B, absent du protocole

Le protocole ne mentionne, à ce stade, qu'une seule source (l'export Intercom, Système A). Un
second système de gestion de réclamations a été découvert dans `dataset/` (8 fichiers relationnels
autour de `tickets_first.xlsx`, 8 005 tickets), actif en parallèle du Système A sur toute la
période opérationnelle. Ce n'est pas un écart au sens des sections précédentes — le protocole n'a
simplement jamais été mis à jour pour en tenir compte. Détail du chantier et des chiffres :
`.claude/plans/je-veux-que-l-on-sequential-babbage.md`, notebooks `niv/notebooks/08` à `12`.

**Ce qui a été fait** :

1. **Le Système A et le Système B ne sont pas des populations indépendantes.** 55 à 70 % des
   3 180 tickets `canal=INTERCOM` du Système B sont des ressaisies manuelles de tickets déjà
   présents côté A (A précède B de quelques heures en médiane). Un dédoublonnage par appariement
   fin (téléphone + montant + date proche, ou référence de transaction commune, chacun validé
   contre un bruit de fond mesuré par permutation) retire 1 182 doublons détectés — notebook 09.
2. **Périmètre consolidé** : 18 056 (Système A) + 6 823 (Système B dédupliqué) = **24 879
   réclamations**, contre un cumul brut naïf de 26 099 qui aurait surcompté.
3. **Le Système B porte une taxonomie de sous-motifs annotée à la main** (23 valeurs, 3 champs
   dropdown, 80 % des tickets qualifiés) — utilisée au notebook 11 comme jeu de référence *de
   fait* pour mesurer précision/rappel/F1 des règles causales du notebook 04 (voir section C
   ci-dessus).
4. **Deux dimensions inédites** : l'agence d'origine (absente du Système A) et un délai de
   résolution réel (`created_at → resolved_on`, la mesure `→ closed_on` étant un artefact de
   clôture automatique à écarter — notebook 08 § 4).
5. **Convergence de contrôle** : la médiane d'exposition financière `debit_non_credit` calculée
   indépendamment sur A (règles) et B (annotation humaine) est identique — 50 000 XAF des deux
   côtés (notebook 12 § 4).

**Ce qui reste ouvert** :

- Le protocole (ce document) ne décrit encore que le Système A — une réécriture intégrant le
  Système B (nouvelles sections 2/3.5/4.2/5.1) reste à faire, au même titre que la mise à jour déjà
  signalée en tête de document pour le périmètre à la journée.
- Le taux de faux négatifs du dédoublonnage (notebook 09 § 6) n'est pas mesuré, seulement borné en
  ordre de grandeur par le bruit de fond par canal.
- La correspondance entre les deux taxonomies ne couvre que 2 des 6 familles causales de A
  (`erreur_client`, `debit_non_credit`) — `acces_otp`, `debit_injustifie`, `carte`, `demande_info`
  restent sans pont validé vers le Système B (notebook 11 § 3).
- `type_reclamation` / `is_reclamation_fondee` sont vides à 100 % dans le Système B : la question
  « réclamation fondée ou non » (proche de la Phase 4 du document de cadrage officiel, § 1.6 du
  protocole) reste sans réponse malgré le second système.

---

## E. Trois cadrages non réconciliés (ajouté le 18/08/2026)

Vérification demandée : le code suit-il **la même feuille de route** que le protocole du
commanditaire ? Réponse courte : il en existe **trois versions distinctes** dans ce dépôt, deux
d'entre elles n'ont jamais été comparées entre elles, et le code n'en suit complètement aucune.

| Document | Date | Contenu | Statut |
|---|---|---|---|
| `protocole d'etude _ Text mining - Analyse des Reclamations Clients - dashboard auto.odt` | 27/07/2026 (`dc:date` du fichier) | Cadrage d'origine du commanditaire. **Une seule source** (Intercom). Objectif : **dashboard Streamlit**, classification par **sentiment** (négatif/neutre/positif) + topic modeling, pas de mention d'un second système. | Fichier binaire, jamais lu par du code ni transcrit intégralement avant aujourd'hui — seul le nom du commanditaire en avait été extrait le 14/08. |
| `protocole_etude.md` | rédigé le 14/08/2026 | Protocole **de l'analyste**, écrit en réponse au fichier ci-dessus. Énonce explicitement un **« écart assumé »** : classification causale par règles (pas de sentiment), restitution en notebooks (pas de dashboard) — justifié § 4.1. Une table de correspondance phase par phase (§ 1.6, lignes 139-141) documente cet écart point par point. Périmètre : Système A (Intercom) seul, 6 notebooks (01-06). | Cohérent avec le `.odt` de 27/07 sur la structure (mêmes 4 phases), assume et justifie l'écart de méthode — mais ne connaît pas encore le Système B ni le chronogramme en 10 étapes ci-dessous. |
| `protocole_etude_officiel.md` | fichier écrit le 17/08/2026 (contenu collé en séance, pas transcrit d'un fichier retrouvé sur le poste) | Texte **collé par l'utilisateur** — identique à celui repartagé le 18/08/2026 pour cette vérification. **Deux sources** (Intercom + second outil), chronogramme en 10 étapes, **aucune mention de sentiment ni de dashboard**. Objectifs spécifiques I-IV chiffrés (≥80 % fiabilité classification, 10 sous-motifs couvrant ≥80 % du volume, 100 % des 10 problèmes avec recommandation + responsable). | **Jamais comparé au `.odt` du 27/07 ni à `protocole_etude.md`.** C'est la version la plus récente et la plus détaillée obtenue du commanditaire — rien n'indique explicitement qu'elle remplace le `.odt`, mais son périmètre (Système B, pas de dashboard) est strictement plus large et incompatible avec un dashboard sentiment mono-source. À faire trancher par le commanditaire : ce texte remplace-t-il le `.odt` de juillet, ou les deux cadrages doivent-ils cohabiter ? |

**Conséquence directe** : `protocole_etude.md`, qui est aujourd'hui le document de référence du code
(cf. son en-tête, « fixe la méthodologie retenue pour la suite de l'étude »), justifie son écart
vis-à-vis du **mauvais** cadrage — celui du 27/07, sans Système B. Il ne traite pas, et ne peut pas
traiter, l'écart réel vis-à-vis du cadrage du 17/08 (Système B, chronogramme en 10 étapes, objectifs
spécifiques chiffrés), qui est pourtant le plus récent des deux.

### E.1 — Chronogramme du cadrage du 17/08 (`protocole_etude_officiel.md`) vs code exécuté

| Étape | Contenu attendu | Notebook(s) | Statut vérifié |
|---|---|---|---|
| 1 | Chargement, qualité, cadrage Intercom | 01, 02, 03 | ✅ fait |
| 2 | Chargement, qualité, cadrage second outil | 08 | ✅ fait |
| 3 | Recoupement + règle de déduplication | 09 | ✅ fait — 1 182 doublons retirés (voir section D) |
| 4 | Consolidation finale dédoublonnée | 12 (partiel) | ⚠️ un périmètre consolidé est calculé (24 879, section D.2) mais aucune table `resultats/` ne porte le jeu de données consolidé lui-même comme livrable unique |
| 5 | Reconstruction sous-motifs (règles + topic modeling) | 04, 07 | ⚠️ fait côté Système A seul ; rappel des règles plafonné à 57 % (documenté) |
| 6 | Validation croisée vs annotation manuelle | 11 | ⚠️ partiel — precision/rappel/F1 mesurés sur 2 familles causales sur 6 seulement (section C) |
| 7 | Stats de criticité + hiérarchisation (Objectif III : 10 sous-motifs, ≥80 % du volume **consolidé**) | 06 (Système A seul), 10, 12 | ❌ pas de table unique de hiérarchisation sur le périmètre consolidé A+B ; `10_exposition_par_sous_motif.csv` existe mais porte uniquement les 23 sous-motifs annotés du Système B, jamais fusionnés à la taxonomie causale du Système A (04) |
| 8 | Recommandations opérationnelles + responsable (Objectif IV : 100 % des 10 problèmes prioritaires) | — | ❌ aucun livrable trouvé. `04_par_responsable.csv` existe (attribution technique par famille causale — Système banque/opérateur 71 %, UX appli 12 %, authentification 6,7 %, monétique 3,8 %) mais c'est une donnée d'entrée, pas une recommandation opérationnelle rédigée |
| 9 | Évaluation exposition financière (Phase 4) | 12 §4 (partiel) | ⚠️ `12_exposition_comparee.csv` : convergence A/B à 50 000 XAF sur `debit_non_credit` uniquement (2 familles sur 6) ; `is_reclamation_fondee` vide à 100 % côté Système B (section D) — la question « fondée ou non » reste sans réponse |
| 10 | Rédaction du mémoire et restitution | — | ❌ aucun mémoire trouvé dans le dépôt |

**Matière première déjà présente mais non assemblée pour les étapes 7-9** : `04_par_responsable.csv`,
`10_exposition_par_sous_motif.csv`, `12_exposition_comparee.csv`, `12_top_agences.csv`,
`12_familles_causales_a.csv`, `12_sous_motifs_b.csv` couvrent chacun un fragment (fréquence, montant,
agence, responsable technique) mais aucune table ne les combine en un classement unique des 10
sous-motifs prioritaires exigé par l'Objectif III, et aucun document ne relie ce classement à une
recommandation + un responsable (Objectif IV).

### E.2 — Deux branches méthodologiques mortes, toujours versionnées

`niv1/` (22 fichiers, sentiment XLM-RoBERTa + topic modeling NMF + dashboard Streamlit — la première
itération, conforme au `.odt` du 27/07) et `niv2- tutoré/` (29 fichiers, statistique descriptive +
évolution temporelle + analyse de montants) précèdent, dans l'historique Git, le commit *« nouvele
approche »* (`b8bedcd`, 12/08) qui a fait basculer le projet vers `niv/`. Aucune des deux n'a été
retirée du dépôt ni marquée comme obsolète dans un README. Elles ne correspondent à aucune étape du
chronogramme du 17/08 et risquent de brouiller la lecture du dépôt pour un relecteur externe
(commanditaire ou comité) qui tomberait dessus en premier.

---

## Récapitulatif — priorité d'action avant mise à jour et validation

| # | Écart | Section | Priorité | Action |
|---|---|---|---|---|
| **E** | Trois cadrages non réconciliés (`.odt` 27/07 sentiment+dashboard, `protocole_etude.md` 14/08, `protocole_etude_officiel.md` 17/08 — Système A+B, 10 étapes) ; `protocole_etude.md` justifie son écart vis-à-vis du mauvais cadrage | tout le document | **Critique** — sans trancher lequel fait foi, aucun autre écart de ce tableau ne peut être corrigé de façon définitive | Faire confirmer par le commanditaire (Cédric Donfack) si `protocole_etude_officiel.md` (17/08) remplace le `.odt` (27/07) ; réécrire `protocole_etude.md` en conséquence |
| **E** | Étapes 7-9 du chronogramme du 17/08 : matière première éparse (`04_par_responsable.csv`, `10_exposition_par_sous_motif.csv`, `12_exposition_comparee.csv`, `12_top_agences.csv`) jamais assemblée en un classement unique des 10 sous-motifs prioritaires (Objectif III) ni en recommandations + responsables (Objectif IV) | E.1 | **Haute** — ce sont deux des quatre objectifs spécifiques chiffrés du cadrage le plus récent | Construire la table de fusion A+B par sous-motif (fréquence, canal, agence, montant), puis rédiger les 10 recommandations + responsables |
| **E** | Étape 10 (mémoire et restitution) : aucun document trouvé | E.1 | Moyenne à ce stade — dépend des étapes 7-9 | À planifier une fois E.1 soldé |
| **E** | `niv1/` et `niv2- tutoré/` (branches méthodologiques mortes) toujours versionnées, aucune ne correspond au chronogramme du 17/08 | E.2 | Basse pour l'analyse, moyenne pour la lisibilité du dépôt | Archiver ou marquer clairement obsolète dans un README |
| **Nouveau** | Protocole (§2-§6) cite les anciens effectifs de périmètre partout, code déjà à 9 381/8 348 | tout le document | **Haute** — le document entier est en décalage avec le code | Réécrire §2.4, §3.4, §3.5, §4.2, §4.4, §4.5, §5.1 avec les nouveaux chiffres (voir README et notebooks) |
| A3 | ~~Règle d'intégralité de l'extrapolation non appliquée, non marquée comme écart~~ | §5.1 | **Corrigé le 12/08/2026** | `AUDIT` corrigé dans le notebook 04, `assert` de non-régression ajouté |
| A1 | ~~Deux périmètres finaux coexistent, un seul est implémenté~~ | §3.4, §3.5 | **Corrigé le 13/08/2026, puis dépassé par l'intégration de `conversations_.xlsx`** | Règle journalière implémentée sur texte enrichi ; périmètre réel 9 381/8 348 |
| B — §7.2 | Cadre réglementaire non renseigné | §7.2, §7.4, §8.3 | Haute — conditionne la diffusion | Faire trancher par le service juridique / conformité |
| A2 | 7ᵉ famille causale absente du code | §4.2 | Moyenne | Ajouter la règle, ou retirer la ligne |
| C | ~~Jeu de référence, kappa, précision/rappel, sensibilité à l'ordre~~ | §4.5, §8.3 | Moyenne — conditionne 4 des 6 critères de succès | **Précision/rappel/F1 partiellement mesurés le 14/08/2026** (notebook 11, section D) sur 2 des 6 familles ; kappa, jeu stratifié de 300 textes et sensibilité à l'ordre toujours à réaliser |
| B — §1.1, §9 | ~~Commanditaire~~, tuteur, calendrier, rôles | §1.1, §9 | Basse pour l'analyse, haute pour la validation formelle | Commanditaire renseigné le 14/08/2026 (Cédric Donfack, DRI — retrouvé dans le document de cadrage officiel de l'étude, jusque-là non lu) ; tuteur/calendrier/rôles toujours à compléter |
| D | Système B (8 005 tickets) absent du protocole | tout le document | **Haute** — change le périmètre total (24 879 consolidés) | Réécrire le protocole pour intégrer le Système B (notebooks 08-12, section D) |

Ce tableau est la liste de travail à solder avant de soumettre le protocole pour validation.

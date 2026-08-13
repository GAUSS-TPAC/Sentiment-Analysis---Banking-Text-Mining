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
| Jeu de référence annoté, 300 textes stratifiés | N'existe pas dans le dépôt |
| Double annotation (100 textes) + coefficient kappa | Non réalisée |
| Précision, rappel, F1 par famille | Non calculables tant que le jeu de référence n'existe pas |
| Test de sensibilité à l'ordre des familles causales | Non réalisé |

**Conséquence directe sur §8.3** — sur les 6 critères de succès listés, seuls deux sont marqués
« atteint » aujourd'hui (représentativité V ≤ 0,20 ; absence de donnée personnelle dans les
livrables versionnés). Les quatre autres dépendent de ces étapes.

---

## Récapitulatif — priorité d'action avant mise à jour et validation

| # | Écart | Section | Priorité | Action |
|---|---|---|---|---|
| **Nouveau** | Protocole (§2-§6) cite les anciens effectifs de périmètre partout, code déjà à 9 381/8 348 | tout le document | **Haute** — le document entier est en décalage avec le code | Réécrire §2.4, §3.4, §3.5, §4.2, §4.4, §4.5, §5.1 avec les nouveaux chiffres (voir README et notebooks) |
| A3 | ~~Règle d'intégralité de l'extrapolation non appliquée, non marquée comme écart~~ | §5.1 | **Corrigé le 12/08/2026** | `AUDIT` corrigé dans le notebook 04, `assert` de non-régression ajouté |
| A1 | ~~Deux périmètres finaux coexistent, un seul est implémenté~~ | §3.4, §3.5 | **Corrigé le 13/08/2026, puis dépassé par l'intégration de `conversations_.xlsx`** | Règle journalière implémentée sur texte enrichi ; périmètre réel 9 381/8 348 |
| B — §7.2 | Cadre réglementaire non renseigné | §7.2, §7.4, §8.3 | Haute — conditionne la diffusion | Faire trancher par le service juridique / conformité |
| A2 | 7ᵉ famille causale absente du code | §4.2 | Moyenne | Ajouter la règle, ou retirer la ligne |
| C | Jeu de référence, kappa, précision/rappel, sensibilité à l'ordre | §4.5, §8.3 | Moyenne — conditionne 4 des 6 critères de succès | Planifier dans le calendrier (§9.1) |
| B — §1.1, §9 | Commanditaire, tuteur, calendrier, rôles | §1.1, §9 | Basse pour l'analyse, haute pour la validation formelle | À renseigner avant soumission |

Ce tableau est la liste de travail à solder avant de soumettre le protocole pour validation.

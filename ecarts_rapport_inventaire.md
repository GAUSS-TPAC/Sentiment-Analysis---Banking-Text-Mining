# Écarts entre le rapport d'inventaire des colonnes et la méthodologie / les objectifs retenus depuis

**Document examiné** : `niv2- tutoré/1- Rapport_Inventaire_Colonnes_Intercom.docx` — « Cadrage préalable
au choix des axes d'analyse », Afriland First Bank, Direction Recherche & Innovation.

**Référence de comparaison** : `protocole_etude.md` (racine du dépôt) et le code de `niv/`
(notebooks 01-06, `niv/src/reclamations/`).

**Nature de ce document** : une note de travail, pas un jugement de valeur sur le rapport. Le
rapport d'inventaire est cohérent en interne (les 4 totaux du §3 se reconstituent exactement à
partir des tableaux détaillés) et tous ses chiffres vérifiables se confirment sur le fichier
source. Les écarts relevés ci-dessous viennent de ce que ce document a été écrit **avant** les
découvertes qui ont ensuite structuré la méthodologie — c'est normal pour un cadrage préalable,
mais cela veut dire qu'il ne peut plus être présenté comme un état à jour sans révision.

---

## A. Écarts par rapport à la méthodologie

### A1 — Le taux de remplissage est traité comme une propriété stable de la colonne, alors que la méthodologie retenue montre qu'il ne l'est pas

C'est l'écart le plus important. Le rapport évalue chaque colonne sur un **taux de remplissage
global** (ex. : `Montant en XAF` à 40 %, `Agence` à 42 %) et en déduit un niveau de potentiel
(Structurante / Utile / Marginale / Sans valeur).

La méthodologie retenue depuis établit que ce taux global est trompeur : quatre champs de
formulaire indépendants (dont `Montant en XAF`, `Agence`, description, titre) sont remplis à
92-99 % de novembre 2025 à février 2026, s'effondrent à 3-16 % en mars-avril 2026, et reviennent à
92-99 % à partir de juin. Un taux moyen de 40 % masque cette rupture datée au 13 mars 2026.

Le notebook 01, section finale, formule exactement cette réserve — écrite **avant** que la rupture
ne soit établie au notebook 02 : « Une moyenne de 55 % de manquants sur la description peut vouloir
dire "les agents remplissent une fois sur deux" (problème de process, diffus) ou "le champ est
rempli à 95 % sauf pendant trois mois où il tombe à 3 %" (problème système, daté). […] rien dans ce
tableau ne permet de trancher. » Le rapport d'inventaire applique précisément le mode de lecture
que cette réserve met en garde.

**Conséquence pour la mise à jour** : les niveaux de potentiel attribués aux colonnes affectées
(`Montant en XAF`, `Agence`, `Date de la transaction`, titre, description) doivent être reconsidérés
à la lumière de la rupture — pas nécessairement rabaissés, mais assortis de la même réserve que le
protocole applique désormais partout : tout indicateur porte son périmètre temporel.

### A2 — `open` est présenté comme un indicateur fiable, ce que la suite de l'analyse contredit

Le rapport (§4) classe `open` : « **Utile** — indicateur simple ouvert/fermé », sans réserve.

Le notebook 05 (cellule 14) établit que `open` vaut `TRUE` pour seulement **0,27 %** des tickets,
alors que `ticket_state_category = resolved` en représente **9,25 %** sur la même période. Les
deux champs, censés mesurer la même chose (un dossier clos), ne racontent pas la même histoire — et
le protocole qui en découle (§5.3, §8.4 point 4) **interdit toute communication d'un taux de
résolution** tant que ce point n'est pas tranché avec l'équipe support.

**Conséquence pour la mise à jour** : `open` ne peut plus être qualifié de « simple » sans la
réserve sur l'ambiguïté du statut. Le champ `ticket_state_category`, classé « Utile » dans le
rapport pour « toute question de taux de résolution », appelle la même réserve.

### A3 — Les colonnes tronquées sont classées au même niveau que les colonnes réellement inutiles

Le rapport classe `ticket_type_ticket_type_attributes_data` et `ticket_parts_ticket_parts` **Sans
valeur analytique**, au même titre que des colonnes constantes comme `type` ou
`ticket_type_icon`. La définition même du niveau « Sans valeur » (§2 du rapport) les regroupe :
« constante, doublon d'une autre colonne, ou champ corrompu à l'export ».

La méthodologie retenue distingue ces deux cas explicitement, parce qu'ils appellent des suites
opposées : *« une colonne constante n'apporte pas d'information : on l'écarte. Un champ tronqué en
apportait et l'a perdue à l'extraction : on redemande l'export »* (`chargement.colonnes_tronquees`,
protocole §2.4). C'est précisément ce champ — le fil de conversation — qui est identifié comme la
première donnée à redemander (protocole §8.4, demande n° 2), parce qu'il contient potentiellement
la matière la plus riche du fichier (~500 000 échanges, compteur `ticket_parts_total_count` à
l'appui).

**Conséquence pour la mise à jour** : séparer, dans le niveau « Sans valeur », un sous-motif
« tronquée à l'export — à ré-extraire », distinct de « constante » et de « doublon ». Ce n'est pas
un détail de présentation : classer ces deux colonnes au même rang que `ticket_type_icon` minimise
ce qui est présenté ailleurs comme le point le plus bloquant du dossier.

### A4 — `ticket_parts_total_count` est sous-évalué et présenté sans la réserve qui s'impose

Le rapport (§8) le classe **Marginale** : « proxy possible de la complexité du dossier ».

Ce compteur devient central dans la suite de l'analyse (notebook 05) : il fonde le calcul de
501 399 messages échangés et 7 959 messages par agent et par mois. Mais sa nature exacte — messages
humains seuls, ou également événements système et changements d'état — **n'est vérifiable par
aucun moyen**, précisément parce que le contenu des parts est tronqué (A3). Le protocole (§6.3)
traite ce point comme une hypothèse non confirmée et exige que tout ratio qui en dérive soit publié
comme conditionnel.

**Conséquence pour la mise à jour** : reclasser au moins en « Utile », avec la réserve sur sa
nature non vérifiée — la classification « Marginale » sans réserve va dans les deux sens à la fois
(elle sous-estime son usage réel et omet la prudence qui s'impose sur ce qu'il mesure).

### A5 — Aucune règle de traitement pour les colonnes signalées « sensibles »

Le rapport identifie correctement `Nom du client` comme « Utile (sensible) » et `Numero de compte`
comme « Utile (très sensible) » (§9), mais ne fixe aucune règle de traitement — masquage,
exclusion des tables versionnées, etc.

C'est un écart d'autant plus concret qu'une exposition réelle de ces mêmes données a eu lieu dans
l'historique du projet : nom et numéro de téléphone d'un client réel dans une table versionnée,
corrigée depuis par réécriture de l'historique (protocole §7.3). Le rapport de cadrage, en amont de
tout traitement, est l'endroit le plus naturel pour poser la règle *avant* qu'elle ne soit apprise
par l'incident.

**Conséquence pour la mise à jour** : ajouter, pour chaque colonne « sensible », la règle
applicable (masquage à l'écriture, jamais d'exemple de valeur en clair dans un document diffusé —
protocole §7.3).

### A6 — Le périmètre de référence utilisé pour recalculer la fiabilité (8 284) ne correspond à aucun périmètre retenu ensuite

Le rapport (§9) recalcule les taux de remplissage sur un sous-ensemble de **8 284 tickets**, défini
comme « titre ou description disponible », sans seuil de longueur. Vérification faite sur le
fichier source : ce chiffre et les deux taux qui en découlent (`Montant en XAF` 87,23 %,
`Numero_tel_client` 92,93 %) sont **exacts**.

Mais ce périmètre ne recoupe aucun de ceux utilisés dans la suite : la méthodologie retenue exige
un texte de plus de 25 caractères (`LONGUEUR_TEXTE_MIN`) et distingue la période opérationnelle
(18 056 → 7 901 textes exploitables), le périmètre d'analyse causale par mois (6 867 → 6 545) et la
règle à la journée retenue par le protocole (7 950 → 7 563). Aucun de ces chiffres ne vaut 8 284.

**Conséquence pour la mise à jour** : soit documenter explicitement que 8 284 est une définition
propre à ce rapport (titre ou description non vide, sans seuil, sans restriction de période), soit
le recalculer sur le périmètre qui a servi de référence ensuite — pour qu'un lecteur ne rapproche
pas involontairement les deux séries de chiffres.

### A7 — Deux imprécisions factuelles mineures, à corriger

- **`admin_assignee_id` : cardinalité 8 dans le rapport (calculée sur les 18 094 lignes), contre 7
  dans le notebook 05** (calculée sur la période opérationnelle, 18 056 lignes). L'écart s'explique :
  un identifiant d'agent (`7304380`) n'apparaît que dans la phase pilote, exclue de la période
  opérationnelle. Les deux chiffres sont corrects sur leur périmètre respectif, mais leur
  coexistence sans note produira une incohérence apparente dans le mémoire si l'un des deux est
  repris sans préciser lequel.
- **`ticket_state_internal_label` et `ticket_state_external_label`** sont qualifiés de « doublon
  libellé » dans le rapport (§4). Vérification faite : ils diffèrent sur **17 lignes sur 18 094**
  (`Waiting on customer` / `Waiting on you`). Ce n'est pas un doublon strict, même si l'écart est
  marginal en volume.

  (`ticket_type_category` est en revanche un doublon exact de `category` sur les 18 094 lignes,
  vérifié — aucune correction à faire sur ce point du rapport.)

---

## B. Écarts par rapport aux objectifs

### B1 — L'angle d'analyse que le rapport refuse explicitement de trancher a été tranché depuis

Le rapport se positionne délibérément en amont de tout choix : *« il ne présuppose pas ce qui sera
étudié »* (§1), et conclut : *« il revient au management de statuer sur l'angle ou les angles
d'analyse à retenir »* (§11).

Ce choix a été fait depuis. La problématique retenue dans le protocole (§1.2) est spécifique :
*« pourquoi une part significative des transferts entre SARA et les opérateurs de mobile money
débite le client sans créditer le bénéficiaire — et comment agir à la source pour réduire le taux
d'incident par transaction »*. C'est un axe causal, centré sur `ticket_type_name = SARA` et sur le
texte libre de la réclamation — que le rapport d'inventaire ne mentionne à aucun moment comme
hypothèse ni comme axe probable, alors qu'il représente 59 % du volume de la période opérationnelle.

**Conséquence pour la mise à jour** : le rapport doit soit être requalifié comme document historique
(« cadrage produit avant le choix d'orientation du [date] »), soit être mis à jour pour acter la
décision prise — auquel cas la section 11 doit être réécrite : ce n'est plus une question ouverte.

### B2 — Le rapport ne pose pas la question « comment résoudre », et rien n'y anticipe les données manquantes qui la bloquent

L'étude, telle que cadrée dans le protocole, répond à deux questions : quels sont les problèmes, et
comment les résoudre. Le rapport d'inventaire, en se limitant à un classement de colonnes, ne peut
pas être confronté à la deuxième — ce n'est pas en soi un défaut, mais une incomplétude à corriger
si ce document doit continuer à servir de référence.

Concrètement, trois données que le protocole identifie comme bloquantes pour la question de
résolution (§8.4, données demandées) sont déjà visibles dans les colonnes inventoriées, sans que le
rapport ne le signale :

| Donnée manquante identifiée dans le protocole | Colonne du rapport qui l'annonçait déjà |
|---|---|
| Journal des transactions (aucun code d'erreur, aucun statut de passerelle) | Absente du fichier — le rapport ne le relève pas comme un manque structurant |
| Fil de conversation complet (issue du dossier) | `ticket_parts_ticket_parts`, classée « Sans valeur » sans alerte sur ce que sa perte empêche (A3) |
| Date de clôture et issue du dossier | `ticket_state_category` / `open`, classées sans réserve (A2) |

**Conséquence pour la mise à jour** : ajouter une colonne ou une note « ce que cette colonne, en
l'état, empêche de conclure » à côté des colonnes concernées — c'est ce déplacement de focale, de
« que contient la colonne » à « qu'est-ce que son état empêche d'établir », qui a produit les
résultats les plus utiles de la suite de l'étude (protocole §6).

### B3 — Le rapport ne mentionne pas le piège de mesure ni l'indicateur cible retenu

Le protocole (§1.2) pose une mise en garde centrale : si l'indicateur de succès devient le *nombre*
de réclamations, le moyen le plus efficace de l'atteindre est de rendre la réclamation plus
difficile à déposer — ce qui s'est produit de fait en mars 2026 (A1). L'indicateur retenu est donc
un **taux d'incident par transaction**, qui suppose un dénominateur absent de ce fichier.

Le rapport d'inventaire, antérieur à cette décision, ne pouvait pas l'anticiper. Mais sa conclusion
(§11) — *« un socle de 7 colonnes structurantes couvrirait la plupart des analyses envisageables »*
— suggère implicitement que le fichier suffit à cadrer l'analyse, sans mentionner que la question la
plus importante (le taux, pas le volume) restera hors de portée quel que soit l'angle choisi parmi
les colonnes disponibles.

**Conséquence pour la mise à jour** : ajouter, en conclusion, que le fichier inventorié ne permet de
répondre qu'à des questions de structure et de volume, jamais de taux — ce point ne dépend d'aucun
angle d'analyse et aurait sa place dans un rapport de cadrage.

---

## Récapitulatif — ce qui doit changer dans le document

| # | Section du rapport | Nature de la mise à jour |
|---|---|---|
| A1 | §9 (et toute colonne notée par son taux global) | Ajouter la réserve temporelle : taux stable hors mars-mai 2026, effondré pendant |
| A2 | §4, lignes `open` et `ticket_state_category` | Retirer la mention « fiable » / « simple » ; ajouter la réserve d'ambiguïté |
| A3 | §5 et §8, colonnes tronquées | Créer un sous-motif « tronquée — à ré-extraire », distinct de « constante » |
| A4 | §8, `ticket_parts_total_count` | Reclasser en Utile, avec réserve sur sa nature non vérifiée |
| A5 | §9, colonnes sensibles | Ajouter la règle de traitement (masquage, non-diffusion en clair) |
| A6 | §9, base de recalcul (8 284) | Documenter la définition ou la réaligner sur le périmètre retenu ensuite |
| A7 | §4, §6 | Corriger la cardinalité `admin_assignee_id` (préciser le périmètre) et la qualification de doublon des deux libellés de statut |
| B1 | §11 | Acter la décision d'angle prise depuis, ou requalifier le document comme historique |
| B2 | §8, §10 | Signaler ce que chaque colonne dégradée empêche de conclure, pas seulement ce qu'elle contient |
| B3 | §11 | Ajouter la limite du taux d'incident, indépendante de l'angle retenu |

Ce tableau est la base à utiliser pour la mise à jour et la validation par le management /
maître de stage.

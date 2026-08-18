# Protocole d'étude

**Analyse des réclamations clients par text mining — Afriland First Bank**

*Analyse effectuée sur l'export du canal Intercom (`SRC_Intercom_Reclamation_202607201846.csv`) et sur les exports de l'outil de gestion des réclamations interne (`tickets_first.xlsx` et les 7 fichiers relationnels associés — catégories, groupes, utilisateurs, affectations, champs personnalisés, conversations).*

## Confidentialité

Ce document ne saurait être divulgué en partie ou en totalité verbalement ou par écrit, y compris par les moyens de la photocopie, à une tierce personne sans une autorisation écrite de Afriland First Bank.
Ce document ainsi que les annexes et tout autre document qui y est rattaché est la propriété d'Afriland First Bank et doit lui être retourné à sa demande.

## Historique du document

| Auteur(s) | Unités | Acteurs | Signature |
|---|---|---|---|
| Alan TCHAPDA | DRI | Analyste | |
| | | Relecture | |
| | | Relecture | |
| Mr Cédric Donfack | DRI | Commanditaire | |

## TABLE DES MATIÈRES

- TABLE DES MATIÈRES
- Contexte
  - I. Situation actuelle
  - II. Situation désirée
  - III. Questions d'intérêts
- Objectifs
- Démarche méthodologique
  - Phase 1 : Analyse de conformité et conception d'une nouvelle procédure
  - Phase 2 : Analyse des causes profondes
  - Phase 3 : Formulation des recommandations opérationnelles
  - Phase 4 : Évaluation de la responsabilité vis-à-vis des créanciers
- Chronogramme de réalisation

---

## Contexte

### I. Situation actuelle

Les réclamations clients (SARA, comptes, cartes, virements…) ne sont pas centralisées dans un
seul outil. Deux systèmes vivent en parallèle, indépendamment gérés :

- **Intercom**, tous canaux applicatifs confondus (Android, iOS, WhatsApp, réseaux sociaux, e-mail).
  Sur la période observée du 1ᵉʳ février 2024 au 17 juillet 2026, soit un peu plus de 2 ans et
  5 mois, **18 094 tickets** y ont été enregistrés.
- **Un second outil de gestion de réclamations**, à usage interne, qui couvre en plus des canaux
  qu'Intercom ne capte pas (agence, courrier, appel téléphonique, e-mail direct, transmission
  entre collègues), actif sur la même période récente. **8 005 tickets** y sont enregistrés.

Ces deux outils n'ont jamais été rapprochés : on ignore aujourd'hui dans quelle mesure ils se
recoupent (une même réclamation ressaisie deux fois) ou se complètent (un canal que l'un capte et
l'autre non). Tant que ce recoupement n'est pas mesuré, aucun des deux volumes pris isolément ne
donne le nombre réel de réclamations distinctes, et aucune addition brute des deux n'est fiable
non plus.

Le motif précis de chaque réclamation n'est structuré de façon exploitable dans aucun des deux
systèmes à grande échelle : côté Intercom il repose uniquement sur du texte libre ; côté second
outil, une qualification plus fine existe (trois champs de sous-motif renseignés à la main sur une
partie des tickets) mais reste circonscrite à cet outil, non reliée à Intercom, et jamais exploitée
jusqu'ici pour lire l'ensemble des réclamations. Cette situation ne permet pas d'identifier
directement les problèmes les plus fréquents ni les plus critiques pour les clients, ni de savoir
si une piste de résolution a réellement été mise en œuvre : le suivi de résolution (statut, action
prise) n'existe de façon exploitable que dans le second outil, jamais dans Intercom.

### II. Situation désirée

À l'issue de l'étude :

- Chaque réclamation, quelle que soit sa source, est comptée une seule fois — les doublons entre
  les deux systèmes sont identifiés et retirés avant tout comptage.
- Chaque réclamation est rattachée à une catégorie et à un sous-motif réel, reconstruit à partir du
  texte libre côté Intercom, et confronté à la qualification déjà annotée à la main côté second
  outil — ce rapprochement sert à mesurer, chiffres à l'appui, la fiabilité de la reconstruction
  automatique plutôt que de la supposer correcte.
- Les problèmes les plus critiques sont identifiés et hiérarchisés selon des critères mesurables :
  fréquence, canaux concernés, agences concernées (information disponible côté second outil,
  absente d'Intercom), montants engagés.
- Chaque problème prioritaire est relié à une piste de résolution concrète et au service concerné,
  en s'appuyant, quand elle existe, sur l'action de résolution déjà consignée dans le second outil.
- La Banque dispose d'une lecture unique et consolidée de ses principaux points de friction avec
  ses clients, toutes sources confondues, et des leviers pour les corriger.

L'étude doit répondre à deux questions : quels sont les principaux problèmes rencontrés par les
clients, et quelles solutions permettent de les résoudre — la réponse devant s'appuyer sur
l'ensemble de l'information disponible, pas sur une seule des deux sources prise isolément.

### III. Questions d'intérêts

1. Quels motifs et sous-motifs de réclamation génèrent le plus fort volume, une fois les deux
   sources consolidées et les doublons retirés ?
2. Quelles catégories de réclamation concentrent le plus de tickets ?
3. Quels canaux, et quelles agences (information propre au second outil), concentrent le plus de
   réclamations ?
4. Quelles catégories, bien que faibles en volume, concentrent les montants financiers les plus
   élevés ?
5. Existe-t-il une tendance temporelle (dégradation, pic) nécessitant une investigation ciblée ?
6. Pour chaque problème identifié, quelle action corrective est envisageable et quel service en a
   la charge ?
7. Dans quelle mesure les deux systèmes se recoupent-ils, et que capte le second outil que
   Intercom ne capte pas (et réciproquement) ?
8. La reconstruction automatique des sous-motifs à partir du texte libre Intercom est-elle fiable,
   mesurée contre la qualification annotée à la main du second outil ?
9. La méthode d'analyse est-elle reproductible sur un prochain export de chacune des deux sources ?

---

## Objectifs

**Objectif principal :**
Identifier les principaux problèmes rencontrés par les clients à partir de l'ensemble des
réclamations disponibles — toutes sources confondues, doublons retirés — et formuler des
solutions opérationnelles permettant de les résoudre.

**Objectifs spécifiques :**

I. Préparer et consolider les données : nettoyer chaque source séparément, puis identifier et
   retirer les réclamations présentes dans les deux systèmes, afin de disposer d'une base fiable
   et non redondante pour l'analyse.

II. Classer chaque réclamation par sous-motif réel, reconstruit à partir du contenu pour dépasser
   les catégories déclarées souvent trop larges, et **valider cette reconstruction** en la
   confrontant à la qualification annotée à la main disponible pour une partie des réclamations du
   second outil.

III. Établir des statistiques de criticité (volumes, montants médians engagés, par catégorie,
   canal, agence, mois) permettant de hiérarchiser les problèmes plutôt que de les lister à plat.

IV. Formuler, pour chaque problème prioritaire, une piste de résolution concrète associée à un
   responsable identifiable, en s'appuyant sur les actions de résolution déjà consignées quand
   elles existent.

---

## Démarche méthodologique

### Phase 1 : Analyse de conformité et conception d'une nouvelle procédure

- État des lieux des données disponibles dans **chacune des deux sources** : structure des
  exports, taux de remplissage par champ, identification des champs exploitables pour l'analyse.
- Mesure du recoupement entre les deux systèmes : appariement des tickets par identifiants
  partagés (téléphone, montant, date, référence de transaction), pour distinguer les réclamations
  ressaisies deux fois de celles réellement propres à chaque outil.
- Conception de la procédure de préparation : consolidation du texte libre, correction de
  l'encodage, masquage des données personnelles, normalisation du texte, et règle explicite de
  déduplication entre les deux sources.

**Livrable :** jeu de données consolidé, nettoyé et dédoublonné, base de l'ensemble des analyses
suivantes.

### Phase 2 : Analyse des causes profondes

- Reconstruction des sous-motifs réels de réclamation par catégorie, à partir du texte libre côté
  Intercom, complétée par du topic modeling sur les catégories les moins bien couvertes par les
  règles.
- **Validation croisée** : comparaison systématique, sur les réclamations communes aux deux
  sources ou disposant d'une qualification manuelle côté second outil, entre le sous-motif annoté
  à la main et le sous-motif reconstruit automatiquement — mesure chiffrée (précision, rappel) de
  la fiabilité de la reconstruction, et non plus une hypothèse non vérifiée.

**Livrable :** chaque ticket dispose d'une catégorie et d'un sous-motif, exploitables pour la
hiérarchisation des problèmes, accompagnés d'une mesure de fiabilité de la méthode.

### Phase 3 : Formulation des recommandations opérationnelles

- Construction des statistiques de criticité sur la base consolidée : volumes par catégorie,
  canal, agence, mois ; montants médians ; classement des sous-motifs les plus critiques.
- Identification des problèmes prioritaires à partir de ces statistiques, sur un périmètre plus
  large et moins redondant que chacune des deux sources prise isolément.
- Formulation de recommandations opérationnelles pour chaque problème prioritaire, en s'appuyant,
  quand elle est disponible, sur l'action de résolution déjà pratiquée.

**Livrable :** synthèse des problèmes hiérarchisés et des solutions associées, sur l'ensemble des
réclamations consolidées.

### Phase 4 : Évaluation de la responsabilité vis-à-vis des créanciers

- Isoler, parmi les problèmes identifiés, ceux pour lesquels un dysfonctionnement confirmé entraîne
  un préjudice financier pour le client (ex. bénéficiaire erroné, fonds non reçus).
- Quantifier le volume et les montants concernés, en s'appuyant en priorité sur le champ montant
  du second outil, nettement mieux renseigné que le champ équivalent d'Intercom.

**Livrable :** évaluation chiffrée de l'exposition financière associée à ces problèmes, sur une
base de montants plus complète que celle qu'une seule des deux sources permettrait.

---

## Chronogramme de réalisation

| Étape | Contenu | Phase |
|---|---|---|
| 1 | Chargement, qualité et cadrage de la source Intercom | 1 |
| 2 | Chargement, qualité et cadrage du second outil | 1 |
| 3 | Mesure du recoupement entre les deux sources et règle de déduplication | 1 |
| 4 | Consolidation du jeu de données final (dédoublonné) | 1 |
| 5 | Reconstruction des sous-motifs (règles + topic modeling) | 2 |
| 6 | Validation croisée de la reconstruction contre l'annotation manuelle | 2 |
| 7 | Statistiques de criticité et hiérarchisation | 3 |
| 8 | Recommandations opérationnelles | 3 |
| 9 | Évaluation de l'exposition financière | 4 |
| 10 | Rédaction du mémoire et restitution | — |

**[À COMPLÉTER]** — dates et durées par étape, à fixer avec le commanditaire.

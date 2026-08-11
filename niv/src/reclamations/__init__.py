"""
Analyse des réclamations clients Intercom — Afriland First Bank.

Ce package regroupe la logique réutilisée par les notebooks `notebooks/01..06`.
Les notebooks portent le raisonnement et les commentaires d'analyse ; le package
porte le code qui doit être identique d'un notebook à l'autre (chargement,
définition du périmètre, taxonomie des motifs, charte graphique).

Règle de séparation appliquée :
    - une constante ou un seuil utilisé par plus d'un notebook  -> `config.py`
    - une transformation de données réutilisée                  -> `chargement.py` / `texte.py`
    - tout le reste (exploration, interprétation)               -> le notebook

Ordre de lecture des notebooks :
    01  chargement et qualité du fichier source
    02  détection de la rupture de collecte du 13/03/2026
    03  définition du périmètre d'analyse et test de représentativité
    04  analyse causale des motifs de réclamation
    05  récidive client et charge de traitement
    06  synthèse et énoncé de la problématique
"""

from . import chargement, config, texte, viz

__all__ = ["config", "chargement", "texte", "viz"]
__version__ = "1.0.0"

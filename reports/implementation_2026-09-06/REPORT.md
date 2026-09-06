# HyperBot2 — livraison et validation du 6 septembre 2026

La v0 de recherche est installable et exécutable dans HyperBot2. Elle reprend
le noyau HyperBot et ajoute les contrats outcomes, la stratégie sélective,
la comptabilité cash/FIFO, les réservations et le runner de campagne.
**Verdict des données réelles : `DATA_BLOCKED`. Aucun rendement du nouveau
candidat n’est établi et aucun service n’a été déployé.**

## Vérification logicielle

140 tests passent : 82 hérités et 58 nouveaux cas. Ruff et mypy strict passent.
Le sdist et le wheel sont construits avec `uv build`. Le wheel a été installé
dans un environnement isolé ; la commande catalogue y retourne le verdict
attendu, sans installation des anciens bots. Le shadow synthétique final
exécute également ses 18 variantes jusqu’au rapport.
La démonstration synthétique exécute 18 combinaisons preregistrées et produit
des cycles fermés, frais, annulations et liquidations terminales cohérents.
Les sorties synthétiques sont locales dans `data/validation/demo-replay/` et
ne sont pas présentées comme une preuve de marché.

Les nouveaux cas portent sur les frais par opération, les fills partiels et
idempotents, les réservations, les limites de risque, les données causales,
les ACK rapides, le franchissement ALO à l’activation, l’annulation en vol,
la déduplication duale, le PF par cycle, la qualification et les budgets.
Le modèle central et le shadow sur fenêtres partagent la même stratégie,
le même superviseur, la même comptabilité et donnent les mêmes résultats.

## Archives réutilisées

Le [screening intégral](screen.json) ouvre directement le fichier HIP-4 déjà
présent dans TRIDENT, via l’adaptateur HyperBot repris. Il ne copie pas ses
centaines de milliers de lignes dans le dépôt.

| Mesure | Résultat |
|---|---:|
| Snapshots lus | 892 492 |
| Carnets valides retenus | 818 968 |
| Carnets invalides | 73 522 |
| Doublons/hors ordre consécutifs | 2 |
| CPU du run | 26,37 s |
| Pic RSS | 29,14 Mio |
| Clôtures paper legacy | 99, dont 38 anticipées |
| Marchés distincts du paper | 93 |
| PnL paper legacy recalculé | +43,66203616 $ |
| PF paper legacy | 1,08744 |

Sources et SHA-256 sont enregistrés dans le rapport. Le paper décrit l’ancien
bot, pas les exécutions du nouveau candidat. Le scan reproduit les spreads
médians descriptifs de l’audit initial : BTC 0,0040, ETH 0,0353, SOL 0,0356,
HYPE 0,0395 dollar par token. Ces valeurs ne sont pas des rendements.
Les markouts 30 s ne disposent de labels à 30–35 s que sur une petite partie
des observations ; les labels manquants sont explicitement comptés.

## Témoin public borné

Le [témoin](witness.json) a duré 40,25 s depuis l’environnement de développement,
avec les quatre outcomes quotidiens et leurs deux côtés : 16 abonnements
confirmés, 853 événements persistés, zéro événement abandonné, zéro message
malformé et zéro reconnexion. Le processus s’est arrêté normalement.

L’[analyse des carnets enregistrés](witness-quality.json) mesure :

| Mesure | Résultat |
|---|---:|
| Carnets L2 reçus / `fast=true` confirmé dans le payload | 591 / 591 |
| Mises à jour distinctes par coin | 590 |
| Frais à réception, âge ≤ 500 ms | 560 / 591 |
| Frais à activation avec placement 350 ms + horloge 50 ms | **0 / 591** |
| Frais à activation, placement ×2 | **0 / 591** |
| Profondeur observée par côté | 2 à 5 niveaux |
| Volume raw et contrôles | 858 271 octets |

Il s’agit d’un témoin court dans cet environnement, pas d’une mesure de latence
de production. Néanmoins, sous les hypothèses conservées, aucune quote ne
passe la fraîcheur d’activation. Le test stress placement 700 ms dépasse déjà
la limite de 500 ms même avec un carnet reçu sans retard : l’abstention est
attendue, la limite ne doit pas être assouplie pour fabriquer des fills.

## Gaps précis et décision

| Gap | Comportement livré | Suite nécessaire pour lever le gap |
|---|---|---|
| Ticks/lots, statut, règle et frais non attestés | Catalogue découvert mais non qualifié | Rassembler des spécifications et taux effectifs datés, avec hashes ; pas d’imputation rétroactive |
| Prix de référence et calibration causaux non joints aux archives | `fair_value_missing` bloque le candidat | Exporter seulement les périodes nécessaires, joindre références et labels purgés ; le calculateur causal existe |
| File maker duale non qualifiée sur les raws disponibles | Central/pessimiste refusent B/C et A non qualifié | Audit de profondeur, priorité et séquences sur preuves A ; les trades seuls ne reconstruisent pas les annulations |
| Fraîcheur insuffisante dans le témoin local | Abstention avant émission | Une mesure bornée dans l’environnement envisagé et un budget d’exécution étayé ; aucune collecte permanente lancée |
| Quotas réels non attestés | Budget simulé prépaie placement + annulation | Vérifier un snapshot du quota et ses règles avant tout examen d’exécution réelle |
| OOS et 14 jours shadow absents | Promotion toujours désactivée | Préenregistrer et financer séparément une campagne après résolution des gaps précédents |

Les limites logicielles sont explicites : shadow sur fenêtres enregistrées,
pas de daemon de trading ; aucune reprise d’un portefeuille après interruption ;
les logs de simulation en mémoire restent soumis au plafond du processus ;
la qualification des attestations et de la file n’est pas automatisée à partir
de drapeaux JSON. Le runner ne revendique aucun PASS OOS.

Le plan autorise précisément `DATA_BLOCKED` lorsque ces inputs manquent. Le
screening et le témoin s’arrêtent avec ce verdict, sans engager une nouvelle
collecte d’un mois. Le coût CPU du screening est publié séparément des 20 $
mensuels d’infrastructure utilisés comme hypothèse dans les simulations.

Les manifests joints identifient exactement le code exécuté pour chaque run ;
ils précèdent quelques améliorations de diagnostic et de documentation livrées
ensuite. Les anciens dépôts ont été utilisés en lecture seule. Les services
arrêtés à la demande de l’utilisateur n’ont pas été redémarrés.

# Test exploratoire des outcomes à cinq minutes

**Aucun signal ; variante suspendue.** Le chiffre idéal de 181,99 $/mois de
la borne précédente ne se transforme pas en opportunités avec la règle de
référence prudente testée ici. Cela ne démontre pas l'impossibilité de toute
stratégie outcomes, ni une performance nulle sur les observations manquantes.

## Test et données

Le [protocole](PROTOCOL.md) est figé avant ce calcul, mais les résolutions ont
déjà été vues lors des recherches précédentes : ce test est exploratoire,
**pas hors échantillon**. Réutilisation des 892 492 observations Nautilus,
des références brutes mainnet et de la volatilité horaire native existantes.
Aucun achat, nouvelle collecte, import de stratégie TRIDENT ou ordre.

La [documentation officielle](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/contract-specifications.md)
définit le paiement des binaires par interpolation des marks encadrant
l'échéance. Elle distingue aussi les références des perps principalement
libellées en USDT de celles de HYPE/PURR en USD. Une moyenne de prix USD et
USDT ne constitue donc pas automatiquement une référence cohérente avec le
contrat, particulièrement près du seuil de paiement.

Sur les 42 contrats avec références journalisées avant décision, les 18 BTC,
7 ETH et 6 SOL ont une référence OKX SPOT USDT horodatée, non croisée et âgée
d'au plus 60 secondes. Les 11 HYPE sont exclus faute de référence qualifiée
dans la devise correspondante. Les 73 autres contrats n'ont pas de référence
retenue par l'audit antérieur. Les absences restent conditionnées par la
détection d'opportunités legacy : biais de sélection non résolu.

Benchmark digital sans drift à cinq minutes, volatilité native sur 168 heures
complètes, trois échelles de volatilité et prix externe ±15 bps. Prendre la
probabilité minimale pour chaque côté puis retrancher trois points. Exiger
encore cinq points de marge après retenue prudente sur le paiement final.
La bande ±15 bps est une hypothèse de sensibilité explicite, pas une garantie
sur l'écart entre le prix externe et le mark natif. Les prix natifs exacts
restent non qualifiés pour une promotion.

## Résultats

| Filtre | Nombre |
|---|---:|
| Contrats dans l'univers | 115 |
| Référence non qualifiée ou absente | 84 |
| Contrats évalués | 31 |
| Côtés évalués | 62 |
| Carnet absent, invalide ou stale | 17 |
| Ask hors de la plage 0,15–0,85 | 39 |
| Ask dans la plage, mais marge insuffisante | 6 |
| Signaux acceptés | **0** |

Sur les six côtés dans la plage, la meilleure marge prudente est
**−18,54 points**, contre +5 requis. Quatre des six ne satisfont pas non plus
la capacité pour un achat d'environ 10 $ limité à 10 % de la taille affichée.
Aucune optimisation de seuil après ce constat.

Aucun trade simulé : PnL de transactions nul dans les scénarios central, stress
et retard. Le champ −20 $/mois des résumés représente seulement la soustraction
de l'hypothèse d'infrastructure sur cette activité nulle ; ce n'est pas une
perte réelle ni une dépense engagée. Aucun scénario ne justifie de multiplier
le montant des positions pour viser les 150–200 $ mensuels acceptés.

## Livraison et suite

Le module `expiry_reference` qualifie source, devise, produit, horloges et BBO.
Le script réutilise le benchmark, le sizing, les rejets d'exécution et le
paiement du moteur taker existant. Un test supplémentaire couvre notamment
la mauvaise devise, les timestamps futurs/stale et les carnets croisés ou NaN.
231 tests passent, lint/format (191 fichiers) et mypy (58 sources) passent.
Trois artefacts reproduits exactement : [preuve](reproduction.json).

Statut `EXPLORATORY_ONLY_NO_GO`. La règle en fin d'échéance est suspendue avec
les données disponibles. Aucun besoin démontré d'acheter un flux pour la sauver.
L'étape suivante change de mécanisme : examiner une couverture entre les
actions crypto cotées sur HIP-3 (COIN/MSTR) et BTC, avec les historiques natifs
déjà disponibles. Tester un écart relatif après hedge et tous les coûts, plutôt
que recycler le PnL idéal des outcomes. Cette nouvelle hypothèse devra être
figée avant calcul et conserver les restrictions d'échantillon déjà consulté.

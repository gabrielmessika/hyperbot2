# Contrôle passif et effet du sous-panel sur Hyperliquid

Avant le calcul de transfert 2025, les données natives existantes fournissent
deux comparaisons. Même compte1 000 $, période204 jours, seuil de drawdown30 %,
frais/funding/slippage, lots, ticks, reports de petits ordres et risque latent.
Un long passif entre à l'indice193 après warmup, puis conserve ses quantités
jusqu'au dernier open, sauf arrêt de risque. Aucun rééquilibrage.

## Panel original de18 actifs

| Règle, sans infrastructure supplémentaire | Central net | Mensuel équivalent | Stress coûts net | Enveloppe centrale |
|---|---:|---:|---:|---:|
| Candidat50/50, exposition cible1,5x | +538,26 $ | 6,54 % | +206,49 $ | 27,56 % |
| Long passif0,5x | +292,53 $ | 3,85 % | +291,54 $ | 16,98 % |
| Long passif1,5x | −30,74 $ | −0,46 % | −32,97 $ | 36,77 % |

Le contrôle0,5x passe le filtre exploratoire dans les quatre scénarios
payants, aussi avec l'infrastructure hypothétique20 $/30jours. Le contrôle
1,5x s'arrête : drawdown central observé31,99 %, dépassement conservé.
Cela ne valide aucun rendement futur, et les expositions comparées diffèrent.

Le passif0,5x dépend beaucoup de la fin de période : +195,72 $ en août et
+92,23 $ pendant les premiers jours de septembre, contre +4,58 $ cumulés
à fin juillet. Il perd96,12 $ en juin. Son plus gros contributeur est ZEC,
+73,98 $, puis LIT+56,19 $. Aucun gagnant ou perdant retiré après calcul.
Le candidat actif n'est donc pas interchangeable avec le contrôle passif ;
son utilité doit encore être prouvée sous les coûts et sur d'autres périodes.

Bootstrap descriptif du passif,14jours/10 000 tirages : intervalle mensuel
95 % central[−2,63 % ;10,08 %], coûts[−2,64 % ;10,09 %]. Un seul jour
d'entrée pour les positions passives. Ces intervalles ne sont ni prédictifs
ni corrigés pour la sélection du panel et de la période.

## Sous-panel15 admissible pour une année2025 entière

LIT/PUMP/XPL exclus de cette comparaison selon dates de contrat Binance,
avant PnL, afin de préparer un transfert sur des actifs présents toute2025.
Ce sous-panel est d'abord rejoué sur les mêmes204 jours Hyperliquid.

| Règle | Central net | Mensuel équivalent | Stress coûts net | Enveloppe centrale |
|---|---:|---:|---:|---:|
| Candidat50/50,1,5x | +358,82 $ | 4,61 % | +113,42 $ | 29,03 % |
| Long passif0,5x | +258,98 $ | 3,44 % | +257,68 $ | 17,52 % |
| Long passif1,5x | +23,84 $ | 0,35 % | +21,54 $ | 37,46 % |

Le candidat du sous-panel reste positif, mais son enveloppe dépasse30 %
en stress coûts32,18 % et retard34,49 %. Le changement d'univers affecte
donc déjà son filtre de risque. Cela ne suffit pas à isoler l'effet d'une
nouvelle période : le futur résultat Binance2025 doit être comparé à cette
référence15, pas seulement à la référence18 plus favorable.

## Preuves

Soixante simulations de comparaison,65 artefacts reproduits à l'identique.
Les vingt anciens scénarios complets restent économiquement identiques après
ajout du paramètre de cap natif. Les règles actives n'ont pas changé.
Artefacts : `original_summary.json`, `matched_summary.json`,
`native_reproduction.json`, données dans `data/prior_transfer_2026-09-07/`.
Le premier run original pré-lint est conservé comme provenance ; les références
publiées sont `original_final` et `matched_run1`, chacun avec reproduction.
Le transfert2025 fait l'objet du rapport principal une fois les données
entièrement qualifiées. Aucun GO, achat ou ordre réel.

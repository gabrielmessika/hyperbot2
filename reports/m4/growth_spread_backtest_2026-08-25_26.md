# M4 — campagne Growth BTC des 25–26 août 2026

Date : 27 août 2026  
Statut : campagne train terminée ; edge non démontré, aucune promotion

## Périmètre et provenance

L'export `fetch-20260827T155143Z-74396a1c` contient uniquement des segments
fermés des 25 et 26 août. Ses 178 fichiers ont été vérifiés contre le manifeste
et les SHA-256 avant construction. Les deux rapports M3 classent les journées
en niveau A, sans motif de disqualification :

- 25 août : couverture opérationnelle 99,994 % ;
- 26 août : couverture opérationnelle 99,995 %.

Les datasets BTC complets sont :

| Date | SHA-256 dataset | Books | BBO | Trades |
|---|---|---:|---:|---:|
| 25 août | `8d2fcadf...fc553` | 16 087 | 746 267 | 526 718 |
| 26 août | `e929ead4...fcf97f` | 16 088 | 650 872 | 351 200 |

Les sidecars Strategy/Risk couvrent respectivement
00:02:02–23:58:11 UTC et 00:03:15–23:59:24 UTC. Chacun contient 284 cycles. Les
inputs externes portent les SHA-256 `818a188c...615ed1` et
`e9c14918...31260`.

## Expérience préenregistrée

La configuration `config/hyperbot_backtest_growth_spread_v1.json`, SHA-256
interne `0f708f21...6c80c2`, compare trois variantes. Seule la demi-largeur
minimale change : 3, 4 ou 6 bps. Les autres paramètres Strategy, Risk et
Execution restent identiques. La matrice comprend :

- modèles de file central et pessimiste ;
- scénarios base, latence x2 et frais x2 ;
- portefeuille et hard stop portés du 25 au 26 août ;
- 18 agrégats et 36 rapports journaliers.

Le rapport agrégé est
`data/replay_reports/experiments/growth-btc-spread-v1/growth-btc-spread-v1-283313c60344.json`.
Son SHA-256 externe est `2c1dd849...19625` et son hash d'expérience interne est
`283313c6...ed9bb`. Les 37 JSON de la campagne ont un checksum valide. Les trois
variantes ont été ajoutées au journal hash-chaîné
`data/research/strategy_variants.jsonl`, validé à trois records.

## Qualité causale des cycles

Chaque agrégat voit 568 décisions, mais seulement 56 sont tradables et 512
restent fail-closed. Le taux exploitable est donc 9,86 %. La cause est uniquement
l'âge du dernier L2 face à la limite de 500 ms :

| Date | Cycles tradables | Âge médian | p90 | Maximum |
|---|---:|---:|---:|---:|
| 25 août | 27 / 284 | 2 694 ms | 4 756 ms | 5 468 ms |
| 26 août | 29 / 284 | 2 634 ms | 4 586 ms | 5 344 ms |

Aucun cycle dont le book a au plus 500 ms n'est rejeté pour une autre raison
health ou définition. Le mécanisme stale fonctionne donc comme prévu, mais la
cadence L2 actuelle limite fortement la puissance de l'expérience.

## Résultats

Les trois variantes produisent 112 quotes sur les 56 cycles tradables. Aucun
ordre n'est rejeté par le superviseur, aucun hard stop n'est déclenché et aucun
markout 30 s ne manque.

| Scénario | Variante | Central : fills / PnL 30 s | Pessimiste : fills / PnL 30 s |
|---|---|---:|---:|
| Base | 3, 4 et 6 bps | 1 / -0,000231 USD | 0 / 0 USD |
| Frais x2 | 3, 4 et 6 bps | 1 / -0,001698 USD | 0 / 0 USD |
| Latence x2 | 3 bps | 2 / -0,005410 USD | 2 / -0,003980 USD |
| Latence x2 | 4 bps | 2 / -0,005410 USD | 2 / -0,003980 USD |
| Latence x2 | 6 bps | 3 / -0,002440 USD | 3 / -0,001010 USD |

Le PnL marqué terminal est positif dans les runs avec fills, mais provient de
positions BTC encore ouvertes au dernier mark. Il ne constitue ni un round
trip ni une preuve d'edge. Tous les scénarios ayant effectivement rempli une
quote ont un PnL économique 30 s négatif après frais. Le modèle pessimiste de
base ne confirme aucun fill.

La latence x2 retarde aussi les annulations et augmente ici le temps exposé :
elle produit davantage de fills, mais leurs markouts restent négatifs. Ce stress
ne doit donc pas être lu comme une amélioration de performance.

## Décision

Aucune des trois largeurs n'est promue. Les variantes sont indiscernables en
base sur cet échantillon et le signal économique disponible est défavorable.
La campagne reste intégralement dans la partition train ; calibration, test,
trois folds OOS, 500 round trips et shadow 14 jours ne sont pas acquis.

La prochaine série doit continuer à accumuler des journées A et conserver le
seuil causal de 500 ms. Une évolution séparée de la cadence L2 peut être étudiée
pour augmenter le nombre de cycles exploitables, après estimation explicite de
la charge réseau, du stockage et du risque opérationnel sur la collecte.

Cette campagne n'a ni redémarré ni reconfiguré le collector. Tous les calculs
ont été réalisés sur la copie locale vérifiée.

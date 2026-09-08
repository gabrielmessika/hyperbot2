# Frais actions HIP-3 : amélioration, sans edge qualifié

**`HYPOTHESIS_NOT_CONFIRMED`** pour les stratégies étudiées. Le tarif réduit
améliore les résultats, mais les intervalles statistiques et l'économie à
capital total plafonné ne permettent toujours pas une promotion.

L'utilisateur accepte désormais aussi une cible de **+15 % ou +20 % nets par
mois**, soit 150–200 $ sur 1 000 $. Ce n'est pas une garantie et cette cible
reste très au-dessus des résultats économiques calculés ici.

## Tarif vérifié et portée historique

Le snapshot natif existant indique growth mode et deployer scale 1 pour TSLA,
NVDA, HOOD, COIN, META et AMZN : tarif de base calculé **0,9 bp par côté**.
MSTR conserve le tarif standard **9 bps**. Aucun discount staking, referral,
volume ou builder n'est supposé. Le stress double ces frais et conserve le
slippage renforcé de l'expérience originale.

La [documentation trade.xyz](https://docs.trade.xyz/trading/fees) confirme ces
barèmes et l'exclusion de MSTR du growth mode. L'
[annonce officielle du 24 novembre 2025](https://t.me/hyperliquid_announcements/481)
confirme l'activation de ce mode par trade.xyz, avant la période de test.
Son HTML et son horodatage sont archivés dans
`data/hip3_fee_review_2026-09-07/announcement-page.json`.

Cette preuve ne fournit pas une timeline complète par marché : le résultat
reste une **sensibilité au barème observé**, avec activation ancienne corroborée,
pas une reconstitution exhaustive des frais historiques du compte. Les anciens
résultats au tarif standard sont conservés.

## Résultats sans changer les signaux

Le [protocole](PROTOCOL.md) fixe une modification des frais uniquement. Tous les
signaux, prix, directions, horaires, slippages et fundings sont inchangés.

| Stratégie / segment | Événements | Net base, bps | Stress, bps | Retard, bps |
|---|---:|---:|---:|---:|
| Week-end fade, univers initial | 19 | +134,67 | +126,87 | +151,93 |
| Week-end fade, réplication COIN/MSTR | 25 | +73,23 | +56,25 | +2,51 |
| Nocturne follow, ancien | 174 | +21,28 | +10,07 | +25,50 |
| Nocturne follow, validation | 170 | +21,84 | +10,53 | +25,78 |

Les contrôles week-end follow et nocturne fade restent négatifs.

Le follow nocturne passe désormais les filtres de coût, PF et stabilité des
blocs, mais ses IC 97,5 % restent **[−25,64 ; +63,62] bps** dans l'ancien et
**[−89,46 ; +85,47] bps** dans la validation. Ils ne permettent pas de distinguer
un avantage positif du bruit. Les faibles effectifs indépendants week-end ne
permettent toujours pas d'IC conforme aux gates initiales.

## Économie avec 1 000 $ de notional total

Une moyenne par événement n'est pas un rendement du capital. Lorsque plusieurs
actifs déclenchent ensemble, répartir 1 000 $ entre eux donne une pondération
différente de celle d'un notional de 1 000 $ **par** événement.

| Stratégie / segment | PnL proxy sur la période | Jours | Proxy /30 j après 20 $ infra |
|---|---:|---:|---:|
| Week-end fade, initial | +139,04 $ | 206 | +0,25 $ |
| Week-end fade, réplication | +68,03 $ | 206 | −10,09 $ |
| Nocturne follow, ancien | +60,18 $ | 109 | −3,44 $ |
| Nocturne follow, validation | +11,88 $ | 97 | −16,33 $ |

Chaque ligne est une simulation séparée, pas une allocation cumulable.
Capital constant, sans réinvestissement. Ce proxy ne modélise ni liquidation,
ni profondeur, ni taille minimale : il ne remplace pas un backtest de
portefeuille. Même avant les 20 $ hypothétiques d'infrastructure, les revenus
restent très éloignés de 150–200 $ mensuels. Aucun coût réel nouveau n'est engagé.

La réduction des frais ne suffit donc pas à retenir ces règles. Aucun actif,
créneau ou horizon n'est sélectionné après coup pour contourner ce résultat.

## Preuves et suite

**5 256 comparaisons** du calcul ajusté avec `leg_return` sur les bougies brutes
passent à une tolérance de 1e-18 bps ; les identités des événements restent
strictement identiques. Les six fichiers d'événements et le résumé sont
reproduits exactement par SHA-256. Voir [résultats](summary.json) et
[preuves](reproduction.json).

**224 tests passent**, lint/format sur 180 fichiers et mypy sur 56 sources.
Nouveaux tests : barème HIP-3, états inconnus refusés, exception sans growth
mode, prix entrée/sortie et funding inchangés par la révision des frais.

```bash
rtk proxy uv run python scripts/investigate_hip3_fees.py --output data/hip3_fee_new_run
```

La reproduction est offline et réutilise les données existantes. Aucun service
ni trading modifié. La recherche reste active : un inventaire complémentaire
a retrouvé des observations proches de l'expiration sur 110 contrats outcomes
dans les anciens logs. Prochaine étape : qualifier leurs références de prix et
leur profondeur, puis tester une borne économique avant de développer une
nouvelle stratégie de fin d'échéance. Les modèles legacy ne sont pas des preuves.

# Comparaison Hyperliquid / Binance USDC : aucun déclenchement économique

21 requêtes publiques ont fourni gratuitement 12 960 bougies horaires et
1 620 paiements de funding Binance : BTC/ETH/SOL du 10 mars au 6 septembre
2026 UTC exclusif. Confrontation avec les archives natives HL déjà disponibles.
Contrats USDC, sans conversion implicite USDT/USDC. Aucun compte consulté.

| Coin | Écart à la médiane 7 j, 99e percentile absolu | Maximum absolu |
|---|---:|---:|
| BTC | 7,59 bps | 11,27 bps |
| ETH | 8,31 bps | 13,32 bps |
| SOL | 9,01 bps | 14,53 bps |

Les deux règles préenregistrées ne déclenchent **aucun événement** : écart de
prix >=30 bps ; différentiel de funding passé >=10 bps/jour avec écart <20 bps.
Un écart de prix de 30 bps ne représente qu'environ 15 bps sur le notionnel
total des deux jambes en cas de convergence complète. Les hypothèses de frais
et slippage de base coûtent environ 13,5 bps sur ce même notionnel à prix stables.
Réduire le seuil pour générer artificiellement des trades n'est pas justifié.

Les seuils n'ont pas été modifiés. Cela écarte cette approche horaire sur ces
trois marchés ; cela ne prouve pas l'absence d'occasions intrahoraires ou sur
d'autres actifs. **HYPOTHESIS_NOT_CONFIRMED**, pas de rendement estimable.

Le validateur a arrêté la première analyse à cause d'offsets de funding de
0–26 ms. Les 540 échéances par coin sont complètes après contrôle de grille ;
les timestamps exacts sont conservés pour les paiements Binance. Voir ADAPTER.md.
HL conserve son proxy horaire. Les tests couvrent quantités opposées, quatre
exécutions, frais propres à chaque plateforme, signe et limites de funding.

Reproduction : `rtk proxy uv run python scripts/investigate_cross_venue.py
--output <nouveau_dossier>`. Archive checksumée sous
`data/cross_venue_2026-09-07/binance/`, résumé dans ce dossier, événements sous
`data/cross_venue_2026-09-07/run2/`. Opens/closes non synchronisés au niveau des
quotes ; pas de simulation de marge, transfert, risque de plateforme ou ADL.
Cette étude n'autorise pas un bot live. Les nouvelles OHLCV incluent aussi les
volumes d'achats agressifs, réutilisables pour une hypothèse d'ordre flow.

Sources tarifaires : [HL](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees),
[Binance](https://www.binance.com/en-BH/fee/futureFee). Frais Binance de 5 bps par
côté retenus sans remise ; tarif historique du compte non qualifié.

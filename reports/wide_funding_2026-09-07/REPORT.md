# Portage élargi : revenu apparent, puis échec du hedge statique

20 perpétuels core sélectionnés par volume 24 h courant, hors les quatre majors
déjà testés. 39 requêtes publiques de funding, 1,23 Mo, aucune dépense.
19 actifs ont 720 heures complètes ; PONS n'en a que 140, sans imputation.
Le biais d'univers actuel interdit de traiter ce filtre comme un backtest validé.

| Meilleurs revenus proxy sur 30 j | 500 $ de short à notionnel constant |
|---|---:|
| CASHCAT | 35,29 $ |
| XMR | 24,28 $ |
| FARTCOIN | 10,46 $ |
| PUMP | 7,43 $ |
| ZEC | 7,42 $ |

Seul CASHCAT passe le filtre économique préenregistré : funding cumulé 7,06 %,
quatre semaines positives, 99,58 % des heures positives, résultat positif
sans les cinq meilleurs paiements. Ces montants ignorent prix, couverture,
marge et coûts ; ils ne sont pas des rendements de portefeuille.

## Vérification du hedge effectivement effectuée

Spot CASHCAT/USDT confirmé par l'API publique KuCoin, réseau Robinhood et contrat
`0x020bfc650a365f8bb26819deaabf3e21291018b4`. Pas de CASHCAT spot dans le snapshot
HL disponible ; Binance annonce ne pas le proposer en spot. Historiques OHLCV
KuCoin, perp HL, funding ancien et cours USDC/USDT Binance acquis gratuitement.
Les limites de couverture aux sorties ont nécessité un complément de 27 heures,
dans le budget initial : huit GET externes et six /info natifs au total.

Les quantités identiques long spot/short perp sont arrondies au coin entier
(lot HL), avec capital 1 000 $ partagé en 500 $ spot et 500 $ marge HL.
Frais spot conservateurs 30 bps/côté (catégorie API 3), HL 4,5 ; slippage 5/2 ;
conversion USDC/USDT historique avec coût supposé 10 bps par conversion.
Le symbole spot est actif, incrément 0,01 ; minimum spot 0,1 USDT. Les frais de
compte et l'identité du sous-jacent côté perp restent non qualifiés.

**Le hedge statique échoue au stress de marge dans les deux segments.**

| Segment | Quantité base | Première violation du buffer de maintenance 20 % | Equity short au prix adverse | Buffer manquant |
|---|---:|---|---:|---:|
| 16 juillet–7 août | 4 850 | 5 août, 22:00 UTC | 102,86 $ | 80,01 $ |
| 7 août–6 septembre | 4 873 | 24 août, 14:00 UTC | 130,27 $ | 48,92 $ |

Les scénarios coûts doublés, funding positif divisé par deux, retard 24 h et
même contrôle sans frais violent aussi ce buffer. Il s'agit d'un stress prudent
de 20 % sur les highs horaires, pas d'une reconstitution de liquidation native.
Le maxLeverage actuel vaut 3 ; sa table détaillée n'est pas incluse dans le
snapshot. Le profit du spot sur une autre plateforme ne peut pas être supposé
immédiatement transférable en collatéral. Aucun gain à la sortie prévue n'est
crédité après une violation, même si la somme économique des deux jambes
aurait semblé favorable. **HEDGE_ECONOMICS_NOT_CONFIRMED**.

Cela rejette la version statique 500/500 testée. Ce n'est pas une preuve que
tout portage CASHCAT est impossible : une allocation plus faible ou des transferts
changeraient la stratégie et nécessiteraient d'autres preuves, tout en réduisant
un revenu déjà modeste. Aucun seuil ni levier n'a été retouché pour obtenir un GO.

Reproduction offline : `scripts/investigate_wide_funding.py --raw
data/wide_funding_2026-09-07/history --output <nouveau_dossier>` puis
`scripts/investigate_cashcat_hedge.py --output <autre_dossier>`, via `rtk proxy uv run
python`. Raw append-only, grilles/checksums/overlaps et conversions contrôlés.
Les tests vérifient signe du funding, couverture, neutralité à quantité fixe,
conversion de devise et absence de sauvetage fictif de la marge par le spot.

Sources : [annonce spot KuCoin](https://www.kucoin.com/ja/announcement/jp-cash-cat-cashcat-listed-on-kucoin),
[profil/contrat](https://www.kucoin.com/price/CASHCAT),
[API de marché](https://www.kucoin.com/docs-new/rest/ua/get-klines),
[absence de spot Binance](https://www.binance.com/en-IN/how-to-buy/cash-cat).

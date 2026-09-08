# Flux agressif et carnet : deux règles rejetées après réplication

**`HYPOTHESIS_NOT_CONFIRMED`**. Ni la continuation d'une pression soutenue par
le carnet ni son absorption ne produisent un avantage net dans ce test. Aucun
achat de données, aucun ordre, aucun changement de service ou de serveur.

Les règles, dates, coûts et critères figurent dans le [protocole](PROTOCOL.md).
La [précision d'adaptateur](ADAPTER.md), enregistrée avant les résultats,
utilise l'identifiant natif coin/time/tid pour dédupliquer les transactions.
Les paramètres n'ont pas changé entre le pilote et la réplication.

## Résultats à cinq minutes

| Règle | Segment | Signaux | Évaluables | Mid brut, bps | Net, bps | Stress, bps |
|---|---|---:|---:|---:|---:|---:|
| Continuation | 16–17 août | 171 | 120 | +1,47 | **−10,11** | −19,11 |
| Continuation | 25–27 août | 394 | 294 | +0,33 | **−10,85** | −19,85 |
| Absorption | 16–17 août | 226 | 167 | −0,11 | **−11,61** | −20,61 |
| Absorption | 25–27 août | 389 | 272 | +1,40 | **−10,06** | −19,06 |

Le markout brut utilise les événements avec deux quotes fraîches ; les résultats
nets exigent aussi une profondeur suffisante. Leurs dénominateurs diffèrent.
Un petit markout mid positif n'est donc ni un fill ni une marge après spread.

Les pertes sont présentes sur **chaque jour et chaque actif**, pour les deux
règles. Le retard de deux secondes reste négatif : −10,59/−10,57 bps pour la
continuation pilote/réplication, −11,49/−9,75 pour l'absorption. L'horizon
descriptif de 30 minutes reste également négatif ; il ne remplace pas l'horizon
principal après constat d'échec.

À environ 50 $ de notional par fill simulé, PnL des événements évaluables :
continuation −6,04 $ pilote puis −15,85 $ réplication ; absorption −9,65 $
puis −13,60 $. **Ce ne sont pas des résultats complets de portefeuille** :
des sorties ou profondeurs manquent. La couverture évaluée n'est que de
69,9–74,6 % des signaux, loin du seuil de qualification enregistré de 99 %.
Les événements incomplets ne sont jamais imputés comme gagnants.

Chaque segment ne comporte que deux ou trois journées ; aucun IC bootstrap
n'est annoncé sur un nombre aussi faible de blocs indépendants. Il serait
incorrect de considérer les centaines de transactions comme autant de jours.
Les critères de profit, de stress et de couverture échouent déjà nettement.
Ces deux règles sont suspendues, sans prolonger la collecte ni abaisser les coûts.

## Données existantes et exécution simulée

336 segments fermés, 44 198 986 lignes parcourues, **11 731 394 événements
BBO/trades BTC/ETH/HYPE** retenus. L'extrait fournit 1 198 609 secondes-actifs
valides. Les autres instruments ne sont pas inclus dans la recherche.

Les fichiers source sont dédupliqués et vérifiés par SHA-256 avant/après lecture.
Le format Hyperbot et son adaptateur de replay servent de référence ; aucun
import runtime vers un ancien dépôt. Les heures événement/réception sont
conservées. Un événement reçu à une seconde exacte ne peut pas entrer dans
la décision de cette seconde ; ce cas et la déduplication sont testés.

Le modèle utilise un BBO reçu frais à l'heure de décision +1 s, puis +301 s,
avec variante +2 s. Il s'agit d'une approximation par quotes observables,
pas d'une preuve du carnet réellement présent lors d'un ordre. Les refus
pour quotes absentes et profondeur sont conservés. Aucun résultat maker
ni validation d'absence de pertes silencieuses du flux n'en est déduit.

Base : frais 4,5 bps et supplément slippage 1 bp **par côté**, spread payé,
funding signé. Stress : 7 et 3 bps par côté. Le funding utilise les taux natifs
existants et une ouverture horaire perp comme proxy du prix oracle, limitation
explicite. Aucun taux préférentiel, levier ou remise fictive.

Sources primaires : [schémas WebSocket natifs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions),
[frais perps](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees),
[mécanique funding](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding).

## Vérification et réutilisation

**221 tests passent**, lint/format (174 fichiers) et mypy (55 sources) passent.
Les nouveaux tests couvrent les règles, coût aller-retour, funding à la frontière,
profondeur, réception causale et identité des transactions. Une réextraction
du 16 août reproduit exactement le CSV gzip ; les deux évaluations complètes
sont reproduites exactement. Voir [preuves](reproduction.json),
[pilote](pilot_summary.json) et [réplication](replication_summary.json).

Raw et extraits ignorés Git dans `data/microstructure_2026-09-07/`, avec manifestes
checksumés. Réutilisation sans réseau :

```bash
rtk proxy uv run python scripts/investigate_microstructure.py --input data/microstructure_2026-09-07/pilot_verified --output data/microstructure_new_pilot
rtk proxy uv run python scripts/investigate_microstructure.py --input data/microstructure_2026-09-07/replication --output data/microstructure_new_replication
```

La recherche reste active. Le prochain travail porte sur un point de coût
repéré dans les expériences actions HIP-3 : six marchés du précédent univers
affichent `growthMode=enabled`, tandis que les scénarios utilisaient le tarif
standard. Vérifier l'effet du tarif applicable sans changer les signaux, garder
MSTR au tarif standard, distinguer frais actuels et historique non attesté.

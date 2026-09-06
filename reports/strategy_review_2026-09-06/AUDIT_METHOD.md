# Méthode de l’audit stratégique du 6 septembre 2026

Cet audit descriptif accompagne
[le plan d’implémentation](../../STRATEGY_IMPLEMENTATION_PLAN.md).
Il ne contient aucun nouveau backtest de stratégie, fill simulé ou ordre réel.

## Fichiers de preuve

- `evidence.json` : recalcul du CSV paper, lecture du fichier principal de
  snapshots HIP-4, premier filtrage du catalogue public et contexte des perps.
- `recurring_outcomes.json` : contrôle complémentaire des quatre outcomes
  quotidiens `Recurring/priceBinary`, huit snapshots L2 publics.
- `fast_l2_probe.json` : deux connexions WebSocket BTC simultanées pendant
  40 secondes, avec `fast=false` et `fast=true`.
- Chaque JSON dispose d’un sidecar SHA-256. Ces fichiers sont des snapshots
  immuables ; une nouvelle mesure doit utiliser un autre répertoire.
- `audit_evidence.py.txt` et `probe_l2_fast.py.txt` conservent le texte exact
  des deux scripts exploratoires, avec leur hash dans les JSON correspondants.
  Ils ne font pas partie du package ou des commandes de production.

Les réponses publiques intégrales du premier script sont conservées localement
sous `tmp/strategy_review_public_2026-09-06/`, avec chemins et SHA-256 dans le
manifest de requêtes. Les fichiers sources TRIDENT restent à leur emplacement,
sans copie massive. Les deux JSON de carnets contiennent aussi leurs niveaux.

## Recalcul legacy

Le CSV est lu intégralement. Le champ utilisé est `net_pnl_usdc`, repris sans
réécrire les anciens frais. PF = somme des PnL positifs / valeur absolue de
la somme des PnL négatifs. Calculs descriptifs en flottants, valeurs non arrondies
conservées au JSON ; ce n’est pas un nouveau ledger financier en production.
Les types `EARLY_EXIT`, `YES`, `NO` sont comptés séparément.

Le book est lu ligne par ligne en calculant le SHA-256 des octets bruts. Pour
chaque couple marché/côté, le script écarte un timestamp exchange identique au
dernier retenu, puis un timestamp antérieur ; il exige ensuite
`0 < best_bid < best_ask < 1`. Les champs vides sont invalides. Le filtre
est volontairement strict et exclut aussi les états aux bornes 0/1 ; il ne
permet pas d’affirmer que tous les rejets sont des carnets croisés.

Le spread est `ask − bid`, groupé par préfixe de sous-jacent dans `market_id`.
Les quantiles utilisent l’indice `int(q * (n − 1))` dans la liste triée.
Les observations ont un poids égal ; ce n’est pas une moyenne temporelle et
le script ne prétend pas détecter toutes les duplications non consécutives.

Une paire de complémentarité est comptée lorsqu’un YES et un NO du même
marché ont exactement le même `ts_event`, une seule fois par timestamp retenu.
Le test demande `ask_yes + ask_no < 1 − 1e-9` ou
`bid_yes + bid_no > 1 + 1e-9`. Il ne déduit aucun fill et ne suppose pas une
réception simultanée. Ni frais ni taille exécutable ne sont requis pour ce
simple test de croisement brut, qui ne trouve aucun cas positif.

Le `source_latency_ms` décrit le champ du fichier, pas la fraîcheur entre
snapshots ni la latence d’une transaction d’ordre. Aucun markout nouveau,
PnL maker ou rendement mensuel n’est calculé à partir des snapshots.

## Catalogue public : deux schémas à distinguer

Le champ `binary_crypto_outcomes` du premier `evidence.json` est limité au
filtre exact `name == template:binaryPrice` et à un préfixe `perp:BTC|`,
`perp:ETH|`, `perp:SOL|` ou `perp:HYPE|`. Ses six résultats BTC ne représentent
**pas l’intégralité des outcomes crypto**.

Le contrôle complémentaire lit la même réponse `outcome_meta.json`, sélectionne
`name == Recurring` et `description.startswith("class:priceBinary|")`, puis
interroge les deux côtés des quatre marchés trouvés. Les requêtes exactes,
timestamps, définitions et réponses sont conservés dans
`recurring_outcomes.json`. Encodage utilisé :
`coin = "#" + str(10 * outcome_id + side)`, avec side 0/1.

Ce contrôle corrige le premier inventaire partiel. Le plan final utilise bien
BTC, ETH, SOL et HYPE quotidiens ; les nouveaux templates restent exclus v0.
Les snapshots ont été obtenus séquentiellement et ne mesurent aucune cadence,
durée d’opportunité, quantité remplie ou qualité historique du marché.

## Sonde rapide

Endpoint public : `wss://api.hyperliquid.xyz/ws`.
Requête sur chaque connexion :

```json
{"method":"subscribe","subscription":{"type":"l2Book","coin":"BTC","fast":true}}
```

Le témoin utilise la même requête avec `fast=false`. Les ACK, timestamps
exchange/réception et nombres de niveaux sont enregistrés. L’âge apparent est
`received_ms − exchange_ms`, sans calibration indépendante d’horloge.
Les intervalles et quantiles sont descriptifs sur un petit échantillon.
Le script n’enregistre pas les niveaux complets de cette sonde : il ne peut
pas servir à rejouer la file ou à qualifier une stratégie.

## Documentation consultée

Pages officielles vérifiées via leur contenu HTML, récupéré avec `curl`
et extraction du texte principal après échec du lecteur web sur le MIME Markdown :

- [Historique et S3](https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data)
- [Frais](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees)
- [HIP-4](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-4-outcome-markets)
- [API info](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint)
- [Identifiants d’assets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids)
- [Subscriptions WebSocket](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions)
- [Limites API](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits)
- [Funding](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding)

L’incohérence entre la mention initiale de frais nuls dans HIP-4 et les règles
de frais courantes est conservée comme un point à résoudre, pas arbitrée en
faveur du scénario le plus rentable. Aucun endpoint privé `userFees` n’a été
interrogé pour un compte de l’utilisateur.

## Reproduction et portée

Relire les sources aux chemins et hashes fournis, ou les copies brutes locales
indiquées, reproduit l’audit de ces octets. Relancer les appels réseau donnera
de nouvelles observations : ce n’est pas une reproduction du marché historique.
Les scripts figent des chemins locaux et refusent d’écraser certains outputs ;
pour une nouvelle exécution, copier le script et choisir de nouveaux chemins
de sortie, conserver son nouveau hash et ne jamais écraser ce dossier.

Tous les reads TRIDENT/BOT05 sont restés en lecture seule. Aucun contrôle
serveur nouveau n’a été réalisé ; les chiffres de production cités proviennent
des audits déjà publiés, avec leurs limites. Les données brutes ne sont pas
reclassées A et les preuves présentes ne permettent aucune promotion.

# Recherche de profondeur historique — 7 septembre 2026

**L'accès gratuit autonome à 90–180 jours de liquidations n'est pas établi.**
La recherche des sources est terminée pour cette passe. Deux voies concrètes
restent : export 0xArchive ciblé ou accès Build à l'API déjà intégrée. Aucun
achat, abonnement, message à un fournisseur ou ordre de trading n'a été effectué.
Le résultat économique demeure `INSUFFICIENT_SAMPLE`, sans nouveau backtest.

## Sources examinées

| Source | Vérification | Conclusion pour le test 180 jours |
|---|---|---|
| HyperBot, TRIDENT, BOT05 locaux | Inventaire des dossiers de données, y compris ignorés par Git ; recherche des champs dans le code des anciens collectors | Aucun dataset de liquidations identifié. Prix/funding existants réutilisables. Inventaire de noms et schémas, pas preuve d'absence de chaque événement dans tous les fichiers. |
| Serveur existant | Lecture seule des chemins `/opt/hyperbot/shared/data`, `/opt/trident/data`, `/opt/bot05`, `/opt/hyperbot2/shared/data` | Aucun fichier de liquidations identifié ; `/opt/bot05` absent à cet emplacement. Aucun service touché. |
| Archive native S3 Hyperliquid | Documentation officielle et tentative anonyme de liste bornée : HTTP 403 | Fills disponibles via `node_fills_by_block`, mais transfert facturé au demandeur, authentification AWS nécessaire. Pas de téléchargement massif lancé. |
| Dépôt officiel `hyperliquid-dex/historical_data` | API GitHub, CSV de 5 632 octets, 62 lignes | Du 28 février au 1er mai **2023** ; agrégats de comptes, sans coin/sens/exécution. Incompatible avec l'étude BTC/ETH de 2026. |
| HypeDexer | Portail public, code client de l'export, documentation et requête `/fills/` ancienne, limitée à une ligne | API : HTTP 401 « missing api key ». Portail : jeton CAPTCHA Turnstile demandé avant l'export. Pas de contournement ; aucun export créé. |
| ByKaranteli | Documentation des liquidations brutes et des exports mensuels | Liste de places sans Hyperliquid ; archive annoncée depuis le 30 juillet 2026. Ne fournit pas la source requise. |
| PurrData | Page officielle et état d'accès | Liste d'attente ; exemples et offres annoncées, API indiquée disponible après lancement. Pas un accès opérationnel confirmé. |
| 0xArchive | Refus gratuit déjà capturé, pages de prix, schémas et catalogues BTC/ETH | Couverture liquidations annoncée depuis décembre 2025 dans les deux catalogues ; période mars–septembre 2026 compatible avec l'annonce. Couverture effective à contrôler après acquisition. |

Sources primaires : [archive native Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data),
[CSV officiel](https://github.com/hyperliquid-dex/historical_data),
[portail HypeDexer](https://trade-export.hypedexer.com/),
[documentation HypeDexer](https://docs.hypedexer.com/guides/historical-trade-archive),
[ByKaranteli](https://bykaranteli.com/developers), [PurrData](https://www.purrdata.io/).
Les annonces commerciales ne sont pas assimilées à des données livrées.

## Vérification native supplémentaire : 3/3 lignes confirmées

Avant les appels, sélection déterministe de la première, de la médiane et de
la dernière des 2 565 lignes de l'épisode BTC du 28 août. Trois requêtes
publiques `userFillsByTime`, chacune sur une fenêtre de deux millisecondes.
Hyperliquid renvoie les trois identifiants attendus, avec la propriété native
`liquidation`, méthode `market`, et le bon compte liquidé.

Les prix, tailles, mark prices, PnL clos, horodatages, transactions, sens et
directions correspondent. Comparaison numérique `Decimal`, indispensable :
`78275` et `78275.0` représentent le même prix. Le premier relevé exploratoire
contenait une égalité de chaînes fausse ; [l'audit final](native_audit.json)
la remplace explicitement, sans modification des snapshots.

Cette preuve renforce la confiance dans **ces trois liquidations réellement
forcées**. Elle ne valide pas les 2 565 lignes individuellement, la couverture
de six mois, ni le champ fournisseur `liquidator_user`. Le nom de ce dernier
ne doit pas servir à attribuer une contrepartie ; le compte liquidé, lui, est
confirmé sur l'échantillon. Aucun changement de signal ou de résultat économique.

## Acquisition prête à examiner

Le [paquet d'acquisition](acquisition_packet.json) fixe BTC et ETH **core perps**,
du **10 mars 2026 00:00 au 6 septembre 2026 00:00 UTC exclusif**. Liquidations
brutes et OI uniquement ; prix/funding déjà archivés. Aucun L2/L4 supplémentaire
n'est nécessaire pour cette étude exploratoire.

**Option A — export ponctuel.** Deux marchés × deux schémas : `liquidations`
et `oi`, Parquet/ZSTD. Minimum publié par marché : 12,50 $ liquidations et
2,50 $ OI, soit **30 $ de minimum théorique total**, pas un devis ni un plafond.
La taille réelle peut augmenter le montant. Catalogues prêts à configurer :
[BTC](https://0xarchive.io/data/hyperliquid/perpetuals/btc) et
[ETH](https://0xarchive.io/data/hyperliquid/perpetuals/eth).
Les commandes d'export ne font pas partie de l'API REST publique ; aucun
checkout n'est créé avec la clé de marché. [Contrat des exports](https://docs.0xarchive.io/export-schemas),
[parcours de commande](https://docs.0xarchive.io/export-checkout).

**Option B — accès API Build.** Prix mensuel affiché : **49 $**, avec accès
annoncé à l'historique complet. C'est la voie la plus directe pour le client
déjà testé : 24 requêtes de séries horaires (deux actifs × six blocs de
30 jours × liquidation/OI), puis vérification brute des heures retenues.
Les paramètres de ces 24 requêtes figurent dans le paquet. L'offre annuelle
à 39 $/mois exige 468 $ d'engagement annuel et n'est pas la proposition.
La carte mensuelle est renouvelable jusqu'à résiliation ; une option 30 jours
USDC sans renouvellement est annoncée lorsqu'elle est proposée.
[Tarifs et conditions publiés](https://0xarchive.io/pricing).

**Alternative gratuite non qualifiée — HypeDexer.** Une intervention dans le
navigateur est nécessaire pour le CAPTCHA. Avant un export de six mois,
demander seulement BTC, tous comptes, du 28 au 29 août UTC, CSV : comparer le
schéma, le champ identifiant une liquidation et la couverture avec notre épisode
connu. Le portail exporte des fills ; la présence de métadonnées suffisantes
pour distinguer liquidation/contrepartie dans le CSV n'est pas prouvée. La
documentation de l'archive gratuite décrit surtout 2024–janvier 2025, alors
que l'interface accepte des dates récentes : disponibilité effective à vérifier.
Ne pas lancer un export massif sur la seule base du formulaire.

## Reprise après accès

1. Préserver le pilote et enregistrer la nouvelle campagne avant de consulter
   les rendements des événements supplémentaires ; le mois déjà étudié reste
   identifié comme déjà vu.
2. Contrôler identité des marchés, bornes UTC, partitions manquantes, doublons,
   types et direction. Vérifier la correspondance avec les données récentes
   et un échantillon natif ; interrompre si un export omet les identifiants
   nécessaires à la vérification. Ne pas interpréter une heure absente comme zéro.
3. Reprendre les critères fixes de l'étude principale avec 30 jours de chauffe,
   tester six heures après coûts et témoins appariés. Aucun réglage des seuils
   pour atteindre arbitrairement un nombre de trades ou un GO.

L'étape suivante nécessite donc un accès supplémentaire ou une intervention
sur l'export gratuit. **Aucun rendement additionnel n'a été calculé pendant
cette recherche de sources.** L'accès aux données et l'avantage économique
restent deux vérifications distinctes.

## Livraison technique

Audit natif offline réutilisable, comparaisons numériques et tests de refus
sur liquidation absente, mauvais compte, prix divergent ou trade dupliqué.
**187 tests**, lint/format et types passent. Raws et métadonnées de recherche
sont dans `data/liquidation_history_2026-09-07/`, hors Git ; empreintes des
preuves dans [le manifeste](evidence_manifest.json). Aucun secret enregistré.

Reproduction sans réseau, destination nouvelle :

```bash
rtk proxy uv run python scripts/audit_native_liquidations.py --output tmp/native-liquidation-reproduction.json
```

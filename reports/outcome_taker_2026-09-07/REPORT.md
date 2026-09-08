# Outcomes taker : aucun signal au seuil enregistré

**`HYPOTHESIS_NOT_CONFIRMED`**, aucun GO. La règle quotidienne fondée sur une
probabilité prudente ne déclenche aucun achat. Ce résultat porte sur cette
règle et cette période, pas sur l'impossibilité de négocier les outcomes avec
profit. Aucune dépense de données, aucun ordre ni changement serveur.

Le [protocole](PROTOCOL.md) a été enregistré avant calcul des signaux/PnL.
Deux contrats dont la résolution avait été sondée (111 et 762) sont exclus ;
le troisième sondé, 1715, est hors période. Le cours des sous-jacents avait déjà
été utilisé ailleurs : pas de prétention à un historique global vierge.

## Données récupérées gratuitement

L'archive Nautilus existante contient **892 492 lignes**, 115 contrats
(40 BTC et 25 chacun ETH/SOL/HYPE), sur 40 dates d'expiration entre le 28 mai
et le 7 juillet 2026, soit une enveloppe calendaire de 41 jours. L'extraction
conserve les horloges événement et réception originales, contrairement à
l'import agrégé qui ne conservait que l'heure événement.

642 observations sélectionnées de façon déterministe : 214 carnets à la
décision, 214 pour l'exécution différée et 214 pour le retard supplémentaire.
L'extrait et ses manifestes occupent environ 512 ko. Aucun déplacement ni
modification des anciens dépôts, aucune copie massive des archives.

Les **113 requêtes publiques `settledOutcome`** nécessaires ont retourné des
résolutions binaires officielles. Toutes les identités, strikes, sous-jacents,
échéances, côtés et quote USDC correspondent aux carnets. Ces labels remplacent
l'usage incorrect des 99 résultats paper legacy, qui incluent des sorties
avant échéance et ne constituent pas des résolutions officielles.

Sources locales :

- `data/outcome_taker_2026-09-07/extract_verified/` : carnets, univers, provenance.
- `data/outcome_taker_2026-09-07/labels/` : requêtes et réponses natives checksumées.
- `data/search_2026-09-06/history/` : bougies horaires natives déjà acquises.
- `data/outcome_taker_2026-09-07/final/` : décisions et résultats reproductibles.

Le SHA-256 du fichier source original est
`e23544528c2e64b6c72ae42e93458e4ed6a002993aa4808e75ce933cb435d959`.
Il est contrôlé avant et après extraction. Les archives restent classées B.

## Résultat du filtre

Une décision par contrat à 12:00:05 UTC, environ 18 h avant résolution.
Benchmark digital existant, volatilité des 168 rendements horaires antérieurs,
variantes ×0,75/1/1,25 ; minimum de la probabilité du côté considéré, moins
3 points d'incertitude. Il faut encore 5 points de marge après provision de
settlement pour déclencher un achat.

| Filtre sur les 226 côtés des 113 contrats | Nombre |
|---|---:|
| Carnet manquant ou vide à l'heure fixée | 16 |
| Carnet frais, ask hors de [0,15 ; 0,85] | 12 |
| Carnet frais dans la plage, marge trop faible | 198 |
| Marge suffisante | **0** |

Les 210 observations non vides sont fraîches selon la tolérance enregistrée
de 60 s ; le problème ne vient donc pas ici d'un blocage général de transport.
La meilleure marge prudente est **2,57746 points de probabilité**, sur le NO
HYPE du 23 juin, contre 5 requis. La profondeur ne sauve pas un signal qui
échoue déjà au filtre de prix. Aucun seuil n'a été abaissé après résultat.

**Zéro trade** dans les scénarios de base, stress et retard. Il n'existe donc
ni rendement par trade mesuré ni intervalle de confiance de performance.
Le proxy mensuel −20 $ dans le JSON correspond uniquement à l'hypothèse
comptable de 20 $/mois d'infrastructure avec revenu nul ; ce n'est pas une
perte de trading observée ni une nouvelle facture.

## Portée et suites

La règle est suspendue. L'idée d'une erreur de prix des outcomes peut rester
pertinente avec un autre modèle ou un autre mécanisme, mais ce test ne la
confirme pas. On ne transforme pas la probabilité du modèle en preuve d'edge.

La référence perp reste un proxy du mark de résolution ; sa disponibilité
à cinq secondes après clôture est une hypothèse. Les asks échantillonnés ne
prouvent pas des fills. Les taux de settlement 7/20 bps sont des scénarios,
pas une attestation historique de frais de compte. La
[documentation officielle](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees)
indique des frais à la fermeture/résolution plutôt qu'à l'ouverture.

La [publication Arrakis](https://arrakis.finance/blog/hip-4) motive l'examen des
écarts de probabilités, mais ses comparaisons de prix et markouts ne démontrent
pas la rentabilité nette de ce bot. Aucun résultat externe n'a servi de label
ni de PnL. L'[endpoint de résolution documenté par QuickNode](https://www.quicknode.com/docs/hyperliquid/info-endpoints/settledOutcome)
a été interrogé directement sur l'API native Hyperliquid, sans fournisseur payant.

Prochaine recherche à cadrer : flux agressif et déséquilibre du carnet comme
signal taker sur les perps liquides, à partir des flux publics déjà collectés
par Hyperbot en août. Mesurer d'abord réception, disponibilité des BBO et coût
aller-retour ; figer une règle distincte avant tout markout/PnL. Réutiliser
les lecteurs et données existants, sans nouvelle collecte longue ni achat.

## Vérification

**216 tests passent**, lint et format passent (166 fichiers), mypy passe sur
54 fichiers source. Les tests ajoutés vérifient causalité, fraîcheur, profondeur,
prix d'exécution défavorable, limite de dépense, retard et frais sur payout.
Deux extractions ont produit les mêmes carnets et univers ; deux évaluations
ont produit les mêmes décisions et résultats, quatre comparaisons SHA-256.
Voir [preuves](reproduction.json) et [résultat détaillé](summary.json).

Reproduction locale, sorties nouvelles obligatoires :

```bash
rtk proxy uv run python scripts/fetch_outcome_taker.py --output data/outcome_taker_new_extract
rtk proxy uv run python scripts/investigate_outcome_taker.py --extract data/outcome_taker_new_extract --output data/outcome_taker_new_run
```

Le lecteur réutilise les labels existants ; cette reproduction n'effectue
aucune requête réseau. Livraison offline, aucun service déployé ou relancé.

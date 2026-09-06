# HyperBot2 — stratégie pour 1 000 $ et plan d’implémentation

**Date : 6 septembre 2026.** Audit des trois projets, recalcul de données
TRIDENT et sondes publiques Hyperliquid réalisés pour ce document.

**Décision : retenir pour une dernière expérience bornée un market making
sélectif sur les outcomes crypto quotidiens HIP-4, avec inventaire plafonné et
prix fondés sur la probabilité de settlement. Ne pas engager de capital réel
aujourd’hui.** C’est la piste de recherche la mieux justifiée parmi celles
examinées ; sa rentabilité reste à démontrer.

**Aucune solution examinée ne permet de soutenir « +30 % minimum chaque mois ».**
Le plan vise à déterminer si 300 $ mensuels nets sont plausibles avec 1 000 $,
puis à arrêter si les preuves ne le soutiennent pas. Les mois négatifs restent
possibles, même avec une stratégie profitable en moyenne.

Ce document précise l’exécution de la thèse de
[la fondation](HYPERBOT_FOUNDATION.md), sans remplacer ses limites de risque ni
ses gates. [FOLLOW_UP.md](FOLLOW_UP.md) conserve le statut opérationnel.
Le développement dans ce nouveau dépôt a ensuite été explicitement autorisé
par l’utilisateur. La [livraison v0](reports/implementation_2026-09-06/REPORT.md)
implémente les outils de recherche/simulation ; les travaux « à faire »
ci-dessous décrivent le plan initial, leur statut courant est dans le suivi.
Aucune collecte permanente ni trading réel n’est autorisé par ce document.

## 1. Ce que les trois bots ont réellement appris

| Projet | Preuve examinée | Conclusion économique |
|---|---|---|
| TRIDENT A/C | Dernière review locale complète du 10 août : A −188,85 $, C −15,29 $, soit −204,14 $ réalisés | Ne pas recycler les anciens patterns directionnels et leur sélection de paramètres |
| TRIDENT HIP-4 | CSV recalculé : 99 clôtures paper, +43,6620 $, PF 1,0874 ; mainnet observateur sans trade dans la review | Petit résultat paper positif, insuffisant ; aucune preuve d’edge maker |
| HyperBot | Campagne BTC des 25–26 août : 1 fill central en base, markout économique 30 s négatif ; aucun fill pessimiste en base | Pas de preuve de rentabilité ni de rotation exploitable |
| HyperBot | Diagnostic des 1er–3 septembre : environ 10 % des quotes avec preuve de file à l’activation ; verdict `DATA_BLOCKED` | Le dernier essai ne produit pas de rendement ; il mesure une incompatibilité de données |
| BOT05 | Une session indépendante ; breakout central +0,06791 R, stress −0,07781 R ; historiques et coûts encore incomplets | Chaîne technique fonctionnelle, edge non établi ; les variantes sur la même session ne multiplient pas l’échantillon |

Sources : [review A/C](../trident/server-data/reviews/20260810T120656Z/review_summary.md),
[review HIP-4](../trident/server-data/hip4/reviews/20260810T125746Z/hip4_outcome_run_review.md),
[campagne BTC](reports/m4/growth_spread_backtest_2026-08-25_26.md),
[diagnostic borné](reports/m10/bounded-20260906T145628Z/report.md),
[audit BOT05](../bot05/reports/audits/bot05_status_2026-09-06.md).
Ces archives ne certifient pas l’état actuel de TRIDENT en production.

Le reproche « collecte sans résultat » est économiquement justifié : du
logiciel et des données ont été livrés, mais aucun edge déployable. L’audit
serveur déjà publié décrit des raws du 11 août au 6 septembre, avec premières
et dernières journées partielles, et 17 journées qualifiées sur 21 du 16 août
au 5 septembre. Cela ne représente pas 30 jours continus qualifiés.
Je n’ai pas refait de contrôle SSH dans cette tâche.

Le défaut de méthode à corriger : le témoin économique est BTC perp, marché
très serré, alors que la thèse principale repose sur les outcomes. Le volume
de données BTC et la santé des conteneurs ne valident pas cette thèse.
La collecte doit désormais répondre à une hypothèse et à une date de verdict.

### Recalcul des archives HIP-4

Le [nouvel audit descriptif](reports/strategy_review_2026-09-06/evidence.json)
a relu le fichier de 892 492 snapshots, du 27 mai au 6 juillet, et le CSV des
clôtures. Les checksums concordent avec les sources legacy inventoriées.

| Sous-jacent | Clôtures paper | PnL net paper | PF | Spread médian historique par token |
|---|---:|---:|---:|---:|
| BTC | 45 | −26,84 $ | 0,902 | 0,0040 $ |
| ETH | 17 | −20,66 $ | 0,707 | 0,0353 $ |
| SOL | 19 | +85,21 $ | 2,290 | 0,0356 $ |
| HYPE | 18 | +5,95 $ | 1,067 | 0,0395 $ |

Les médianes portent sur les observations valides, sans pondération par durée.
73 522 lignes sont exclues par le contrôle `0 < bid < ask < 1` après filtre
temporel, et deux répétitions consécutives de timestamp par marché/côté sont
écartées. Ce n’est ni une mesure de volume exécuté, ni une mesure de profits
accessibles. Un spread de 0,0353 $ est une différence de prix par token,
pas un rendement de 3,53 % sur le portefeuille.

Le gain SOL dépasse le gain total : retenir SOL seul après lecture du résultat
serait de la sélection rétrospective. Les 99 lignes du CSV comprennent
**38 sorties anticipées et 61 clôtures YES/NO**, sur 93 identifiants de marché
distincts. Elles ne constituent donc pas 99 observations indépendantes de
settlement terminal, encore moins les 300 settlements exigés pour la promotion.

Sur 409 349 paires YES/NO valides au même timestamp exchange : **zéro somme
d’asks < 1 et zéro somme de bids > 1**, à une tolérance numérique de 10⁻⁹.
Aucun arbitrage brut de complémentarité n’apparaît dans cet échantillon.
Ce test ne prouve pas une réception simultanée ni une exécution possible.

## 2. Vérifications actuelles qui changent le plan

### Un flux L2 plus rapide existe déjà

La documentation officielle décrit `l2Book` avec **`fast: true` : cinq niveaux
par côté**, contre vingt dans le mode lent. Une comparaison locale de deux
connexions publiques pendant 40 secondes donne :

| Abonnement BTC | Snapshots distincts | Intervalle médian reçu | Âge apparent médian à réception |
|---|---:|---:|---:|
| `fast: false` | 8 | 5 392 ms | 302 ms |
| `fast: true` | 74 | 537 ms | 270 ms |

71/74 snapshots rapides ont un âge apparent ≤500 ms ; le p99 empirique est
575 ms. **Cela ne qualifie pas la file** : entre publications le carnet vieillit,
la quote arrive après une latence supplémentaire et son prix peut sortir des
cinq niveaux. L’horloge n’a pas été calibrée indépendamment ; le test est court
et local, sans mesure de latence d’ordre.

Avec l’hypothèse de placement à 350 ms du diagnostic existant, un snapshot
déjà âgé de 270 ms atteindrait 620 ms sans nouvelle publication : le mode
rapide ne résout donc pas automatiquement le blocage à 500 ms.

Priorité technique : évaluer ce flux sur les marchés utiles avant le sampler
REST envisagé précédemment. Aucun abonnement du collector existant n’a été
modifié. [Documentation des subscriptions](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions),
[preuve de la sonde](reports/strategy_review_2026-09-06/fast_l2_probe.json).

### Les outcomes quotidiens existent ; leur schéma doit être correctement lu

Le catalogue public récupéré le 6 septembre contient 145 outcomes. Il comprend
les quatre contrats quotidiens sous **`name=Recurring`, `class:priceBinary`**,
ainsi que des `template:binaryPrice`, des barrières `priceTouch` et des événements.
Un filtre limité aux templates manquerait les quatre marchés historiques.

[Sondage des carnets quotidiens](reports/strategy_review_2026-09-06/recurring_outcomes.json),
expiration du 7 septembre à 06:00 UTC, côté YES :

| Sous-jacent / strike | Bid | Ask | Spread par token |
|---|---:|---:|---:|
| BTC / 79 963 | 0,34627 | 0,36000 | 0,01373 $ |
| ETH / 2 513 | 0,18524 | 0,20659 | 0,02135 $ |
| SOL / 106,41 | 0,33000 | 0,40000 | 0,07000 $ |
| HYPE / 86,762 | 0,88000 | 0,91000 | 0,03000 $ |

Ces captures sont séquentielles et ponctuelles. Elles confirment une surface
de recherche, pas sa permanence. Par exemple, l’ask ETH ne contient que
29 tokens, soit environ 5,99 $ : un ordre de 10 $ traverse déjà ce premier
niveau en taker. La profondeur agrégée ne doit pas masquer ce problème.

La mécanique officielle **fusionne les carnets YES et NO** et donne une
priorité prix/côté/temps. Acheter YES et vendre NO au prix complémentaire
touchent donc la même liquidité. Il faut éviter de compter deux fois volumes,
file et capital. Les contrats sont entièrement collatéralisés ; l’inventaire
reste exposé à sa perte de valeur. [Spécification HIP-4](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-4-outcome-markets).

### Frais : pas d’hypothèse « outcomes gratuits »

Le catalogue reçu contient `feeScale = "1.0"` ; certains marchés ont aussi
un `deployerFeeScale`. Ces champs seuls ne donnent pas le tarif du compte.
La page HIP-4 conserve une mention de gratuité initiale, tandis que la page
des frais décrit la facturation des fermetures/settlements et l’absence de
rebates outcomes. **Cette incohérence documentaire interdit de supposer zéro.**

La référence générale tier 0 des perps est 1,5 bps maker et 4,5 bps taker.
Le growth mode HIP-3 dépend du marché et des multiplicateurs applicables ;
BTC perp natif n’en bénéficie pas. Les frais outcomes devront être calculés
par type d’opération, avec snapshots causaux et rapprochement des frais payés.
[Barèmes et règles de frais](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees).

## 3. Choix entre les stratégies

| Famille | Décision pour ce projet | Motif |
|---|---|---|
| Market making sélectif outcomes quotidiens | **Priorité de recherche** | Spreads observables plus larges, payoff borné, archives réutilisables et infrastructure déjà disponible |
| Market making BTC perp au meilleur prix | Écarter comme moteur de rendement actuel | Spread médian publié de 0,124 bp le 4 septembre, inférieur aux 3 bps de deux fills maker tier 0 ; coter plus loin exige un véritable edge d’inventaire |
| HIP-3 growth | Secondaire, sans allocation avant sa propre validation | Frais faibles possibles, mais aucun marché qualifié et profitable démontré ici ; un faible tarif ne crée pas de spread |
| BOT05 opening-drive/pullback | Ne pas en faire le véhicule de la cible +30 % | Échantillon insuffisant et fréquence/risque trop faibles pour cette cible dans sa variante 2R |
| Patterns et filtres directionnels TRIDENT | Ne pas reprendre | Résultats réels défavorables, promotions sur petits échantillons |
| Arbitrage YES/NO d’un même outcome | Rejeter comme thèse autonome | Carnet fusionné et aucun croisement exploitable observé dans l’audit |
| Funding spot/perp | Ne pas retenir pour +30 % | Le funding instantané observé de 0,0000125/h représente seulement 0,9 %/30 jours du notionnel short s’il restait constant, avant marge du hedge et coûts |
| Copy trading, TWAP, liquidations, LLM | Hors campagne | Aucun edge causal démontré dans les preuves examinées ; ajouter ces moteurs diluerait l’expérience |

Source du spread BTC et des limites BOT05 :
[audit du 6 septembre](../bot05/reports/audits/bot05_status_2026-09-06.md).
Le funding est payé chaque heure et peut changer de signe ; le calcul précédent
est une illustration, pas un rendement anticipé.
[Mécanique du funding](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding).

Avec BOT05, 44 gains consécutifs à 2R et 0,25 % risqué par trade ne donneraient
que `(1,005)^44 − 1 = 24,54 %`, avant coûts, sous l’hypothèse de 22 jours et
deux trades/jour. La cible causale non plafonnée à 2R est un autre cas, encore
non validé. Relever le risque pour atteindre 30 % ne résout pas l’absence d’edge.

## 4. Traduire +30 % en contraintes vérifiables

Le rendement est mesuré sur les **1 000 $ du compte**, réserve et capital
inoccupé inclus, après trading, sorties, settlements et infrastructure
attribuable ; hors fiscalité personnelle. Objectif : 300 $ nets sur 30 jours.
Il équivaut à environ 0,8784 % composé/jour et à ×23,30 sur douze mois.

Définir une convention unique :

```text
Q = somme quotidienne des notionnels d’entrée des cycles réellement clôturés
e = PnL net de trading de ces cycles / somme de leurs notionnels d’entrée
F = coût mensuel d’infrastructure attribué à la stratégie
PnL mensuel illustratif = 30 × Q × e − F
```

Un aller-retour de 10 $ représente 10 $ dans Q, et environ 20 $ de volume
d’exécution total. Ne pas doubler le rendement en mélangeant ces conventions.
Les positions encore ouvertes sont valorisées séparément au coût de liquidation
réaliste ; elles ne deviennent pas des cycles gagnants fictifs.

Sensibilité avec **F = 20 $**, hypothèse de budget et non facture observée :

| Edge net par cycle | Q nécessaire par jour | Cycles d’entrée de 10 $/jour | Rotations/jour de 200 $ actifs |
|---|---:|---:|---:|
| 5 bps | 21 333 $ | 2 134 | 106,67 |
| 10 bps | 10 667 $ | 1 067 | 53,33 |
| 25 bps | 4 267 $ | 427 | 21,33 |
| 50 bps | 2 133 $ | 214 | 10,67 |
| 70 bps | 1 524 $ | 153 | 7,62 |
| 100 bps | 1 067 $ | 107 | 5,33 |

Les nombres de cycles sont arrondis au supérieur. **Aucune de ces combinaisons
n’est aujourd’hui mesurée.** La fondation limite l’inventaire brut à 50 $ par
outcome et quatre marchés : au plus 200 $ actifs simultanément, souvent moins
avec les caps de perte corrélée. Allouer 700 $ à la poche ne signifie donc pas
que 700 $ tournent simultanément. Les ordres en attente doivent aussi réserver
le collatéral de leurs fills possibles.

Les tableaux de rendement de la fondation restent des scénarios arithmétiques.
Les résultats depuis août ne permettent pas de les transformer en prévisions.
Une moyenne mensuelle de +30 %, si elle apparaissait un jour, ne prouverait
toujours pas un minimum mensuel de +30 %.

## 5. Spécification du candidat `outcome_selective_v2`

### Univers et information

- Univers fixé avant les tests : outcomes `Recurring/priceBinary` quotidiens
  BTC, ETH, SOL, HYPE ; pas de sélection SOL seul à partir du PnL legacy.
- Chaque révision conserve ID, strike, expiration, source exacte de settlement,
  règle d’égalité, éventuelle moyenne temporelle, collatéral, ticks/lots,
  frais et statut. Exclure templates nouveaux, barrières et événements v0.
- Joindre les observations selon leur disponibilité à réception, jamais avec
  le futur. Les données post-settlement servent uniquement de labels.
- Écarter marchés inconnus, pauses, carnets invalides et propriétés non
  documentées. Une ressemblance de nom ne suffit pas à qualifier un contrat.

### Fair value et décision

Réutiliser le benchmark digital de `research/outcomes.py` avec volatilité
estimée uniquement sur le passé et calibration sur fenêtres antérieures.
Le prix de référence doit correspondre à celui qui résout le contrat.
Ne pas remplacer une moyenne de trades par un mark instantané sans modèle adapté.

Construire toutes les marges **en unités de prix par token** :

```text
p = probabilité calibrée de settlement YES
h = coût attendu d’un cycle
  + estimation prudente de sélection adverse
  + incertitude de calibration
  + coût d’inventaire + marge opérationnelle
bid_yes = arrondi_inférieur(min(best_bid, p − h − skew))
ask_yes = arrondi_supérieur(max(best_ask, p + h − skew))
```

Le coût attendu inclut les branches de sortie maker, sortie de risque taker et
settlement, sans facturer deux fois la même opération. L’incertitude et la
sélection adverse viennent du passé. Un markout conditionné à un touch legacy
n’est pas une estimation validée du markout d’un fill maker réel.

Préenregistrer au plus trois variantes : même règle, avec marge opérationnelle
additionnelle de **0,000 / 0,005 / 0,010 $ par token**. Ces valeurs sont des
hypothèses de sensibilité, pas des paramètres rentables identifiés. Vérifier
que tick, prix contraints et coûts ne rendent pas les trois variantes identiques.

Paramètres communs v0 : prix/fair value dans `[0,15 ; 0,85]`, au moins
30 minutes avant expiration, taille cible 10 $, aucun levier. Ces restrictions
sont plus prudentes que le minimum de la fondation ; elles doivent rester
identiques dans les trois variantes. Ne pas les desserrer après un manque de fills.

### Exécution et inventaire

- Entrées normales ALO ; ventes limitées aux avoirs disponibles ou à une
  transformation collatéralisée explicitement modélisée. Aucun short de token
  fictif. Comptabiliser split/merge et frais avant de les autoriser.
- Un seul état d’inventaire et de carnet fusionné par outcome. Ne pas émettre
  des quotes YES/NO équivalentes qui doublent le risque ou la liquidité supposée.
- Décision déclenchée par un événement utile ; pas de cancel/replace aveugle
  toutes les 250 ms. Réutiliser TTL/latences validés, journaliser chaque ACK,
  rejet ALO, fill partiel, annulation et fill pendant l’annulation.
- Garder la fraîcheur de 500 ms. Avant émission, exiger une marge causale
  `âge + latence_placement_prudente + incertitude_horloge ≤ 500 ms` et une
  profondeur couvrant le prix. Vérifier de nouveau le scénario stress.
- Si les cinq niveaux rapides ne couvrent pas une quote, s’abstenir. Ne pas
  interpréter un niveau absent comme zéro volume devant l’ordre.
- Un gap après émission est un incident d’une position exposée : conserver
  la période et appliquer la sortie/pénalité prévue ; ne pas effacer ce cycle
  du PnL après avoir vu qu’il perdait.
- Sortie normale en maker ; annulation des entrées quand fair value, flux ou
  risque changent. Sortie de risque IOC bornée et inventaire résiduel pris au
  pire payoff si aucune liquidité n’est disponible. Pas de hedge perp en v0.

La cadence doit aussi respecter les limites d’actions du compte. Les frais et
le volume contribuant aux quotas ne sont pas identiques selon les opérations.
Le budget initial de requêtes ne finance pas indéfiniment une stratégie sans
fills. [Limites officielles](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits).

### Risque pour les 1 000 $

Conserver le superviseur unique replay/shadow/futur live et les limites de la
fondation : 50 $ d’inventaire brut/outcome, 25 $ de perte au settlement/marché,
quatre marchés, 30 $ de perte corrélée, 50 $ agrégés ; arrêt à −1,5 % journalier,
réduction à 8 % de drawdown mensuel, arrêt dur à 12 % absolu.

Calculer les pertes sur tous les fills encore possibles des ordres en attente,
pas seulement sur les positions confirmées. Les stops de PnL ne garantissent
pas une perte maximale en cas de gap ou de panne. Aucun rattrapage par levier.
Les 250 $ prévus pour Growth restent disponibles tant que ce moteur n’est pas
promu ; aucune redistribution automatique ne relève les caps outcomes.

## 6. Utiliser les données existantes avant tout nouveau mois de collecte

| Source | Usage immédiat | Limites et acquisition |
|---|---|---|
| HyperBot `data/legacy_imports/` et manifestes | Événements déjà normalisés, fair value, spreads, contrôles de parité | B/C ; pas de nouveaux imports massifs ni de fills maker validés |
| TRIDENT HIP-4, 892 492 books et journaux | Reproduire les trades paper, estimer la surface d’opportunités et les markouts exploratoires | B ; réception/cadence/staleness à auditer ; raw en lecture seule |
| HyperBot A local et segments serveur déjà existants | Références BTC/ETH/SOL/HYPE, volatilité, trades, BBO ; contrôle de coûts d’exécution | Les perps sous-jacents ne remplacent pas les carnets outcomes manquants |
| BOT05, fenêtres H1 qualifiées et contrats de session | Réutiliser la qualification et les leçons d’exécution ; contrôle directionnel documentaire | H1 BOT05 ne devient pas automatiquement A ; ne pas importer sa stratégie |
| Hyperliquid `/info`, `outcomeMeta`, `l2Book` | Catalogue actuel et qualification des contrats ; captures publiques ciblées | Snapshots actuels, pas historique complet ; versionner les réponses |
| Hyperliquid `candleSnapshot` | Volatilité/contexte manquant avec bougies clôturées | Seulement les 5 000 bougies les plus récentes par intervalle : ≈3,47 jours en 1m, 17,36 jours en 5m, 208,33 jours en 1h |
| S3 `hyperliquid-archive/market_data/.../l2Book/` et `asset_ctxs/` | Tester la couverture d’une ancienne journée/marché manquants | Publications approximativement mensuelles, trous possibles ; pas de garantie outcomes |
| S3 `hl-mainnet-node-data/node_fills_by_block/` | Reconstituer trades/frais et volume agressif sur gaps justifiés | Dédupliquer les deux faces et les représentations duales ; les fills seuls ne reconstruisent pas toutes les annulations |
| Fournisseur externe de L2/L3 | Seulement si l’API rapide échoue et qu’un edge justifie son coût | Échantillon, schéma, licence, provenance, séquences et devis avant abonnement |

Les 5 000 bougies sont une **limite de profondeur historique**, pas une simple
taille de page contournable avec `startTime`. L’archive officielle ne promet
pas des bougies ni l’historique spot/outcomes. Les snapshots L2 ne donnent pas
magiquement la file exacte. [API info](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint),
[archives officielles](https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data).

Ordre d’acquisition : inventaire local → couverture qualifiée par
marché/canal/intervalle → liste des gaps → export sélectif des raws déjà
collectés → API ou échantillon S3 pour les seuls gaps. S3 est requester-pays :
aucun téléchargement payant n’a été lancé ici. Prévoir un plafond proposé de
10 $ pour un échantillon, puis demander l’accord sur le coût concret si nécessaire.
Pas de nœud complet ni de nouveau fournisseur en dépendance initiale.

Une archive publique extérieure garde une provenance distincte ; ne pas la
rebaptiser A. La politique A/B/C actuelle réserve la validation maker aux
données A qualifiées. Une extension de cette politique serait une décision
explicite ultérieure, avec preuve d’équivalence, pas une astuce de promotion.

Les manifests d’import conservent source, SHA-256, période, lignes, schéma,
cadence, gaps, transformations et version d’adaptateur. Les reads croisés
servent à préparer des artefacts autonomes, sans dépendance runtime aux autres bots.

## 7. Plan d’implémentation avec limites de temps

**Premier verdict en cinq journées de travail au maximum**, à compter du début
de l’implémentation, pas cinq jours de rendement. Aucun engagement de trente
jours de collecte supplémentaire avant ce verdict. Les délais ci-dessous sont
des budgets d’effort ; ils ne promettent pas une validation statistique.

### Lot P0 — audit et sélection : livré dans cette tâche

Livrables : ce plan, audit CSV/books checksumé, catalogue/carnets actuels et
comparaison `fast=false/true`. Résultat : candidat outcomes retenu pour étude,
aucun edge validé. Les trois dépôts ont été lus ; seuls HyperBot et ses
artefacts de recherche locaux ont reçu des écritures.

### Lot P1 — prouver que l’étude est faisable : journée 1

1. Figer manifestes, données déjà examinées, variantes et budget ; ajouter au
   journal une nouvelle expérience outcomes, distincte du diagnostic BTC clos.
2. Qualifier le schéma `Recurring`, source de settlement, ticks/lots et frais.
   Refuser toute valeur par défaut donnant artificiellement `market_ready`.
3. Exécuter un témoin outcomes `l2Book fast=true` isolé, court puis jusqu’à
   24 h si utile. Mesurer timestamps distincts, niveaux, fraîcheur à décision
   et activation base/stress, volume disque et budget de requêtes.
4. Exporter seulement les fenêtres sous-jacentes nécessaires aux archives
   outcomes déjà présentes. Ne pas reconstruire toutes les journées multi-Go.

Sortie : matrice des inputs réellement disponibles et raisons d’abstention.
Si settlement/frais/flux adéquats manquent : `DATA_BLOCKED`, avec un gap précis
et le coût borné d’une éventuelle correction. Pas de poursuite automatique.

### Lot P2 — produire un verdict économique exploratoire : journées 2–3

Créer `research/opportunity_screen.py` et un runner de campagne streaming.
Réutiliser adaptateurs et événements existants. Publier simultanément :

- couverture temporelle, marchés éligibles, spreads après coûts, profondeur à
  10 $, vieillissement, markouts et concentration ;
- scénario volontairement favorable `optimistic_touch`, avec capital,
  collatéral, caps, rotation et clôtures cohérents ; jamais appelé central ;
- sensibilités de coûts/latence et entonnoir complet, périodes sans signal et
  incidents compris ; comparaison au cash et au paper legacy reproduit.

Ce scénario peut **rejeter la configuration sur les périodes étudiées** si
même ses hypothèses favorables échouent. Il ne réfute pas toute stratégie
future ; il ne devient pas une preuve positive s’il gagne. Avec les seules B/C,
ne calculer aucun fill présenté comme central ou pessimiste validé.

Limiter la campagne à trois variantes, deux modèles lorsque A est qualifié,
trois scénarios : base, frais ×2, latences ×2. Plafond global proposé :
24 CPU-heures, 4 Gio RSS, 10 Gio d’artefacts supplémentaires, aucune relance
automatique ; faire appliquer ces plafonds par l’orchestrateur du run.

### Lot P3 — corriger uniquement les obstacles du candidat : journées 4–5

| Composant existant | Travail nécessaire | Test d’acceptation utile |
|---|---|---|
| `market_catalog.py` | Parser les descriptions, règle de settlement, `feeScale`, deployer et étapes de frais ; le code actuel utilise une référence spot 4/7 bps pour outcomes | Métadonnée manquante/incompatible → refus ; replay des révisions historiques sans taux actuel rétroactif |
| `services/public_collector.py` | Option de flux rapide explicite et provenance nouvelle ; témoin séparé avant intégration | Aucun abandon silencieux du paramètre ; cinq niveaux jamais interprétés comme profondeur complète |
| `strategies/outcome_maker.py` | Marges dans la bonne unité, abstention causale, inventaire/collatéral communs YES/NO | Prix/tailles distincts, pas de vente nue ni de double réservation ; identique replay/shadow |
| `replay/engine.py` | Qualifier la priorité prix/côté/temps et les opérations duales outcomes ; conserver les modèles de file prudents | Une transaction duale ne remplit pas deux fois ; annulations/partiels/ACK et gaps stressés |
| `replay/backtest.py`, runner de campagne | PnL de portefeuille fermé, cycles appariés, cash, settlements et liquidation terminale | Cash + inventaire + frais se réconcilient ; aucun rendement issu d’une position oubliée |
| `research/gates.py` | Auditer le PF actuellement agrégé depuis le PnL des folds : trois folds positifs donnent zéro fold perdant et `None` | Calculer PF sur gains/pertes des cycles nets ; folds tous positifs mais PF des trades ≤1,20 → rejet |
| `risk/supervisor.py`, `services/shadow_runner.py` | Même contrat d’ordres/risque, fermeture fail-closed et réservations des ordres en vol | Déconnexion, stale, inventaire dual, ordre orphelin, redémarrage et dépassement de caps |

Il s’agit de travaux **à faire**, pas d’une affirmation que l’adaptateur maker
outcomes est déjà qualifié. Si ces corrections dépassent deux journées,
publier le blocage et arrêter le lot à son budget ; ne pas livrer une version
financièrement incomplète pour respecter artificiellement la date.

### Verdict obligatoire à J5

- `REJECT_RESEARCH` : surface économique insuffisante dans le scénario
  favorable, coûts excessifs ou échec des critères préenregistrés ; archiver.
- `DATA_BLOCKED` : causalité/exécution non simulables ; publier les gaps et
  leur coût, sans rendement inventé et sans nouvelle collecte indéfinie.
- `INCONCLUSIVE` : données ou puissance insuffisantes ; arrêter à la date,
  sans présenter cela comme un échec économique ni sélectionner le meilleur bruit.
- `CONTINUE_RESEARCH` : surface favorable plausible, faisabilité documentée,
  et conditions de l’étape suivante remplies. Ce verdict n’est ni un pass OOS,
  ni une autorisation de trading. Budgéter séparément la suite.

Rapport obligatoire même avec zéro trade : hypothèse, hashes, période,
couverture, abstentions, fills, cycles, frais, PnL réalisé, PnL terminal, capital
immobilisé, drawdown, turnover, concentration, stress et cible arithmétique.
Le coût de recherche est publié séparément du coût d’exploitation mensuel.

## 8. Conditions de poursuite et de promotion

Les archives déjà explorées restent exploratoires. Le protocole BTC existant
réserve calibration 7–13 septembre et test 14–22 septembre ; cette campagne
est close `DATA_BLOCKED` et ces dates ne sont pas recyclées silencieusement.
Préenregistrer les nouvelles fenêtres outcomes avant d’ouvrir leurs résultats.

Pour une poursuite positive : séparation chronologique train/calibration/test,
purge de toute position dont le settlement traverse une frontière, puis trois
folds OOS. Bootstrap par blocs de journées en conservant la dépendance entre
cryptos ; pas de 892 492 snapshots traités comme autant d’observations indépendantes.
Conserver toutes les variantes et tous les rejets au journal.

Les gates de la fondation restent nécessaires :

1. 30 jours continus de carnet, complétude ≥99 % et critères opérationnels M3
   applicables ; données A et preuve de file pour chaque quote simulée.
2. Au moins 300 settlements outcomes exploitables et 500 round trips pour le
   moteur candidat, définis sans compter plusieurs sorties comme settlements.
3. Trois folds OOS positifs, PF net des cycles >1,20, drawdown OOS <10 %,
   concentration d’un sous-jacent ≤40 % et borne bootstrap positive.
4. Central positif, pessimiste non catastrophique ; pour recommander une
   poursuite vers l’objectif agressif, exiger en plus pessimiste et stress
   non négatifs. Ne pas sélectionner des paramètres par leur mois maximal.
5. Au moins 14 jours shadow consécutifs sans violation ; un fill shadow reste
   simulé. Aucune promotion ne découle des tests logiciels seuls.
6. Review sécurité puis **autorisation explicite séparée** avant tout canary :
   plafond total 100 $, ordres de 10 $, aucun levier outcomes. Calibrer les
   hypothèses de fill sur ces petits ordres avant toute montée en taille.

Avec seulement quatre marchés quotidiens, 300 settlements distincts
correspondent à au moins **75 jours de marchés** si chacun ne résout qu’une
fois par jour. Les B historiques ne suffisent pas à valider l’exécution A.
**Une validation complète en cinq jours, ou automatiquement après trente jours,
est donc incompatible avec ces gates.** J5 sert à décider si le projet mérite
encore cette durée ; si ce délai est inacceptable, la décision est de ne pas
déployer sous les règles actuelles, pas d’abaisser discrètement les critères.

Pour parler ultérieurement d’une cible +30 % plausible, publier plusieurs
fenêtres OOS de 30 jours : distribution du rendement total après infrastructure,
probabilité empirique de perte, fréquence ≥30 %, incertitude et capacité aux
tailles autorisées. Ne pas extrapoler quelques jours ou relever les tailles
jusqu’à ce qu’une simulation affiche 300 $. Aucun de ces résultats n’est acquis.

## 9. Impact et travail autorisé par ce document

Cette livraison contient un plan et de petits artefacts d’audit locaux.
Les sondes ont utilisé uniquement des endpoints publics et se sont terminées.
Aucun ordre, signature, secret, téléchargement payant, déploiement ou changement
de configuration produit. TRIDENT et BOT05 restent inchangés.

L’implémentation proposée ajouterait un flux outcomes rapide, des métadonnées
versionnées, des rapports et des modèles spécialisés. Les raws restent
append-only ; la nouvelle provenance sera explicite, sans réécrire l’historique.
Le cron quotidien reste suspendu. La réserve et l’archive froide M10 restent
des sujets de conservation nécessaires aux données existantes, mais un nouvel
achat de stockage ne doit pas être présenté comme une preuve économique.

Validation de cette livraison : recalcul descriptif sur les raws indiqués,
requêtes publiques, contrôle des checksums, des calculs et des liens locaux.
Pas de nouvelle suite de tests produit : aucun code runtime n’est modifié.
Les tests replay/shadow/fail-closed du tableau P3 seront obligatoires lors de
l’implémentation, suivis de pytest, Ruff et Mypy.

Méthode et limites des nouvelles mesures :
[dossier de preuves](reports/strategy_review_2026-09-06/AUDIT_METHOD.md).

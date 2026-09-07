# Recherche de nouvelles pistes — 6 septembre 2026

**Aucun GO économique défendable obtenu.** La recherche a été poursuivie sur
quatre branches, avec deux variantes dans la branche taker. Les résultats
défavorables sont conservés. La piste restante la plus concrète est l’accès
L4 HIP-4 de 0xArchive : couverture annoncée sur les marchés utilisés, compte
gratuit documenté, sonde et reconstructeur implémentés. Son accès effectif est
bloqué par l’absence de clé, confirmée par l’utilisateur et par un HTTP 401.

Il ne s’agit pas d’une preuve qu’aucune stratégie ne peut fonctionner. Il n’est
pas possible de fabriquer un GO en multipliant les variantes jusqu’à trouver
un résultat chanceux. Le plan impose toujours des preuves d’exécution, des
folds hors échantillon et 14 jours shadow ; ces derniers ne peuvent pas être
remplacés par des tests logiciels.

## Protocole et données réutilisables

[Protocole](PROTOCOL.md) enregistré avant les nouvelles lectures de données,
[horodatage et hash](registration.json). Univers fixé : BTC, ETH, SOL, HYPE.
Les stratégies TRIDENT/BOT05 n’ont pas été importées. Réutilisation du stockage,
des artefacts checksumés, des contrats et des protections HyperBot2.

Téléchargement public Hyperliquid : **17 280 bougies horaires et 17 280 taux
de funding**, 4 320 heures par coin, du 10 mars au 6 septembre 2026 00:00 UTC,
borne de fin exclue. Pagination funding vérifiée, absence de trou et de doublon
horaire vérifiée, OHLC contrôlés. Le téléchargement historique/métadonnées
représente 46 requêtes et 4 063 911 octets de réponses. L’écran de paniers ajoute
32 requêtes de carnets. Aucun raw n’est ajouté à Git.

L’API officielle limite les bougies aux 5 000 plus récentes : les 4 320 demandées
ont été effectivement récupérées. Les observations historiques de bougies et
de funding sont des données de recherche, sans preuve de carnet disponible à
la réception historique.
[API Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint).

## Résultats des pistes

| Branche | Résultat de cette vague | Décision |
|---|---|---|
| Maker HIP-4, L2 public | Diagnostic précédent : 0/36 fenêtres complètes fraîches pendant l’exposition, file non reconstructible | NO-GO inchangé pour ce flux |
| L4 externe | Schémas et couverture disponibles ; endpoint 0xArchive répond 401 sans clé | Piste à tester dès accès fourni, aucun GO de données acquis |
| Paniers d’outcomes liés | 22 paniers, 16 défavorables avant frais, 6 avec jambe illiquide | Aucune opportunité validée dans cet instantané |
| Funding spot/perp | Au mieux 4,93 $/30 jours pour 500 $ short, avant tous les coûts | Rejet de cette variante comme moteur de +300 $/mois |
| Breakout taker 24 h | −56,99 $ après infrastructure sur les trois blocs de test | Rejet de la variante |
| Retour à moyenne taker 24 h | −74,46 $ après infrastructure sur les trois blocs de test | Rejet de la variante |

### Taker horaire : test réservé, sans réglage après lecture

Deux règles fixées : breakout Donchian 24 h et retour à moyenne 24 h à deux
écarts-types. Signal connu après clôture, entrée au plus tôt à l’ouverture
suivante, stop 2 ATR, sortie à 24 h. Notionnel limité à 50 $/coin, risque au stop
à 2,50 $/coin, minimum d’ordre 10 $. Aucun levier ajouté pour atteindre la cible.

Les premiers 60 jours servent au développement, les 30 suivants au contrôle.
[Le code et les paramètres ont été verrouillés](holdout_lock.json) avant
l’évaluation des 90 derniers jours ; aucune optimisation après ces résultats.
Chaque bloc démarre avec 1 000 $ et liquide ses positions à sa frontière.
L’historique antérieur sert seulement aux indicateurs causaux.

| Variante, après frais/slippage/funding adverse et 20 $ d’infrastructure par bloc | 8 juin–8 juillet | 8 juillet–7 août | 7 août–6 septembre | Total des 3 blocs |
|---|---:|---:|---:|---:|
| Breakout 24 h | −26,74 $ | −18,33 $ | −11,92 $ | **−56,99 $** |
| Retour à moyenne 24 h | −35,96 $ | −28,71 $ | −9,80 $ | **−74,46 $** |

Les trois blocs sont négatifs après infrastructure pour chaque stratégie.
282 cycles breakout et 427 cycles retour à moyenne dans le scénario de base.
Les rendements sur les 1 000 $ initiaux sont les montants divisés par 10,
en pourcentage ; ils ne sont pas calculés sur les seuls 200 $ potentiellement
engagés. Les sommes ci-dessus portent sur des blocs réinitialisés, sans prétendre
être une courbe de compte continu avec compounding.

| Scénario sur les trois blocs réservés | Breakout | Retour à moyenne |
|---|---:|---:|
| Base : 4,5 bps frais/côté, 2 bps slippage/côté | −56,99 $ | −74,46 $ |
| Stress : frais doublés et 5 bps slippage/côté | −77,89 $ | −106,50 $ |
| Entrée retardée d’une heure supplémentaire | −61,64 $ | −80,16 $ |
| Zéro frais, zéro slippage et zéro funding ; infrastructure conservée | −37,46 $ | −59,60 $ |

Même le contrôle sans coûts de trading perd sur chaque bloc réservé. Il ne
constitue pas une borne mathématique du PnL : les stops et les trajectoires
peuvent changer lorsque les prix d’exécution changent. Tous les résultats des
48 simulations (2 règles × 4 scénarios × 6 blocs) sont conservés.

Limites : prix OHLC, profondeur d’exécution inconnue, slippage hypothétique,
funding traité comme coût adverse absolu sur les positions reportées, perte
intrahoraire de portefeuille inconnue. Les gaps au-delà du stop prennent le
prix d’ouverture défavorable. Le superviseur de recherche vérifie les seuils
de portefeuille à fréquence horaire ; il ne remplace pas celui du runtime.
Les résultats ne qualifient donc pas une exécution A, même s’ils étaient positifs.
Ces fenêtres réservées sont désormais consommées : ne pas les recycler comme
nouveau test indépendant après optimisation.

### Funding : six blocs de 30 jours, pas une annualisation instantanée

Benchmark fixe favorable : 500 $ short perp et 500 $ spot, sans frais, basis,
coût de rebalancement, financement ou risque des actifs enveloppés. Le funding
est calculé depuis les taux historiques horaires, sur 500 $ de notionnel constant.
Les marchés spot UBTC/UETH/USOL ne sont pas assimilés automatiquement aux actifs
natifs ; l’appariement économique resterait à qualifier.

| Coin | Plus faible revenu funding sur un bloc | Plus élevé |
|---|---:|---:|
| BTC | −0,09 $ | 3,74 $ |
| ETH | 0,26 $ | 3,81 $ |
| SOL | −3,50 $ | 3,65 $ |
| HYPE | 2,43 $ | 4,93 $ |

Même choisir rétrospectivement le meilleur coin et le meilleur bloc donne
moins de 0,5 % des 1 000 $ initiaux avant coûts. Ce calcul rejette la variante
testée pour +30 % ; il n’épuise pas toutes les stratégies de basis ou tous les
autres actifs possibles. Les quatre revenus ne s’additionnent pas sur le même
capital de 1 000 $ : chacun suppose son allocation complète de 500/500 $.

### Paniers : tenir compte des jambes réellement achetables

Lecture des métadonnées, regroupement des binaires par référence, durée de
moyennage, échéance, venue et collatéral identiques. Test d’achat YES au strike
inférieur + NO au strike supérieur, et du panier complet de YES d’une question
récurrente BTC incluant le fallback. Le minimum de payoff supposé est 1 token.

32 carnets lus pour 22 paniers : 16 coûts visibles supérieurs à 1, 6 paniers
sans ask sur au moins une jambe. La meilleure marge visible est encore
**−0,40097 par bundle**, à frais nuls. Les captures REST sont séquentielles et
ne prouvent pas une exécution simultanée ; aucune anomalie n’a nécessité un
second test de causalité. Ce résultat ne valide pas un arbitrage split/sell,
qui n’a pas été simulé dans cette vague.

## Piste L4 : nouvel accès possible, restant à éprouver

0xArchive expose des routes HIP-4 de checkpoint, diffs ordonnés et historique.
Son catalogue public renvoie des entrées L4 pour les huit coins actuels
`#17150` à `#17181`, dont les paires BTC/ETH/SOL/HYPE. C’est une affirmation
de couverture du fournisseur, distincte de l’accès aux données et de leur
qualification. [Couverture par famille](https://docs.0xarchive.io/venue-coverage),
[preuve du catalogue capturé](archive_coverage.json).

Le plan gratuit annonce 50 000 crédits mensuels, les 30 derniers jours et
l’accès aux routes de données ; il exige un compte et une clé. Il permet
d’envisager un petit test, sans présumer de la capacité d’une collecte L4 continue.
Le forfait Build est affiché à 49 $/mois ; des exports L4 séparés sont annoncés
à 4 $/Go, avec minimum de 12,50 $. Les coûts et la couverture doivent être
vérifiés pour une sélection précise avant achat.
[Tarifs 0xArchive](https://0xarchive.io/pricing),
[conditions du démarrage gratuit](https://docs.0xarchive.io/free-crypto-data-api).

Deux alternatives restent documentaires : QuickNode L4 HIP-4, déjà décrit dans
le diagnostic précédent, et HyperliquidRPC, qui annonce un L4 à 49 $/mois hors
promotion initiale et une clé d’évaluation sur demande. Le support HIP-4 précis
de ce dernier n’a pas été confirmé. Aucun compte créé, aucun tiers contacté,
aucun abonnement payé. [L4 HyperliquidRPC](https://hyperliquidrpc.com/docs/streams/l4-book),
[accès et prix](https://hyperliquidrpc.com/pricing).

Le contrôle réel sans clé sur 0xArchive retourne **HTTP 401**. Aucune clé
configurée trouvée dans les emplacements examinés ; l’utilisateur confirme
« Aucun accès connu ». La documentation ne suffit donc pas à produire un GO.
[Preuve d’accès](archive_access_probe.json).

## Implémentation prête et prochain déclencheur

Le nouveau reconstructeur immuable conserve la priorité reçue et l’insertion
`insert_before`, contrôle tailles/profondeur, identités, ordre des diffs et
rapproche les deux checkpoints. Il bloque les cas ambigus. La sonde vérifie
YES puis NO, sur une fenêtre maximale de 60 s, sans ordre exchange et sans clé
dans les arguments de processus. Les données ne deviennent jamais A par simple
ajout d’un drapeau. [Contrat L4 utilisé](https://docs.0xarchive.io/rest-api/order-books-l4).

**Déclencheur nécessaire : une clé gratuite 0xArchive fournie dans un fichier
protégé hors Git.** Ensuite exécuter la sonde, examiner les raws et la
réconciliation. En cas de succès, qualifier continuité, timestamps, dualité,
fills et fraîcheur ; en cas d’échec, conserver la raison et tester l’autre accès
disponible. Un rapprochement de checkpoints ne sera pas présenté comme GO maker.
[Commande et procédure](../../docs/L4_RESEARCH.md).

La sonde est installée séparément sur le serveur ; chemin, manifestes et test
sans clé dans [la preuve d’installation](server_research_install.json). La
release runtime `b44a0baa421ac7f2` demeure inchangée. Aucun conteneur relancé.
163 tests passent, lint et typage strict sur 44 modules passent.

## Artefacts

- [Données historiques et requêtes](history_manifest.json).
- [Développement/contrôle](development_summary.json), [test réservé](holdout_summary.json).
- [Paniers et captures](basket_summary.json).
- [Sonde bloquée sans clé](l4_probe.json), [code livré](implementation_manifest.json).

Chaque JSON publié possède son SHA-256. Les cycles détaillés sont dans les
chemins `data/search_2026-09-06/{development,holdout}` référencés et checksumés
par les résumés. Les anciens dépôts et leurs données sont restés en lecture seule.

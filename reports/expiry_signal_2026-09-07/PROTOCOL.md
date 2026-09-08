# Référence fin d'échéance : test exploratoire figé

Les 115 labels et la borne gagnante ont déjà été consultés. Ce test est
exploratoire, jamais une validation hors échantillon. Figer la règle avant son
PnL évite les modifications après résultat, sans effacer cette contamination.

À expiry−300 s, utiliser seulement la dernière référence mainnet journalisée
dans la minute précédente. Aucun score legacy. BTC/ETH/SOL : OKX SPOT USDT,
midpoint bid/ask positif non croisé, horodatage exchange antérieur à la
journalisation et âgé au plus de 60 s à la décision. HYPE exclu : la référence
qualifiée dans sa devise USDC manque dans ces logs. Pas de moyenne USD/USDT.
Les références sont issues de logs conditionnés par la détection d'opportunités
legacy : biais de sélection persistant, aucun GO possible sur cet échantillon.

Benchmark digital existant sans drift, volatilité des 168 dernières heures
complètes Hyperliquid, échelles 0,75/1/1,25. Évaluer le prix OKX multiplié par
0,9985 et 1,0015, soit ±15 bps d'incertitude hypothétique sur le prix natif.
Cette marge n'est pas une borne empirique garantie du basis ou de la latence.
Pour chaque côté, minimum des six probabilités, puis haircut 3 points ; marge
exigée 5 points après retenue prudente 20 bps sur le payout. Ask entre 0,15 et
0,85. Réutiliser sans changement `select_intent` du test taker quotidien.

Carnet décision : dernier reçu avant décision, événement/réception âgés ≤60 s,
même si vide (aucune recherche rétroactive d'un ask favorable). Premier carnet
reçu entre +1 s et +60 s pour l'exécution, entre +60 s et +120 s pour le retard.
Prix payé = maximum des asks décision/exécution ; rejet si vide, stale,
au-dessus de la limite ou profondeur insuffisante. Simulation optimiste de
fills, aucune preuve de file. Quantité entière arrondie pour ~10 $ : ≤11 $ et
≤10 % de la taille affichée à décision ET exécution. Au plus un côté par
contrat, quatre contrats par échéance, capital total 1 000 $, sans levier.

Paiement officiel, retenue 7 bps centrale ; stress 20 bps et coût supplémentaire
0,01 par unité. Conserver jusqu'à règlement. Aucun ordre ni frais réels payés.
Enveloppe entière 41 jours pour le proxy /30 jours, soustraire 20 $/mois infra.
Rapporter tous les signaux, les rejets et les résultats, y compris négatifs ;
aucune hausse de taille destinée à atteindre la cible. Un résultat négatif ou
rarissime suspend cette règle ; un résultat positif nécessite au minimum un
autre échantillon indépendant et une qualification native avant promotion.

Source officielle consultée le 7 septembre 2026 :
[contrats et interpolation du mark](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/contract-specifications.md).
Ces spécifications distinguent aussi les perps USDT et HYPE/PURR USD.

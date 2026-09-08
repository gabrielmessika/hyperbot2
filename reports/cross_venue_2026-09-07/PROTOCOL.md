# Écarts entre plateformes — protocole avant acquisition complète

BTC/ETH/SOL, Hyperliquid et perpétuels Binance USDC, même unité de règlement.
Période du 10 mars au 6 septembre 2026 UTC exclusif. API publique GET Binance,
sans clé, plafond 40 requêtes / 20 Mo. Un probe BTC de deux bougies confirme
l'accessibilité ; aucun rendement inter-plateformes calculé avant ce protocole.
Frais sans remise supposés conservateurs : HL 4,5 bps, Binance 5 bps par côté ;
slippage 2 bps par jambe et côté. Stress double frais / 5 bps slippage.
Tarif du compte non vérifié : hypothèse de recherche, pas qualification live.

Deux règles distinctes, comparaison de deux perpétuels et quantités de coin
strictement égales/opposées (pas simplement des notionnels égaux).

1. Écart transitoire : ratio des clôtures HL/Binance moins sa médiane des 168
   heures antérieures. Si |écart| >= 30 bps, vendre la jambe chère, acheter
   l'autre. Entrée à l'open suivant, sortie 6 h plus tard ; 1 h/24 h secondaires.
   Espacement des événements 25 h minimum par coin.
2. Différentiel de funding : somme des funding payés dans les dernières 24 h
   HL moins Binance. Si |différentiel| >= 10 bps/jour et |écart de prix à la
   médiane précédente| < 20 bps, vendre la jambe au funding le plus élevé.
   Détention fixe 72 h, espacement 73 h. Le passé ne prédit pas avec certitude
   les paiements futurs. Aucun taux futur utilisé dans le signal.

Funding réellement payé pendant chaque position, horodatages natifs, exclusion
du paiement à l'entrée et inclusion de celui à la sortie (proxy d'ordre
d'exécution explicite). Funding Binance valorisé au markPrice fourni, HL à
l'open horaire. Évaluation brute sans coûts/funding puis nette, coût stressé,
retard entrée/sortie 1 h, funding adverse (chaque jambe paie la valeur absolue).
PnL rapporté à la somme des deux notionnels d'entrée, sans levier implicite.

Exiger >=30 événements sur >=20 dates, PF>1,2, net positif dans chaque stress,
IC temporel 97,5 % (deux règles) avec borne basse >0, >=4/6 blocs positifs,
positif après retrait du meilleur événement pour approfondir. Pas de sélection
opportuniste d'un horizon, coin ou seuil. Données HL déjà consultées : étude
exploratoire, pas validation indépendante. Les clôtures/opens de trades ne
prouvent ni synchronisation des quotes ni exécution simultanée : candidat
positif exigera contrôle avec données plus fines et simulation capital/risque.

Sources : [marché public Binance](https://github.com/binance/binance-futures-connector-python/blob/main/binance/um_futures/market.py),
[tarifs Binance](https://www.binance.com/en-BH/fee/futureFee),
[tarifs HL](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees).

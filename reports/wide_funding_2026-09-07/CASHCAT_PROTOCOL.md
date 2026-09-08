# CASHCAT : vérifier le hedge, le PnL et la marge avant de retenir le portage

Candidat sélectionné par le filtre enregistré sur 20 coins, pas par son prix.
Funding du 7 août au 6 septembre déjà observé : sélection exploratoire assumée.
Un spot CASHCAT/USDT est annoncé par KuCoin depuis le 15 juillet 2026 ;
CASHCAT n'apparaît pas dans le spotMeta HL archivé et Binance indique ne pas
le proposer en spot. Sources natives/annonces à confirmer, sans ouvrir de compte.

Acquisition publique bornée : HL OHLCV 1 h et funding manquant du 15 juillet
au 7 août ; KuCoin OHLCV 1 h, métadonnées de symbole/devise et carnet public ;
USDC/USDT spot Binance 1 h pour convertir les prix et PnL. Dix requêtes GET
externes maximum, six /info HL, zéro clé. Pas de trou imputé ni mélange de
tokens homonymes. Comparer contrats/réseaux annoncés et cohérence de prix ;
une identité non qualifiée interdit tout GO même si le calcul exploratoire passe.

Deux segments fixés avant prix : 16 juillet–7 août (ancien), 7 août–6 septembre
(déjà sélectionné sur funding), UTC. Quantity fixe identique long spot / short
perp, bornée par 500 $ de budget spot frais inclus et 500 $ de notionnel short
initial, arrondie vers le bas au plus gros lot commun. 500 $ de marge réservée
sur HL, pas de levier ajouté et pas de transfert entre plateformes en cours.
Funding payé chaque heure sur la quantité fixe × prix horaire HL (proxy oracle).
Spot USDT converti en USDC avec cours historique USDC/USDT, coûts de conversion
explicitement séparés et jamais supposés nuls dans un scénario net final.

Frais de recherche conservateurs spot 30 bps par côté, perp 4,5 ; slippage
spot 5 bps et perp 2. Stress double frais et slippage spot 10/perp 5 bps.
Ne pas supposer un tarif de compte qualifié ou remise. Sensibilités funding
recevable réduit de moitié, entrée/sortie retardées 24 h, coût fixe 20 $/30 j
(budget hypothétique). Horaires de sortie doivent exister dans les raw.

Contrôler séparément PnL de chaque jambe, funding, coûts, equity totale, pire
excursion de marge short à partir des highs horaires. Le maximum de levier
actuel HL est 3 : vérifier la table de marge native. Utiliser un stress prudent
de maintenance 20 % pour le filtre, pas le présenter comme formule exacte de
liquidation. Toute breach historique du stress bloque le candidat. Comparer
gain total et besoin en capital, pas seulement rendement sur marge utilisée.

Pas de GO avec seulement un mois de taux favorables sélectionné a posteriori.
Un candidat doit au minimum rester positif net dans l'ancien segment et les
stress, survivre à la marge, puis disposer de preuves d'identité, frais,
liquidité/exécution et observation prospective. Si le hedge ou l'économie
échoue, suspendre et passer à un mécanisme différent sans achat.

Sources : [annonce KuCoin](https://www.kucoin.com/ja/announcement/jp-cash-cat-cashcat-listed-on-kucoin),
[profil KuCoin](https://www.kucoin.com/price/CASHCAT),
[API publique klines](https://www.kucoin.com/docs-new/rest/ua/get-klines),
[absence spot Binance](https://www.binance.com/en-IN/how-to-buy/cash-cat).

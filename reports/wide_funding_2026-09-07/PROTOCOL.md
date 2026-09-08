# Portage : filtre économique sur un univers élargi

But : vérifier à coût nul si des fundings plus élevés que ceux des quatre
majors offrent une marge qui mérite une vraie simulation spot/perp. Ce filtre
n'est pas un backtest rentable : le funding seul ignore le prix du hedge,
les contraintes de marge et les coûts de rééquilibrage.

Univers figé : 20 premiers perpétuels core non délistés par volume notionnel
24 h du snapshot public `data/wide_funding_2026-09-07/meta.json`, hors
BTC/ETH/SOL/HYPE, volume >=10 M$. Snapshot déjà vu, incluant les taux instantanés ;
ces taux ne servent pas au classement. Biais de survivance/univers actuel
explicitement accepté pour le filtre exploratoire, jamais pour une validation.
Pas de HIP-3 ni marché de deployer.

Acquisition publique fundingHistory du 7 août au 6 septembre 2026 UTC exclusif,
au plus 3 requêtes par coin et 60 au total, client existant sans clé.
Conserver les trous et dates de lancement, pas d'imputation à zéro.

Mesures fixées : somme signée, minimum/maximum horaire, sommes par blocs 7 j,
fraction des heures positives, contribution des 5 plus grands taux positifs.
Approximation de revenu : 500 $ de notionnel short constamment rééquilibré
gratuitement × somme des taux, 500 $ réservés au spot. Ce n'est pas le PnL d'une
quantité fixe de coin et ce n'est pas une stratégie mise en œuvre.
Un taux négatif n'est pas converti en revenu sans hedge short spot qualifié.

Approfondir seulement si couverture 720 h complète, proxy positif >=30 $ sur
30 j, au moins trois des quatre blocs complets de 7 j positifs, et revenu
positif après retrait des cinq meilleurs paiements. Seuil économique de tri,
pas confiance statistique. Ensuite seulement chercher spot réellement négocié,
prix du hedge et coûts, ancienne période gratuite et stabilité prospective.
À défaut, suspendre ce portage sur cet univers, sans abaisser les seuils.

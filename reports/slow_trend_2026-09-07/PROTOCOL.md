# Tendance lente et allocation selon volatilité passée

Nouvelle hypothèse enregistrée avant PnL : suivre la direction propre à
chaque actif sur 30 jours et réviser les quantités une fois par semaine.
Réduire le poids des actifs volatils, sans retrait nominatif de perdants,
augmentation du cap, martingale ou redémarrage après arrêt.

Chaque lundi 00 UTC, avec au moins 721 bougies horaires antérieures,
direction = signe(close[i-1]/close[i-721]-1). Rendement exactement nul :
aucune intention. Volatilité = écart-type échantillonnal des 30 rendements
logarithmiques quotidiens terminés avant l'entrée, calculés à intervalles
de 24 heures. Poids brut = 1/max(0,01, volatilité). Normaliser entre les
actifs ayant une intention à cette date. Le plancher est fixé à 1 % de
volatilité quotidienne pour éviter un poids explosif ; aucun réglage après PnL.

Maintien 168 heures, remplacement hebdomadaire des intentions ; compensation
native des anciennes/nouvelles cibles. Le poids est celui connu à la date
du signal, également lorsque l'entrée est retardée. Le warmup de 30 jours
repousse le premier panier 2025 au 3 février : ce test ne prétendra donc
pas rejouer le choc du 19 janvier ayant invalidé la stratégie précédente.

Contrôle prédéfini : mêmes directions, calendrier et horizon, poids égaux.
Comparer les deux règles aux caps bruts fixes 0,5x et 1,5x. Un seul compte
de 1 000 $, pas de multiplicateur selon les gains/pertes. Réutiliser le
moteur natif et ses budgets ; limiter chaque actif à un tiers du budget.
Une fraction plafonnée reste inutilisée, sans redistribution opportuniste.

Trois panneaux existants : Hyperliquid18 /204 jours, Hyperliquid15 mêmes
dates, Binance15 /année2025. Aucun nouvel appel ou achat. Les données
Binance restent un transfert, avec les hypothèses de coûts/lots/ticks
Hyperliquid de référence explicitement séparées des données de marché.

Cinq scénarios usuels, central4,5bps/2bps, coûts9bps/5bps, retard1h,
funding adverse, zéro coût descriptif avec ticks conservés. Infra marginale
0 et sensibilité hypothétique20 $/30jours. Seuil global30 %, pertes ouvertes,
overshoots, petits ordres reportés et éventuels résidus terminaux conservés.
120 simulations : trois panneaux, deux règles, deux caps, cinq scénarios,
deux sensibilités d'infrastructure. Tous les résultats seront publiés.

Avant calcul, tester causalité des signaux/poids, direction, normalisation,
cap par actif et comportements invalides. Préserver exactement les anciens
résultats lorsque les poids optionnels ne sont pas fournis ; vérifier des
références complètes natives et de transfert, pas seulement le PnL final.

Filtre exploratoire : quatre scénarios payants positifs sur les trois
panneaux, enveloppes <=30 %, pas d'incident de marge ni résidu terminal.
Évaluer séparément la cible moyenne de10 % mensuels équivalents après coûts.
Une amélioration d'un seul panneau ne vaut pas généralisation. Aucun GO
automatique : périodes déjà explorées, essais multiples, proxies d'exécution
et absence de validation prospective restent à considérer.

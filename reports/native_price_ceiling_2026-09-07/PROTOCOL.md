# Plafond de prix d'une règle existante sur la cohorte native disponible

Contrôle borné motivé par la qualification nouvelle de l'historique natif 2025.
Aucune nouvelle acquisition et aucune recherche de paramètres. L'univers est
défini par la couverture native 2025 complète et sans volume nul : ARB, BNB,
DOGE, INJ, LINK, NEAR, UNI, WLD, XRP. XMR et ZEC sont exclus par disponibilité,
avant ce calcul. Leurs anciens résultats Binance sont connus : ce changement
d'univers n'est pas une validation indépendante de la stratégie précédente.

Deux panneaux Hyperliquid : 2025 en bougies 4 h, et les 204 jours existants
de 2026, regroupés par blocs consécutifs de quatre bougies horaires complètes.
Ne pas interpoler d'heures manquantes. Séparer la qualification des sources
de toute conclusion sur la disponibilité réelle des fills ou des oracles.

Règle acheteuse conservée : chaque lundi 00 h UTC, sélectionner les trois
volatilités journalières les plus faibles et les trois plus fortes sur les
trente rendements journaliers révolus ; acheter ces six actifs à poids
notionnels égaux, garde 168 h. Égalité à une frontière : abstention. Contrôle :
acheter les neuf actifs aux mêmes dates. Aucun contrôle inversé ni autre règle.
Volatilité = écart-type échantillonnal de trente rendements logarithmiques,
avec 31 clôtures distantes de 24 h, toutes antérieures à l'entrée.

Utiliser le calculateur existant `leg_return`, indexé en barres, horizon 42
barres de 4 h. Publication de trois scénarios, funding fixé à zéro :
central frais/slippage 4,5/2 bps par côté ; coûts renforcés 9/5 ; entrée et
sortie retardées d'une barre (4 h) avec coûts centraux. Publier aussi le prix
brut. Le retard de 4 h remplace explicitement le stress de 1 h indisponible ;
ne pas déclarer les scénarios identiques aux anciens tests horaires.

Pour un panier acheteur et le scénario défavorable qui transforme chaque
funding en débit, le résultat sans funding est un plafond sous le même proxy
de prix. S'il est négatif, inclure ces débits ne peut pas le rendre positif.
Cela ne borne pas le scénario de funding signé, où des recettes sont possibles.
Ce diagnostic ne remplace pas un portefeuille, ne mesure pas son drawdown
et ne doit pas être converti en rendement mensuel ou en dollars de capital.

Filtre pour justifier une collecte de funding : au moins vingt paniers par
panneau ; plafonds centraux/coûts/retard positifs dans les deux panneaux ;
borne inférieure bootstrap centrale 95 % positive (7 jours, 5 000 réplications,
calendrier complet incluant les jours sans événement). Le benchmark est
descriptif. Même si le filtre passe, aucun GO : funding signé et défavorable,
capital de 1 000 $, limites de drawdown 20/30 %, minimums, lots, ticks et marge
restent à qualifier avant une éventuelle promotion.

Les périodes et les résultats associés ont déjà été consultés ; les moyennes
ne constituent pas une découverte indépendante. Conserver les échecs précédents
et l'univers onze initial. Plafond de travail : un calcul fixe sur ces deux
panneaux, une reproduction et un contrôle des agrégats, pas une nouvelle
campagne de variantes. Aucun achat, ordre réel, service ou serveur modifié.

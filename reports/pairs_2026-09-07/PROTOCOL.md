# BTC/ETH — protocole exploratoire avant calcul

7 septembre 2026. Hypothèse : un écart inhabituel du prix ETH relativement
au BTC se résorbe sur quelques heures et permet de couvrir les coûts de deux
positions. Les 180 jours horaires existants ont déjà été consultés ; aucun
bloc de cette étude ne constitue une nouvelle preuve hors échantillon.
Pas de recherche d’autres paires, de grille de paramètres ou de levier ajouté.

## Définition figée

- Données : BTC et ETH, OHLC 1 h et funding, 10 mars au 6 septembre 2026
  00:00 UTC exclu. Réutiliser le lecteur et les contrôles checksumés existants.
- À chaque clôture horaire, ajuster `log(ETH) = alpha + beta * log(BTC)` par
  moindres carrés sur les 720 clôtures précédentes, hors clôture du signal.
  Écart standardisé `z = (log(ETH) - alpha - beta*log(BTC))/sigma` ; sigma
  est l’écart-type des résidus de la fenêtre d’ajustement (n−2).
- Signal si `2 ≤ |z| < 4`, `0,25 ≤ beta ≤ 4`, sigma strictement positif.
  Un signal au maximum toutes les 25 heures ; pas de trades superposés.
  Les paramètres alpha/beta/sigma sont gelés jusqu’à la sortie : un changement
  de moyenne estimée ne peut pas fabriquer un retour de l’écart.
- z positif : short ETH, long BTC ; z négatif : long ETH, short BTC.
  Notionnel BTC = beta × notionnel ETH à l’entrée ; quantités ensuite fixes.

## Test de l’hypothèse

Étude des événements distincts, entrée à l’ouverture horaire suivante,
mesure aux ouvertures +1 h, **+6 h (critère principal)** et +24 h.
Publier l’évolution de l’écart avec modèle gelé et le rendement de la paire
par dollar de notionnel brut engagé, avec et sans 6,5 bps par exécution
(4,5 frais + 2 glissement), hors funding pour ce diagnostic normalisé.
Les événements dont +24 h dépasse la fin des données sont exclus.
Le délai nominal représente une frontière de bougie, pas une latence mesurée.

Publier les cinq blocs de 30 jours après 30 jours de chauffe, bêta, corrélation
des rendements horaires et persistance AR(1) des résidus d’ajustement.
L’AR(1) et sa demi-vie éventuelle sont descriptifs : ni test de cointégration,
ni preuve de convergence future. Comparer le diagnostic empirique à cette
apparence de réversion, sans filtrer après lecture des résultats.

## Simulation économique d’une seule règle

Entrée après signal, sortie à l’ouverture suivant une clôture où `|z| ≤ 0,5`
ou franchissement du zéro, ou `|z| ≥ 4`, ou perte marquée nette ≥2,50 $ ;
sortie temporelle à 24 heures. Sortie des deux jambes ensemble supposée,
non garantie par les données horaires. Liquidation à la dernière clôture du
bloc mensuel. Aucun stop intrabougie fictif, aucune hausse de taille après perte.

Capital 1 000 $ ; 50 $ maximum par jambe, notionnel ETH également plafonné
par `2,50 / (sigma*(4−|z|))` comme estimation locale du risque de spread.
Quantités arrondies vers le bas au pas des métadonnées publiques ; chaque
jambe doit rester ≥10 $. La limite de risque est une règle de sortie observée
à l’heure, pas une garantie de perte maximale. Arrêt journalier à −15 $,
réduction de taille à 8 % de drawdown mensuel, arrêt dur à 12 % depuis le pic.

Scénarios fixes : base 4,5 bps de frais +2 bps de slippage par exécution ;
stress 9+5 bps ; retard d’une heure supplémentaire avec coûts de base ;
contrôle zéro frais/slippage/funding. Base et stress débitent la valeur
absolue du funding de chaque jambe, sans crédit. Publier également le funding
signé comme attribution indicative, sans en faire un filtre de signal.
Le prix d’ouverture remplace l’oracle historique absent : approximation signalée.
Une position portée est chargée au début de chaque heure avant sa fermeture ;
une nouvelle entrée n’est chargée qu’à partir de l’heure suivante.
Infrastructure : 20 $ par bloc de 30 jours, y compris contrôle zéro trading.

## Décision et incertitude

Bootstrap par blocs mobiles de 7 jours, 5 000 répétitions, seed 20260907,
sur les journées calendaires y compris sans trade. Pour l’événement principal,
rééchantillonner conjointement sommes de rendements et nombres d’événements ;
intervalle percentile 95 % de la moyenne par événement. Publier les résultats
1/24 h sans remplacer le critère principal par le meilleur horizon.

Poursuite vers une validation sur données inédites seulement si ≥30 événements,
borne inférieure 95 % du rendement principal après frais/slippage >0,
simulation de base positive après infrastructure, ≥4/5 blocs positifs après
infrastructure et PF net des cycles >1,20. Sinon, hypothèse exploitable non
confirmée dans cette définition. Un résultat favorable reste exploratoire,
sans promotion du bot ni GO économique.

Budget : une requête publique de métadonnées, aucun accès privé nécessaire,
aucun service serveur, 30 minutes CPU maximum, pas de nouvelle collecte.
Versionner protocole, code, résumés et checksums ; détails sous `data/`.

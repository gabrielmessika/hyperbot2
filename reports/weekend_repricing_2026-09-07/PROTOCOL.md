# Repricing du week-end sur actions HIP-3

Nouvelle hypothèse structurelle, aucun indicateur optimisé : les mouvements du
perpétuel pendant la fermeture du marché régulier américain peuvent se résorber
à sa réouverture. Ils peuvent aussi refléter de vraies nouvelles ; le cours
du vendredi n'est pas supposé être une juste valeur ou une borne d'arbitrage.

Univers fixé avant rendements : xyz:TSLA, xyz:NVDA, xyz:HOOD, xyz:META, xyz:AMZN.
La disponibilité actuelle a été vérifiée par metaAndAssetCtxs public, aucun
historique de rendement consulté pour ces marchés dans cette famille. Les
anciennes données BOT05/TRIDENT ne servent pas à choisir des paramètres.
OHLCV/funding natifs horaires demandés du 12 février au 6 septembre 2026 UTC
exclusif, 60 requêtes maximum / 50 Mo / zéro achat. Historique de 206 jours
choisi pour rester sous les 5 000 bougies natives compte tenu de l'heure de
collecte. Toute grille incomplète doit être signalée avant calcul, sans imputation.

Référence : close du perp sur la bougie du vendredi 15:00–16:00 New York.
Signal : close de la bougie du dimanche 11:00–12:00 New York, comparée à cette
référence. Si |variation| >=1 %, fade : vendre le mouvement haussier ou acheter
le mouvement baissier. Entrée à l'open du dimanche 12:00, sortie lundi 10:00,
après l'ouverture régulière de 09:30. Un événement par marché/week-end.
Contrôle enregistré : suivre le même mouvement avec les mêmes dates ; les deux
directions comptent comme hypothèses testées, aucune inversion postérieure cachée.

Exclure les week-ends dont le vendredi ou le lundi est férié de marché :
16 février, 3 avril, 25 mai, 19 juin, 3 juillet 2026. Le 7 septembre est férié
et sa sortie est de toute manière hors période. ZoneInfo America/New_York,
gestion explicite du changement d'heure du 8 mars. Pas de prix actions externes
supposés disponibles, ni confusion entre fermeture régulière et absence de news.

Frais supposés 9 bps/côté, slippage 2 ; stress 18/5. Le 18 bps inclut la borne
actuelle de supplément deployer de 300 % sur 4,5 bps core, sans remise growth
ou de compte. Ce sont des hypothèses de recherche : les frais historiques exacts
restent à qualifier avant GO. Funding signé payé chaque heure, prix horaire
comme proxy ; stress de funding adverse et retard d'entrée/sortie 1 h. Contrôle
zéro coût et zéro funding. Unité : bps du notionnel d'entrée de chaque événement.

Gates pour approfondir gratuitement : 30 événements et 20 week-ends distincts,
net positif dans les quatre scénarios, PF>1,2, intervalle bootstrap 97,5 % de
moyenne avec borne basse >0 (rééchantillonnage de blocs de trois week-ends,
5 000 réplications ; deux règles), >=5 des 7 blocs de 30 jours positifs, net
positif après retrait du meilleur événement. Pas de sélection d'un ticker,
jour, seuil ou direction après résultats. Les recherches antérieures restent
une source de sélection. Toute réussite exigerait validation supplémentaire,
contrôle des frais/oracles/événements corporate, tailles et risques du compte.

Sources : [calendrier NYSE 2026](https://www.nyse.com/publicdocs/nyse/ICE_NYSE_2026_Yearly_Trading_Calendar.pdf),
[tarifs HL/HIP-3](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees),
[growth mode](https://paragraph.com/@hyperliquid/hip-3-growth-mode).

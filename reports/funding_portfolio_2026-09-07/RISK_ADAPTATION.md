# Adaptation d'exposition après le premier calcul

Le lot préenregistré 0,5x/1x/1,5x est conservé. À 0,5x, les quatre scénarios
payants sont positifs, mais l'enveloppe OHLC dépasse 20 %, maximum environ
20,97 % avec infra. Les tailles supérieures déclenchent l'arrêt du compte.

Tester un seul nouveau plafond **0,4x**, réduction ronde de 20 % depuis 0,5x,
avec les quatre règles et les mêmes scénarios d'exécution/infra. Aucun autre
seuil, horizon, sens ou actif ajusté. Conserver le plafond d'un tiers par actif
et la limite de drawdown de 20 %. Les arrondis et rejets minimum d'ordre peuvent
modifier le nombre de positions ; recalcul complet, aucune multiplication du
profit seul.

Cette calibration de risque utilise des données déjà examinées. Elle ne
constitue pas une réplication ni une optimisation validée hors échantillon.
Même si le résultat satisfait rendement et risque sur ces 52 jours, il faudra
un autre historique gratuit et une qualification d'exécution avant tout GO.
Pas de recherche supplémentaire de taille pour approcher exactement 20 %.

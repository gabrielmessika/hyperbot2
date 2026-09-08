# Réplication exploratoire COIN/MSTR avant lecture de leurs prix

Résultat initial déjà connu : fade +118,47 bps/event, coûts stressés +94,46,
19 événements sur 11 week-ends. 2 073,53 des 2 250,88 bps cumulés viennent de
HOOD ; les gates initiales échouent (échantillon et seulement 4/7 blocs positifs).
Il ne s'agit donc pas d'une promotion obtenue grâce au protocole initial.

Nouvelle vérification de portabilité, motivée explicitement par cette observation :
appliquer la règle INCHANGÉE aux deux contrats xyz:COIN et xyz:MSTR. Ces symboles
étaient présents dans les métadonnées vues mais leurs OHLCV/funding et résultats
n'ont pas été consultés dans cette campagne. Ne pas ajouter d'autres symboles
si l'extension échoue, ne pas sélectionner HOOD seul et ne pas changer le seuil.

Mêmes dates 12 février–6 septembre, calendrier, variation >=1 %, Sunday 12:00
vers Monday 10:00 New York, frais 9/18 bps, slippage 2/5, funding et retard.
Toujours conserver le contrôle follow. Rapporter la réplication séparément de
l'original ; l'agrégation éventuelle ne peut remplacer un échec de réplication.
Mêmes gates, dont 30 événements /20 week-ends et 5/7 blocs positifs. Corriger
localement les deux sens, sans prétendre effacer la sélection de cette extension.
Acquisition gratuite bornée à 24 requêtes, aucune nouvelle dépense.

Même un succès serait un candidat à vérifier : données exactes d'exécution,
frais, stocks de marge, événements corporate, risque et observation prospective.
L'ancien résultat reste `HYPOTHESIS_NOT_CONFIRMED`, quelle que soit cette passe.

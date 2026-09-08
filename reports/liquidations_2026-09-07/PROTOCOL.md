# Protocole fixé avant étude des rendements

## Hypothèse et données

Des ventes forcées massives de positions longues peuvent provoquer un excès
baissier suivi d'un rebond sur six heures. BTC/ETH perpétuels uniquement.
Ce test exploratoire réutilise les prix et funding déjà consultés : aucun OOS
indépendant, aucune autorisation de trading ou garantie de rendement.

Période fixe : 10 mars 2026 00:00 au 6 septembre 2026 00:00 UTC exclusif,
180 jours ; les 30 premiers jours servent de chauffe. Demander les volumes de
liquidations et OI horaires par blocs de 30 jours, 24 requêtes. Si le fournisseur
refuse cette profondeur, arrêter et rapporter la restriction, sans déplacer
la fenêtre pour obtenir un résultat favorable. Budget total avec audit initial :
100 requêtes, 50 Mo, 30 minutes d'acquisition ; aucun achat.

Les agrégats sont étiquetés au début de l'heure et ne deviennent utilisables
qu'après sa fin. Exclure strictement la borne de fin, même si l'API la renvoie.
Pas de zéro implicite : quantiles calculés exclusivement sur les heures positives
effectivement publiées des 30 jours précédents, avec au moins 60 observations.
L'absence de couverture dédiée aux liquidations limite toute inférence.

## Sélection unique et gelée

À la clôture d'une heure, événement si toutes les conditions suivantes passent :

- Volume liquidé long supérieur ou égal au quantile empirique 95 % des volumes
  longs strictement positifs des 30 jours précédents (rang supérieur).
- Volume long ≥ 100 000 $ BTC, ≥ 50 000 $ ETH ; au moins cinq liquidations longues.
- Au moins 80 % du volume liquidé est long ; variation close/open de l'heure ≤ −0,5 %.
- Un seul événement par actif sur 25 heures, priorité chronologique.

Entrée théorique à l'open de l'heure suivante ; sortie principale à six heures.
Diagnostics secondaires à une et 24 heures ; ne pas choisir le meilleur après coup.
Exclure à la sélection les événements sans 25 heures de prix futurs disponibles
pour que les stress et horizons portent sur les mêmes épisodes.
OI : diagnostic seulement, variation des moyennes horaires en contrats de l'heure
du choc et de l'heure précédente. Aucun usage de la moyenne avant la fin du bucket.

## Contrôle du mécanisme et coûts

Pour chaque événement, chercher au maximum trois heures témoins du même actif
dans les 30 jours précédents, dont les sorties à 24 h sont antérieures au signal.
Elles doivent avoir un volume long publié positif inférieur ou égal à la médiane
passée, une baisse horaire à ±0,25 point de pourcentage de celle du choc et une
volatilité (écart-type des 24 rendements horaires précédents) entre 0,5 et deux fois
celle du choc. Trier par proximité de baisse, puis chronologie. Espacer les témoins
d'un événement de 25 h. Ne jamais choisir les témoins sur leur rendement futur.
Un événement sans témoin reste dans le résultat brut, absent de l'effet apparié.
Les témoins peuvent être réutilisés entre événements : aucune indépendance prétendue.

Coûts de base taker : 4,5 bps de frais + 2 bps de slippage par côté, proportionnels
aux notionnels effectivement achetés/vendus. Funding conservateur : somme des
valeurs absolues horaires, oracle approximé par l'open, sur les échéances
entrée exclue / sortie incluse. Stress : frais 9 + slippage 5 bps par côté,
puis entrée/sortie retardées d'une heure ; contrôle sans coûts de trading.
Rendements en bps du notionnel, pas du capital ; aucune extrapolation à +30 %/mois.

Vérifier les agrégats de chaque heure événement avec les lignes brutes, pagination
complète, déduplication et direction Close Long/A ou Close Short/B. Si ambiguïté,
budget épuisé ou agrégat divergent, conserver la preuve et interdire toute qualification.
Les identités liquidateur/liquidé sont suspectes sur l'audit initial (identiques) :
elles ne sont utilisées pour aucun signal et restent une limite de provenance.

## Décision

Bootstrap exploratoire par blocs calendaires de sept jours, BTC/ETH groupés,
5 000 réplications, seed 20260907. Rapporter concentration, nombre d'événements,
jours distincts et effet apparié. Pour justifier une validation indépendante :
au moins 30 événements sur 20 jours, 20 appariements, rendement moyen net six heures
et effet apparié avec bornes basses 95 % > 0, stress moyens positifs, vérification
brute de tous les événements. Sinon hypothèse non confirmée ou échantillon insuffisant.
Même un résultat positif ne donne aucun GO live : disponibilité causale, exécution,
risques et validation indépendante restent à démontrer. Aucun seuil ne sera retouché
après inspection ; pas de nouveau bot ni de collecte permanente à ce stade.

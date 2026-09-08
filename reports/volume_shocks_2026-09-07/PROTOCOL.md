# Chocs de volume horaires — protocole avant calcul

Archives natives BTC/ETH/SOL/HYPE du 10 mars au 6 septembre 2026 UTC,
déjà consultées pour d'autres hypothèses : exploration, pas holdout indépendant.
Aucune dépense, aucun ordre, aucune optimisation des seuils après résultats.

Une bougie complète est comparée aux 168 bougies qui la précèdent, sans
l'inclure : volume natif en unités du coin au moins 3 fois la médiane ;
amplitude (high-low)/open au moins 2 fois la médiane et au moins 0,5 %.
Deux hypothèses, symétriques long/short :

- Continuation : corps au moins 0,5 % de l'open, clôture dans les 20 %
  supérieurs pour un corps haussier, inférieurs pour un corps baissier.
- Rejet : mèche basse au moins 50 % de l'amplitude et clôture au-dessus
  du milieu (long) ; mèche haute au moins 50 % et clôture sous le milieu
  (short). Un doji centré ne déclenche pas de signal.

Entrée à l'open suivant ; détention principale 6 h ; 1 h et 24 h secondaires
uniquement descriptifs. Un événement par coin/règle au plus toutes les 25 h,
sélection commune aux horizons et indépendante des résultats. Retard stressé
d'une heure à l'entrée ET à la sortie, en conservant le signal initial.
Frais par côté 4,5 bps, slippage 2 bps ; stress 9 et 5 bps. Funding réel
horaire signé, prix horaire comme proxy ; scénario adverse paie |funding|.
Contrôle sans aucun coût/funding. Réutilisation de leg_return existant.

Résumé par coin, sens et blocs de 30 jours, PF, pire événement, retrait du
meilleur événement et bootstrap temporel par blocs de 7 jours (5 000 réplications,
IC 97,5 % corrigé pour les deux hypothèses). Minimum 30 événements et 20 dates
distinctes pour un intervalle. La correction locale n'efface pas les recherches
antérieures. Événements de plusieurs coins regroupés dans les mêmes blocs.

Retenir pour approfondissement gratuit seulement si, à 6 h : net positif en
base, coûts stressés, retard et funding adverse ; PF > 1,2 ; borne basse de
l'intervalle > 0 ; au moins 4 des 6 blocs positifs ; résultat positif après
retrait du meilleur événement. Ensuite vérifier contrôle apparié, autre période
gratuite, dépendance à un coin, puis allocation/risque/taille avec 1 000 $.
Un signal retenu ici ne constitue pas un GO, ni un rendement de portefeuille.
Si échec, suspendre la famille et essayer un autre mécanisme sans achat.

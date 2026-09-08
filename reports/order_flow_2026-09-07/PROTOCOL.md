# Flux agressif Binance comme signal externe pour Hyperliquid

BTC/ETH/SOL, mêmes six mois que l'étude interplateformes. Aucune nouvelle
requête ni dépense. Données prix déjà consultées ; nouveaux champs de flux
pas encore analysés. Étude exploratoire, aucune promesse de validation hors
échantillon. Volume acheteur agressif natif des klines Binance USDC, divisé
par volume total du coin ; déséquilibre = 2*part acheteuse - 1.

Un choc exige volume >=2 fois la médiane des 168 bougies précédentes et
|déséquilibre| >=0,15 (part acheteuse >=57,5 % ou <=42,5 %).
Deux mécanismes, aucun ajustement après calcul :

- Pression acceptée : corps de la bougie >=0,25 % en valeur absolue, même
  sens que le déséquilibre. Acheter/vendre HL dans le sens du flux.
- Pression absorbée : corps <=0,25 % en valeur absolue. Acheter/vendre HL
  dans le sens opposé au flux, hypothèse de liquidité passive résistante.

Les conditions aux bornes peuvent appartenir aux deux familles, analysées
séparément. Bougie Binance complète, entrée HL à l'open suivant, détention
principale 6 h, secondaires 1 h et 24 h. Espacement 25 h par coin/famille.
Coûts et funding HL identiques à l'étude de volume (4,5+2 bps par côté ;
stress 9+5 ; retard une heure ; funding adverse ; contrôle zéro coût).
Pas de jambe Binance : cette plateforme fournit seulement le signal.

Gates pour approfondir : 30 événements/20 dates, net positif dans les quatre
scénarios de coûts, PF>1,2, borne basse bootstrap 97,5 % >0 (5 000 blocs 7 j,
deux règles), >=4/6 blocs 30 j positifs, positif sans le meilleur événement.
Ces gates ne corrigent pas l'ensemble des hypothèses antérieures. Ensuite
extension gratuite et contrôle apparié sont nécessaires. L'absence de timestamps
de réception empêche de qualifier l'open immédiatement suivant comme exécutable.
Le retard d'une heure sert de stress de persistance, pas d'estimation réseau.

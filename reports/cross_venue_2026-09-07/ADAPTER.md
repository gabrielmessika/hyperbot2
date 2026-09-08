# Vérification de schéma avant calcul des rendements

L'acquisition publique a retourné 4 320 bougies et 540 paiements par coin.
Le validateur strict a bloqué le calcul avant tout résultat : les timestamps
de funding Binance sont décalés de 0 à 26 millisecondes des heures prévues.
Chaque intervalle de huit heures possède exactement un paiement, aucun trou.

Adaptation de format uniquement : vérifier la grille en groupant les timestamps
par huit heures, mais conserver les millisecondes natives pour attribuer les
paiements aux positions. Un paiement à entrée+12 ms appartient à la position ;
un paiement à sortie+12 ms n'y appartient pas. Les taux futurs restent exclus
du signal. Les timestamps bruts et checksums sont inchangés. HL conserve le
modèle horaire existant (prix proxy et exclusion de l'heure d'entrée).
Cette différence de convention reste une limite documentée, pas un bénéfice
supposé exploitable autour des heures de funding. Aucun seuil modifié.

# Pilote d'accès limité — enregistré avant téléchargement

Le protocole 180 jours est arrêté : première requête refusée HTTP 403
`history_window_exceeded` ; l'abonnement existant ne fournit que les 30 derniers
jours. Aucun résultat de cette étude n'a été calculé. Pas d'achat.

Pilote distinct, explicitement non qualifiant : du 9 août 2026 00:00 au
6 septembre 2026 00:00 UTC exclusif, soit les 28 journées complètes communes
à l'accès confirmé et aux prix/funding déjà archivés. Sept jours de chauffe,
21 jours d'observation ; le choix dépend de l'accès, pas des rendements.

Reprendre exactement les règles, coûts et diagnostics de `PROTOCOL.md`, sauf :
lookback des quantiles et témoins de sept jours au lieu de 30. Le minimum de
60 observations positives, les seuils absolus, les 95 %, la baisse de 0,5 %,
les cinq liquidations et la part de 80 % restent inchangés. Charger quatre séries
(deux actifs × volumes/OI) et vérifier toutes les heures événement par le brut
dans le budget global restant. Les prix/funding sont réutilisés sans requête.

Ce pilote ne peut satisfaire la profondeur du protocole initial. Toujours
`promotion_authorized=false`, même si les chiffres sont positifs. Rapporter
séparément manque d'échantillon, résultat économique et qualité des données.
Pas d'élargissement des seuils, de variante short ou de recherche du meilleur
horizon après calcul. La prochaine décision sera documentée selon le résultat.

# Brent/WTI : qualification et test distinct

Les références sont des paniers de futures, pas deux prix identiques d'un même
actif livrable. Brent référence une échéance plus lointaine que WTI dans le
tableau officiel. Les pages commodities et roll-schedules diffèrent sur les
jours de pondération (5e–10e contre 5e–9e jour ouvré). Le tableau daté couvre
avril–août 2026 : 8–14 avril, 7–13 mai, 5–11 juin, 8–14 juillet, 7–13 août.

Cette exploration n'est pas un arbitrage garanti. Exclure **les jours 4 à 17
inclus de chaque mois New York** pour couvrir largement les rouleaux publiés,
sans reconstruire de faux prix ajustés. Aucun historique externe de futures
payant ni imputation d'une courbe de terme.

## Données et disponibilité

Réutiliser CL déjà acquis. Obtenir uniquement BRENTOIL par client natif gratuit,
du 31 mars au 6 septembre 2026 exclusif : une journée de warm-up supplémentaire
avant le test du 1er avril au 6 septembre. Budget dix requêtes, 10 Mo ; une
requête bougies 1 h et jusqu'à huit pages funding de 500 lignes, une dernière
requête seulement si nécessaire. Destinations neuves, checksums et manifeste.
Gaps ou identité incorrecte empêchent l'évaluation, aucune donnée inventée.

Les cours CL ont déjà été consultés ; aucune prétention de holdout global.
Ces paramètres sont fixés avant réception des rendements Brent et calcul du
ratio. Le tarif snapshot est 0,9 bp par côté pour les deux marchés ; la timeline
complète historique n'est pas attestée. Sources officielles archivées.

## Signal, calendrier et risque

Log(BRENT/CL), moyenne et sigma sur les 24 heures closes précédant la bougie
signal, celle-ci exclue. Sigma minimal 0,002. Entrée si 2 <= |z| <4 : short
Brent/long CL si z positif, inverse sinon. Le moteur de ratio existant est
réutilisé avec actifs et horizon explicitement paramétrés, sans nouveau fit.

Entrées du lundi au vendredi entre **09 h et 14 h New York incluses**, hors
jours 4–17 ; les 24 heures de calcul doivent elles aussi être hors de cette
zone. Exclure les jours fériés US de la liste projet. Ces exclusions ne
constituent pas une qualification complète des horaires historiques CME/ICE.
Durée maximale **deux heures**, puis sortie au prochain open prévu. Moyenne et
sigma figés ; sortie anticipée au retour à 0,5 sigma ou à quatre sigmas adverses.
Cooldown 24 h depuis toute sortie. Retard statistique d'une heure en stress ;
entrée doit toujours respecter le même calendrier. Aucun paramètre ajusté
après résultat ni sélection d'un mois gagnant.

Portefeuille initial 1 000 $, deux notionals égaux avant arrondis, trois plafonds
bruts 0,5x/1x/1,5x à l'equity courante. Arrondis natifs, minimum 10 $ par jambe.
Conserver les protections existantes : perte de paire observée de 3 % de
l'equity d'entrée, drawdown compte de 20 % depuis sommet, sorties au prochain
open, gaps et dépassements conservés, aucun redémarrage après arrêt.

## Évaluation

Scénarios existants : central (frais 0,9 bp, slippage 2 bps par côté), frais
doublés/slippage 5 bps, délai d'une heure, funding toujours adverse, aucun coût.
Chacun avec infra supplémentaire nulle et 20 $/30 jours débités heure par heure.
Funding natif signé sur positions détenues, valorisé à l'open proxy.

Publier tous les scénarios, courbes horaires avec positions ouvertes, pertes
et gains mensuels, drawdowns observés et enveloppes OHLC, récupération et
rendement composé. Les mois rouges sont acceptés ; seuil de drawdown 20 %.
Risque de fills, marks/liquidations et indépendance intrahoraire des extrêmes
restent non qualifiés. Un petit résultat positif ne suffit pas à la cible
150–200 $ mensuels ; ne pas multiplier artificiellement le levier.

Retenir pour examen seulement les tailles positives en central, coûts renforcés
et funding adverse avec enveloppe de drawdown <=20 %. Exiger une autre période
et une qualification d'exécution avant promotion. Ce test de cinq mois ne
valide pas huit mois gagnants sur douze.

Sources : [commodities](https://docs.trade.xyz/asset-directory/commodities.md),
[roulements](https://docs.trade.xyz/consolidated-resources/roll-schedules.md),
[oracle](https://docs.trade.xyz/perp-mechanics/oracle-price.md).

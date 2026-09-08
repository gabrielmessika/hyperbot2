# Drawdown à 30 % : meilleur scénario central, fragilité persistante

**Oui, relever le seuil d'arrêt change le résultat ; cela ne suffit pas à
valider un meilleur edge.** À 1x, la cassure avec volume passe de +69,62 $
avec arrêt20 % à **+559,23 $ avec arrêt30 %**, sur 180 jours et 1 000 $ initiaux,
frais/funding inclus, sans infrastructure. Équivalent composé mensuel
**7,68 %**, drawdown observé27,30 %, enveloppe29,01 %. Mais les scénarios
de coûts renforcés et de retard deviennent négatifs et franchissent30 %.

## Comparaison à règle inchangée

18 actifs, 10 mars–6 septembre exclusif, mêmes signaux/arrondis et exécution
horaire que le contrôle précédent. Seulement le seuil d'arrêt change à taille
identique ; aucune hausse de taille après perte. Le cap est un plafond brut
à l'entrée, pas une exposition constante pendant la détention.

| Cap brut d'entrée | Net avec arrêt20 % | Net avec arrêt30 % | Mensuel équivalent à30 % | DD observé /enveloppe à30 % |
|---|---:|---:|---:|---:|
| 0,5x | +290,02 $ | +290,02 $ | +4,34 % | 14,39 % /15,36 % |
| 1x | +69,62 $ | +559,23 $ | +7,68 % | 27,30 % /29,01 % |
| 1,5x | −85,07 $ | +49,40 $ | +0,81 % | 30,66 % /34,01 % |

Scénarios centraux sans infrastructure. À 1x, 805 cycles à30 % contre378
à20 % ; le compte peut traverser la baisse puis participer à la reprise.
À1,5x, il s'arrête encore. Les dépassements ne sont pas écrêtés.

## Stress à1x avec arrêt30 %

| Scénario | Net sur180 jours, sans infra | DD observé /enveloppe |
|---|---:|---:|
| Central | +559,23 $ | 27,30 % /29,01 % |
| Coûts renforcés | −138,87 $ | 30,20 % /31,94 % |
| Retard1 h | −151,13 $ | 30,05 % /31,72 % |
| Funding adverse | +473,95 $ | 28,78 % /30,45 % |
| Contrôle zéro coût | +922,77 $ | 24,67 % /26,43 % |

Frais/slippage4,5/2 bps par côté, stress9/5 ; funding timestampé et oracle
approché par l'open. Les frais et retards modifient toute la trajectoire : les
scénarios défavorables s'arrêtent avant la reprise. Leur résultat n'est pas
une simple déduction des coûts du gain central. Le zéro coût à+11,51 % mensuel
équivalent n'est pas exploitable comme objectif net.

Avec20 $/30 jours d'infrastructure hypothétique : central +377,38 $
(+5,48 % mensuel équivalent), enveloppe31,38 % ; coûts−224,32 $, retard−234,11 $,
funding adverse−170,72 $. L'infrastructure continue après arrêt du trading,
d'où des drawdowns finaux pouvant dépasser encore le seuil. Aucun coût engagé.

## Pertes, concentration et décision

À1x/30 %, central sans infra : juin−266,76 $ (−21,43 % sur le mois),
avril+189,43 $, mai+59,75 $, juillet+212,51 $, août+400,23 $. Mars/septembre
partiels négatifs. Temps sous sommet90,75 jours, pire cycle−77,12 $.
ENA contribue−286,91 $, ARB+187,60 $, UNI+141,62 $, NEAR+141,35 $,
ZEC+134,58 $. Aucun actif perdant retiré après calcul.

Le mois rouge de juin est accepté dans l'analyse ; le problème est la
disparition du gain global sous stress et le franchissement du risque permis.
Le seul cap qui passe les quatre scénarios payants reste0,5x : sans infra aux
deux seuils, et avec infra au seuil30 %. Il conserve un résultat de quelques
pourcents mensuels, sans preuve de+10 %. Pas de GO.

Cette calibration est faite sur une période déjà étudiée, après sélection d'un
contrôle positif. Elle ne démontre pas une espérance future. La tolérance
utilisateur est désormais30 % pour la recherche avec comparaison20 % ; aucune
limite live modifiée. L'extension antérieure gratuite est en cours de
qualification à0,5x, avec les deux seuils enregistrés avant son calcul.

Audit descriptif supplémentaire, méthode existante par blocs de 14 jours et
10 000 tirages : intervalle mensuel central 95 % de **−1,52 % à +10,60 %**
à 0,5x, et **−3,86 % à +20,82 %** à 1x. Ces intervalles ne sont pas corrigés
pour toutes les stratégies testées et ne sont pas des prévisions ; le bootstrap
ne rejoue pas les arrêts ni les allocations. Ils illustrent l'incertitude,
sans prouver un gain attendu. Les deux comptes restent positifs par simple
soustraction de leur meilleur cycle (+247,59 $ /+471,34 $), ce qui ne constitue
pas une nouvelle simulation. Voir `uncertainty.json`, reproduit exactement.

## Vérification

63 artefacts reproduits exactement. Les trente simulations20 % conservent
**tous les champs économiques, cycles et courbes** de la baseline précédente ;
seul le champ explicite de seuil est ajouté, labels exclus de la comparaison.
263 tests passent, dont tenue d'une perte latente25 % au seuil30 % et
dépassement35 % conservé sans réentrée. Lint/format261 fichiers et mypy67 sources
passent. Voir `baseline_checks.json`, `reproduction.json`, `review.json`.

Aucun achat, ordre, secret, changement de service ou de serveur. Les anciens
résultats restent conservés et reproductibles avec leur version de code.

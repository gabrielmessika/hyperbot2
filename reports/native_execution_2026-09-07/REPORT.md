# Compte natif : rendement conservé, robustesse encore non démontrée

**Mise à jour : promotion suspendue après échec du transfert2025.** Voir le
[rapport de généralisation](../prior_transfer_2026-09-07/REPORT.md). Les résultats
ci-dessous restent ceux de la période native initiale, pas le statut actuel.

Le portefeuille cassures/rotation 50/50 conserve un résultat central de
**+538,26 $ sur 204 jours**, soit **+6,54 % mensuels équivalents**, après
simulation des positions natives, petits ordres différés et ticks de prix.
Le scénario de coûts renforcés tombe à **+206,49 $ /+2,80 % mensuels**.
Le plafond de recherche de 30 % permet de conserver ce candidat ; le seuil
20 % déclenche des arrêts et ne passe pas le filtre. Aucun GO réel.

## Ce qui a changé

Le compte de 1 000 $ contient une position nette par actif. Les intentions
des deux mécanismes gardent leurs horizons 24/168 heures et budgets 50/50.
La formule de budgets séparés existante est réutilisée, avec dimensionnement
sur l'equity native, réserve des coûts de sortie et des écarts résiduels.
Les dix portefeuilles virtuels de référence restent économiquement identiques
après extraction de cette formule : tous leurs cycles, courbes et résumés
ont été comparés, pas seulement leur PnL final.

Les deltas <10 $ sont reportés, sans modification fictive de position.
Le funding et les variations de prix concernent exclusivement l'inventaire
détenu. Les réductions précèdent les autres ordres ; une augmentation ou
inversion dépassant le budget natif est refusée puis réévaluée. Les prix
supposés sont arrondis au tick dans le sens défavorable ; aucun lot n'est
arrondi vers le haut pour forcer une exécution.
[Précision native](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size),
[minimums et erreurs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/error-responses).

L'arrêt de drawdown est irréversible et les dépassements restent comptés.
Les positions impossibles à fermer continuent de porter risque et funding ;
le modèle ne les efface pas à la fin. Les tests couvrent explicitement ce cas.
Dans les vingt scénarios historiques étudiés, la position terminale est nulle.

## Résultats à 30 %, exposition cible 1,5x

Même panel gratuit : 18 actifs, 4 896 heures du 14 février au 6 septembre
2026 exclu. Frais taker simulés 4,5 bps et slippage 2 bps par transaction ;
stress 9/5 bps, retard une heure, funding adverse en valeur absolue.

| Scénario, sans infrastructure supplémentaire | Gain net | Mensuel équivalent | Drawdown observé | Enveloppe prudente OHLC |
|---|---:|---:|---:|---:|
| Central | +538,26 $ | 6,54 % | 20,21 % | 27,56 % |
| Coûts renforcés | +206,49 $ | 2,80 % | 22,41 % | 29,43 % |
| Entrées retardées | +368,65 $ | 4,72 % | 21,86 % | 29,09 % |
| Funding adverse | +365,41 $ | 4,69 % | 22,18 % | 29,34 % |
| Zéro coût, plafond descriptif | +855,57 $ | 9,52 % | 18,12 % | 25,62 % |

Les quatre scénarios payants sans infrastructure passent le filtre
exploratoire : profit positif, enveloppe sous 30 %, marge sans incident,
positions terminales fermées. Avec la sensibilité **hypothétique** de
20 $/30 jours, le central est +348,26 $ /4,49 % mensuels ; coûts et retard
restent positifs (+92,92 $ /+194,98 $) mais leur enveloppe atteint
30,82 % /30,24 %. Ce groupe ne passe donc pas le filtre.

À seuil 20 %, sans infrastructure : central +127,66 $, coûts −24,08 $,
retard +58,54 $, funding adverse +54,56 $. Les quatre s'arrêtent. Le seuil
d'arrêt ne garantit pas une perte bornée exactement à 20 % ; le replay
conserve le risque entre observations et les mouvements avant sortie.

## Ordres, inventaire et concentration

Central 30 % : 2 022 ordres natifs, 838 épisodes de position, 148,66 $ de
frais et 16,45 $ de funding net débité. Un épisode regroupe les ajustements
depuis une position nulle jusqu'au retour à zéro ou à une inversion ; son
nombre n'est donc pas comparable directement aux cycles virtuels précédents.

840 tentatives différées pour minimum et 28 pour budget : les tentatives
horaires répétées ne sont pas autant d'incidents indépendants. 820 heures
présentent un écart à la cible. Le plus grand écart vaut **327,67 $** ; il
correspond à une entrée ARB refusée pour budget le 19 août, sans position ARB
détenue, et non à une poussière de cette valeur. Les autres intentions trop
petites sont aussi refusées au dimensionnement (909). Ce comportement modifie
réellement les positions et leurs gains ; aucune économie forfaitaire ajoutée.

Le ratio brut natif maximal observé est 1,669x après mouvements de prix :
1,5x désigne le budget à l'entrée, pas un plafond d'exposition continu.
Buffer de marge prudent minimal 592,26 $. Durée maximale sous sommet :
75,33 jours. Juin perd 162,15 $ (−12,55 %), juillet gagne 212,55 $ et août
215,91 $. Février et septembre sont partiels.

La concentration reste une faiblesse. Un épisode **PUMP du 20 juillet au
31 août**, regroupant plusieurs ajustements sur six semaines, rapporte
254,36 $ au central et 206,18 $ sous coûts renforcés. Une simple soustraction
comptable laisse respectivement +283,90 $ et **+0,31 $**. Ce calcul ne rejoue
pas les allocations et ne prédit pas ce qui se serait produit sans PUMP ;
il indique une dépendance à cette phase favorable. Ce n'est pas un seul fill.
ENA contribue −498,71 $ au central ; aucun actif perdant n'a été retiré.

Bootstrap descriptif des rendements quotidiens, blocs chevauchants de 14 jours,
10 000 tirages : intervalle mensuel central 95 % **[−2,27 % ; +16,12 %]**,
coûts **[−5,58 % ; +11,79 %]**. Non corrigé pour les recherches antérieures,
ni prédictif, ni validation indépendante. L'espérance de gain future et
la cible de +10 % nets mensuels restent non démontrées.

## Qualification obtenue et limites restantes

Le défaut identifié de petits ajustements remplis implicitement est traité
dans ce simulateur. La comptabilité a été reconstruite indépendamment avec
un registre cash/inventaire signé, sans réutiliser le calcul de prix moyen
du moteur. Sur les vingt portefeuilles, chaque equity horaire concorde à
1e-18 $, les frais/fundings et le drawdown observé aussi. Tous les ordres
simulés satisfont minimum, lot, précision de prix et budget d'entrée.

Cela ne prouve pas leur remplissage réel : open horaire utilisé à open+60 s,
slippage forfaitaire, profondeur et fills partiels non observés, oracle de
funding approximé par l'open, paramètres de marge simplifiés. Le panel a déjà
servi à plusieurs recherches. L'enveloppe OHLC est un majorant de recherche,
pas un prix intrahoraire observé ou un plafond garanti en production.

Statut : **NATIVE_EXECUTION_RESEARCH_CANDIDATE_UNQUALIFIED**. Le candidat mérite
une épreuve sur une autre période/régime, avec comparaison à une exposition
passive. Prochaine acquisition éventuelle : qualifier gratuitement la
couverture d'archives publiques antérieures, sans achat. Une série d'une autre
plateforme pourra falsifier la généralisation des signaux ; elle ne validera
pas à elle seule l'exécution Hyperliquid. Ne pas chercher de nouveaux poids
ou retirer PUMP/ENA en fonction de ces résultats.

## Artefacts et vérifications

`scripts/investigate_native_execution.py`, `scripts/audit_native_execution.py`
et l'audit d'incertitude existant. Sources et résultats checksumés ; protocole
enregistré avant calcul. Vingt simulations, qualité, dix références et résumé
sont reproduits à l'identique ; incertitude reproduite séparément.
Quatorze nouveaux tests, suite complète **289 tests**, lint/format et mypy
passent. Aucun achat, appel de marché, ordre réel, service ou serveur modifié.
La consultation des deux pages de documentation publique n'a pas utilisé
de clé. Recherche active, trading réel désactivé.

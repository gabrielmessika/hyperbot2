# Cassures avec volume : extension positive au total, rendement plus modeste

Les 24 jours supplémentaires sont perdants, mais **le compte continu sur
204 jours gagne 255,36 $** pour 1 000 $ initiaux à 0,5x, frais et funding
inclus, sans infrastructure supplémentaire. Équivalent mensuel composé
**3,40 %**, contre 4,34 % sur les 180 jours précédemment examinés.
Le résultat reste positif sous stress sans infra ; il ne démontre pas +10 %
mensuels ni une espérance future assez robuste pour un GO.

## Données et méthode

54 appels publics gratuits, 2 327 340 octets. Les 18 actifs ont chacun leurs
576 bougies et paiements horaires du 14 février au 10 mars exclusif, sans trou
ni volume nul. Les données sont ajoutées au panel existant, conservées avec
manifeste et SHA-256. Aucun actif retiré selon ses résultats.

Règle inchangée : cassure d'une boîte de 24 h dans le sens de la bougie,
volume au moins doublé, sans compression. Démarrage conservé à l'index 193,
espacement 25 h et détention 24 h. Même moteur, arrondis/minimums, partage du
capital, funding timestampé, marge stress et exécution open+60 s supposée.
Les fills et oracles historiques restent des proxys horaires.

Deux comptes distincts sont étudiés : antérieur seul sur 24 jours, chauffe
comprise ; continu sur 204 jours sans remise à zéro au 10 mars. Seuils de
drawdown 20 % et 30 %, cap 0,5x fixé avant lecture des résultats. Les seuils
n'affectent pas les scénarios sans infra, qui restent sous 20 %. La nouvelle
période n'est pas un holdout annuel : univers courant, contrôle sélectionné
après examen des autres études, seulement 24 jours supplémentaires.

## Net sur le compte continu

| Scénario | Net sans infra | Mensuel équivalent | Enveloppe de drawdown |
|---|---:|---:|---:|
| Central | +255,36 $ | +3,40 % | 15,34 % |
| Coûts renforcés | +115,77 $ | +1,62 % | 17,38 % |
| Retard 1 h | +157,53 $ | +2,17 % | 17,18 % |
| Funding adverse | +220,94 $ | +2,98 % | 15,87 % |
| Zéro coût de trading/funding | +410,79 $ | +5,19 % | 13,94 % |

783 cycles centraux sur 191 dates d'entrée. Drawdown central observé 14,37 %,
pire cycle −34,61 $, 89,33 jours sous le sommet. Pas de rupture de marge
simulée dans le filtre positif sans infra. Le cap d'entrée ne garantit pas
une exposition constante pendant les mouvements de prix.

Avec 20 $/30 jours d'infrastructure hypothétique : central +96,21 $
(+1,36 % mensuel), coûts −37,12 $, funding adverse +60,15 $. Le retard finit
à −185,49 $ avec arrêt 20 %, contre +2,75 $ avec seuil 30 % : la tolérance
supérieure permet ici de traverser un drawdown observé de 20,21 %. Cela ne
rend pas tous les scénarios positifs avec cette infra. Aucune dépense engagée.

## Période rouge, concentration et incertitude

Antérieur seul : central −46,32 $, coûts −55,46 $, retard −29,56 $, funding
adverse −48,22 $, zéro coût −38,55 $, sans infra. Le résultat central porte
sur 76 cycles. Il n'est pas rejeté pour sa couleur : toutes ces pertes sont
conservées dans la comparaison. Les cooldowns, positions et budgets hérités
changent la suite ; ne pas additionner ces comptes réinitialisés pour calculer
le résultat continu.

Compte continu central : février −28,57 $, mars +0,45 $, avril +97,64 $,
mai +29,30 $, juin −120,30 $, juillet +109,98 $, août +176,39 $,
septembre −9,52 $. Février/septembre partiels. Principaux contributeurs :
ARB +101,43 $, TAO +76,67 $, ZEC +74,99 $, FARTCOIN +74,46 $ ;
ENA −136,23 $, XPL −59,41 $. Aucun perdant écarté.

Audit descriptif par blocs de 14 jours, 10 000 tirages : intervalle mensuel
95 % central **[−2,22 % ; +9,40 %]**, coûts **[−3,92 % ; +7,48 %]**.
Ces intervalles ne sont ni prédictifs ni corrigés pour toutes les recherches
précédentes ; les arrêts/allocations ne sont pas rejoués dans le bootstrap.
Simple soustraction du meilleur cycle : central encore +214,04 $, coûts
+77,42 $. Cela réduit le soupçon d'un gain porté par un seul trade, sans
établir une réplication indépendante ou une espérance garantie.

## Décision et livraison

`POSITIVE_SMALL_RETURN_EXTENSION_UNQUALIFIED`. Conserver le candidat de
recherche à quelques pourcents et ses pertes ; aucun GO, aucune validation de
la cible 10 %. Le test à 1x/30 % sur les 180 jours reste fragile sous stress,
voir le [rapport risque](../breakout_risk30_2026-09-07/REPORT.md).

49 artefacts reproduits exactement : 24 par seuil et un audit. Moteur couvert
par 263 tests après ajout du seuil 30 %, lint/format 263 fichiers et mypy
67 sources passent. Code d'acquisition, signal et portefeuille réutilisé.
Aucun achat, secret, ordre, service ou serveur modifié. Recherche active.

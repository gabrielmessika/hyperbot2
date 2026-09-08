# Exploration sans achat — règles fixées avant calcul

Instruction du 7 septembre : priorité à des hypothèses différentes avec les
données déjà disponibles gratuitement. Suspendre liquidations/historique payant,
maker avec transport inadéquat et variantes déjà rejetées. Aucun compte payant,
achat, collecte permanente ou changement serveur. Budget financier additionnel : 0 $.

## Trois mécanismes distincts

Univers fixé BTC, ETH, SOL, HYPE ; données Hyperliquid horaires déjà archivées du
10 mars au 6 septembre 2026 00:00 UTC exclusif. Trente jours de chauffe puis
150 jours exploratoires. Historique déjà consulté : aucun nouvel OOS prétendu.
Trois règles, aucun balayage de paramètres, aucun réemploi des stratégies TRIDENT.

1. **Force relative sept jours.** Chaque jour à 00:00 UTC, classer les rendements
   close/close sur sept jours, en excluant les dernières 24 heures. Acheter le
   meilleur, vendre le moins bon, mêmes notionnels initiaux, sortie 24 h après.
   L'exclusion du dernier jour distingue la persistance lente des rebonds courts.
2. **Portage relatif.** Même fréquence, acheter l'actif au funding moyen des
   24 dernières heures le plus faible et vendre celui au funding le plus élevé.
   Deux notionnels égaux, sortie 24 h après. Cela teste la sélection dynamique
   et le risque de prix relatif, pas seulement le revenu d'un short couvert en spot.
3. **Tendance lente.** Tous les sept jours à partir de la fin de chauffe, chacun
   des quatre actifs est acheté/vendu selon le signe du rendement des 30 derniers
   jours clos. Notionnels initiaux égaux, sortie sept jours après. Aucun signal
   si rendement nul. Pas de canal 24 h, ATR ou réglage de seuil après résultat.

Les classements n'utilisent que des clôtures/taux strictement antérieurs à
l'entrée. Égalité de tous les scores des paires : pas de trade ; autres égalités
départagées par ordre alphabétique. Aucun événement dont la sortie stressée
ne possède pas d'open disponible. Les positions sont des paniers hypothétiques
indépendants, sans stops ni modèle de portefeuille : ce filtre ne qualifie pas
le risque et ne contourne pas les limites d'exécution héritées.

## Économie et réfutation

Rendements exprimés en bps du notionnel brut du panier, pas du capital.
Exécution hypothétique aux opens ; quantités fixées à l'entrée sur les notionnels
égaux, conservées jusqu'à la sortie. Frais/slippage proportionnels au notionnel
de chaque côté. Funding signé : long paie un taux positif, short le reçoit ;
valorisation approchée par l'open horaire, entrée exclue/sortie incluse. Les taux
futurs servent uniquement à la comptabilité réalisée, jamais au classement.

Scénarios : base 4,5 bps de frais + 2 bps slippage par côté ; coûts stressés
9 + 5 bps ; entrée/sortie décalées d'une heure ; funding stressé entièrement
adverse en valeur absolue ; contrôle zéro coûts de trading. Pas d'infrastructure
ajoutée au filtre du signal : ce coût devra être soustrait à une vraie simulation.

Publier moyenne, somme, PF, taux de succès, pire panier, maximum de perte depuis
un pic sur la somme des paniers clos, et résultats par blocs calendaires de
30 jours. Cette perte ne représente pas le drawdown intraposition. Montrer la
contribution de chaque actif et la décomposition prix/frais/funding.

Pour distinguer l'effet des règles de la hausse générale des cryptos : témoin
long équipondéré des quatre actifs aux mêmes dates, et permutation des signaux
entre actifs (tendance : signes équiprobables), 2 000 trajectoires, seed 20260907.
Le benchmark long n'est pas une couverture bêta équivalente et reste descriptif.
Test unilatéral de permutation, seuil familial 0,05/3. Aucun résultat favorable
d'une seule variante ou d'un seul actif ne suffit.

Bootstrap des sommes/nombres par blocs de sept jours avec dates communes aux
actifs et jours sans événement conservés ; 5 000 réplications. Intervalle
98,33 % pour trois règles, pas présenté comme correction de toutes les recherches
antérieures. En dessous de 30 paniers ou 20 dates distinctes, pas d'intervalle
inférentiel publié. Le minimum rend la tendance lente volontairement préliminaire
sur ces 150 jours ; un résultat favorable appelle un historique quotidien gratuit
plus long, pas l'abaissement du minimum.

Candidat à approfondir seulement si moyenne de base positive, stress coûts,
délai et funding adverse positifs, au moins quatre blocs sur cinq positifs,
PF > 1,2, échantillon suffisant, borne basse > 0 et permutation corrigée favorable.
Un candidat passe ensuite sur davantage d'historique gratuit et une simulation
de risque complète ; ce statut n'est jamais GO live. Sinon publier le motif de
rejet/insuffisance et passer à une autre famille. Aucune promesse de +30 %/mois.

# Tendance collective : effet du drawdown 20 % / 30 %

**Décision : `COLLECTIVE_TREND_CROSS_PERIOD_SCREEN_FAILED`.** Le plafond de
30 % permet à une configuration de traverser une baisse historique et de
profiter du rebond suivant. Son rendement ne se retrouve pas sur le panneau
Hyperliquid. Aucun GO ni espérance de +10 % mensuels démontrée.

## Hypothèse et données

Le [protocole](PROTOCOL.md) et son [enregistrement](registration.json) précèdent
le calcul de cette nouvelle règle. Chaque lundi à 00 h UTC, acheter à poids
notionnels égaux les trois actifs les moins volatils et les trois plus volatils
sur 30 jours, seulement si la médiane des rendements passés sur 30 jours des
onze actifs est positive. Garde de 168 h ; aucune réévaluation de la condition
en cours de semaine. Contrôle : même panier sans condition de tendance.

Univers : ARB, BNB, DOGE, INJ, LINK, NEAR, UNI, WLD, XMR, XRP et ZEC.
Binance 2024–2025 : 731 jours consécutifs, un seul capital initial de 1 000 $,
sans remise à zéro du capital ou de la chauffe au changement d'année.
Hyperliquid : 204 jours du 14 février au 6 septembre 2026 exclu, compte séparé.
Les 22 corrections REST d'octobre 2024 restent explicites ; archives intactes.

Le panneau continu comporte 99 dates hebdomadaires, dont 42 autorisées par
la condition. Les 94 anciens classements sont identiques ; cinq semaines
deviennent couvertes par la continuité annuelle. Le natif comporte 23 dates,
dont dix admissibles, avec les 23 anciens classements inchangés.

160 simulations : deux panneaux, deux règles, caps d'exposition 0,5/1,5 fois
l'equity, arrêts globaux 20/30 %, cinq scénarios de coûts et infrastructure
0/20 $ par 30 jours. Les caps limitent les nouvelles allocations ; ils ne
garantissent pas un ratio constant entre deux ajustements. Moteur natif réutilisé
sans changement : lots, ticks, minimum de 10 $, financement, frais, inventaire
résiduel et capital partagé. Infrastructure à 20 $ purement hypothétique.

## Comparaison centrale

Gains cumulés après frais, slippage et funding, sans coût marginal de serveur.
L'équivalent mensuel composé couvre toute la période, y compris chauffe, cash
et arrêt. Il ne représente pas un gain mensuel régulier ou une prévision.

| Période | Cap | Arrêt demandé | Gain cumulé | Équiv. mensuel | Enveloppe de drawdown OHLC | Arrêt déclenché |
|---|---:|---:|---:|---:|---:|---|
| Binance 2024–2025 | 0,5x | 20 % | −0,83 $ | −0,003 % | 21,50 % | Oui |
| Binance 2024–2025 | 0,5x | 30 % | +582,16 $ | +1,90 % | 27,55 % | Non |
| Hyperliquid 2026 | 0,5x | 20 % | +2,29 $ | +0,034 % | 13,69 % | Non |
| Hyperliquid 2026 | 0,5x | 30 % | +2,29 $ | +0,034 % | 13,69 % | Non |
| Binance 2024–2025 | 1,5x | 20 % | +467,71 $ | +1,59 % | 29,79 % | Oui |
| Binance 2024–2025 | 1,5x | 30 % | +281,18 $ | +1,02 % | 35,44 % | Oui |
| Hyperliquid 2026 | 1,5x | 20 % | +49,25 $ | +0,71 % | 26,52 % | Oui |
| Hyperliquid 2026 | 1,5x | 30 % | −43,04 $ | −0,64 % | 33,80 % | Oui |

L'arrêt s'applique au drawdown observé et peut être dépassé. L'enveloppe OHLC
est une mesure prudente du risque intrahoraire, pas une trajectoire de fills
observée. Les dépassements restent dans les résultats ; aucune perte n'est
tronquée à la limite. À 1,5x, élargir l'arrêt laisse ici restituer davantage de
gains avant la fermeture, sans augmenter le rendement final.

## Robustesse et concentration

À 0,5x / 30 %, Binance donne +563,21 $ sous coûts renforcés, +557,81 $ avec
une heure de retard et +567,25 $ sous funding adverse. Ces quatre scénarios
payants restent sous 30 % dans le modèle. Mais le natif donne respectivement
−0,91 $, +9,36 $ et −5,20 $ : la rentabilité ne se confirme pas entre périodes.
Avec 20 $ d'infrastructure par 30 jours, le central devient −470,14 $ sur
731 jours et −130,58 $ sur 204 jours. La dépense continue après l'arrêt ; elle
modifie aussi les allocations et la date d'arrêt, pas seulement le gain final.

Le gain central continu se répartit en +400,88 $ en 2024 puis +181,28 $ en
2025 sur le même compte. Novembre 2024 apporte à lui seul +423,19 $ ; octobre
2025 +192,57 $. La plus longue période sous le sommet dure 305 jours.
Le gain de janvier 2025 (+87,56 $) provient des positions du panier autorisé
le 30 décembre, conservées au changement d'année et toutes fermées le
6 janvier à 00 h 01. Aucun nouveau panier n'est autorisé les quatre lundis
de janvier. Le compte n'était donc pas en cash pendant tout janvier.

Le contrôle sans condition, à 0,5x / 30 %, donne +6,19 $ sur 2024–2025 après
arrêt en août 2024, sans reprise annuelle. Sur Hyperliquid, il gagne +201,11 $
contre seulement +2,29 $ avec condition : celle-ci manque notamment une grande
part de la phase favorable d'août 2026. Ni la condition ni le contrôle ne
passent l'ensemble des huit scénarios payants des deux panneaux pour un même
cap, arrêt et coût d'infrastructure : **zéro groupe compatible sur seize**.

## Vérification et limites

[Reproduction](reproduction.json) : 172 artefacts JSON identiques à la seconde
exécution, dont 160 simulations. Audit indépendant cash/inventaire des
160 comptes, avec rapprochement horaire de l'equity, frais, funding, contraintes
d'ordres, capital et arrêt. Les 40 contrôles natifs sont intégralement identiques
à la précédente étude du capital. Tous les comptes terminent plats ; aucun
incident de marge observé dans le modèle. L'audit comptable ne constitue pas
une vérification indépendante des fills réels ou de l'enveloppe OHLC.

328 tests complets passent ; lint et format vérifiés, typage de 76 sources.
Les sources de prix/funding existantes sont revalidées, sans acquisition de
nouvelles données ni dépense. Aucun ordre réel, service ou serveur modifié.

Les périodes ont déjà servi à la recherche et l'hypothèse suit plusieurs
échecs. Les résultats ne sont pas une validation prospective indépendante.
Binance USDT constitue un transfert de plateforme avec coûts et contraintes
Hyperliquid simulés ; USDT assimilé au dollar, métadonnées actuelles et biais
de survie conservés comme limites. Aucune preuve de file maker n'en découle.

Le [verdict détaillé](review.json) conserve tous les motifs d'échec.
Recherche active : archiver cette condition sans optimiser son seuil sur
ces gains. Le plafond de recherche reste 30 %, avec comparaison à 20 % ;
le trading live demeure désactivé.

# Choc baissier collectif : continuation et rebond

Deux hypothèses concurrentes, fixées avant PnL : une vente généralisée peut
se prolonger pendant les 24 h suivantes, ou être suivie d'un rebond. Tester
les deux directions sur exactement les mêmes dates et actifs. La littérature
documente des effets de momentum crypto, mais ne valide ni notre seuil de choc
ni sa rentabilité sur Hyperliquid : [Liu et Tsyvinski, NBER](https://www.nber.org/papers/w24877).

Réutiliser l'univers de onze actifs fixé avant 2024 : ARB, BNB, DOGE, INJ, LINK,
NEAR, UNI, WLD, XMR, XRP, ZEC. Panneaux existants Binance 2024–2025 continu
(731 jours) et Hyperliquid 2026 (204 jours). Pas d'acquisition ni d'achat ;
correction REST 2024 explicite et qualités historiques revalidées.

À chaque ouverture horaire, calculer pour chaque actif le rendement des
24 heures entièrement révolues : close[i−1] / close[i−25] − 1. Un choc est
admissible si au moins huit des onze rendements sont inférieurs ou égaux à
−5 %. Prendre la première heure admissible, puis imposer 26 h entre entrées
de paniers, y compris si le choc persiste. Aucun croisement supplémentaire
ou retour préalable sous le seuil n'est exigé. Au plus un panier par période
de détention ; la séparation inclut le scénario retardé.

Règle continuation : vendre les onze actifs à notionnels égaux. Règle rebond :
acheter les onze, aux mêmes poids. Aucun classement individuel ni exclusion
des actifs qui n'ont pas baissé de 5 %. Détention fixe 24 h ; aucune optimisation
des seuils, nombre d'actifs, délai ou horizon après résultats. Première
observation à i=25 ; dernière entrée seulement si la sortie retardée est
couverte. Aucune remise à zéro de la chauffe au changement d'année.

Comptabilité d'événements normalisés par le notionnel brut initial, moteur
existant. Proxy ouverture horaire +60 s pour entrée/sortie. Scénarios : central
frais/slippage 4,5/2 bps par côté ; stress 9/5 ; retard d'une heure ; funding
adverse ; zéro frais/slippage/funding. Inclure les paiements réellement datés
entre entrée et sortie ; prix oracle historique approximé par l'ouverture
horaire comme dans les études précédentes. Séparer prix, frais, slippage,
funding et net. Publier les heures en choc écartées par l'espacement.

Pour chaque direction, publier tous les scénarios, gains par année d'entrée,
actif et mois, moyenne et pire panier, PF, nombre de gains/pertes, dépendance
aux meilleurs événements. Comparaison appariée rebond moins continuation.
Bootstrap par blocs de sept jours, 5 000 réplications, calendrier complet
y compris les jours sans événement ; les paniers ne sont pas des tirages
indépendants. Les intervalles 95 % sont descriptifs et ne corrigent pas la
sélection entre ces deux règles ni les recherches antérieures.

Filtre de diagnostic de capital pour une même direction : au moins vingt
événements par panneau ; moyenne positive dans les scénarios central, coûts,
retard et funding adverse des deux panneaux ; borne inférieure centrale 95 %
positive dans chacun. Sinon archiver la faiblesse ou l'échec sans modifier
les paramètres. Un succès n'autorise pas le live : examiner alors le compte
natif de 1 000 $, le drawdown 20/30 %, coûts, lots, ticks, minimums, positions
ouvertes, marge et infrastructure 0/20 $ hypothétique dans un protocole séparé.

Les périodes ont déjà été consultées et le choix de cette famille suit les
échecs précédents ; aucune validation prospective indépendante revendiquée.
Un rendement d'événement n'est pas un rendement du capital ni une performance
mensuelle. Survie de l'univers, transfert Binance USDT et fills proxy restent
des limites. Aucun ordre réel, client de signature, service ou serveur modifié.

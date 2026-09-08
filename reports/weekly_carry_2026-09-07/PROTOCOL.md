# Carry relatif hebdomadaire avec seuil de couverture des coûts

Hypothèse : les écarts de funding persistent assez longtemps pour rémunérer
un panier de contrats à notionnel acheteur/vendeur équilibré. La neutralité
du notionnel initial ne garantit pas une neutralité de bêta ou de prix.
Le carry relatif de quatre grandes cryptos sur 24 h avait échoué ; cette
expérience teste explicitement une détention plus longue, onze actifs et un
seuil économique, sans effacer cet échec ni prétendre découvrir une hypothèse
sans rapport avec les recherches précédentes.

Univers fixé par la qualification avant 2024 déjà enregistrée : ARB, BNB, DOGE,
INJ, LINK, NEAR, UNI, WLD, XMR, XRP, ZEC. Deux panneaux : Binance 2024–2025
continu, 731 jours, et Hyperliquid 2026, 204 jours. Sources existantes vérifiées,
correction REST 2024 explicite, aucun achat ni acquisition. La chauffe n'est
pas réinitialisée au changement d'année. Les périodes ont déjà été consultées.

Chaque lundi 00 h UTC après 168 h complètes, sommer les taux effectivement
réglés pendant les 168 heures précédentes, sans le paiement de l'heure courante.
Acheter les trois sommes les plus faibles, vendre les trois plus élevées,
six notionnels égaux. S'abstenir en cas d'égalité à une frontière de sélection.
Les sommes hebdomadaires rendent comparables les fréquences de règlement,
sans annualiser un taux de huit heures comme s'il était horaire.

Condition d'entrée unique : recette attendue sous persistance des taux, égale
à (somme des trois taux hebdomadaires hauts − somme des trois bas) / 6,
strictement supérieure à 13 bps du notionnel brut. Ce seuil correspond à
deux fois les frais/slippage centraux 4,5 + 2 bps, sans présumer de la recette
future réelle. Aucun balayage de seuil ou de fenêtre. Garde 168 h, entrée et
sortie à ouverture horaire +60 s dans le proxy. Couverture nécessaire de la
sortie retardée d'une heure. Contrôle : inverser les six côtés sur exactement
les mêmes dates et actifs ; ne pas promouvoir un contrôle après observation.

Étape initiale : événements normalisés par le notionnel brut, sans portefeuille
ni levier. Scénarios : central frais/slippage 4,5/2 bps ; coûts 9/5 ; retard 1 h ;
funding adverse où chaque paiement devient un débit ; zéro frais/slippage/funding.
Publier séparément mouvement des prix, slippage, frais et financement. Les
paiements futurs n'interviennent que dans le PnL, selon leurs horodatages réels.
Conserver toutes les semaines admissibles ou refusées et les contributions
par actif, année et côté, les pires événements et intervalles bootstrap.

Filtre pour justifier un portefeuille : au moins vingt événements par panneau,
moyennes positives sous central/coûts/retard dans les deux panneaux et borne
inférieure 95 % centrale positive. Bootstrap par blocs calendaires de sept
jours, 5 000 réplications, toutes les dates y compris sans événement. La
comparaison appariée au contrôle reste publiée. Pour cette hypothèse, supprimer
tout revenu de funding retire la source de rendement recherchée : ce scénario
est un diagnostic de dépendance et de risque, pas une exigence de rentabilité.
Cette distinction est fixée avant PnL et ne modifie aucun ancien verdict.

Si le filtre passe, tester ensuite le compte natif de 1 000 $, coûts, marge,
minimums, lots, ticks, positions ouvertes, drawdown 20/30 % et infrastructure
0/20 $ hypothétique. Les rendements d'événement ne sont jamais assimilés à
des gains de compte ou à des performances mensuelles. Même un filtre positif
ne suffirait pas à un GO : périodes réutilisées, sélection successive,
survie de l'univers, transfert Binance USDT et fills proxy restent des limites.

Le funding Hyperliquid est réglé chaque heure et converti au prix oracle :
[documentation officielle](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding).
Notre comptabilité historique existante utilise l'ouverture de la bougie
comme approximation de ce prix, à publier comme limite, particulièrement
matérielle pour une stratégie de funding. Aucun ordre, client de signature,
service ou serveur modifié.

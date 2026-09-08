# Panier acheteur des extrêmes de volatilité — épreuve2024 figée

Cette hypothèse est sélectionnée après le contrôle positif de l'étude
volatility_spread sur2025/2026. Conserver explicitement ce statut exploratoire.
Les résultats de2024 ne sont pas encore calculés à l'enregistrement présent.

Règle inchangée du contrôle : lundi00h UTC, acheter les trois actifs aux
plus faibles volatilités et les trois aux plus fortes, notionnels initiaux
égaux. Réutiliser volatility_baskets :30 rendements quotidiens logarithmiques
passés, écart-type échantillonnal,721 heures minimales, frontières sans
égalité, détention168h. Aucune direction par momentum, aucun nouveau seuil.

Panneaux fixes11 : Hyperliquid2026 sur les204 jours disponibles, Binance2025
sur l'année et Binance2024 sur l'année bissextile. Onze actifs retenus par
dates de contrat, avant tout PnL de cette étude. Les anciens18/15 résultats
restent publiés, mais ne sont pas mélangés au nouveau sous-panel. Aucun
retrait selon le gain, les trous ou le coût de funding après calcul.

Contrôle fixe : achat hebdomadaire équipondéré de tous les onze actifs aux
mêmes dates, mêmes horizons et coûts, pour mesurer l'intérêt du classement.
Ne pas transformer un contrôle gagnant en preuve d'alpha. Les deux règles
ont une exposition acheteuse au marché, pas une neutralité directionnelle.

Premier filtre événementiel : somme des rendements de chaque jambe divisée
par6 pour la règle, par11 pour le contrôle. Chaque quantité reste constante
pendant la semaine ; aucune capitalisation ou réallocation intra-semaine.
Frais/slippage4,5/2bps par transaction, stress9/5, retard entrée/sortie1h,
funding adverse en valeur absolue et zéro coût descriptif. Paiements exacts
traversés, proxy de valorisation open horaire à +60s, horizon retardé couvert.
Pas d'économie présumée pour les actifs conservés entre deux semaines.

Publier comptes par actif/panier, contributions, pires semaines, moyennes
nettes et comparaison au contrôle. Bootstrap7jours/5 000 tirages, calendrier
complet depuis la première sélection, jours sans entrée inclus, panier
comme unité statistique. Intervalle apparié de la différence au contrôle.
Les intervalles sont descriptifs, non corrigés pour les recherches passées.

Pour justifier la qualification native du candidat : au moins20 paniers
par panneau, les quatre scénarios payants positifs sur chacun, borne
inférieure95 % centrale positive sur chaque panneau et avantage moyen
central au contrôle positif sur2024. Si ce filtre échoue, le candidat
n'est pas promu ; ne pas régler la fenêtre ou le nombre d'actifs pour
faire passer2024. Aucun résultat mensuel déduit de ce seul filtre.

Si le filtre passe, simuler le compte natif1 000 $, caps fixes0,5/1,5x,
drawdown30 % et comparaison20 %, infrastructure marginale0 et sensibilité
hypothétique20 $ par30 jours. Arrondis, lots, minimums, positions ouvertes,
coûts, dépassements d'arrêt et résidus restent inclus. Aucun ordre réel.

Limites : univers issu des actifs actuels, période de sélection déjà explorée,
BinanceUSDT assimilé au dollar pour les transferts, paramètres économiques
Hyperliquid de référence et non barème historique Binance, prix/oracle/fills
approximés. Aucune nouvelle donnée payante, aucun GO automatique.

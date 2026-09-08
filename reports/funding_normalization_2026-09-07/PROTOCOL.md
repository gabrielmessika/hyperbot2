# Normalisation du funding : étude d'événements enregistrée

7 septembre 2026. Aucun achat, ordre ou modification serveur. Historiques déjà
consultés pour d'autres règles ; cette étude n'est pas un holdout indépendant.

## Hypothèse et sélection

Un funding élevé puis en baisse peut signaler le dénouement d'un positionnement
concentré. Tester deux sens explicitement : **correction**, opposé au signe du
funding initial ; **continuation**, de même signe. Un financement positif ne
prouve pas une future baisse du sous-jacent.

Univers figé du précédent filtre public : ses 19 actifs avec 720 heures complètes,
PONS exclu pour couverture, pas pour rendement. Période 7 août–6 septembre exclusif.
Comparaison séparée BTC/ETH/SOL/HYPE, 10 mars–6 septembre, données déjà locales.
Le biais de sélection par volume courant et de survivance interdit une promotion.
Ne pas agréger ces deux cohortes de durées différentes en un rendement.

Avant une entrée dans la bougie i, utiliser uniquement les taux des douze heures
précédentes : moyenne A des heures i−12 à i−5 ; moyenne B de i−4 à i−1.
Signal si |A| >= 0,00005 par heure (0,5 bp/h), et −0,25 <= B/A <= 0,5.
Il faut donc une réduction d'au moins moitié ; un petit retournement de signe
est permis. Seul le premier signal d'une condition continue est candidat.
Espacement minimal 73 heures par actif, identique dans les deux sens et tous
les scénarios. Ne pas retoucher seuils, univers ou horizon après résultat.

## Causalité, exécution et coûts

Taux natifs conservés avec timestamps exacts, également regroupés à l'heure
pour le signal ; doublons, trous et valeurs non finies refusés. Aucun taux
annoncé futur utilisé. Entrée hypothétique au prix open de i, **horodatée i+60 s**,
sortie après 24 h au même décalage. Ce prix n'est pas une quote prouvée à +60 s.
Conserver seulement les paiements dont le timestamp natif est strictement après
l'entrée et au plus à la sortie. Valorisation au prix open de l'heure du paiement
comme proxy de l'oracle (la documentation officielle utilise l'oracle spot).

Horizon principal 24 h ; 6 h et 72 h descriptifs, sans sélection du meilleur.
Central : taker 4,5 bps/côté, slippage 2 bps/côté ; stress coûts 9/5 bps.
Retard : décision appliquée une heure plus tard. Funding adverse : tous les taux
sont des débits absolus. Contrôle sans aucun coût. Quantité constante durant
chaque événement, rendement par dollar notionnel, pas portefeuille composé.

Signaler moyenne/médiane nettes, profit factor, pire événement, résultat sans
le meilleur, contributions par actif et signe, gains/pertes par bloc de dix jours
(altcoins) ou trente jours (majors). Aucun bloc rouge n'est un veto isolé.
Intervalle descriptif 97,5 % par blocs de sept jours, 5 000 tirages, graine
20260907, uniquement si >=30 événements et >=20 jours d'entrée distincts.
Cette correction locale pour deux sens ne corrige pas toutes les recherches.

Poursuivre une règle si total net positif dans les quatre scénarios payants,
PF central >1,2 et résultat positif sans meilleur événement. Un intervalle
contenant zéro reste une incertitude, pas une validation. Tout candidat exige
une autre période gratuite et simulation réelle de portefeuille : capital
1 000 $, sizing et arrondis, frais, financement, positions ouvertes, drawdown
20 % depuis le sommet, dépassements conservés. Ces statistiques d'événements
ne valident ni le capital ni le risque. Aucun GO issu de cette seule étude.

## Acquisition et preuves

Réutiliser le client public existant et les financements archivés. Au plus
19 appels candleSnapshot horaires pour les prix manquants, 10 Mo cumulés,
zéro clé ; CASHCAT réutilisé si sa couverture complète est identifiable.
Archiver requêtes/réponses, SHA-256, couverture, offsets des paiements,
volumes nuls, code et protocole. Reproduire les sorties offline à l'identique.

Source mécanique consultée avant l'étude :
[funding Hyperliquid](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding.md).

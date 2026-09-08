# Chocs résiduels couverts : nouvelle hypothèse de retour à la moyenne

Hypothèse distincte du funding : un mouvement d'altcoin inhabituel par rapport
à BTC peut se corriger, avec une couverture du mouvement commun du marché.
Ce n'est ni une égalité de prix ni une cointégration supposée.

## Univers, données et causalité

Les 18 actifs complets du test de transfert, plus BTC comme couverture. Panel
natif 10 mars–6 septembre, 180 jours, entièrement local. CASHCAT exclu pour la
couverture antérieure déjà constatée. Univers courant et prix déjà consultés :
pas de holdout indépendant. Aucun téléchargement, achat ou ordre.

À l'entrée dans la bougie i, utiliser les closes jusqu'à i−1 seulement. Modèle
OLS des rendements logarithmiques **sur 28 blocs de six heures**, immédiatement
antérieurs au dernier bloc de six heures servant au signal. Le dernier retour
d'entraînement finit en i−7 ; le signal va du close i−7 au close i−1.
Les blocs d'entraînement ne se recouvrent pas, le signal en est exclu.

Réutiliser fit_return_hedge : alpha, bêta, sigma résiduel avec n−2 degrés de
liberté, corrélation. Exiger bêta entre 0,25 et 4, corrélation >=0,3,
sigma >=0,005 (0,5 % par bloc de six heures). Signal si **3 <= |z| < 6**.
Premier franchissement de la condition ; espacement 25 h par actif, commun à
tous les scénarios et horizons. Vendre l'altcoin si z positif, l'acheter si
z négatif ; BTC prend le sens opposé.

## Événements et coûts

Horizon principal **six heures** ; 24 h uniquement descriptif, sans sélectionner
le meilleur résultat. Bêta figé à l'entrée, poids notionnels 1/(1+bêta) pour
l'altcoin et bêta/(1+bêta) pour BTC, somme égale à un dollar brut de panier.
Quantités constantes par jambe ; pas de rééquilibrage fictif.

Entrées/sorties hypothétiques open+60 s avec prix open. Même code de paiement
timestampé que l'étude funding : aucun paiement avant l'entrée, valorisation
à l'open comme proxy de l'oracle. Taker central 4,5 bps/côté et slippage 2 pour
les deux jambes ; stress 9/5, retard supplémentaire 1 h, funding adverse,
contrôle sans aucun coût. Le funding n'intervient pas dans le signal.

Publier rendements par dollar de panier brut, moyenne/médiane/PF, pire événement,
total sans meilleur, contributions par actif et sens, blocs de trente jours.
Intervalle descriptif à 95 % via blocs de sept jours, 5 000 tirages, graine fixe,
si au moins 30 événements et 20 dates d'entrée. Réutiliser le bootstrap existant.
Pas de correction globale pour les recherches antérieures ni de prévision.

Poursuivre vers un portefeuille si les quatre scénarios payants sont positifs
au principal six heures, PF >1,2 et total positif sans meilleur événement.
Un bloc rouge n'est pas un veto. Un passage reste exploratoire : ensuite,
capital 1 000 $, sizing/arrondis et positions simultanées, drawdown 20 %,
comparateurs et réplication doivent être traités avant un GO.
Pas de changement de seuil, d'actif, de sens ou d'horizon après échec.

Archiver protocole, code, sources/checksums, modèles d'entrée et tous les
événements. Reproduire les résultats offline. Aucun changement serveur.

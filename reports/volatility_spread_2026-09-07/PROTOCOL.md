# Panier relatif de volatilité — protocole avant PnL

Hypothèse : acheter les trois actifs à plus faible volatilité passée et
vendre les trois à plus forte volatilité peut produire un écart net positif.
Cette hypothèse ne suppose pas qu'un actif calme monte ou qu'un actif agité
baisse. Aucune condition de tendance, funding ou identité d'actif.

Chaque lundi00h UTC, utiliser les31 clôtures espacées de24h se terminant
à la bougie i-1. Calculer les30 rendements logarithmiques quotidiens puis
leur écart-type échantillonnal (diviseur29), sans plancher pour le classement.
Il faut721 bougies antérieures. Classer par volatilité croissante ; acheter
les trois premiers, vendre les trois derniers, notionnels initiaux égaux.
Abstention de tout le panier si égalité à une frontière de sélection.
Conserver168h. Pas de recalibrage ni retrait d'actif après résultat.

Panneaux existants : Hyperliquid18 sur204 jours, sous-panel15 mêmes dates,
transfert Binance15 sur2025. Les deux sélections existantes seront checksumées.
Les périodes ont déjà servi à la recherche ; pas de validation indépendante
de la sélection des hypothèses. Pas de nouvel appel de données ni achat.

Premier filtre événementiel : chaque jambe reçoit1/6 du notionnel brut
initial du panier. Prix proxy open à +60s, frais4,5bps/slippage2bps par
transaction ; stress9/5 ; entrée et sortie retardées1h ; funding adverse
en valeur absolue ; zéro coût descriptif. Sorties retardées couvertes.
Les fundings portent sur la quantité initiale constante et les paiements
réellement traversés. Débiter fermeture et réouverture chaque semaine même
si un actif reste sélectionné : pas d'économie de compensation présumée.

Publier les contributions long/short, actif et panier. Le contrôle descriptif
achète les mêmes six actifs à notionnels égaux, mêmes dates et coûts ; il ne
sera pas promu après résultat. L'équilibre notionnel long/short du panier
principal ne constitue pas une neutralité au bêta ou au risque de marché.

Pour justifier une simulation native : sur chaque panneau, >=20 paniers,
moyenne nette positive dans les quatre scénarios payants et borne inférieure
95 % de la moyenne centrale positive. Bootstrap7jours/5 000 tirages sur
calendrier complet à partir du premier panier, jours sans entrée inclus ;
un panier est une observation, ses six jambes ne sont pas indépendantes.
Les intervalles restent descriptifs et non corrigés pour les recherches.

Ce filtre ne simule ni capital partagé, ni lots/minimums, ni marge/drawdown.
Si réussi, utiliser le moteur natif avec1 000 $, caps fixes0,5/1,5x et risque
30 % (comparaison20 %), sensibilité infrastructure0/20 $ par30 jours.
Sinon archiver l'échec et changer de mécanisme, sans recherche de paramètres.
Aucun rendement mensuel ni GO live déduit du seul filtre.

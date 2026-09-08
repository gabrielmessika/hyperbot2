# Modèle conditionnel avec apprentissage chronologique

Avant PnL, fixer une régression linéaire ridge, sans recherche de paramètres.
Trois panneaux existants : Hyperliquid18 /204 jours, Hyperliquid15 mêmes dates,
Binance15 /2025. Chaque panneau apprend séparément ; aucun poids appris sur
les données futures de l'autre panneau. Aucun nouvel appel ni achat.

Prédire le rendement arithmétique open->open des six prochaines heures,
divisé par sigma_horaire*sqrt(6). Sigma = écart-type échantillonnal des
168 rendements log horaires antérieurs, plancher0,001 (0,1 % horaire).
Une observation par actif toutes les six heures UTC, avec au moins169
bougies antérieures. Évaluation événementielle à quantité constante.

Huit variables fixées, toutes arrêtées à la bougie i-1 : rendements log
1/6/24/168h divisés par sigma*sqrt(horizon) ; log(volume moyen6h /médiane
volume168h) ; somme du funding réalisé des24 heures précédentes /0,001 ;
rendement24h relatif à la médiane des actifs /sigma*sqrt(24) ; interaction
du rendement1h normalisé et du signal de volume /5. Borner chaque variable
à [-5,5]. Aucun identifiant d'actif ni sélection nominative.

Réentraîner le premier jour de chaque mois UTC, seulement après90 jours
d'historique. Fenêtre d'entraînement glissante90 jours, uniquement observations
dont le label est disponible au moins1 heure avant le réentraînement.
Disponibilité du label = horaire de sortie+60 secondes. >=1 000 observations
d'entraînement requises ; sinon abstention pour le mois, sans élargissement
de fenêtre. Standardiser les variables sur l'entraînement uniquement.
Objectif : moyenne des erreurs quadratiques +1*norme² des coefficients ;
intercept non pénalisé. Borner le label normalisé d'entraînement à [-5,5],
mais conserver les rendements réalisés complets pour l'évaluation.

Pendant le mois suivant, modèle gelé. Long si prévision brute >=0,004,
short si <=-0,004 ; sinon pas de trade. Seuil fixe40 bps sur6h, sans balayage.
Contrôle : prévision par l'intercept seul, même seuil. Publier aussi les
erreurs de prévision sur toutes les observations testées ; elles sont un
diagnostic, pas un objectif de profit. Aucune sélection sur les labels test.

Scénarios usuels : frais4,5bps/slippage2bps, stress9/5, entrée/sortie
retardées1h, funding adverse, zéro coût. Réutiliser la comptabilité des
événements ; garde6h et prix proxy open à +60s. Sorties des scénarios couvertes.
Ni ticks/lots, capital partagé, marge ou limite de drawdown validés à ce stade.
Résultats en bps du notionnel, aucune conversion en rendement mensuel garanti.

Filtre pour justifier un portefeuille : sur chacun des trois panneaux,
>=30 événements et>=30 jours, moyenne nette positive sur les quatre
scénarios payants, borne inférieure95 % de la moyenne centrale positive.
Bootstrap descriptif7jours/5 000 tirages sur calendrier d'évaluation complet,
jours sans signal compris. Signaler concentration, comparaison à l'intercept
et erreurs ; ne pas retirer de mois/actif après résultat.

Si ce filtre passe, simuler ensuite capital partagé1 000 $, cap fixe et
drawdown30 % avec moteur natif. Aucun GO automatique : essais antérieurs et
périodes déjà consultées empêchent de présenter cette procédure comme une
validation prospective. Tester purge des labels, standardisation passée,
variables causales et solution ridge sur exemples analytiques avant PnL.

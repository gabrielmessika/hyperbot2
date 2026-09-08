# Cassures avec volume : comparaison de drawdown 20 % /30 %

Demande utilisateur pendant la préparation de l'extension historique : accepter
un drawdown de 30 % si cela améliore l'espérance de gains. Enregistrer cette
comparaison avant de calculer les scénarios à 30 %. Aucune garantie de gain.

Même contrôle de cassure avec volume, même univers 18 altcoins, même panel
10 mars–6 septembre exclusif /180 jours. Conserver tous les paramètres du
contrôle `compression_breakout`, y compris chauffe193, espacement25, hold24.
L'étude est sélectionnée après résultat positif du contrôle : pas holdout.

Comparer capital1 000 $, caps bruts d'entrée **0,5x /1x /1,5x** et seuils
d'arrêt **20 % /30 %** depuis le sommet, latent et coûts inclus. Pas de montée
de taille après une perte ; chaque scénario commence avec son paramètre fixe.
Arrêt définitif au franchissement observé, sortie au prochain open+60 s,
dépassements conservés. Le moteur accepte ces deux seuils uniquement ; marge
stress 20 % du notional et levier de configuration 2 restent inchangés.

Frais/slippage centraux 4,5/2 bps par côté, stress9/5 ; retard1 h ; funding
adverse ; contrôle zéro coût. Infra0 et20 $/30 jours hypothétiques. Quantités,
minimums, partage du capital, funding timestampé et enveloppe OHLC identiques.
Réexécuter les trente portefeuilles 20 % et vérifier l'identité économique
avec les anciens artefacts, hors ajout explicite du champ de seuil et labels.

Rapporter net, mensuel composé équivalent, mois, drawdown observé/enveloppe,
concentration, pire cycle, durée sous sommet, marge et arrêts. Un mois rouge
n'est pas un veto. Filtre préliminaire par seuil : quatre scénarios payants
positifs, enveloppe <=seuil, marge observée et enveloppe sans rupture.
Comparer l'économie aux cibles envisagées 10 % et15–20 %, sans transformer
un rendement historique ou une hausse de tolérance en espérance garantie.

Un candidat positif doit ensuite être vérifié sur l'extension antérieure
gratuite en préparation, puis sur exécution et incertitude. Aucun GO produit
par cette calibration sur les mêmes données, aucun achat, ordre ou serveur.

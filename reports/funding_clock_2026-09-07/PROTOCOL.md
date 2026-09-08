# Prix après un règlement de funding anticipé

Hypothèse enregistrée avant calcul : après un funding important, la pression
liée au paiement peut se relâcher. Tester une position dans le sens du taux
précédent : long après un taux positif, short après un taux négatif. C'est
une hypothèse de mouvement de prix, pas une promesse de collecter le funding.

Premier filtre uniquement sur les 15 actifs Binance 2025 déjà acquis, sans
nouveau téléchargement. Pour chaque paiement précédent, connu depuis plusieurs
heures, si |taux| >=0,001 (10 bps par règlement), prévoir le prochain horaire
à partir de son intervalle de 4 ou 8 heures. Ne jamais utiliser le taux du
paiement à venir pour choisir le signal. Garder les prédictions même si
l'horaire réalisé diffère ; mesurer leur concordance sans filtrage futur.

Entrée principale au prochain horaire prévu +60 secondes, prix proxy open
horaire, maintien 1 heure. Contrôle apparié : même direction issue du même
signal, entrée deux heures plus tard, maintien 1 heure. Stress de retard :
entrée/sortie principales retardées d'une heure. Exiger les prix de sortie
des trois fenêtres avant de retenir un événement, sans sélectionner selon PnL.
Chaque actif est évalué séparément, pas de compte partagé à ce premier filtre.

Réutiliser la comptabilité événementielle existante : quantité constante par
notionnel d'entrée, frais sur entrée/sortie, funding signé uniquement pendant
la détention. Scénarios central4,5bps/2bps, coûts9bps/5bps, retard1h,
funding adverse, zéro coût descriptif. Coûts Hyperliquid de référence sur
données Binance, pas un backtest natif. Ce filtre n'inclut ni lots/minimums,
ticks, capital partagé, marge ni preuve de fills ; résultats en bps, pas en
rendement mensuel du capital. Aucun dollar fictif de profit n'est crédité.

Publier événements, nombre de jours distincts, signes, actifs, rendements
centraux/stressés, contribution et pire événement. Comparer le résultat
principal au contrôle +2h. Bootstrap descriptif apparié : blocs de 7 jours,
5 000 tirages, calendrier complet incluant jours sans événement ; réutiliser
l'outil existant. Intervalle95 %, non corrigé pour les autres recherches.

Filtre pour justifier un portefeuille et une réplication native : >=30
événements sur >=30 jours, moyenne principale positive sous central/coûts/
retard/funding adverse, borne inférieure95 % de l'avantage net central sur
contrôle >0. Examiner la concentration, sans retirer d'actif après résultat.
Si le filtre échoue, suspendre cette règle sans inverser son signe ou
optimiser son horaire/seuil. Pas d'achat, de client signé ou de trading réel.

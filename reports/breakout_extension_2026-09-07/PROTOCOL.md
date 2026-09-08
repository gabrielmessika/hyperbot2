# Extension antérieure de la cassure avec volume

Étude enregistrée après le résultat positif du contrôle sans compression,
avant téléchargement/calcul sur la fenêtre supplémentaire. Il s'agit d'une
nouvelle vérification du contrôle sélectionné, pas de sa promotion immédiate.
La sélection après examen reste une limite explicite.

## Données gratuites et règle inchangée

Fenêtre supplémentaire : **14 février–10 mars 2026 exclusif**, 24 jours.
Elle doit rentrer dans la rétention des 5 000 dernières bougies horaires.
Même univers fixé de 18 altcoins que `funding_transfer/selection.json` ;
aucun retrait selon résultats. Client public existant, au plus **54 appels**
(un candleSnapshot et deux pages fundingHistory par actif), 5 Mo de réponses,
requêtes séquentielles espacées de trois secondes. Arrêter sur erreur/budget,
conserver réponses, manifeste et hashes. Aucun secret, achat ou ordre.

Exiger toutes les heures de prix et funding, identités cohérentes et absence
de volume nul avant simulation avec le moteur actuel. Si cette qualification
échoue, conserver le diagnostic sans combler les trous ni inventer de fills.

Signal identique au contrôle : close au-delà du plus haut/bas des 24 heures
précédentes et dans le sens de sa propre bougie, volume >=deux fois la médiane
de ces 24 heures. **Aucun filtre de compression**. Conserver le démarrage
à l'index 193 de l'étude initiale, même s'il dépasse le besoin minimal du
contrôle, espacement 25 heures par actif et détention 24 heures. Pas de
retouche de seuil, côté, horizon ou univers selon le résultat.

## Mesures fixées

Deux simulations : fenêtre antérieure seule (24 jours, chauffe comprise), puis
**courbe continue du 14 février au 6 septembre exclusif**, 204 jours sans reset
au 10 mars. Capital 1 000 $, cap brut d'entrée **0,5x seulement**, allocations,
arrondis/minimums et moteur identiques. Aucun nouveau levier pour viser 10 %.
Les positions/cooldowns hérités peuvent changer les trades après le 10 mars ;
ne pas additionner deux comptes réinitialisés pour annoncer le net continu.

Cinq scénarios inchangés : central frais/slippage 4,5/2 bps par côté, coûts 9/5,
retard 1 h, funding adverse, zéro coût de trading/funding. Infra 0 et
20 $/30 jours hypothétiques. Entrée/sortie open+60 s aux opens supposés,
funding timestampé et oracle approché par open. Marge cross hypothétique,
levier de configuration 2, maintenance stress 20 % du notional, snapshot
natif vérifié. Suite à l'accord utilisateur reçu avant acquisition, comparer
les seuils de drawdown **20 % et30 %**, à taille0,5x inchangée. Leur franchissement
observé entraîne arrêt définitif, overshoots
conservés ; publier latent, enveloppe OHLC, marge, mois et temps sous sommet.

Le résultat antérieur négatif n'est pas à lui seul un veto : évaluer le net
continu et son risque, sans effacer les pertes. Le passage préliminaire exige
les quatre scénarios payants continus positifs, enveloppe <=seuil testé et aucune
rupture de marge. Publier aussi concentration par actif, dépendance aux meilleurs
cycles et sensibilité aux coûts pour interpréter une éventuelle réussite.

Comparer les équivalents mensuels historiques à **10 %**, et conserver la
référence 15–20 % ; aucune garantie. 24 jours supplémentaires ne suffisent
pas à prouver une robustesse annuelle ou des fills réalistes. Une réussite
reste non qualifiée ; une faiblesse globale conduit à suspendre puis chercher
un autre mécanisme. Reproduction offline et preuves SHA-256 obligatoires.

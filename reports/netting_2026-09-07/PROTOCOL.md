# Qualification des positions nettes : volumes minimaux et risque

Avant calcul, auditer le portefeuille partagé 50/50 déjà étudié, caps1,5x
et2x, cinq scénarios et deux sensibilités d'infrastructure. Ne changer ni
signaux, quantités acceptées, dates d'entrée/sortie, poids ou historique.
Même panel204 jours. Étude de qualification, pas nouvelle optimisation.

Reconstruire à chaque transaction la somme signée des changements de positions
sur chaque actif natif, toutes sous-stratégies confondues. Contrôler lots
natifs et montant de chaque delta non nul au prix d'exécution supposé du
scénario. Le minimum documenté est10 $ ; aucune exception reduce-only ne sera
présumée. Classer les deltas trop petits : ouverture/augmentation, réduction,
inversion. Conserver aussi les annulations exactes sans transaction nette.

Comparer nombre et notionnel des jambes virtuelles aux deltas nets, sans
créditer de nouveaux gains ou d'économies de frais. Un delta non réalisable
bloque la qualification de la traduction directe, même si son effet semble
petit. Il ne faut pas supprimer la transaction et continuer à utiliser
gratuitement sa position cible dans un backtest présenté comme exécutable.

Auditer le risque après compensation sur les positions nettes, en conservant
l'equity originale et donc **tous les coûts conservateurs déjà facturés**.
Avant/après chaque transaction, comparer exposition nette et brute virtuelle.
Pour chaque heure et actif, l'enveloppe utilise la plus grande position positive
et la plus grande position négative présentes aux deux frontières. Appliquer
leurs mouvements adverses/favorables OHLC ; les mouvements opposés sont
additionnés par prudence. Référencer le même open et les mêmes phases de cash
que le moteur initial, déduites des quantités, prix et coûts timestampés.
L'enveloppe reste un majorant de recherche, pas un chemin de prix observé.

Si sa reconstruction exacte exige une donnée absente, publier seulement les
mesures prouvables et bloquer la qualification correspondante. Aucun fill ou
prix intraminute inventé. Une baisse du risque brut virtuel ne valide pas
l'exécution ni le rendement futur. Pas de hausse du cap selon le résultat.

Rapporter exceptions de taille, fréquence des positions opposées, brut/net,
coûts originaux et statut ; préserver les SHA-256 des cycles et données.
Avant un GO : planner natif causal, traitement des ajustements non réalisables,
frais/funding/capital après exécution et validation indépendante restent requis.
Aucun ordre, signature, achat, service ou serveur modifié.

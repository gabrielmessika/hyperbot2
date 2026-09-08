# Ajustement de couverture avant calcul des rendements anciens

Les quatre requêtes gratuites donnent 644 bougies BTC/ETH/SOL et seulement
640 HYPE : première bougie HYPE le 5 décembre 2024, pas le 1er décembre.
Le validateur a arrêté l'étude sur ce défaut d'alignement **avant la boucle
de calcul des paniers** ; aucun résultat ancien n'a été obtenu.

La fenêtre initiale de l'extension n'est donc pas complète. Ajustement explicite
et purement mécanique : intersection des couvertures quotidiennes des quatre
actifs, soit 5 décembre 2024–6 septembre 2026 exclusif. Garder l'univers,
la règle 30 jours / 7 jours, les jeudis, tous les coûts et les critères.
Utiliser les raws déjà téléchargés, aucun nouvel appel de prix. Enregistrer
cet ajustement avant le premier rendement ancien. Ne pas choisir une autre
date en fonction du résultat obtenu.

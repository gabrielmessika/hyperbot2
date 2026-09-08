# Extension gratuite de la tendance lente

Enregistrée après les trois premiers calculs, avant lecture de nouveaux prix.
Force relative fragile aux coûts, portage relatif négatif : suspendre ces règles.
Tendance 30 j / détention 7 j positive sur 21 paniers, y compris en stress,
mais permutation non convaincante et échantillon insuffisant. Ne pas la promouvoir.

Tester la profondeur gratuite quotidienne de l'API native, BTC/ETH/SOL/HYPE,
du 1er décembre 2024 au 6 septembre 2026 UTC exclusif. Date fixe commune après
le lancement de HYPE ; si un coin ne dispose pas de la couverture, rapporter
l'échec sans modifier discrètement l'univers ou la date. Quatre requêtes 1d,
pas de clé. Réutiliser le funding déjà local ; acquérir uniquement la période
antérieure manquante si les prix bruts ne rejettent pas la règle.

Signal inchangé : close de la veille / open du début des 30 jours clos,
signe par actif. Entrées le jeudi 00:00 UTC (alignement de la campagne initiale),
à partir de 30 jours de chauffe, sortie sept jours plus tard. Les 644 jours
potentiels incluent l'échantillon déjà étudié : publier ancien segment et
recouvrement séparément, sans déclarer le tout indépendant ou OOS.

Premier filtre bon marché : rendement brut moyen de la règle doit être positif
sur le segment antérieur aux 180 jours déjà vus. Sinon arrêt de l'extension,
pas de téléchargement de funding et pas de nouvelle durée de signal.
Ce filtre rejette l'hypothèse de prévision des prix, sans prétendre borner tout
gain possible de funding. Si positif, compléter funding gratuitement pour
calculer coûts et stresses, ainsi que le benchmark long aux mêmes dates.

L'historique ancien n'a que des bougies quotidiennes : le prix servant à
valoriser le funding horaire est approximé par l'open du jour. Le stress de
délai ancien est d'un jour, sans déplacer le signal. Aucune précision horaire
inventée. Sorties exigées dans la fenêtre pour tous les scénarios. Budgets
maximums 110 requêtes / 25 Mo / 10 minutes ; pas de tâche permanente.

Pour poursuivre la recherche : base et stress positifs dans l'ancien segment,
au moins 30 paniers anciens, PF > 1,2, intervalle bootstrap familial favorable
et permutation de signes favorable selon le protocole principal. Ces critères
restent nécessaires mais pas suffisants pour simuler un compte sous limites de
risque. Pas d'achat si la route gratuite échoue. Tous les résultats conservés.

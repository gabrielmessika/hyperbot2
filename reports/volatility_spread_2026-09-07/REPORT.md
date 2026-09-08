# Acheter les faibles volatilités et vendre les fortes : hypothèse rejetée

**Le panier long/short perd sur les trois panneaux, même sans coûts.**
Les achats des actifs calmes sont positifs, mais les ventes des actifs les
plus volatils les dépassent en pertes. Aucun GO ni simulation native justifiés
par le filtre principal. Le contrôle acheteur mérite au plus une nouvelle
épreuve historique explicitement sélectionnée après ces résultats.

## Règles figées et données

Chaque lundi00h UTC : trois achats aux plus faibles volatilités quotidiennes
passées et trois ventes aux plus fortes. Écart-type échantillonnal sur30
rendements, prix arrêtés à la dernière bougie terminée. Notionnels initiaux
égaux, détention168h, aucune condition de tendance. Abstention aux égalités
de frontière ; aucune rencontrée dans les panneaux réels.
[Protocole](PROTOCOL.md), [enregistrement avant PnL](registration.json).

Réutilisation des données contrôlées : Hyperliquid18 et sous-panel15 sur204
jours2026, archives Binance15 sur2025. Après l'historique minimal,23 paniers
natifs à partir du23 mars2026,47 paniers de transfert à partir du3 février2025.
Le choc du19 janvier2025 n'est donc pas couvert par les positions de ce test.
Les six jambes d'un panier ne sont pas six observations indépendantes.

Prix proxy open horaire à +60s. Frais4,5bps/slippage2bps par transaction,
stress9/5, retard1h, funding adverse, zéro coût. Paiements seulement pendant
la détention réelle simulée ; fermeture et réouverture payées chaque semaine,
y compris les actifs conservés. Pas d'économie de compensation inventée.

## Panier principal

Moyennes en points de base du **notionnel brut initial du panier**.
100bps=1 %. Ce ne sont pas des rendements sur le compte de1 000 $.

| Panneau | Paniers | Central net | Coûts renforcés | Retard1h | Funding adverse | Zéro coût |
|---|---:|---:|---:|---:|---:|---:|
| Hyperliquid18 | 23 | −191,53 | −206,85 | −189,01 | −219,74 | −180,70 |
| Hyperliquid15 | 23 | −102,38 | −117,60 | −103,59 | −129,87 | −90,65 |
| Binance15,2025 | 47 | −80,69 | −95,85 | −79,24 | −114,56 | −65,94 |

Les intervalles descriptifs95 % de la moyenne centrale sont respectivement
[−471,95 ;+57,39], [−330,46 ;+96,76] et [−293,96 ;+84,40]bps. Bootstrap7jours,
5 000 tirages, calendrier complet depuis la première sélection ; jours sans
entrée inclus. Aucun panneau ne passe les critères de signe après coûts
et de borne inférieure positive. Le critère de20 paniers est satisfait.

Paniers gagnants11/23,10/23 et25/47 ; profit factors0,439 /0,603 /0,717.
Pire panier central−14,57 %,−12,77 % et−23,48 % du notionnel brut. Ces pertes
hebdomadaires ne sont pas un calcul de drawdown intrapériode.

La contribution des achats calmes est positive dans les trois panneaux,
mais insuffisante. En natif18, les ventes PUMP, ZEC et LIT dominent les pertes.
Dans le transfert2025, la contribution ZEC est−4 888,40bps cumulés de panier,
supérieure à la perte agrégée en valeur absolue. Aucun actif retiré après PnL.

## Contrôle acheteur : positif, incertain et concentré

Le contrôle achète les mêmes six actifs, aux mêmes dates et aux mêmes poids.
Il reste directionnel ; le panier principal, équilibré en notionnels, n'était
pas pour autant neutre au bêta. Aucun des deux n'a une marge qualifiée ici.

| Panneau | Central net moyen | Coûts renforcés | Retard1h | Funding adverse | IC95 % central |
|---|---:|---:|---:|---:|---:|
| Hyperliquid18 | +278,57bps | +263,26bps | +273,81bps | +269,10bps | [−112,92 ;+834,33] |
| Hyperliquid15 | +189,56bps | +174,35bps | +188,54bps | +178,87bps | [−174,61 ;+687,08] |
| Binance15,2025 | +134,35bps | +119,21bps | +137,55bps | +99,53bps | [−148,56 ;+468,69] |

Les quatre scénarios payants sont positifs partout, mais aucune borne
inférieure ne l'est. La semaine du17 août2026 rapporte à elle seule48,47 %
du notionnel brut en natif18 et41,59 % en natif15. Le meilleur panier2025
(29 septembre) rapporte33,51 %. Le contrôle subit aussi des semaines de
−12,37 %,−13,08 % et−20,18 % respectivement. Ces profils interdisent de
convertir la moyenne hebdomadaire en une espérance mensuelle stable.

Le contrôle n'est pas promu. Son choix éventuel pour une nouvelle étude
serait **postérieur à ces résultats**. Un test gratuit plus ancien pourrait
falsifier cette nouvelle hypothèse sans changer le classement ni les poids.
Les lots, minimums, inventaire natif, capital partagé et arrêt30 % restent
à simuler avant tout jugement de rentabilité sur1 000 $.

## Décision et livraison

Statut **VOLATILITY_SPREAD_HYPOTHESIS_NOT_CONFIRMED**. Archiver le long/short ;
ne pas inverser opportunément les signaux et les présenter comme validés.
Les périodes et univers actuels ont déjà servi à la recherche ; même une
nouvelle période ne supprimerait pas tout biais de sélection/survivance.
Le transfert utilise prix et funding Binance avec coûts de référence
Hyperliquid ; il ne qualifie pas l'exécution native Hyperliquid2025.

Douze artefacts reproduits octet pour octet ; classements, agrégation des
six jambes et signes des contrôles audités. Quatre nouveaux tests couvrent
volatilité analytique sans tendance, causalité, frontières ex aequo, calendrier
et sortie retardée, données invalides. Suite complète319 tests ; lint/format308
fichiers et mypy74 sources passent. [Reproduction](reproduction.json),
[revue](review.json), résultats détaillés dans les résumés par panneau.

Aucun nouvel appel de marché, achat, ordre réel, service ou serveur modifié.
Tous les calculs sont terminés. Recherche active. Prochaine étape : qualifier
gratuitement une période antérieure pour le contrôle acheteur, figer son
statut de nouvelle hypothèse sélectionnée après résultat, puis vérifier le
risque natif si les preuves économiques justifient de continuer.

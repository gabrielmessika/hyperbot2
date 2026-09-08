# Panier acheteur : trois périodes positives, avantage non confirmé

**Mise à jour : le diagnostic du compte1 000 $ échoue au filtre de risque
entre périodes.** Voir [le diagnostic de capital](../volatility_capital_2026-09-07/REPORT.md).
Les moyennes événementielles ci-dessous sont conservées ; elles ne représentent
pas les gains d'un compte soumis à son arrêt global.

**L'épreuve2024 est positive après coûts, mais ne permet pas de donner un GO.**
Le panier gagne en moyenne sur les trois panneaux ; les bornes statistiques
restent négatives et son avantage sur l'achat de tout l'univers est incertain.
La rentabilité d'un compte1 000 $ avec arrêt30 % n'est pas encore calculée.

## Correction de données explicitement qualifiée

Les ZIP originaux sont inchangés. Le loader les rejette toujours par défaut
en raison des bougies de volume nul. Une option explicite construit une
vue dérivée donnant priorité à REST aux deux heures du28 octobre2024, pour
les onze actifs. Les744 heures REST d'octobre sont validées, et toutes les
autres bougies OHLCV doivent être identiques aux archives. Une correction
incomplète, supplémentaire, de volume nul ou appliquée à2025 échoue.

La priorité de sources est une convention de recherche documentée, pas une
preuve de prix réellement exécutables. Sources/checksums et version de
correction sont dans la qualité. [Amendement](SOURCE_AMENDMENT.md),
[enregistrementv2 avant PnL2024](economic_registration_v2.json),
[validation](overlay_validation.json). Aucun nouvel appel public nécessaire.

La vue dérivée couvre8 784 heures pour chacun des onze actifs, sans trou
ni volume nul.22 bougies remplacées,8 162 bougies d'octobre inchangées.
Les calendriers de funding restent ceux des archives, vérifiés intégralement.

## Résultats événementiels sur le même univers11

Règle figée : acheter chaque lundi trois actifs aux volatilités passées les
plus faibles et trois aux plus fortes, notionnels initiaux égaux, détention168h.
Contrôle : achat équipondéré hebdomadaire des onze actifs. Le classement ne
prévoit pas la direction des prix ; les deux portefeuilles théoriques sont longs.

Moyennes en bps du notionnel brut initial du panier,100bps=1 %. Aucun
réinvestissement, minimum d'ordre, marge ou arrêt de risque n'est simulé ici.

| Panneau | Paniers | Central net | Coûts renforcés | Retard1h | Funding adverse | Zéro coût |
|---|---:|---:|---:|---:|---:|---:|
| Binance2024 | 47 | +218,52 | +203,27 | +234,16 | +206,88 | +257,05 |
| Binance2025 | 47 | +88,46 | +73,37 | +94,54 | +62,46 | +103,45 |
| Hyperliquid2026 | 23 | +175,90 | +160,71 | +174,82 | +161,01 | +199,82 |

Les frais/slippage centraux sont4,5/2bps par transaction, stress9/5bps.
L'hypothèse de fill reste un proxy open horaire à +60s. Les moyennes portent
sur des semaines de détention intégralement couvertes après le warmup30 jours,
pas sur toute l'année dès le premier janvier. Premières entrées :5 février2024,
3 février2025 et23 mars2026. Les chocs antérieurs ne sont pas rejoués.

| Panneau | Contrôle central | Avantage moyen | IC95 % avantage | IC95 % rendement candidat |
|---|---:|---:|---:|---:|
| 2024 | +173,08bps | +45,45bps | [−22,31 ;+126,91] | [−108,82 ;+559,37] |
| 2025 | +34,12bps | +54,34bps | [−29,27 ;+149,44] | [−179,54 ;+397,32] |
| 2026 | +176,28bps | −0,38bps | [−104,18 ;+91,96] | [−134,24 ;+580,11] |

Bootstrap descriptif7jours/5 000 tirages, calendrier complet avec jours
sans entrée, panier comme unité et différence appariée au contrôle. Non corrigé
pour les recherches précédentes. Le contrôle comparé à lui-même a mécaniquement
un avantage nul ; son intervalle nul n'est pas une précision prédictive.

## Risque et concentration encore déterminants

En2024,25 semaines sur47 sont positives, PF1,622, pire semaine−20,41 %,
meilleure+28,14 % du notionnel brut. DOGE et XRP dominent les gains.
En2025,23/47 positives, PF1,276, pire−22,96 %, meilleure+33,43 %. ZEC
contribue6 611,94bps cumulés, davantage que le gain agrégé de tous les paniers.
En2026,12/23 positives, PF1,881, pire−13,08 %, meilleure+30,87 %.

Ces écarts empêchent d'extrapoler directement2,19 % par semaine vers un
objectif mensuel. Les ordres réels, le dimensionnement sur capital variable,
les pertes ouvertes et l'arrêt global peuvent changer fortement le résultat.
Un plafond de drawdown accepté à30 % n'est pas une promesse de perte bornée.

## Décision et suite

Statut **VOLATILITY_LONG_POSITIVE_HISTORY_STATISTICAL_GATE_FAILED**. Aucun
panneau ne passe le filtre complet prévu, car aucune borne centrale n'est
positive. L'avantage moyen2024 au contrôle est positif mais non confirmé
statistiquement. Les règles, seuils et comptes d'échantillon n'ont pas été
retouchés. Le choix de cette hypothèse après le contrôle initial reste signalé.

La qualification native comme candidat promu n'est donc pas obtenue. Un
**diagnostic distinct de faisabilité du capital** sera enregistré pour répondre
à la contrainte utilisateur1 000 $/30 % : mêmes signaux, tailles fixes et
benchmark, coûts, lots et arrêt réel du simulateur. Ce diagnostic est choisi
après le présent résultat positif ; il conserve l'échec du filtre statistique
et ne peut pas le transformer en réussite. Il permettra de mesurer si la piste
est économiquement trop faible ou trop risquée, même avant de chercher plus
de confiance statistique.

Douze artefactsv2 reproduits à l'identique ; huit contrôles v1/v2 confirment
les résultats2025/2026 entièrement inchangés (qualité, sélections, événements,
tous scénarios économiques). Quatre nouveaux tests, suite complète325 tests,
lint/format316 fichiers et mypy75 sources passent. [Reproduction](reproduction_v2.json),
[régression économique](v1_v2_economic_regression.json), [revue](review_v2.json).
Tous les calculs sont terminés. Aucun nouvel appel, achat, ordre réel, service
ou serveur modifié. Recherche active, aucune promotion autorisée.

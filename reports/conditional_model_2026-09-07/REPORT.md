# Modèle conditionnel : pas d'avantage confirmé entre périodes

**La régression combinant tendance, volume et funding échoue au filtre fixé.**
Elle est positive sur les archives Binance2025, mais négative sur les deux
panneaux Hyperliquid2026, même sans coûts. Aucun portefeuille ni GO justifié.

## Hypothèse et protocole

Régression ridge à huit variables, horizon6h, régularisation1 et seuil40bps,
fixés avant calcul. Chaque premier du mois, apprentissage sur les90 jours
antérieurs ; seules les cibles connues depuis au moins une heure sont admises.
Normalisation apprise sur ces seules lignes, modèle gelé pendant le mois.
Les cibles d'entraînement sont bornées, les pertes réalisées ne le sont pas.
[Protocole](PROTOCOL.md) et [enregistrement](registration.json).

Trois panneaux existants et vérifiés par checksum, sans nouvelle acquisition :
18 actifs Hyperliquid sur204 jours, leur sous-panel15, et15 contrats Binance
sur2025. Les données Binance constituent un transfert de plateforme, pas des
fills natifs Hyperliquid. Les panneaux apprennent séparément. Les périodes
ont déjà servi aux recherches précédentes : cette procédure chronologique
n'est pas une validation prospective ou indépendante de toute sélection.

Après l'historique minimal, évaluation du1 juin au6 septembre2026 exclu
(97 jours, quatre modèles) et du1 avril2025 au1 janvier2026 exclu
(275 jours, neuf modèles). Respectivement6 966 /5 805 /16 485 prédictions.
Les dernières observations sans sortie retardée couverte sont exclues.

## Résultats événementiels

Moyennes en points de base du notionnel initial par événement ;1bp=0,01 %.
Ces valeurs ne sont ni des dollars de gain, ni des rendements de portefeuille.

| Panneau | Événements /jours actifs | Central net | Coûts renforcés | Retard1h | Funding adverse | Zéro coût |
|---|---:|---:|---:|---:|---:|---:|
| Hyperliquid18,2026 | 144 /28 | −52,86 | −67,84 | −8,29 | −54,89 | −40,14 |
| Hyperliquid15,2026 | 123 /28 | −22,44 | −37,45 | +22,78 | −24,83 | −9,91 |
| Binance15,2025 | 373 /121 | +30,46 | +15,41 | +28,60 | +25,20 | +41,40 |

Central : frais4,5bps et slippage2bps par transaction ; stress9/5bps.
Funding chargé seulement pendant la détention, aux dates historiques.
Entrée/sortie au proxy open horaire à +60s ; zéro coût retire frais,
slippage et funding. Pas de preuve de prix réellement exécutable à +60s,
de lots/ticks, minimums, capital partagé, marge ou drawdown à ce stade.

Bootstrap descriptif par blocs7jours,5 000 tirages, jours sans signaux inclus :
intervalles95 % de la moyenne centrale **[−183,41 ;+5,73]**, **[−140,23 ;+29,92]**,
**[−27,97 ;+83,38]** bps. Aucun n'a une borne inférieure positive. Certains
tirages du sous-panel15 ne contiennent aucun événement ;4 997 ratios définis
sont publiés. Ces intervalles ne corrigent pas les recherches antérieures.

Le filtre exigeait au moins30 événements et30 jours, quatre scénarios payants
positifs et une borne inférieure centrale positive sur chaque panneau.
Aucun panneau ne passe ; celui de2025 passe seulement les deux premiers critères.

## Concentration et contrôle

Les modèles déclenchent surtout des longs :128/144,111/123 et303/373.
Sur Hyperliquid18,135 événements sur144 se produisent en juin ; sur le
sous-panel15,110 sur123. Ce ne sont pas144 ou123 observations indépendantes.
Profit factors centraux0,733 /0,881 /1,168 ; pire événement natif−1 479,33bps.

En2025, ZEC représente127 événements et une somme de12 365,71bps, supérieure
à la somme positive de tous les événements réunis. FARTCOIN représente92
événements et−4 772,71bps. Octobre porte la plus grande somme mensuelle.
Ces sommes sont des diagnostics à notionnels initiaux égaux, sans compte
partagé ni capitalisation ; aucune conversion en performance mensuelle.

La moyenne historique seule, soumise au même seuil, ne déclenche aucun signal
natif et un seul signal2025, perdant. Son intervalle bootstrap dégénéré sur
un événement ne constitue aucune précision statistique exploitable.
Sur **toutes** les prédictions, la régression n'améliore pas l'erreur quadratique :

| Panneau | MSE ridge | MSE moyenne seule |
|---|---:|---:|
| Hyperliquid18 | 1,09403 | 1,08804 |
| Hyperliquid15 | 1,10968 | 1,10282 |
| Binance15 | 1,17175 | 1,17148 |

Cette erreur porte sur les rendements normalisés par la volatilité passée,
pas directement sur des dollars. Elle reste un diagnostic secondaire.

## Décision et vérifications

Statut **CONDITIONAL_MODEL_CROSS_PERIOD_SCREEN_FAILED**. Archiver cette
configuration ; ne pas baisser le seuil, inverser les signaux ou retirer des
actifs après lecture des gains. L'échec ne prouve pas que tout apprentissage
statistique est impossible, mais ne justifie pas ici davantage de risque.

Cinq tests nouveaux : solution ridge analytique et colinéarité, cible bornée,
entrées invalides, embargo exact et normalisation passée, modèle mensuel
gelé malgré des labels futurs modifiés, variables causales. Suite complète
315 tests ; lint/format303 fichiers et mypy73 sources passent.

Quinze artefacts reproduits octet pour octet. Audit des dates de purge,
reconstruction des prévisions depuis les coefficients enregistrés et présence
de tous les signaux franchissant le seuil. Sources/qualité, modèles, prévisions,
événements et paramètres conservés avec SHA-256 ; détail dans
[reproduction](reproduction.json) et [revue](review.json).

Aucun nouvel appel de marché, achat, ordre réel, service ou serveur modifié.
Tous les calculs de cette étude sont terminés. Recherche active : prochaine
hypothèse distincte, panier hebdomadaire long des actifs les moins volatils
et short des plus volatils, sans condition de momentum. Fixer les règles
avant PnL et réutiliser les trois panneaux existants.

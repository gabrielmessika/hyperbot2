# Normalisation du funding : réplication positive, portefeuille non qualifié

**Aucun GO.** Le test principal à 24 h ne confirme ni la correction ni la
continuation. Un résultat exploratoire à 72 h est plus élevé, mais son avantage
sur des comparaisons simples dépend de CASHCAT. Sa réplication antérieure
est désormais positive, avec un échantillon très court et concentré.
Le résultat du test principal demeure inchangé.

## Données et règle figée

[Protocole enregistré](PROTOCOL.md) avant calcul des rendements : funding initial
moyen sur huit heures d'au moins 0,5 bp/h en valeur absolue ; moyenne des quatre
heures suivantes réduite de moitié, avec retournement limité à un quart. Première
apparition de la condition, espacement 73 h par actif, entrée suivante +60 s.
Correction = sens opposé au funding initial ; continuation = même sens.

19 altcoins sur 30 jours, du 7 août au 6 septembre exclusif ; PONS exclu pour
funding incomplet selon le filtre déjà publié. BTC/ETH/SOL/HYPE sont étudiés
séparément sur 180 jours. Les données sont déjà explorées pour d'autres règles ;
pas de holdout indépendant. L'univers altcoin dépend du volume courant, avec
biais de survivance et de sélection.

Tous les financements et les prix CASHCAT/majors sont réutilisés. **18 requêtes
publiques**, **1 758 148 octets**, complètent 12 960 bougies altcoin ; aucune
clé ni dépense. Les 19 × 720 et 4 × 4 320 heures étudiées sont complètes,
sans volume nul. Timestamps natifs des paiements : décalage de 0–134 ms après
l'heure pour les altcoins, jusqu'à 261 ms pour les majors.

Les paiements antérieurs à l'entrée sont exclus. Le décalage hypothétique +60 s
évite notamment de créditer le paiement publié juste après l'open d'entrée.
La [documentation native](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding.md)
définit les paiements horaires et leur valorisation à l'oracle spot. Le calcul
utilise un open horaire comme proxy de cet oracle et du prix d'exécution, sans
prouver qu'une quote était accessible à +60 s.

## Horizon principal : 24 heures

Moyenne nette en points de base **par événement et dollar notionnel engagé**.
Ces chiffres ne sont pas des rendements de portefeuille ni des revenus mensuels.
Central : frais taker 4,5 bps/côté, slippage 2 ; stress : 9/5. Funding signé,
stress adverse, retard d'une heure et contrôle sans coût conservés.

| Cohorte / sens | Événements | Central | Coûts renforcés | Retard | Funding adverse | Sans coût |
|---|---:|---:|---:|---:|---:|---:|
| Altcoins / correction | 40 | −48,71 | −63,78 | −147,50 | −75,68 | −48,90 |
| Altcoins / continuation | 40 | +22,61 | +7,56 | +121,21 | +22,13 | +48,90 |
| Majors / correction | 4 | +348,85 | +334,21 | +354,52 | +338,88 | +356,59 |
| Majors / continuation | 4 | −374,24 | −388,85 | −379,91 | −374,29 | −356,59 |

La continuation altcoin a un PF de seulement **1,12**. Son total est +904,44 bps
additionnés, mais devient **−713,62 bps sans le meilleur événement**. Deux blocs
de dix jours positifs et un négatif ; le bloc rouge n'est pas le motif du rejet.
La comparaison aux autres actifs au même instant donne un excès moyen de
**−81,03 bps**, celle aux entrées périodiques du même actif **−54,09 bps**.

Les quatre événements majors sont tous HYPE. La correction y paraît positive,
mais son total devient également négatif sans le meilleur trade : **−26,99 bps**.
Ce très petit échantillon ne permet aucune conclusion sur BTC/ETH/SOL.

L'intervalle prévu n'est calculé dans aucune cohorte : seulement **19 dates
d'entrée distinctes** pour les 40 événements altcoin, quatre événements majors.
Le minimum enregistré était 30 événements et 20 dates ; pas de baisse du seuil.

## Horizon descriptif : 72 heures

La continuation altcoin affiche **+642,64 bps nets moyens** sur les mêmes
40 événements, +626,83 en stress de coûts, +631,18 avec retard, +640,98 en
funding adverse. PF central 5,70 ; total positif sans le meilleur trade.
Ce résultat, découvert après examen, ne remplace pas l'horizon principal.

**CASHCAT représente 62,19 % du total net pour sept événements sur quarante.**
Le pire événement de la cohorte perd **23,07 % de son notional** à la sortie.
Ce n'est pas un drawdown du compte : sizing et chemin des positions ouvertes
restent à simuler avant toute conclusion sur la limite utilisateur de 20 %.

L'[audit descriptif](controls.json) compare chaque événement à deux repères :
les autres actifs au même instant, dans le même sens ; le même actif avec des
entrées espacées régulièrement de 73 heures. Même modèle de frais/funding.

| Moyenne nette à 72 h | Tous les événements | Sans CASHCAT, sensibilité seulement |
|---|---:|---:|
| Signal observé | +642,64 bps | +294,49 bps |
| Autres actifs au même instant | +366,90 bps | +365,77 bps |
| Même actif, entrées périodiques | +530,98 bps | +348,04 bps |
| Excès contre le marché simultané | +275,74 bps | −71,27 bps |
| Excès contre les entrées périodiques | +111,65 bps | −53,54 bps |

La hausse du marché explique donc une part importante du résultat ; l'avantage
restant dépend de CASHCAT. Ces repères ne corrigent pas le bêta et ne constituent
ni un portefeuille couvert ni un test randomisé. L'exclusion de CASHCAT mesure
la concentration : elle n'autorise pas à sélectionner un nouvel univers.

## Décision et suite

Les quatre tests principaux portent `HYPOTHESIS_NOT_CONFIRMED`. L'anomalie à
72 h reste **exploratoire, concentrée et non qualifiée**. La réplication
ci-dessous justifie d'étudier son portefeuille, sans accorder de GO.

**245 tests passent**, lint et format 222 fichiers passent, mypy 63 sources.
Sept artefacts d'étude/audit sont reproduits exactement : [preuve](reproduction.json).
Anciennes baselines préservées, aucun changement serveur ou ordre réel.

## Réplication antérieure effectuée

[Protocole séparé](REPLICATION_PROTOCOL.md) enregistré avant acquisition :
16 juillet–7 août exclusif, **22 jours**, mêmes 19 actifs/seuils et continuation
72 h. CASHCAT entièrement réutilisé ; **54 requêtes gratuites /2 132 826 octets**
pour les 18 autres actifs. Les 19 × 528 heures sont complètes, sans volume nul.
Le choix de cette période réutilise la couverture du précédent hedge CASHCAT ;
ces données ont donc déjà servi à une autre recherche, pas un holdout pur.

| Scénario 72 h | Moyenne nette par événement | PF | Total sans le meilleur événement |
|---|---:|---:|---:|
| Central | +1 218,12 bps | 4,40 | +1 857,53 bps |
| Coûts renforcés | +1 201,73 bps | 4,31 | +1 719,65 bps |
| Retard 1 h | +726,66 bps | 3,17 | +206,27 bps |
| Funding adverse | +1 216,03 bps | 4,38 | +1 837,93 bps |
| Sans coût | +1 303,15 bps | 4,83 | +2 474,93 bps |

**Dix événements sur six dates**, six CASHCAT et quatre XMR. CASHCAT contribue
**95,96 % du total**, le pire événement perd **31,51 % de son notional**.
Le premier bloc de dix jours est légèrement négatif et le suivant fortement
positif ; le total et les stress passent le filtre, malgré le bloc rouge.

Les contrôles figés donnent −35,20 bps moyens pour les autres actifs au même
instant et +442,36 bps pour les entrées périodiques du même actif. Le signal
les dépasse dans cette fenêtre. Cela ne corrige ni le bêta, ni la concentration,
ni le choix antérieur de l'univers et de l'horizon.

Décision d'examen : [REPLICATION_EVENT_SCREEN_PASSED_PORTFOLIO_UNQUALIFIED](review.json).
Prochaine étape : enregistrer puis simuler une courbe continue sur les 52 jours
disponibles, capital 1 000 $, positions simultanées, arrondis, coûts, financement
et drawdown 20 % depuis le sommet. Conserver les dépassements ; comparer aux
expositions simples. Les 50 événements des deux études ne se concatènent pas
automatiquement en portefeuille : les fenêtres ont des échauffements et fins
distincts, à réconcilier dans une simulation continue.

Les quatre artefacts de réplication sont [reproduits exactement](replication_reproduction.json),
soit onze preuves au total avec l'étude initiale et son audit. Lint/format passent
sur 225 fichiers ; le code source testé reste inchangé (245 tests, mypy 63 sources).
**Aucun rendement mensuel de compte ni respect du drawdown n'est encore validé.**

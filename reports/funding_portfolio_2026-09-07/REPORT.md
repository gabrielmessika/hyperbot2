# Funding 72 h : candidat rentable dans l'échantillon, robustesse à confirmer

**Mise à jour : la promotion est suspendue.** Le [test antérieur de transfert](../funding_transfer_2026-09-07/REPORT.md)
perd de l'argent et dépasse la limite de drawdown sur les 18 autres actifs.
Les chiffres ci-dessous restent le résultat historique court, non généralisé.

**Le portefeuille atteint la cible sur les 52 jours étudiés, mais aucun GO n'est
accordé.** Avec un plafond brut d'entrée de 0,4x, le capital passe de 1 000 $
à **1 280,27 $** après frais, slippage, funding et budget hypothétique
d'infrastructure de 20 $/30 jours. L'équivalent mensuel géométrique est
**+15,32 %**, le drawdown horaire **11,24 %** et l'enveloppe adverse OHLC
**17,85 %**. Ces valeurs décrivent ce backtest, pas un rendement futur.

Le sizing 0,4x est une calibration de risque après examen des premières tailles.
CASHCAT fournit environ 68 % du gain ; le signal, l'univers et l'horizon ont
déjà été explorés. Il faut donc vérifier la transférabilité de l'hypothèse
sur d'autres données gratuites et qualifier son exécution.

## Simulation réellement effectuée

[Protocole](PROTOCOL.md) enregistré avant sizing. **19 actifs, 1 248 heures
continues**, du 16 juillet au 6 septembre exclusif, sans reset au 7 août.
Prix et funding entièrement réutilisés ; aucune nouvelle acquisition pour le
portefeuille. Cinquante-deux candidats de signal, **33 trades exécutés dans
le modèle à 0,4x**, 19 rejets pour budget disponible ou minimum 10 $.

Signal repris de l'étude précédente : funding ancien élevé puis réduit,
continuation dans son sens, détention 72 h, espacement 73 h par actif.
Les candidats simultanés partagent le budget disponible ; plafond d'un tiers
par actif, quantités natives arrondies vers le bas. À 1 000 $, 0,4x représente
jusqu'à **400 $ de notional total à l'entrée**, environ 133 $ par actif.
Les positions peuvent ensuite dériver ; exposition observée maximale 0,434x,
cinq positions simultanées au maximum. Aucune martingale ni reprise après arrêt.

L'equity inclut le latent, chaque paiement horaire de funding, frais, slippage
et infrastructure. Les paiements déjà passés avant l'entrée sont exclus.
Entrée/exit hypothétiques open+60 s, prix open ; timestamps de funding vérifiés.
L'enveloppe utilise les hauts/bas indépendants des actifs et les positions avant
et après les transactions ; elle peut être plus sévère qu'un chemin réalisable.

Marge cross simulée avec levier de configuration fixe 2, maintenance stress
20 % du notional. Le snapshot ne comporte pas de restriction isolated pour
ces actifs et donne maxLeverage >=3. Ce stress utilise la mécanique décrite
dans la [documentation de marge](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margining.md),
mais ne reconstitue pas les marks ou liquidations natifs historiques.
Aucune violation du stress de marge pour le candidat 0,4x.

## Résultats à 0,4x

Les scénarios sont alternatifs. Tous incluent des coûts de trading, sauf le
contrôle explicite sans coût. Le budget infra est débité chaque heure et agit
aussi sur les tailles ultérieures : sa différence finale n'est pas seulement
la soustraction de 34,67 $ au résultat sans infra.

| Scénario | Net, infra marginale 0 | Net, infra 20 $/30 j | Équivalent mensuel avec infra | Enveloppe DD avec infra |
|---|---:|---:|---:|---:|
| Central, frais 4,5 / slippage 2 bps par côté | +320,41 $ | **+280,27 $** | **+15,32 %** | 17,85 % |
| Coûts renforcés, 9 / 5 bps par côté | +312,14 $ | +272,24 $ | +14,90 % | 17,85 % |
| Retard supplémentaire d'une heure | +224,85 $ | +186,15 $ | +10,35 % | 17,33 % |
| Funding systématiquement adverse | +319,66 $ | +279,63 $ | +15,29 % | 17,85 % |
| Contrôle sans coût de trading | +357,22 $ | +316,16 $ | +17,17 % | 17,84 % |

Sans infrastructure supplémentaire, l'équivalent mensuel central est **17,39 %**.
Le stress de retard reste positif, mais réduit sensiblement le gain : ne pas
présenter 15–20 % comme acquis dans tous les scénarios.

Sans infra, les périodes calendaires donnent juillet partiel +10,84 $, août
+237,80 $ (+23,52 %), septembre partiel +71,77 $. Avec infra : +0,15 $,
+213,55 $, +66,57 $. **Un seul mois complet**, pas douze mois validés.
La période maximale sous le sommet atteint **21,04 jours**. Le pire cycle
réalisé perd **51,70 $** en central sans infra. Les mois rouges restent acceptés
dans les critères ; leur absence ici ne prouve pas la stabilité future.

## Tailles initiales conservées

| Plafond initial | Net central sans infra | DD horaire | Enveloppe OHLC | Trades |
|---|---:|---:|---:|---:|
| 0,5x | +411,96 $ | 13,31 % | 20,94 % | 34 |
| 1x | +417,82 $ | 20,05 % | 32,18 % | 12 |
| 1,5x | −26,60 $ | 20,35 % | 23,44 % | 4 |

0,5x ne permet pas de certifier la limite dans l'enveloppe horaire ; 1x/1,5x
dépassent également la mesure observée et arrêtent le compte. Leurs pertes
et dépassements restent conservés. L'[adaptation à 0,4x](RISK_ADAPTATION.md)
réduit de 20 % l'exposition de 0,5x ; elle a été enregistrée avant son propre
calcul, mais **après consultation du même échantillon**. Aucune autre taille
n'a été recherchée pour approcher exactement 20 %.

## Comparaisons simples

Même plafond 0,4x, mêmes coûts, sans infra marginale :

| Règle | Net 52 jours | Équivalent mensuel | Enveloppe DD |
|---|---:|---:|---:|
| Funding 72 h | +320,41 $ | +17,39 % | 17,83 % |
| Panier conservé, 19 actifs | +201,95 $ | +11,20 % | 10,51 % |
| Panier long périodique, 72 h tous les 73 h | +127,65 $ | +7,18 % | 9,05 % |
| CASHCAT conservé, plafond par actif 0,4/3 | +192,44 $ | +10,69 % | 19,60 % |

Le signal gagne davantage dans cet échantillon, mais son risque dépasse celui
du panier diversifié. Cette comparaison ne prouve pas un alpha à risque égal.
CASHCAT seul est un diagnostic de concentration choisi après l'étude ; ce
n'est pas une stratégie indépendante validée à promouvoir.

## Concentration et incertitude

Sur les 33 trades centraux, **24 dates d'entrée distinctes**. CASHCAT apporte
+217,60 $, soit **67,91 % du gain de trading** sans infra ; les autres gains
proviennent de XMR, PUMP, LIT, FARTCOIN, JUP et INJ. Le meilleur cycle apporte
+140,86 $. Soustrait comptablement, il reste +179,55 $ sans infra, +141,20 $
avec infra. Cela ne resimule pas les allocations qui auraient suivi sa suppression.

[Audit descriptif](uncertainty.json) par blocs mobiles de 14 jours, 10 000
tirages, graine fixe : intervalle mensuel central à 95 % **[+3,78 % ; +41,24 %]**
sans infra, **[+1,90 % ; +38,72 %]** avec infra. Retard + infra :
**[−0,96 % ; +27,60 %]**. Seulement 52 jours, blocs qui se recouvrent, sélection
de stratégie et de sizing : ces intervalles ne corrigent pas les nombreuses
recherches antérieures, ne prédisent pas les prochains mois et ne rejouent pas
l'arrêt de risque dans chaque tirage.

## Qualification de l'historique antérieur et suite

Une [qualification séparée](HISTORY_QUALIFICATION.md) a demandé les bougies
CASHCAT entre le 10 mars et le 16 juillet, via **un appel natif gratuit**.
La réponse ajoute seulement **116 heures**, du **11 juillet 04:00 UTC** au
15 juillet 23:00 UTC. Aucun trou interne ; cette absence de prix plus anciens
ne prouve pas à elle seule une date de listing. Elle ne permet pas une longue
réplication CASHCAT par cette requête native.

Prochaine action : enregistrer un test antérieur de la même mécanique sur les
autres actifs, puis acquérir seulement les bougies/fundings gratuits manquants.
Ce sera une vérification de transférabilité, à distinguer d'une longue histoire
CASHCAT inexistante dans la réponse obtenue. Si la performance dépend seulement
de son épisode récent, suspendre la promotion et poursuivre une autre hypothèse.
Les propriétés d'exécution des petites positions restent également à qualifier.

Statut : [PROMISING_SHORT_SAMPLE_RESEARCH_CANDIDATE](review.json).
**Aucun GO live, aucun ordre, aucune nouvelle dépense ni modification serveur.**

## Vérification technique

**251 tests passent**, lint/format 231 fichiers, mypy 64 sources. Tests ciblés :
capital partagé, pertes latentes, gap dépassant 20 %, arrêt sans reprise,
timing exact des paiements, trous refusés et signal continu sans reset de fold.
**165 artefacts reproduits exactement**, 121 artefacts initiaux conservés
identiques après ajout de la taille 0,4x : [preuve](reproduction.json).
Les seules différences du résumé initial concernent la version de code,
le hash du script et les métadonnées explicites d'adaptation, pas les résultats.

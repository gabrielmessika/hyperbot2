# Deux mécanismes partagés : candidat plus intéressant, encore non qualifié

**Mise à jour : promotion suspendue après l'échec du transfert 2025.**
Voir [le rapport ultérieur](../prior_transfer_2026-09-07/REPORT.md).
Les résultats historiques ci-dessous sont conservés comme provenance.

Un portefeuille fixe 50/50 entre cassures avec volume et rotation hebdomadaire
gagne **538,72 $ sur 204 jours** avec un capital total de **1 000 $**, au cap
brut d'entrée 1,5x. Équivalent mensuel composé **6,54 %**, frais et funding
inclus, sans infrastructure supplémentaire. Les scénarios payants restent
positifs et sous 30 % d'enveloppe de drawdown. Cela justifie une qualification
supplémentaire, pas un GO ou une validation de +10 % mensuels.

## Pourquoi ce test

Sur les 180 jours des études individuelles, la corrélation quotidienne entre
les deux mécanismes est −0,007 au central, −0,001 sous coûts renforcés,
+0,026 avec retard et −0,009 avec funding adverse. Les deux perdent ensemble
39 à 43 jours ; faible corrélation ne signifie pas absence de pertes communes.
La corrélation avec le panier long passif est environ 0,26 pour les cassures et
0,14 pour la rotation. Le panier passif reste un contrôle, pas un composant
sélectionné pour gonfler le résultat.

Ces mesures portent sur des mécanismes sélectionnés après leurs résultats.
Les corrélations calculées seulement sur jours négatifs sont conditionnelles
et ne prouvent pas une protection des queues de distribution. Voir
`PROTOCOL.md` et `covariance.json`. Les poids 50/50 ont été fixés avant le
calcul du portefeuille, sans optimisation sur les données.

## Un seul capital, risque commun

18 actifs, panel natif déjà local du 14 février au 6 septembre exclusif,
204 jours. Les deux mécanismes utilisent chacun au plus la moitié du budget
global courant, avec leurs horizons respectifs 24 h et 168 h. Ils partagent
cash, gains/pertes, coûts et un arrêt irréversible à 30 % de drawdown, latent
inclus. Le budget inactif d'un mécanisme n'est pas prêté à l'autre.

Arrondis natifs, minimum 10 $, réserve pour frais/slippage, marge initiale à
levier de configuration 2, maintenance stress 20 % du brut conservées. Une
hausse de prix peut faire dériver le brut au-delà du cap d'entrée : maximum
observé 1,752x dans le scénario central à cap 1,5x. Pas de martingale.

Les positions des deux mécanismes sont suivies dans un registre virtuel sur
les mêmes actifs ; elles ne sont pas deux comptes dotés chacun de 1 000 $.
Chaque transaction est facturée intégralement. Le brut, la marge et les
extrêmes OHLC comptent les positions avant compensation, même opposées :
ces contraintes peuvent surestimer le risque. La conversion en transactions
nettes natives reste à qualifier avant toute exécution. Aucun gain de frais
par compensation ou fill maker gratuit n'est crédité.

## Résultats sur 204 jours

| Cap brut d'entrée | Net central, infra 0 $ | Mensuel équivalent | DD observé /enveloppe |
|---|---:|---:|---:|
| 0,5x | +163,53 $ | +2,25 % | 7,11 % /10,16 % |
| 1x | +346,46 $ | +4,47 % | 14,11 % /19,49 % |
| 1,5x | +538,72 $ | +6,54 % | 19,74 % /27,17 % |
| 2x | +698,48 $ | +8,10 % | 25,94 % /34,63 % |

Le niveau 2x ne passe pas l'enveloppe de 30 %. À 1,5x, 1 065 cycles,
contribution cassures +407,99 $, rotation +130,73 $. Le résultat vient du
compte réellement partagé ; ce n'est pas la somme de performances séparées.

| Scénario à 1,5x | Net, infra 0 $ | Mensuel équivalent | Enveloppe |
|---|---:|---:|---:|
| Central | +538,72 $ | +6,54 % | 27,17 % |
| Coûts renforcés | +236,54 $ | +3,17 % | 29,41 % |
| Retard 1 h | +378,88 $ | +4,84 % | 28,67 % |
| Funding adverse | +381,00 $ | +4,86 % | 28,45 % |
| Zéro coût de trading/funding | +854,44 $ | +9,51 % | 25,86 % |

Frais/slippage centraux 4,5/2 bps par côté ; stress 9/5 ; entrée et sortie
open+60 s aux opens supposés ; paiements timestampés et oracle horaire approché.
Les scénarios diffèrent aussi par budget disponible, arrondis et nombre de
cycles, pas seulement par une facture soustraite à la fin.

Avec 20 $/30 jours hypothétiques, débités une seule fois, le central à 1,5x
gagne +352,04 $ (4,54 % mensuel), les coûts +86,81 $, le retard +209,55 $.
Les enveloppes coûts/retard atteignent toutefois 30,38 % /30,68 %. Seul 1x
passe tous les scénarios payants avec cette infra, à 2,56 % mensuel central
et 0,29 % sous coûts renforcés. Aucune dépense n'est engagée par ces hypothèses.

## Pertes et incertitude

À 1,5x central sans infra : février −31,61 $, mars +41,71 $, avril +203,75 $,
mai +73,28 $, juin −155,33 $, juillet +214,94 $, août +212,13 $,
septembre −20,15 $. Février/septembre partiels. Juin perd 12,07 % ; ce mois
rouge est conservé et n'est pas un veto. Pire cycle −163,03 $, 75,29 jours
sous le sommet. ENA perd dans les deux mécanismes, environ −496,65 $ au total :
la faible corrélation globale n'élimine pas la concentration sur un actif.

Audit descriptif par blocs de 14 jours et 10 000 tirages : intervalle mensuel
95 % central **[−2,27 % ; +16,11 %]**, coûts **[−5,41 % ; +12,29 %]**.
Ces intervalles ne sont ni prédictifs ni corrigés pour les stratégies déjà
explorées ; le bootstrap ne rejoue pas les arrêts et allocations. Par simple
soustraction du meilleur cycle, le central reste à +377,34 $, les coûts
à +104,52 $, sans que cela constitue une nouvelle simulation.

## Décision et suite

`DIVERSIFIED_RESEARCH_CANDIDATE_UNQUALIFIED`. Le cap 1,5x sans infra constitue
une piste plus rémunératrice sous les contraintes testées. Mais la période
est déjà consultée, les prix de fill/oracle sont approximés, la compensation
native et une validation indépendante restent à établir. Aucun rendement futur
ni objectif net de 10 % démontré.

Prochaine étape : qualifier la comptabilité et le risque sur les positions
nettes natives, en gardant poids et signaux fixes. Vérifier les sources gratuites
supplémentaires avant promotion ; ne pas augmenter mécaniquement la taille ou
retirer ENA après avoir vu ses pertes.

45 artefacts reproduits exactement ; dix anciennes courbes/cycles/économies
du moteur restent identiques. 267 tests passent, dont budgets indépendants sur
cash partagé, horizons distincts, arrêt global et mapping invalide. Lint/format
268 fichiers et mypy 67 sources passent. Aucun téléchargement de marché, achat,
ordre, secret, service ou serveur modifié. Recherche active.

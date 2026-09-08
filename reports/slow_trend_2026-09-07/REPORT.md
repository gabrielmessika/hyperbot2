# Tendance lente : avantage non confirmé entre périodes

**La pondération par volatilité ne produit pas un edge robuste.** À exposition
0,5x, elle gagne 126,41 $ sur le transfert 2025, mais perd 36,42 $ sur le panel
Hyperliquid 2026 complet. Les gains du sous-panel natif sont minuscules et
disparaissent avec le funding adverse. À 1,5x, les enveloppes de drawdown
dépassent 30 %. Aucun réglage étudié ne passe le filtre entre les périodes.

## Règle effectivement testée

Chaque lundi : acheter les actifs dont le prix a monté sur 30 jours, vendre
ceux dont il a baissé, conserver les intentions 168 heures. Volatilité calculée
sur 30 rendements logarithmiques quotidiens entièrement antérieurs au signal,
poids proportionnel à son inverse avec plancher quotidien de 1 %. Contrôle
à poids égaux, mêmes signaux, dates et horizons. Aucun classement des actifs
selon leur résultat futur, aucun retrait de FARTCOIN ou ENA.

Le moteur natif réutilise sa comptabilité, ses budgets, ses lots/ticks et ses
ordres différés. Les poids restent ceux connus à la date du signal, même
pour l'entrée retardée. Cap brut fixe de 0,5x ou 1,5x, pas d'augmentation
selon les gains/pertes. Plafond par actif d'un tiers du budget ; excédent
non redistribué. Le capital est de 1 000 $ pour chaque simulation distincte.

Le warmup demande 721 bougies : première entrée le **3 février 2025** sur
Binance et le **23 mars 2026** sur Hyperliquid. Respectivement 47 et 23 dates
de paniers possibles. Les rendements mensuels équivalents utilisent toute
la période disponible, y compris le warmup et les phases sans position.
La règle ne rejoue donc pas le choc du 19 janvier ayant invalidé le candidat
précédent ; ce décalage de période active est explicitement conservé.

## Résultats à exposition 0,5x

Montants nets, sans infrastructure supplémentaire, après frais, funding et
slippage simulés. Panneaux 2026 de 204 jours ; transfert 2025 de 365 jours.

| Pondération par volatilité | Central | Coûts renforcés | Entrée retardée | Funding adverse | Zéro coût descriptif |
|---|---:|---:|---:|---:|---:|
| Hyperliquid, 18 actifs | −36,42 $ | −41,95 $ | −32,25 $ | −62,81 $ | −15,26 $ |
| Hyperliquid, sous-panel 15 | +12,09 $ | +7,04 $ | +5,72 $ | −14,81 $ | +17,51 $ |
| Binance, sous-panel 15, 2025 | +126,41 $ | +122,10 $ | +120,63 $ | +133,45 $ | +137,72 $ |

Équivalents mensuels centraux : **−0,54 %**, **+0,18 %**, **+0,98 %**.
Les enveloppes centrales sont respectivement 12,50 %, 13,25 % et 22,90 %.
Le niveau de risque est donc compatible dans ces cas, mais les gains ne sont
ni suffisamment stables entre périodes, ni proches de la cible de 10 %.

Le contrôle à poids égaux ne résout pas le problème : central −5,80 $ sur
18 actifs natifs, +0,81 $ sur 15 natifs, +148,51 $ sur 2025. Son retard 2025
est plus favorable (+273,54 $), mais ce scénario ne devient pas une nouvelle
règle choisie après résultat. La pondération par volatilité n'améliore pas
systématiquement le rendement par rapport à ce contrôle.

## Augmenter l'exposition ne crée pas l'avantage manquant

À 1,5x, la règle pondérée donne −6,51 $ sur 18 actifs natifs, +43,11 $ sur
15 natifs et +93,32 $ sur 2025. Enveloppes centrales **36,22 %**, **34,16 %**
et **32,65 %**. Les comptes natifs ne déclenchent pas nécessairement l'arrêt
sur les observations horaires, mais l'enveloppe intrahoraire reste supérieure
à 30 %. Le compte 2025 déclenche effectivement son arrêt. Dépassements et
absence de reprise sont conservés, sans troncature des pertes.

Avec l'infrastructure **hypothétique** de 20 $/30 jours, les trois résultats
centraux pondérés à 0,5x sont −182,82 $, −137,32 $ et −339,52 $. Ce coût
continue après un éventuel arrêt et modifie aussi le dimensionnement et
les dates d'arrêt ; ce n'est pas une simple soustraction à un compte inchangé.
Il ne s'agit pas d'une dépense réelle de cette recherche.

Cinq scénarios du panel natif 18, pondération par volatilité, cap 0,5x et
infra 20 $, conservent une petite position terminale impossible à clôturer
sous le minimum supposé de 10 $. Au central, 1 985 PUMP représentent 7,64 $
de notionnel et −2,75 $ de PnL latent. L'equity les inclut : aucune clôture
gratuite ou disparition de l'inventaire n'a été simulée. Les autres cas
terminent à plat ; aucun incident de marge observé sur les 120 simulations.

## Décision

**SLOW_TREND_CROSS_PERIOD_SCREEN_FAILED**. Ni la règle pondérée ni son contrôle
ne passent les quatre scénarios payants sur les trois panneaux, même avec
l'infrastructure marginale nulle. Le test est arrêté à cette conclusion,
sans recherche d'un autre horizon, plancher de volatilité ou sous-panel gagnant.
Pas de GO, pas de cible nette mensuelle de 10 % démontrée.

Les données Binance restent un test de transfert avec prix, volume et funding
Binance, sous contraintes économiques Hyperliquid de référence ; aucune
validation des fills natifs n'en découle. Les périodes ont déjà été consultées
dans d'autres recherches : ce n'est pas une validation prospective. Les prix
open+slippage à open+60 s, oracle approximé et marges simplifiées restent les
limites du moteur. Les ticks adverses sont conservés même dans le scénario
dit zéro coût. Une réussite n'aurait donc pas suffi à promouvoir en réel.

Prochaine famille à examiner : effets temporels autour des règlements de
funding, avec signaux connus avant l'événement, fenêtres horaires prédéfinies
et contrôle des heures sans règlement. Vérifier ce mécanisme sur les données
déjà présentes avant toute nouvelle acquisition ; ne pas répéter le simple
classement de portage relatif déjà rejeté sur les quatre majors.

## Livraison

120 simulations, 132 artefacts reproduits à l'identique, 30 anciennes
références complètes conservées. Six nouveaux tests de causalité, volatilité,
calendrier, plafonnement et validation des poids. Suite complète **304 tests**,
lint/format **293 fichiers**, mypy **71 sources** passent. Les sources et
configurations sont checksumées, protocole enregistré avant PnL. Aucun appel
de marché, achat, ordre réel, service ou serveur modifié. Tous les calculs
sont terminés ; recherche active.

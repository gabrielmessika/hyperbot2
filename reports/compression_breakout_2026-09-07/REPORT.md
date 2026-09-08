# Sorties de compression : hypothèse rejetée

La condition de compression ne fournit pas l'avantage recherché. À 0,5x de
notional brut maximal à l'entrée, la stratégie perd **73,39 $ sur 180 jours**,
avec 1 000 $ de capital, frais et funding inclus, sans infrastructure. Elle
perd encore **41,69 $ sans coûts de trading ni funding**. Les autres tailles
et scénarios sont également négatifs. Aucun GO.

## Expérience et risque

18 altcoins, données natives locales complètes du 10 mars au 6 septembre
2026 exclusif. Boîte de 24 heures au plus moitié de l'amplitude médiane de
sept blocs précédents, puis cassure avec volume doublé, détention 24 h,
signaux espacés de 25 h. Signal clôturé, références sans chevauchement,
aucune consultation du prix d'entrée ou des bougies futures pour le décider.
Voir `PROTOCOL.md`, enregistré avant calcul.

234 signaux de compression dans le panel ; 192 cycles réellement acceptés
à 0,5x dans le scénario central, après partage du budget et minimums natifs.
Courbe continue, prix d'exécution open+60 s supposés à l'open, arrondis,
funding timestampé et coûts. Arrêt à 20 % de drawdown observé, pas de reprise
ou d'écrêtage. Marge cross hypothétique, maintenance stress et enveloppe OHLC
conservées. Ces proxys ne constituent pas une qualification de fills réels.

| Scénario compression, 0,5x | Net sans infra | Net avec 20 $/30 j hypothétiques |
|---|---:|---:|
| Central | −73,39 $ | −195,87 $ |
| Coûts renforcés | −108,06 $ | −200,94 $ |
| Retard 1 h | −161,77 $ | −207,56 $ |
| Funding adverse | −80,85 $ | −196,91 $ |
| Zéro coût de trading/funding | −41,69 $ | −189,88 $ |

Frais/slippage centraux 4,5/2 bps par côté, stress 9/5. Les 20 $ sont une
sensibilité, aucune dépense engagée ; ils continuent après un arrêt du trading.
Le nombre de cycles varie avec les coûts, arrondis et arrêts, y compris en
zéro coût. Ne pas interpréter les scénarios comme les mêmes fills simplement
refacturés.

Drawdown central sans infra à 0,5x : **17,02 % observé /17,55 % enveloppe**,
sans arrêt. Retard : 20,11 % observé /20,55 % enveloppe, arrêt. À 1x,
central −116,45 $, drawdown observé 20,31 % /enveloppe 21,79 % ; à 1,5x,
−84,96 $, 21,53 % /22,56 %. Les dépassements sont conservés.

Pire cycle central 0,5x −20,22 $, 164,46 jours sous le sommet. Quatre périodes
calendaires négatives et trois positives, mars/septembre partiels ; rejet sur
résultat global, pas veto sur les mois rouges. WLD contribue −55,15 $, LIT
−27,41 $, INJ +24,04 $, UNI +22,47 $. Aucun actif retiré après résultat.

## Le contrôle sans compression est positif, mais ne valide pas +10 %

Le contrôle enregistré utilise la même cassure et le même volume, sans exiger
de compression. Il produit 1 593 signaux, 692 cycles centraux acceptés à 0,5x.

| Contrôle, 0,5x | Net sans infra | Mensuel composé équivalent |
|---|---:|---:|
| Central | +290,02 $ | +4,34 % |
| Coûts renforcés | +160,02 $ | +2,50 % |
| Retard 1 h | +171,80 $ | +2,68 % |
| Funding adverse | +259,97 $ | +3,93 % |
| Zéro coût de trading/funding | +428,45 $ | +6,12 % |

Sans infrastructure, les enveloppes des quatre scénarios payants vont de
15,36 % à 17,21 %. Central avec 20 $/30 jours : +150,22 $, équivalent +2,36 %
mensuel, enveloppe 17,42 % ; retard avec cette infra : +32,93 $, enveloppe
20,19 %. À 1x sans infra, le central s'arrête à 20,09 % de drawdown observé
(enveloppe 22,37 %) et termine à +69,62 $. À 1,5x : −85,07 $, arrêt.
Multiplier le résultat 0,5x pour annoncer +10 % serait injustifié.

Central 0,5x : avril +98,62 $, mai +31,31 $, juin −124,13 $, juillet +114,64 $,
août +181,89 $ ; mars/septembre partiels négatifs. Meilleurs contributeurs
ARB +86,58 $, ZEC +71,17 $, NEAR +64,94 $ ; ENA −123,90 $. Temps sous sommet
89,33 jours, pire cycle −35,70 $. Un résultat positif à approfondir si une
nouvelle étude le justifie, **pas une stratégie promue** par sélection du
meilleur contrôle. Univers courant et données déjà examinées, pas holdout.

La cible de +10 % évoquée pendant le calcul reste non démontrée. Le protocole
et les paramètres n'ont pas été modifiés après cette question. Le résultat
positif du contrôle est conservé sans cacher l'échec de l'hypothèse initiale.

## Livraison

64 artefacts reproduits exactement : 60 portefeuilles, deux listes de signaux,
qualité et résumé. Voir `reproduction.json` pour les hashes. 261 tests,
lint/format256 fichiers et mypy67 sources passent. Nouveau signal couvert
contre la fuite de données futures, absence de compression/volume et limites
temporelles ; moteurs existants réutilisés. Aucun appel de marché, achat,
ordre ou serveur modifié. Recherche active.

# Compte1 000 $ : la piste acheteuse échoue au filtre de risque entre périodes

**Aucune combinaison fixe testée ne reste positive et compatible avec sa
limite de risque sur les trois panneaux et les quatre scénarios payants.**
Le diagnostic du capital ne transforme pas les moyennes événementielles
positives en une espérance mensuelle élevée. Le filtre statistique précédent
reste également échoué ; aucune promotion ni ordre réel.

## Cadre enregistré avant les simulations

240 simulations : trois panneaux11 actifs, panier acheteur des six extrêmes
de volatilité et contrôle acheteur des onze, caps0,5/1,5x, arrêts20/30 %,
cinq scénarios de coût et infrastructure0/20 $ par30 jours. Le comparateur
et les signaux sont intégralement identiques à l'étude précédente.
[Protocole](PROTOCOL.md), [enregistrement](registration.json).

Le moteur natif existant n'est pas modifié. Il conserve une position réelle
simulée par actif, applique lots/ticks et minimum10 $, reporte les petits
ajustements, facture les ordres effectifs et le funding sur l'inventaire détenu.
Capital initial1 000 $ pour chaque simulation indépendante, arrêt irréversible,
aucune reprise ni augmentation du cap après perte. Les trois périodes ne sont
pas chaînées en une trajectoire multiannuelle de capital.

## Scénario central, limite30 %, aucune infrastructure supplémentaire

Gains après frais et funding simulés ; équivalent mensuel géométrique calculé
sur toute la durée du panneau, warmup et immobilisation après arrêt compris.

| Panneau | Cap à l'entrée | Gain net | Mensuel équivalent | DD observé | Enveloppe OHLC | Arrêt |
|---|---:|---:|---:|---:|---:|---|
| Binance2024,366 jours | 0,5x | +6,19 $ | +0,05 % | 30,18 % | 31,77 % | 5 août |
| Binance2025,365 jours | 0,5x | +180,65 $ | +1,37 % | 18,85 % | 26,91 % | Aucun |
| Hyperliquid2026,204 jours | 0,5x | +201,11 $ | +2,73 % | 13,02 % | 13,88 % | Aucun |
| Binance2024 | 1,5x | +907,10 $ | +5,43 % | 32,46 % | 35,46 % | 19 mars |
| Binance2025 | 1,5x | −273,62 $ | −2,59 % | 30,51 % | 36,71 % | 9 mars |
| Hyperliquid2026 | 1,5x | +127,97 $ | +1,79 % | 30,14 % | 33,79 % | 5 juin |

Le seuil30 % est un déclencheur d'arrêt, pas un plafond garanti de perte.
Le replay conserve les dépassements. L'enveloppe OHLC est une mesure prudente
du risque entre observations ; elle ne décrit pas des prix intrahoraires
connus avec précision. Aucune combinaison1,5x n'est compatible avec30 %.

À0,5x,2025 et2026 restent positives et sous30 % d'enveloppe dans les quatre
scénarios payants sans infra. Mais2024 échoue. Le comparateur des onze actifs
n'apporte pas de solution entre périodes : central0,5x/30 %,−36,40 $ en2024,
+44,58 $ en2025,+203,65 $ en2026. Aucun des seize groupes règle/cap/limite/infra
ne passe les douze cas requis (trois panneaux ×quatre scénarios payants).

## Pourquoi davantage de risque n'améliore pas nécessairement le gain

En2026 à1,5x, l'arrêt20 % conserve236,66 $, contre127,97 $ avec30 %.
En2024 à1,5x,20 % conserve1 185,33 $, contre907,10 $ avec30 %. Ces gains
ne valident pas20 % : les enveloppes dépassent aussi ce seuil. Un arrêt plus
large peut simplement rendre davantage de gains avant la fermeture.

À0,5x en2025, les comptes20/30 % donnent le même gain central, car le
drawdown observé reste sous20 %. L'enveloppe26,91 % empêche toutefois de
déclarer le risque20 % satisfait. Le choix30 % change cette classification,
mais ne résout pas la faiblesse du panneau2024.

Le risque de trajectoire est visible en2024 à0,5x/30 % : central+6,19 $, coûts
renforcés+555,47 $, retard+9,09 $, funding adverse−5,84 $, zéro coût+679,28 $.
Le stress de coûts ne devient pas une stratégie supérieure : ses tailles,
arrondis et ajustements suivent une autre trajectoire. Au moment où le central
franchit30 %, le stress reste autour de28,97 % observés et continue ; il profite
ensuite de la reprise. Son maximum observé29,09 % et son enveloppe30,59 % ne
passent pas le filtre30 %. L'audit indépendant réconcilie aussi ce cas.

## Coûts, petits ordres et concentration

Central0,5x/30 % :89 ordres natifs en2026,161 en2025 et108 en2024 avant arrêt.
Les frais sont respectivement2,48 /4,20 /2,92 $, et le funding13,02 /6,74 /46,89 $.
Il n'y a pas une fermeture/réouverture facturée fictivement à chaque semaine
si la position nette reste inchangée. Les tentatives trop petites sont
reportées :11 499 /26 992 /12 583 refus sous le minimum sont des tentatives
répétées, pas autant d'incidents ou de trades indépendants.

Le cap0,5x désigne le budget d'entrée. Après mouvement, le ratio brut observé
atteint environ0,568 /0,555 /0,555x. Les240 comptes terminent plats, sans
incident de marge dans le modèle. Cela ne prouve pas l'exécution réelle ni
la sécurité d'une liquidation exchange ; les oracles/marges sont approximés.

La concentration des gains persiste : août2026 apporte151,44 $ sur201,11 $
de gain central, juin perd73,23 $. En2025, octobre apporte164,79 $ sur180,65 $,
novembre perd78,64 $. Le nombre de mois gagnants2025 est cinq, contre six
perdants et janvier sans position. En2024, l'arrêt d'août empêche de bénéficier
du mouvement de fin d'année qui contribuait à la moyenne événementielle.

Avec la sensibilité **hypothétique**20 $/30 jours, le central0,5x/30 % devient
−163,77 $ en2024,−85,12 $ en2025,+42,53 $ en2026. L'infrastructure continue
après arrêt et réduit les tailles futures ; il ne faut pas simplement la
soustraire au résultat sans infra. Aucun achat ou coût de données nouveau.

## Décision et limites

Statut **VOLATILITY_CAPITAL_CROSS_PERIOD_RISK_SCREEN_FAILED**. La piste
constamment acheteuse n'atteint pas l'objectif10 % mensuel sous risque30 %,
et n'offre pas une configuration robuste parmi les tailles enregistrées.
Le résultat positif d'un panneau ne constitue pas une espérance future.

Les premières positions restent5 février2024,3 février2025 et23 mars2026.
Le choc du19 janvier2025 n'est pas exposé ici : il serait trompeur d'inférer
une robustesse sur une année entière sans ce rappel. Les données Binance
sont un transfert avec paramètres Hyperliquid de référence, pas des fills
historiques Hyperliquid. Les corrections REST2024 restent explicitement tracées.

Prochaine hypothèse : une condition de tendance collective définie à l'avance
pour décider d'être exposé ou en cash, sans retirer d'actif selon ses pertes.
Utiliser notamment2024–2025 en chronologie continue, sans remise à zéro du
warmup/capital au changement d'année, et conserver le panneau natif séparé.
Le protocole devra précéder les gains ; aucun rattrapage par levier.

## Vérifications

252 artefacts reproduits par hash exact. Le registre indépendant cash/inventaire
reconstruit chaque equity horaire, funding, frais, drawdown observé, lots/ticks,
minimums et budgets d'entrée des240 portefeuilles. L'auditeur existant a été
étendu aux panneaux2024/2025 et au cap0,5x ; les vingt audits historiques
précédents retrouvent exactement leurs résultats. Le moteur de simulation
et les signaux antérieurs restent inchangés.

325 tests complets,23 ciblés, lint/format319 fichiers et mypy75 sources passent.
[Reproduction](reproduction.json), [revue des groupes](review.json), audits
indépendants par panneau et [régression ancienne](legacy_audit_regression.json).
Tous les calculs sont terminés. Aucun nouvel appel public, achat, ordre réel,
service ou serveur modifié. Recherche active, aucune promotion autorisée.

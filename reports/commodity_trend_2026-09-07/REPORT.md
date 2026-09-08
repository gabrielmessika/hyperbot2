# Tendance sur métaux et énergie : pas d'edge retenu

**La règle perd de l'argent sur l'ensemble des 206 jours, même sans coûts.**
Les mois rouges sont acceptés conformément à la nouvelle tolérance utilisateur ;
le rejet vient du résultat global négatif. Augmenter l'exposition ne transforme
pas cette règle en candidat rentable. Aucun GO, aucun achat ni trading réel.

## Données gratuites et règle enregistrée

33 requêtes publiques natives, 3 443 523 octets de réponses, aucun credential :
4 944 bougies horaires et 4 944 paiements de funding chacun sur GOLD, SILVER
et CL. Couverture commune complète du 12 février au 6 septembre 2026 exclusif.
Zéro heure de volume nul sur les métaux, quatre sur CL : pas d'entrée sur
une bougie de volume nul, aucune imputation des prix/funding.

Le [protocole](PROTOCOL.md) a été figé avant acquisition et calcul : breakout
du canal des 240 heures précédentes, stop initial/trailing trois ATR sur 24 h,
détention maximale sept jours et délai de réentrée de 24 h. Les signaux utilisent
les bougies complètes ; le trailing calculé sur une close n'agit qu'à l'heure
suivante. Les tests vérifient cette causalité et les gaps au-delà du stop.

Capital initial 1 000 $, gains/pertes répercutés dans le sizing, risque initial
visé 1 % par position au stop théorique. Trois plafonds de notional brut à
l'ouverture : 0,5x, 1x, 1,5x de l'equity ; au plus un tiers de chaque plafond
par actif. Pas de double comptage du capital, arrondis natifs et minimum 10 $.
Aucun changement du superviseur live ; cette hausse de risque est simulée.

Les frais sont calculés par le module HIP-3 déjà audité : GOLD **9 bps** par
côté, SILVER/CL **0,9 bp**, plus 2 bps de slippage central. La
[documentation actuelle trade.xyz](https://docs.trade.xyz/perp-mechanics/fees.md)
confirme l'exclusion de l'or du growth mode et les tarifs. L'ancienne URL
`trading/fees` a été déplacée ; les anciennes publications restent conservées.
La timeline exhaustive des frais n'est pas attestée : sensibilité au snapshot.

## Résultats de portefeuille

Les montants ci-dessous sont nets de trading avec **coût marginal d'infrastructure
nul**, afin de ne pas rejeter une règle uniquement à cause des 20 $/mois
hypothétiques. Les trois tailles sont des simulations distinctes, pas des
résultats additionnables. 94 trades centraux par taille ; 97 avec signal retardé.

| Plafond brut | Central, PnL 206 j | Frais/slippage renforcés | Signal retardé 1 h | Funding adverse | Tous coûts nuls |
|---|---:|---:|---:|---:|---:|
| 0,5x | −22,95 $ | −41,29 $ | −43,79 $ | −33,00 $ | −8,41 $ |
| 1x | −52,59 $ | −86,80 $ | −79,77 $ | −69,63 $ | −24,75 $ |
| 1,5x | −56,61 $ | −103,60 $ | −84,17 $ | −77,41 $ | −16,85 $ |

L'augmentation du plafond ne multiplie pas mécaniquement les gains/pertes : le
risque au stop, les arrondis et l'equity courante limitent aussi les quantités.
Chaque scénario réexécute donc le portefeuille complet.

| Central sans infra | Drawdown horaire avec PnL latent | Enveloppe adverse OHLC | Équivalent mensuel composé |
|---|---:|---:|---:|
| 0,5x | 6,01 % | 6,66 % | −0,34 % |
| 1x | 10,21 % | 11,28 % | −0,78 % |
| 1,5x | 11,83 % | 13,06 % | −0,85 % |

Ces scénarios respectent le plafond dans la mesure disponible mais perdent de
l'argent. Chacun compte quatre périodes calendaires positives et quatre
négatives, dont février et septembre **partiels**. Ce ne sont ni huit mois
complets ni une validation sur douze mois. Le plus long temps sous le sommet
atteint environ 170,46 jours, sans récupération avant la fin.

Avec 20 $/30 jours d'infrastructure débités heure par heure, les PnL centraux
sont −158,46 $, −186,37 $ et −188,20 $. Le coût total hypothétique est 137,33 $
sur 206 jours ; il influence le sizing et les arrêts, ce n'est donc pas une
simple soustraction finale aux scénarios sans infra. Aucune dépense réelle
correspondante n'est engagée.

## Plafond de risque et limites de la simulation

Equity horaire = cash et PnL des positions ouvertes, après frais/funding et
infrastructure débités. L'arrêt est déclenché à 20 % depuis le sommet puis les
positions restantes sont fermées au prochain open. Les pertes supplémentaires
restent comptées ; aucun PnL n'est tronqué pour prétendre respecter le plafond.
Les frais d'infrastructure continuent aussi après arrêt de la stratégie.

À 1,5x avec retard et infra, le drawdown horaire atteint **25,78 %** ; ce scénario
ne respecte pas la tolérance de 20 %. Le central 1x avec infra affiche 19,67 %
aux observations horaires, mais son enveloppe OHLC atteint 20,73 % : les seules
closes ne suffisent pas à affirmer une conformité intraday.

L'enveloppe suppose les extrêmes défavorables des actifs simultanés et les
positions exposées sur la bougie entière ; elle peut surestimer la perte
réalisable. Elle n'est pas une trajectoire observée. Les stops, opens et
slippages restent des hypothèses ; ni profondeur ni mark natif ni liquidations
réelles ne sont qualifiés par ces bougies. Aucun dépassement n'est caché.

## Livraison et suite

Le client public, le loader natif, les barèmes et le modèle de bougie sont
réutilisés. Nouveau moteur avec positions immuables, réconciliation exacte
cash/PnL/frais/funding, courbes horaires et synthèses mensuelles. Tests : absence
d'accès aux bougies futures, PnL latent, sortie adverse lors d'un gap, dépassement
du plafond conservé et blocage des réentrées après arrêt.

236 tests passent, lint/format (203 fichiers) et mypy (60 sources) passent.
Les 30 scénarios, la qualité et le résumé sont reproduits exactement, voir
[preuve](reproduction.json). Raw et essais initiaux préservés, aucune configuration
serveur ni ancien dépôt modifié.

Décision : `HYPOTHESIS_NOT_CONFIRMED`. La recherche reste active et cette règle
est suspendue. La prochaine hypothèse peut utiliser ces mêmes données pour un
écart relatif or/argent, avec portefeuille couvert, plutôt qu'augmenter le
levier de la tendance perdante. Figer la règle avant son calcul et réserver une
réplication : les rendements de cette période ont maintenant été consultés.
